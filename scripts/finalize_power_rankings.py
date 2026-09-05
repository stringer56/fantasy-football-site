"""Explicitly finalize one reviewed Power Rankings export."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from . import build_power_rankings, voting_common
    from .import_power_rankings import preview_import, print_preview
    from .voting_common import active_franchises, file_fingerprint, load_import, load_preview_receipt, load_yaml, write_json
except ImportError:
    import build_power_rankings, voting_common
    from import_power_rankings import preview_import, print_preview
    from voting_common import active_franchises, file_fingerprint, load_import, load_preview_receipt, load_yaml, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Sanitized CSV or JSON export")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--deadline", help="ISO-8601 deadline")
    parser.add_argument("--published-at", required=True, help="ISO-8601 commissioner publication time")
    parser.add_argument("--allow-rejected", action="store_true")
    parser.add_argument("--override-finalized", action="store_true")
    parser.add_argument("--override-reason", help="Required audit reason with --override-finalized")
    args = parser.parse_args()

    if args.deadline is None:
        args.deadline = (load_yaml("community.yml").get("power_rankings") or {}).get("closes_at")
    if not args.deadline:
        raise SystemExit("A ranking deadline is required")
    voting_common.require_review("power-rankings", args.season, args.week, args.input, args.deadline)
    voting_common.require_lock_reached(args.deadline, args.published_at)

    payload, report = preview_import(
        load_import(args.input), season=args.season, week=args.week, deadline=args.deadline
    )
    print_preview(payload, report)
    if not payload["rankings"]:
        raise SystemExit("Nothing finalized: no valid ballots")
    if report["rejected_ballots"] and not args.allow_rejected:
        raise SystemExit("Nothing finalized: review rejected rows or pass --allow-rejected")

    snapshot_path = (
        build_power_rankings.ROOT / "_data" / "generated" / "live" /
        str(args.season) / f"week-{args.week:02d}.json"
    )
    standings_by_id = {}
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        standings_by_id = {
            row["franchise_id"]: row.get("rank")
            for row in snapshot.get("standings", [])
            if row.get("franchise_id")
        }
    final_path = build_power_rankings.persist_finalized_week(
        payload,
        override=args.override_finalized,
        standings_by_id=standings_by_id,
        published_at=args.published_at,
        override_reason=args.override_reason,
    )
    final = json.loads(final_path.read_text(encoding="utf-8"))
    final["voting"] = payload.get("voting") or {}
    write_json(build_power_rankings.OUTPUT_PATH, final)
    history = build_power_rankings.build_history(
        args.season,
        active_franchises(load_yaml("franchises.yml")),
        build_power_rankings.load_finalized_weeks(args.season),
    )
    write_json(build_power_rankings.HISTORY_OUTPUT_PATH, history)
    print(f"Finalized {final_path.relative_to(build_power_rankings.ROOT)}")


if __name__ == "__main__":
    main()
