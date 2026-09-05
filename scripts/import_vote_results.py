"""Preview sanitized general-vote responses and explicitly publish aggregates."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from . import voting_common
    from .voting_common import (
        BallotError,
        ROOT,
        file_fingerprint,
        generated_at_from_rows,
        load_import,
        load_preview_receipt,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid_report,
        write_preview_receipt,
        write_json,
    )
except ImportError:
    import voting_common
    from voting_common import (
        BallotError,
        ROOT,
        file_fingerprint,
        generated_at_from_rows,
        load_import,
        load_preview_receipt,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid_report,
        write_preview_receipt,
        write_json,
    )


OUTPUT_PATH = ROOT / "_data" / "generated" / "votes.json"
GENERAL_TYPES = {
    "league_rule", "draft_date", "scoring_change", "award", "hall_of_fame",
    "rivalry_name", "commissioner_proposal", "custom",
}


def poll_selection_report(
    poll: dict[str, Any], rows: list[dict[str, Any]], owner_ids: set[str]
) -> dict[str, Any]:
    option_ids = {item["id"] for item in poll.get("options") or []}

    def validate(row: dict[str, Any]) -> None:
        if poll.get("status") == "upcoming":
            raise BallotError("poll has not opened")
        opened = parse_deadline(poll.get("open_date"))
        if opened and voting_common.parse_timestamp(row.get("submitted_at")) < opened:
            raise BallotError("submission is before poll opens")
        if row.get("vote_id") != poll["vote_id"]:
            raise BallotError("response references another poll")
        if row.get("option_id") not in option_ids:
            raise BallotError("unknown option_id")

    selected, rejected, superseded = select_latest_valid_report(
        rows, owner_ids, validate, parse_deadline(poll.get("close_date"))
    )
    return {
        "selected": selected,
        "rejected": rejected,
        "superseded": superseded,
        "missing_owner_ids": sorted(owner_ids - {row["owner_id"] for row in selected}),
    }


def public_poll(poll: dict[str, Any]) -> dict[str, Any]:
    return {
        field: poll.get(field)
        for field in (
            "vote_id", "season", "title", "description", "type", "status",
            "open_date", "close_date", "options", "results_visibility",
            "anonymous_or_named", "form_url", "embed_url", "result_summary",
            "results_source", "notes",
        )
    }


def aggregate_poll(
    poll: dict[str, Any], rows: list[dict[str, Any]], owner_ids: set[str]
) -> tuple[dict[str, Any], int, int]:
    report = poll_selection_report(poll, rows, owner_ids)
    selected = report["selected"]
    counts = Counter(row["option_id"] for row in selected)
    ballots = len(selected)
    result_options = []
    for option in poll.get("options") or []:
        count = counts[option["id"]]
        result_options.append(
            {
                "id": option["id"],
                "label": option["label"],
                "vote_count": count,
                "percentage": round(count / ballots, 3) if ballots else 0.0,
            }
        )
    result = public_poll(poll)
    result["ballots_counted"] = ballots
    visible = poll.get("results_visibility") == "public" or (
        poll.get("results_visibility") == "after_close" and poll.get("status") == "closed"
    )
    result["results"] = result_options if visible else []
    return result, ballots, len(report["rejected"])


def build_output(
    config: dict[str, Any], owners_data: dict[str, Any], imported: dict[str, Any] | None = None,
    *, archived_polls: list[dict[str, Any]] | None = None, community: dict[str, Any] | None = None,
) -> dict[str, Any]:
    imported = imported or {}
    rows = imported.get("responses") or imported.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError("vote responses must be an array")
    owners = owner_index(owners_data)
    by_poll: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if isinstance(row, dict):
            by_poll.setdefault(str(row.get("vote_id") or ""), []).append(row)

    saved = {poll["vote_id"]: poll for poll in archived_polls or []}
    active: list[dict[str, Any]] = []
    archive: list[dict[str, Any]] = []
    accepted = rejected = superseded = 0
    for poll in config.get("polls") or []:
        if poll.get("type") in GENERAL_TYPES:
            rendered, count, invalid = aggregate_poll(poll, by_poll.get(poll["vote_id"], []), set(owners))
            accepted += count
            rejected += invalid
            superseded += len(by_poll.get(poll["vote_id"], [])) - count - invalid
        else:
            rendered = public_poll(poll)
            rendered["ballots_counted"] = 0
            rendered["results"] = []
        if poll["vote_id"] not in by_poll and poll["vote_id"] in saved:
            rendered = saved[poll["vote_id"]]
        if not rendered.get("form_url") and poll["vote_id"] not in saved:
            rendered["form_url"] = ((community or {}).get("league_votes") or {}).get("form_url")
        if poll.get("status") == "open":
            active.append(rendered)
        elif poll.get("status") == "closed":
            archive.append(rendered)

    upcoming = [public_poll(poll) | {"ballots_counted": 0, "results": []} for poll in config.get("polls") or [] if poll.get("status") == "upcoming"]
    known_poll_ids = {poll["vote_id"] for poll in config.get("polls") or []}
    rejected += sum(len(value) for key, value in by_poll.items() if key not in known_poll_ids)
    has_polls = bool(config.get("polls"))
    for poll_id, poll in saved.items():
        if poll_id not in known_poll_ids:
            archive.append(poll)
    return {
        "schema_version": 1,
        "season": imported.get("season") or 2026,
        "week": imported.get("week"),
        "generated_at": generated_at_from_rows(imported, rows),
        "source": {
            "type": "sanitized_google_forms_export" if rows else "none",
            "coverage_status": "published" if accepted or saved else ("configured" if has_polls else "unavailable"),
            "accepted_ballots": accepted,
            "rejected_ballots": rejected,
            "superseded_ballots": superseded,
            "duplicate_policy": "latest_valid_submission_before_deadline",
        },
        "active_polls": active,
        "upcoming_polls": upcoming,
        "archived_polls": archive,
    }


def load_archives(root: Path = ROOT) -> list[dict[str, Any]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted((root / "_data" / "league_votes").glob("*/*.json"))]


def persist_polls(payload: dict[str, Any], *, published_at: str, override: bool = False,
                  reason: str | None = None, poll_ids: set[str], root: Path = ROOT) -> None:
    """Finalize closed polls only; preflight every write before changing any archive."""
    pending = []
    for poll in payload["active_polls"] + payload["archived_polls"]:
        if poll["vote_id"] not in poll_ids:
            continue
        if poll.get("status") != "closed" or not poll.get("close_date"):
            raise ValueError("Close the poll with a verified deadline before finalizing")
        voting_common.require_lock_reached(poll["close_date"], published_at)
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", poll["vote_id"]):
            raise ValueError("poll ID must be a safe lowercase slug")
        path = root / "_data" / "league_votes" / str(poll["season"]) / (poll["vote_id"] + ".json")
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        normalized = {k: v for k, v in poll.items() if k not in {"audit", "published_at", "schema_version"}}
        if previous and normalized == {k: v for k, v in previous.items() if k not in {"audit", "published_at", "schema_version"}}:
            continue
        if previous and not (override and (reason or "").strip()):
            raise ValueError("refusing to overwrite archived poll; reviewed override and reason required")
        finalized = {**normalized, "schema_version": 1, "published_at": published_at,
                     "audit": list((previous or {}).get("audit") or []) + [{
                         "action": "override" if previous else "finalized", "effective_at": published_at,
                         "reason": reason if previous else None,
                         "previous_fingerprint": voting_common.audit_fingerprint(previous) if previous else None}]}
        pending.append((path, finalized))
    for path, finalized in pending:
        write_json(path, finalized)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Sanitized CSV or JSON export")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--publish", action="store_true", help="Write the reviewed public aggregate")
    parser.add_argument("--published-at", help="Actual ISO publication time; required with --publish")
    parser.add_argument("--override-finalized", action="store_true")
    parser.add_argument("--override-reason")
    args = parser.parse_args()
    imported = load_import(args.input) if args.input else None
    payload = build_output(load_yaml("votes.yml"), load_yaml("owners.yml"), imported,
                           archived_polls=load_archives(), community=load_yaml("community.yml"))
    source = payload["source"]
    print(
        f"Preview: {source['accepted_ballots']} accepted, {source['rejected_ballots']} rejected, "
        f"{source['superseded_ballots']} superseded; {len(payload['active_polls'])} polls open"
    )
    if imported:
        rows = imported.get("responses") or imported.get("rows") or []
        owners = owner_index(load_yaml("owners.yml"))
        for poll in load_yaml("votes.yml").get("polls") or []:
            poll_rows = [row for row in rows if isinstance(row, dict) and row.get("vote_id") == poll.get("vote_id")]
            if not poll_rows:
                continue
            report = poll_selection_report(poll, poll_rows, set(owners))
            print(f"{poll['vote_id']}: {len(report['selected'])} valid, {len(report['rejected'])} rejected, {len(report['superseded'])} superseded")
            for item in report["rejected"]:
                print(f"  Row {item['row']}: {item['reason']}")
            missing = [owners[owner_id]["display_name"] for owner_id in report["missing_owner_ids"]]
            print("  Missing managers: " + (", ".join(missing) or "None"))
        known_ids = {poll["vote_id"] for poll in load_yaml("votes.yml").get("polls") or []}
        unknown = [row for row in rows if isinstance(row, dict) and row.get("vote_id") not in known_ids]
        for row in unknown:
            print(f"  Unknown poll ID rejected: {row.get('vote_id')!r}")
        missing_count = sum(
            len(poll_selection_report(poll, [row for row in rows if isinstance(row, dict) and row.get("vote_id") == poll.get("vote_id")], set(owners))["missing_owner_ids"])
            for poll in load_yaml("votes.yml").get("polls") or []
            if any(isinstance(row, dict) and row.get("vote_id") == poll.get("vote_id") for row in rows)
        )
        warnings = ["rejected rows require review"] if source["rejected_ballots"] else []
        receipt = None
        if args.publish:
            voting_common.require_review("league-votes", int(imported.get("season") or 2026), None, args.input)
        else:
            receipt = write_preview_receipt(
                kind="league-votes", season=int(imported.get("season") or 2026), week=None,
                input_path=args.input, accepted=source["accepted_ballots"],
                rejected=source["rejected_ballots"], superseded=source["superseded_ballots"],
                missing=missing_count, warnings=warnings,
                context_sha256=voting_common.review_context("league-votes", int(imported.get("season") or 2026), None),
            )
        print(f"Finalization permitted: {'YES' if source['accepted_ballots'] and not source['rejected_ballots'] else 'NO'}")
        if receipt:
            print(f"Private preview receipt: {receipt.relative_to(ROOT)}")
    if not args.publish:
        print("No public files changed. Private preview receipt saved when input was provided.")
        return
    if not source["accepted_ballots"] or source["rejected_ballots"]:
        raise SystemExit("Nothing published: preview must contain accepted ballots and no rejected rows")
    if not args.published_at:
        raise SystemExit("Nothing published: --published-at is required")
    persist_polls(payload, published_at=args.published_at, override=args.override_finalized,
                  reason=args.override_reason, poll_ids={row.get("vote_id") for row in rows})
    payload = build_output(load_yaml("votes.yml"), load_yaml("owners.yml"), imported,
                           archived_polls=load_archives(), community=load_yaml("community.yml"))
    # Public views use the exact archived poll objects, including their audit trail.
    archived = {poll["vote_id"]: poll for poll in load_archives()}
    payload["archived_polls"] = [archived.get(poll["vote_id"], poll) for poll in payload["archived_polls"]]
    write_json(args.output, payload)
    print(f"Published {args.output}")


if __name__ == "__main__":
    main()
