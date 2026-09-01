"""Validate manager ballots and build deterministic weekly Power Rankings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .voting_common import (
        BallotError,
        ROOT,
        active_franchises,
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
        active_franchises,
        generated_at_from_rows,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid,
        write_json,
    )


OUTPUT_PATH = ROOT / "_data" / "generated" / "power_rankings.json"


def rows_to_ballots(imported: dict[str, Any], team_count: int) -> list[dict[str, Any]]:
    if isinstance(imported.get("ballots"), list):
        return imported["ballots"]
    ballots = []
    for row in imported.get("rows") or []:
        ballots.append(
            {
                "owner_id": row.get("owner_id"),
                "submitted_at": row.get("submitted_at"),
                "rankings": [row.get(f"rank_{rank}") for rank in range(1, team_count + 1)],
            }
        )
    return ballots


def validate_ballot(ballot: dict[str, Any], active_ids: set[str]) -> None:
    rankings = ballot.get("rankings")
    if not isinstance(rankings, list) or len(rankings) != len(active_ids):
        raise BallotError("ranking ballot must contain every active franchise")
    if any(not isinstance(item, str) for item in rankings):
        raise BallotError("ranking entries must be franchise IDs")
    if len(set(rankings)) != len(rankings):
        raise BallotError("ranking ballot contains a duplicate franchise")
    if set(rankings) != active_ids:
        raise BallotError("ranking ballot contains missing or unknown franchises")


def aggregate_rankings(
    ballots: list[dict[str, Any]],
    franchises: list[dict[str, Any]],
    owners: dict[str, dict[str, Any]],
    *,
    deadline: object = None,
    previous_rankings: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], int, int]:
    active_ids = {item["franchise_id"] for item in franchises}
    selected, rejected = select_latest_valid(
        ballots,
        set(owners),
        lambda ballot: validate_ballot(ballot, active_ids),
        parse_deadline(deadline),
    )
    previous = {item["franchise_id"]: item["rank"] for item in previous_rankings or []}
    totals = {
        item["franchise_id"]: {
            "franchise_id": item["franchise_id"],
            "display_name": item["name"],
            "path": f"/teams/{item['slug']}/",
            "identity_image": (item.get("branding") or {}).get("identity_image"),
            "total_points": 0,
            "rank_sum": 0,
            "first_place_votes": 0,
        }
        for item in franchises
    }
    team_count = len(franchises)
    for ballot in selected:
        for rank, franchise_id in enumerate(ballot["rankings"], start=1):
            totals[franchise_id]["total_points"] += team_count - rank + 1
            totals[franchise_id]["rank_sum"] += rank
            totals[franchise_id]["first_place_votes"] += int(rank == 1)
    entries = []
    for item in totals.values():
        item["average_rank"] = round(item.pop("rank_sum") / len(selected), 3) if selected else None
        item["ballots_counted"] = len(selected)
        entries.append(item)
    if selected:
        entries.sort(
            key=lambda item: (
                -item["total_points"],
                -item["first_place_votes"],
                item["average_rank"],
                item["franchise_id"],
            )
        )
        for rank, item in enumerate(entries, start=1):
            item["rank"] = rank
            item["movement"] = previous.get(item["franchise_id"], rank) - rank if previous else None
    else:
        entries = []
    return entries, len(selected), rejected


def build_output(
    imported: dict[str, Any] | None,
    franchises_data: dict[str, Any],
    owners_data: dict[str, Any],
    *,
    deadline: object = None,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    imported = imported or {}
    franchises = active_franchises(franchises_data)
    owners = owner_index(owners_data)
    ballots = rows_to_ballots(imported, len(franchises))
    rankings, accepted, rejected = aggregate_rankings(
        ballots,
        franchises,
        owners,
        deadline=deadline,
        previous_rankings=(previous or {}).get("rankings") or [],
    )
    return {
        "schema_version": 1,
        "season": int(imported.get("season") or 2026),
        "week": int(imported["week"]) if imported.get("week") not in (None, "") else None,
        "generated_at": generated_at_from_rows(imported, ballots),
        "source": {
            "type": "sanitized_google_forms_export" if ballots else "none",
            "coverage_status": "complete" if accepted == len(owners) and accepted else ("partial" if accepted else "unavailable"),
            "accepted_ballots": accepted,
            "rejected_ballots": rejected,
            "superseded_ballots": len(ballots) - accepted - rejected,
            "duplicate_policy": "latest_valid_submission_before_deadline",
            "ranking_input": "manager_ballots_only",
        },
        "scoring": {
            "team_count": len(franchises),
            "first_place_points": len(franchises),
            "last_place_points": 1,
            "tie_breakers": ["total_points", "first_place_votes", "average_rank", "franchise_id"],
        },
        "ballots_counted": accepted,
        "rankings": rankings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Sanitized CSV or JSON export")
    parser.add_argument("--previous", type=Path, help="Previous generated ranking JSON")
    parser.add_argument("--deadline", help="ISO-8601 voting deadline override")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    imported = load_import(args.input) if args.input else None
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    payload = build_output(imported, load_yaml("franchises.yml"), load_yaml("owners.yml"), deadline=args.deadline, previous=previous)
    write_json(args.output, payload)
    print(f"Wrote {args.output}: {payload['ballots_counted']} accepted manager ballots")


if __name__ == "__main__":
    main()
