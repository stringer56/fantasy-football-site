"""Import sanitized general-vote responses and publish aggregate poll results."""

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
        select_latest_valid,
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
        select_latest_valid,
        write_json,
    )


OUTPUT_PATH = ROOT / "_data" / "generated" / "votes.json"
GENERAL_TYPES = {"league_rule", "award", "custom"}


def public_poll(poll: dict[str, Any]) -> dict[str, Any]:
    return {
        field: poll.get(field)
        for field in (
            "id", "season", "week", "title", "description", "type", "status",
            "opens_at", "closes_at", "options", "submission_url", "results_status",
            "results_source", "notes",
        )
    }


def aggregate_poll(
    poll: dict[str, Any], rows: list[dict[str, Any]], owner_ids: set[str]
) -> tuple[dict[str, Any], int, int]:
    option_ids = {item["id"] for item in poll.get("options") or []}

    def validate(row: dict[str, Any]) -> None:
        if row.get("poll_id") != poll["id"]:
            raise BallotError("response references another poll")
        if row.get("option_id") not in option_ids:
            raise BallotError("unknown option_id")

    selected, rejected = select_latest_valid(
        rows, owner_ids, validate, parse_deadline(poll.get("closes_at"))
    )
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
    result["results"] = result_options if poll.get("results_status") in {"provisional", "final"} else []
    return result, ballots, rejected


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
            by_poll.setdefault(str(row.get("poll_id") or ""), []).append(row)

    active: list[dict[str, Any]] = []
    archive: list[dict[str, Any]] = []
    accepted = rejected = superseded = 0
    for poll in config.get("polls") or []:
        if poll.get("type") in GENERAL_TYPES:
            rendered, count, invalid = aggregate_poll(poll, by_poll.get(poll["id"], []), set(owners))
            accepted += count
            rejected += invalid
            superseded += len(by_poll.get(poll["id"], [])) - count - invalid
        else:
            rendered = public_poll(poll)
            rendered["ballots_counted"] = 0
            rendered["results"] = []
        (archive if poll.get("status") == "archived" else active).append(rendered)

    known_poll_ids = {poll["id"] for poll in config.get("polls") or []}
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
        "archived_polls": archive,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Sanitized CSV or JSON export")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    imported = load_import(args.input) if args.input else None
    payload = build_output(load_yaml("votes.yml"), load_yaml("owners.yml"), imported)
    write_json(args.output, payload)
    print(
        f"Wrote {args.output}: {len(payload['active_polls'])} active/configured polls, "
        f"{payload['source']['accepted_ballots']} accepted ballots"
    )


if __name__ == "__main__":
    main()
