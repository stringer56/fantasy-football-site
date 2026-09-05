"""Lock or score one reviewed Pick'em week and rebuild its public archive."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from . import build_picks_leaderboard
    from .import_pickem import load_current_sources, preview_import, print_preview
    from .voting_common import file_fingerprint, load_import, load_preview_receipt, load_yaml, owner_index, write_json
except ImportError:
    import build_picks_leaderboard
    from import_pickem import load_current_sources, preview_import, print_preview
    from voting_common import file_fingerprint, load_import, load_preview_receipt, load_yaml, owner_index, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--lock-at", required=True, help="ISO-8601 weekly lock time")
    parser.add_argument("--published-at", required=True, help="ISO-8601 commissioner publication time")
    parser.add_argument("--allow-rejected", action="store_true")
    parser.add_argument("--publish-manager-picks", action="store_true")
    parser.add_argument("--hide-aggregates", action="store_true")
    parser.add_argument("--override-finalized", action="store_true")
    parser.add_argument("--override-reason", help="Required audit reason with --override-finalized")
    args = parser.parse_args()

    receipt = load_preview_receipt("pickem", args.season, args.week)
    if not receipt or receipt.get("input_sha256") != file_fingerprint(args.input):
        raise SystemExit("Nothing finalized: run the preview command for this exact import first")

    imported = load_import(args.input)
    preview, report = preview_import(
        imported, season=args.season, week=args.week, deadline=args.lock_at
    )
    print_preview(preview, report)
    if not report["valid_ballots"]:
        raise SystemExit("Nothing finalized: no valid Pick'em submissions")
    if report["rejected_ballots"] and not args.allow_rejected:
        raise SystemExit("Nothing finalized: review rejected rows or pass --allow-rejected")

    finalized_import = {
        "season": args.season,
        "week": args.week,
        "closes_at": args.lock_at,
        "results_visible": not args.hide_aggregates,
        "publish_manager_picks": args.publish_manager_picks,
        "ballots": report["_selected_ballots"],
    }
    matchups_data, manifest = load_current_sources()
    payload = build_picks_leaderboard.build_output(
        finalized_import,
        matchups_data,
        manifest,
        load_yaml("site.yml"),
        load_yaml("franchises.yml"),
        load_yaml("owners.yml"),
        deadline=args.lock_at,
        community_data=load_yaml("community.yml"),
    )
    current = payload.get("current_week") or {}
    state = (
        "final"
        if current.get("matchups")
        and all(item.get("winner_status") in {"verified", "no_contest"} for item in current["matchups"])
        else "locked"
    )
    current["state"] = state
    current["lock_at"] = args.lock_at
    current["results_visibility"] = "hidden" if args.hide_aggregates else "public_after_lock"
    current["manager_picks_visibility"] = "public" if args.publish_manager_picks else "private"
    week_payload = build_picks_leaderboard.finalized_week_payload(
        payload, generated_at=args.published_at, state=state
    )
    path = build_picks_leaderboard.persist_finalized_week(
        week_payload, override=args.override_finalized, override_reason=args.override_reason
    )
    week_payload = next(
        item for item in build_picks_leaderboard.load_finalized_weeks(args.season)
        if item["week"] == args.week
    )
    archive = build_picks_leaderboard.load_finalized_weeks(args.season)
    owners = owner_index(load_yaml("owners.yml"))
    payload["current_week"] = week_payload
    payload["weekly_results"] = archive
    payload["leaderboard"] = build_picks_leaderboard.build_leaderboard(archive, owners)
    payload["source"]["coverage_status"] = state
    write_json(build_picks_leaderboard.OUTPUT_PATH, payload)
    print(f"{state.title()} {path.relative_to(build_picks_leaderboard.ROOT)}")


if __name__ == "__main__":
    main()
