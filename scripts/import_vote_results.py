"""Preview sanitized general-vote responses and explicitly publish aggregates."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .voting_common import (
        BallotError,
        ROOT,
        generated_at_from_rows,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid_report,
        write_json,
    )
except ImportError:
    from voting_common import (
        BallotError,
        ROOT,
        generated_at_from_rows,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid_report,
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
    config: dict[str, Any], owners_data: dict[str, Any], imported: dict[str, Any] | None = None
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
        if poll.get("status") == "open":
            active.append(rendered)
        elif poll.get("status") == "closed":
            archive.append(rendered)

    upcoming = [public_poll(poll) | {"ballots_counted": 0, "results": []} for poll in config.get("polls") or [] if poll.get("status") == "upcoming"]
    known_poll_ids = {poll["vote_id"] for poll in config.get("polls") or []}
    rejected += sum(len(value) for key, value in by_poll.items() if key not in known_poll_ids)
    has_polls = bool(config.get("polls"))
    return {
        "schema_version": 1,
        "season": imported.get("season") or 2026,
        "week": imported.get("week"),
        "generated_at": generated_at_from_rows(imported, rows),
        "source": {
            "type": "sanitized_google_forms_export" if rows else "none",
            "coverage_status": "published" if accepted else ("configured" if has_polls else "unavailable"),
            "accepted_ballots": accepted,
            "rejected_ballots": rejected,
            "superseded_ballots": superseded,
            "duplicate_policy": "latest_valid_submission_before_deadline",
        },
        "active_polls": active,
        "upcoming_polls": upcoming,
        "archived_polls": archive,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Sanitized CSV or JSON export")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--publish", action="store_true", help="Write the reviewed public aggregate")
    args = parser.parse_args()
    imported = load_import(args.input) if args.input else None
    payload = build_output(load_yaml("votes.yml"), load_yaml("owners.yml"), imported)
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
    if not args.publish:
        print("No files changed. Re-run with --publish after reviewing this summary.")
        return
    write_json(args.output, payload)
    print(f"Published {args.output}")


if __name__ == "__main__":
    main()
