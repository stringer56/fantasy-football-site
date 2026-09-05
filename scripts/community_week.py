"""Report privacy-safe commissioner readiness for one community week."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    from .voting_common import file_fingerprint, review_context, parse_deadline
except ImportError:
    from voting_common import file_fingerprint, review_context, parse_deadline


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def default_import(root: Path, kind: str, week: int) -> Path:
    stem = {"power-rankings": "power", "pickem": "picks", "league-votes": "votes"}[kind]
    for suffix in ("csv", "json"):
        candidate = root / "private-vote-imports" / f"{stem}-week-{week:02d}.{suffix}"
        if candidate.exists():
            return candidate
    return root / "private-vote-imports" / f"{stem}-week-{week:02d}.csv"


def receipt_path(root: Path, kind: str, season: int, week: int | None) -> Path:
    suffix = f"week-{week:02d}" if isinstance(week, int) else "general"
    return root / "private-vote-imports" / ".community-state" / f"{season}-{suffix}-{kind}.json"


def preview_state(root: Path, kind: str, season: int, week: int, input_path: Path) -> dict[str, Any]:
    pending = input_path.exists()
    path = receipt_path(root, kind, season, week if kind != "league-votes" else None)
    receipt = load_json(path)
    current = bool(pending and receipt and receipt.get("input_sha256") == file_fingerprint(input_path))
    current = current and receipt.get("context_sha256") == review_context(kind, season, week if kind != "league-votes" else None, receipt.get("deadline"), root=root)
    return {
        "pending_import": pending,
        "preview_generated": current,
        "finalization_permitted": bool(current and receipt.get("finalization_permitted")),
        "review_required": bool(current and receipt.get("review_required")),
        "reviewed_deadline": receipt.get("deadline") if current else None,
    }


def build_status(
    *, root: Path = ROOT, season: int = 2026, week: int | None = None,
    power_input: Path | None = None, picks_input: Path | None = None,
    votes_input: Path | None = None, now: datetime | None = None,
) -> dict[str, Any]:
    community = load_yaml(root / "_data" / "community.yml")
    current_time = now or datetime.now(timezone.utc)
    votes = load_yaml(root / "_data" / "votes.yml")
    matchups = load_json(root / "_data" / "generated" / "matchups.json")
    manifest = load_json(root / "_data" / "generated" / "manifest.json")
    current_week = matchups.get("week")
    selected_week = week or (int(current_week) if current_week else 1)
    paths = {
        "power-rankings": power_input or default_import(root, "power-rankings", selected_week),
        "pickem": picks_input or default_import(root, "pickem", selected_week),
        "league-votes": votes_input or default_import(root, "league-votes", selected_week),
    }
    power_archive = root / "_data" / "power_rankings" / str(season) / f"week-{selected_week:02d}.json"
    picks_archive = root / "_data" / "picks" / str(season) / f"week-{selected_week:02d}.json"
    archives = {"power-rankings": load_json(power_archive), "pickem": load_json(picks_archive), "league-votes": {}}
    open_polls = [poll for poll in votes.get("polls") or [] if poll.get("status") == "open"]
    features = {}
    for kind, section in (
        ("power-rankings", community.get("power_rankings") or {}),
        ("pickem", community.get("pickem") or {}),
        ("league-votes", community.get("league_votes") or {}),
    ):
        archive = archives[kind]
        preview = preview_state(root, kind, season, selected_week, paths[kind])
        deadline = section.get("lock_at") if kind == "pickem" else (section.get("closes_at") or preview.get("reviewed_deadline"))
        lock = parse_deadline(deadline)
        reasons = []
        if kind != "league-votes" and (lock is None or current_time < lock):
            reasons.append("deadline missing or not reached")
        if kind == "pickem" and (manifest.get("status") != "ready" or manifest.get("season") != season or current_week != selected_week):
            reasons.append("verified Yahoo slate for requested week unavailable")
        if kind == "pickem" and section.get("lock_week") != selected_week:
            reasons.append("canonical lock week does not match")
        if kind == "league-votes":
            closed = [poll for poll in votes.get("polls", []) if poll.get("season") == season and poll.get("status") == "closed" and parse_deadline(poll.get("close_date")) and parse_deadline(poll.get("close_date")) <= current_time]
            if not closed:
                reasons.append("no closed poll ready to finalize")
        if reasons:
            preview["finalization_permitted"] = False
        state = archive.get("state") or ("finalized" if archive else section.get("status") or "unconfigured")
        if state == "final":
            state = "finalized"
        if kind == "power-rankings" and archive:
            preview["finalization_permitted"] = False
        if kind == "pickem" and archive.get("state") == "final":
            preview["finalization_permitted"] = False
        features[kind] = {
            "state": state,
            "form_configured": bool(section.get("form_url")),
            "archive_status": archive.get("state") or ("finalized" if archive else "not archived"),
            "lock_configured": bool(lock),
            "lock_at": deadline,
            "readiness_notes": reasons,
            **preview,
        }
    general_archives = list((root / "_data" / "league_votes" / str(season)).glob("*.json"))
    features["league-votes"]["archive_status"] = f"{len(general_archives)} finalized polls"
    updated = parse_deadline(manifest.get("source_update_timestamp"))
    snapshot_usable = manifest.get("status") == "ready" and manifest.get("season") == season
    fresh = bool(updated and 0 <= (current_time - updated).total_seconds() <= 12 * 3600)
    return {
        "season": season,
        "week": selected_week,
        "current_yahoo_week": current_week,
        "yahoo": {
            "status": "current" if snapshot_usable and fresh else ("stale" if snapshot_usable else "unavailable"),
            "source_updated_at": manifest.get("source_update_timestamp"),
            "snapshot_week": current_week,
        },
        "features": features,
        "active_votes": [{"vote_id": poll["vote_id"], "title": poll["title"], "close_date": poll.get("close_date")} for poll in open_polls],
    }


def print_status(status: dict[str, Any]) -> None:
    print(f"COMMUNITY WEEK · {status['season']} WEEK {status['week']}")
    yahoo = status["yahoo"]
    print(f"Yahoo: {yahoo['status']} · snapshot week {yahoo['snapshot_week'] or 'unavailable'} · updated {yahoo['source_updated_at'] or 'unavailable'}")
    labels = {"power-rankings": "Power Rankings", "pickem": "Pick’em", "league-votes": "League Votes"}
    for key, label in labels.items():
        item = status["features"][key]
        permission = "YES" if item["finalization_permitted"] else ("REVIEW REQUIRED" if item["review_required"] else "NO")
        print(f"{label}: {str(item['state']).upper()}")
        print(f"  Form configured: {'YES' if item['form_configured'] else 'NO'}")
        print(f"  Pending import: {'YES' if item['pending_import'] else 'NO'}")
        print(f"  Current preview receipt: {'YES' if item['preview_generated'] else 'NO'}")
        print(f"  Finalization permitted: {permission}")
        print(f"  Archive: {item['archive_status']}")
        if key != "league-votes":
            print(f"  Lock/deadline configured: {'YES' if item['lock_configured'] else 'NO'} · {item['lock_at'] or 'TBA'}")
        for reason in item["readiness_notes"]:
            print(f"  Not ready: {reason}")
    print(f"Active league votes: {len(status['active_votes'])}")
    for poll in status["active_votes"]:
        print(f"  {poll['vote_id']}: {poll['title']} (closes {poll['close_date'] or 'unspecified'})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int, help="Defaults to current Yahoo week")
    parser.add_argument("--power-input", type=Path)
    parser.add_argument("--picks-input", type=Path)
    parser.add_argument("--votes-input", type=Path)
    args = parser.parse_args()
    print_status(build_status(season=args.season, week=args.week, power_input=args.power_input, picks_input=args.picks_input, votes_input=args.votes_input))


if __name__ == "__main__":
    main()
