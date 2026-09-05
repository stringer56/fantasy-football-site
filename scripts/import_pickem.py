"""Preview a sanitized weekly Pick'em export without publishing it."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from . import build_picks_leaderboard
    from .voting_common import (
        BallotError,
        ROOT,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid_report,
        write_preview_receipt,
    )
except ImportError:
    import build_picks_leaderboard
    from voting_common import (
        BallotError,
        ROOT,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid_report,
        write_preview_receipt,
    )


def load_current_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    generated = ROOT / "_data" / "generated"
    return (
        json.loads((generated / "matchups.json").read_text(encoding="utf-8")),
        json.loads((generated / "manifest.json").read_text(encoding="utf-8")),
    )


def preview_import(
    imported: dict[str, Any], *, season: int, week: int, deadline: object = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    matchups_data, manifest = load_current_sources()
    franchises_data = load_yaml("franchises.yml")
    owners_data = load_yaml("owners.yml")
    community_data = load_yaml("community.yml")
    owners = owner_index(owners_data)
    matchups, status = build_picks_leaderboard.canonical_matchups_from_yahoo(
        matchups_data, manifest, season, franchises_data
    )
    if status != "ready" or not matchups:
        raise ValueError(f"canonical Yahoo matchups are unavailable: {status}")
    if matchups[0]["week"] != week:
        raise ValueError(
            f"requested Week {week} does not match current Yahoo Week {matchups[0]['week']}"
        )
    ballots = build_picks_leaderboard.rows_to_ballots(
        imported, {item["matchup_id"] for item in matchups}
    )
    matchup_by_id = {item["matchup_id"]: item for item in matchups}

    def validate(ballot: dict[str, Any]) -> None:
        if ballot.get("week") in (None, ""):
            raise BallotError("week is required")
        try:
            submitted_week = int(ballot["week"])
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
        build_picks_leaderboard.validate_pick_ballot(ballot, matchup_by_id)

    selected, rejected, superseded = select_latest_valid_report(
        ballots, set(owners), validate, parse_deadline(deadline)
    )
    normalized = {
        "season": season,
        "week": week,
        "ballots": selected,
        "closes_at": deadline,
        "results_visible": False,
        "publish_manager_picks": False,
        "state": "preview",
    }
    payload = build_picks_leaderboard.build_output(
        normalized,
        matchups_data,
        manifest,
        load_yaml("site.yml"),
        franchises_data,
        owners_data,
        deadline=deadline,
        community_data=community_data,
    )
    payload["source"]["rejected_ballots"] = len(rejected)
    payload["source"]["superseded_ballots"] = len(superseded)
    report = {
        "submitted_ballots": len(ballots),
        "valid_ballots": len(selected),
        "rejected_ballots": rejected,
        "superseded_ballots": superseded,
        "missing_managers": [
            owners[owner_id]["display_name"]
            for owner_id in sorted(set(owners) - {row["owner_id"] for row in selected})
        ],
        "matchups": matchups,
        "_selected_ballots": selected,
    }
    return payload, report


def print_preview(payload: dict[str, Any], report: dict[str, Any]) -> None:
    print(f"PICK'EM · {payload['season']} WEEK {payload['week']}")
    print(f"Yahoo matchups: {len(report['matchups'])}")
    print(f"Valid submissions: {report['valid_ballots']}")
    print(f"Rejected submissions: {len(report['rejected_ballots'])}")
    for item in report["rejected_ballots"]:
        print(f"  Row {item['row']}: {item['reason']}")
    print(f"Superseded duplicates: {len(report['superseded_ballots'])}")
    print("Missing managers: " + (", ".join(report["missing_managers"]) or "None"))
    warnings = []
    if report["missing_managers"]:
        warnings.append("manager participation is incomplete")
    if report["rejected_ballots"]:
        warnings.append("rejected rows require review")
    print("Validation warnings: " + ("; ".join(warnings) or "None"))
    print(f"Finalization permitted: {'YES' if report['valid_ballots'] and not report['rejected_ballots'] else 'NO'}")
    print("\nPrivate aggregate preview:")
    for matchup in report["matchups"]:
        totals = []
        for participant in matchup["participants"]:
            count = sum(
                pick["franchise_id"] == participant["franchise_id"]
                for ballot in report["_selected_ballots"]
                for pick in ballot["picks"]
                if pick["matchup_id"] == matchup["matchup_id"]
            )
            totals.append(f"{participant['display_name']}: {count}")
        print(f"  {matchup['matchup_id']}: " + " · ".join(totals))
    print("\nRequired Google Form response columns:")
    print("  owner_id, submitted_at, season, week")
    for matchup in report["matchups"]:
        names = " / ".join(item["display_name"] for item in matchup["participants"])
        print(f"  {matchup['matchup_id']} ({names})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Sanitized CSV or JSON export")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--deadline", help="ISO-8601 weekly lock time")
    args = parser.parse_args()
    payload, report = preview_import(
        load_import(args.input), season=args.season, week=args.week, deadline=args.deadline
    )
    print_preview(payload, report)
    warnings = []
    if report["missing_managers"]:
        warnings.append("manager participation is incomplete")
    if report["rejected_ballots"]:
        warnings.append("rejected rows require review")
    receipt = write_preview_receipt(
        kind="pickem", season=args.season, week=args.week,
        input_path=args.input, accepted=report["valid_ballots"],
        rejected=len(report["rejected_ballots"]),
        superseded=len(report["superseded_ballots"]),
        missing=len(report["missing_managers"]), warnings=warnings,
    )
    print(f"Private preview receipt: {receipt.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
