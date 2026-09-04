"""Report the commissioner-facing state of one 2026 community week."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int, required=True)
    args = parser.parse_args()

    community = yaml.safe_load((ROOT / "_data" / "community.yml").read_text(encoding="utf-8")) or {}
    votes = yaml.safe_load((ROOT / "_data" / "votes.yml").read_text(encoding="utf-8")) or {}
    power_path = ROOT / "_data" / "power_rankings" / str(args.season) / f"week-{args.week:02d}.json"
    picks_path = ROOT / "_data" / "picks" / str(args.season) / f"week-{args.week:02d}.json"
    matchups = load_json(ROOT / "_data" / "generated" / "matchups.json")
    yahoo_week = matchups.get("week")
    yahoo_label = "current" if yahoo_week == args.week else f"week {yahoo_week or 'unavailable'}"

    print(f"COMMUNITY WEEK · {args.season} WEEK {args.week}")
    print(f"Yahoo matchup snapshot: {yahoo_label}")
    print(f"Power Rankings: {'finalized' if power_path.exists() else (community.get('power_rankings') or {}).get('status', 'unconfigured')}")
    if power_path.exists():
        power = load_json(power_path)
        print(f"  ballots: {power.get('ballots_counted', 0)} · published: {power.get('published_at') or 'unknown'}")
    print(f"Pick’em: {load_json(picks_path).get('state') if picks_path.exists() else (community.get('pickem') or {}).get('status', 'unconfigured')}")
    if picks_path.exists():
        picks = load_json(picks_path)
        print(f"  ballots: {picks.get('ballots_counted', 0)} · lock: {picks.get('lock_at') or 'unknown'}")
    active = [poll for poll in votes.get("polls") or [] if poll.get("status") == "open"]
    print(f"League polls open: {len(active)}")
    for poll in active:
        print(f"  {poll['vote_id']}: {poll['title']} (closes {poll.get('close_date') or 'unspecified'})")


if __name__ == "__main__":
    main()
