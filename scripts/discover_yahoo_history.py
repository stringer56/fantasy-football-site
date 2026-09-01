"""Discover Road to Glory Yahoo renewal history without publishing raw responses."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from pull_yahoo import refresh_access_token
from yahoo_history import (
    SCHEMA_VERSION,
    YahooHistoryClient,
    build_committed_manifest,
    classify_discovery,
    extract_games,
    extract_leagues,
    load_yaml,
    write_json_if_changed,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data"
DEFAULT_OUTPUT = DATA / "generated" / "yahoo_history_manifest.json"


def required_environment() -> dict[str, str]:
    names = ("YAHOO_CLIENT_ID", "YAHOO_CLIENT_SECRET", "YAHOO_REFRESH_TOKEN", "LEAGUE_KEY")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    return {name: os.environ[name] for name in names}


def public_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "season": row.get("season"),
        "game_key": row.get("game_key"),
        "league_key": row.get("league_key"),
        "league_id": row.get("league_id"),
        "league_name": row.get("league_name"),
        "number_of_teams": row.get("number_of_teams"),
        "previous_league_key": row.get("previous_league_key"),
        "next_league_key": row.get("next_league_key"),
        "name_matches": row.get("name_matches"),
        "renewal_link_matches": row.get("renewal_link_matches"),
    }


def discover_live(
    *,
    start_season: int,
    end_season: int,
    request_delay: float,
) -> dict[str, Any]:
    environment = required_environment()
    token = refresh_access_token(
        environment["YAHOO_CLIENT_ID"],
        environment["YAHOO_CLIENT_SECRET"],
        environment["YAHOO_REFRESH_TOKEN"],
    )
    client = YahooHistoryClient(token, request_delay=request_delay)
    canonical_data = load_yaml(DATA / "yahoo_leagues.yml")
    canonical = canonical_data["leagues"]

    games_payload = client.get_json("users;use_login=1/games;game_codes=nfl")
    games = [
        row for row in extract_games(games_payload)
        if row.get("season") is not None and start_season <= row["season"] <= end_season
    ]
    game_keys = [row["game_key"] for row in games]
    discovered: dict[str, dict[str, Any]] = {}
    for offset in range(0, len(game_keys), 10):
        keys = ",".join(game_keys[offset:offset + 10])
        payload = client.get_json(f"users;use_login=1/games;game_keys={keys}/leagues")
        for row in extract_leagues(payload):
            discovered[row["league_key"]] = row

    queue = [row["league_key"] for row in canonical if row.get("verified")]
    queue.append(environment["LEAGUE_KEY"])
    visited: set[str] = set()
    while queue and len(visited) < 30:
        key = queue.pop(0)
        if not key or key in visited:
            continue
        visited.add(key)
        try:
            payload = client.get_json(f"league/{key}")
        except Exception as error:  # the report records the omission; it never stores a response
            print(f"warning: Yahoo league metadata unavailable for configured candidate: {type(error).__name__}")
            continue
        for row in extract_leagues(payload):
            discovered[row["league_key"]] = row
            for linked in (row.get("previous_league_key"), row.get("next_league_key")):
                if linked and linked not in visited:
                    queue.append(linked)

    classified = classify_discovery(discovered.values(), canonical)
    verified_by_key = {row["league_key"]: row for row in canonical if row.get("verified")}
    for row in classified["verified"]:
        known = verified_by_key[row["league_key"]]
        known.update({
            key: value for key, value in row.items()
            if key in {"game_key", "league_id", "previous_league_key", "next_league_key"} and value is not None
        })
    public_verified = [{
        "season": row["season"],
        "game_key": str(row["game_key"]),
        "league_key": row["league_key"],
        "league_id": str(row["league_id"]),
        "previous_league_key": row.get("previous_league_key"),
        "next_league_key": row.get("next_league_key"),
        "source_type": (row.get("source") or {}).get("type", "yahoo_live_discovery"),
    } for row in sorted(verified_by_key.values(), key=lambda item: item["season"])]

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": None,
        "status": "partial" if public_verified else "unavailable",
        "verified_leagues": public_verified,
        "unverified_candidates": [public_candidate(row) for row in classified["unverified"]],
        "ambiguous_candidates": [public_candidate(row) for row in classified["ambiguous"]],
        "archive_coverage": {
            "matchup_seasons": [],
            "roster_seasons": [],
            "player_point_seasons": [],
            "complete_weekly_matchups": 0,
        },
        "notes": [
            "Live discovery is a sanitized candidate report and does not edit the canonical league map.",
            "A candidate requires human review before it can be marked verified.",
            "Verified league identity does not imply that weekly Yahoo archives have been recovered.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-season", type=int, default=2021)
    parser.add_argument("--end-season", type=int, default=2026)
    parser.add_argument("--request-delay", type=float, default=0.25)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true", help="Use only committed verified sources; make no Yahoo request")
    parser.add_argument("--check", action="store_true", help="Fail if the committed dry-run manifest is stale")
    args = parser.parse_args()
    if args.start_season > args.end_season:
        raise SystemExit("start season must not be after end season")
    if args.check and not args.dry_run:
        raise SystemExit("--check requires --dry-run")

    if args.dry_run:
        payload = build_committed_manifest(
            load_yaml(DATA / "yahoo_leagues.yml"),
            load_yaml(DATA / "site.yml"),
        )
    else:
        payload = discover_live(
            start_season=args.start_season,
            end_season=args.end_season,
            request_delay=args.request_delay,
        )

    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != serialized:
            raise SystemExit("Yahoo history manifest is stale; run discover_yahoo_history.py --dry-run")
        print(f"Yahoo history manifest is current: {len(payload['verified_leagues'])} verified leagues")
        return
    changed = write_json_if_changed(args.output, payload)
    print(
        f"{'wrote' if changed else 'unchanged'} {args.output}: "
        f"{len(payload['verified_leagues'])} verified, "
        f"{len(payload['unverified_candidates'])} unverified, "
        f"{len(payload['ambiguous_candidates'])} ambiguous"
    )


if __name__ == "__main__":
    main()
