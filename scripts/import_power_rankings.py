"""Preview a sanitized Google Forms Power Rankings export without publishing it."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from . import build_power_rankings
    from .voting_common import (
        BallotError,
        active_franchises,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid_report,
    )
except ImportError:
    import build_power_rankings
    from voting_common import (
        BallotError,
        active_franchises,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid_report,
    )


def preview_import(
    imported: dict[str, Any], *, season: int, week: int, deadline: object = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    franchises_data = load_yaml("franchises.yml")
    owners_data = load_yaml("owners.yml")
    franchises = active_franchises(franchises_data)
    owners = owner_index(owners_data)
    active_ids = {item["franchise_id"] for item in franchises}
    ballots = build_power_rankings.rows_to_ballots(imported, len(franchises))

    def validate(ballot: dict[str, Any]) -> None:
        raw_week = ballot.get("week")
        if raw_week in (None, ""):
            raise BallotError("week is required")
        try:
            submitted_week = int(raw_week)
        except (TypeError, ValueError) as error:
            raise BallotError("week must be an integer") from error
        if submitted_week != week:
            raise BallotError("submission references another week")
        if ballot.get("season") not in (None, ""):
            try:
                submitted_season = int(ballot["season"])
            except (TypeError, ValueError) as error:
                raise BallotError("season must be an integer") from error
            if submitted_season != season:
                raise BallotError("submission references another season")
        build_power_rankings.validate_ballot(ballot, active_ids)

    selected, rejected, superseded = select_latest_valid_report(
        ballots, set(owners), validate, parse_deadline(deadline)
    )
    normalized = {
        "season": season,
        "week": week,
        "ballots": selected,
    }
    payload = build_power_rankings.build_output(
        normalized,
        franchises_data,
        owners_data,
        deadline=deadline,
        previous=build_power_rankings.previous_finalized(season, week),
        community_data=load_yaml("community.yml"),
    )
    missing = [
        owners[owner_id]["display_name"]
        for owner_id in sorted(set(owners) - {row["owner_id"] for row in selected})
    ]
    report = {
        "submitted_ballots": len(ballots),
        "valid_ballots": len(selected),
        "rejected_ballots": rejected,
        "superseded_ballots": superseded,
        "missing_managers": missing,
    }
    payload["source"]["rejected_ballots"] = len(rejected)
    payload["source"]["superseded_ballots"] = len(superseded)
    return payload, report


def print_preview(payload: dict[str, Any], report: dict[str, Any]) -> None:
    print(f"POWER RANKINGS · {payload['season']} WEEK {payload['week']}")
    print(f"Valid ballots: {report['valid_ballots']}")
    print(f"Rejected ballots: {len(report['rejected_ballots'])}")
    for item in report["rejected_ballots"]:
        print(f"  Row {item['row']}: {item['reason']}")
    print(f"Superseded duplicates: {len(report['superseded_ballots'])}")
    print("Missing managers: " + (", ".join(report["missing_managers"]) or "None"))
    print("\nPreview ranking:")
    for row in payload["rankings"]:
        tied = "T-" if sum(item["rank"] == row["rank"] for item in payload["rankings"]) > 1 else ""
        print(
            f"  {tied}{row['rank']}. {row['display_name']} — "
            f"{row['ranking_points']} pts, avg {row['average_rank']}, "
            f"{row['first_place_votes']} first-place"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Sanitized CSV or JSON export")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--deadline", help="ISO-8601 deadline")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, report = preview_import(
        load_import(args.input), season=args.season, week=args.week, deadline=args.deadline
    )
    print_preview(payload, report)


if __name__ == "__main__":
    main()
