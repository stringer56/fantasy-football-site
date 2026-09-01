"""Discover Road to Glory Yahoo seasons and publish only sanitized metadata."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests
import yaml

from pull_yahoo import API, get_json, refresh_access_token, write_json_if_changed
from yahoo_history_discovery import (
    CAPABILITY_NAMES,
    EXPECTED_LEAGUE_NAME,
    SCHEMA_VERSION,
    extract_games,
    extract_leagues,
    normalized_name,
    renewal_chain,
    safe_league,
    safe_team_mapping,
    validate_safe_output,
    walk_named,
)
from yahoo_normalize import normalize_teams


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_data" / "generated" / "history_manifest.json"
FRANCHISES = ROOT / "_data" / "franchises.yml"


class YahooDiscoveryClient:
    """Small bounded-retry client that never logs URLs, headers, or responses."""

    def __init__(
        self,
        token: str,
        *,
        request_delay: float = 0.2,
        max_retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.token = token
        self.request_delay = max(request_delay, 0)
        self.max_retries = max_retries
        self.sleep = sleep
        self.cache: dict[str, dict[str, Any]] = {}

    def get(self, resource: str) -> dict[str, Any]:
        if resource in self.cache:
            return self.cache[resource]
        for attempt in range(self.max_retries + 1):
            try:
                payload = get_json(f"{API}/{resource}?format=json", self.token)
                self.cache[resource] = payload
                if self.request_delay:
                    self.sleep(self.request_delay)
                return payload
            except requests.RequestException as error:
                status = error.response.status_code if error.response is not None else None
                retryable = status is None or status == 429 or (status is not None and status >= 500)
                if not retryable or attempt >= self.max_retries:
                    raise
                self.sleep(min(2**attempt, 8))
        raise RuntimeError("unreachable")


def required_environment() -> dict[str, str]:
    names = ("YAHOO_CLIENT_ID", "YAHOO_CLIENT_SECRET", "YAHOO_REFRESH_TOKEN", "LEAGUE_KEY")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    return {name: os.environ[name] for name in names}


def load_franchises() -> list[dict[str, Any]]:
    payload = yaml.safe_load(FRANCHISES.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("franchises.yml must be a schema_version 1 mapping")
    return list(payload.get("franchises") or [])


def entity_count(payload: Any, entity: str) -> int:
    return sum(1 for _ in walk_named(payload, entity))


def probe(
    client: YahooDiscoveryClient,
    resource: str,
    entity: str,
) -> tuple[str, dict[str, Any] | None]:
    try:
        payload = client.get(resource)
    except (requests.RequestException, ValueError, KeyError):
        return "unavailable", None
    return ("available" if entity_count(payload, entity) else "empty"), payload


def probe_capabilities(
    client: YahooDiscoveryClient,
    league: dict[str, Any],
    franchises: list[dict[str, Any]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    key = league["league_key"]
    capabilities = {name: "not_probed" for name in CAPABILITY_NAMES}
    capabilities["league_metadata"] = "available"

    capabilities["teams"], teams_payload = probe(client, f"league/{key}/teams", "team")
    teams = normalize_teams(teams_payload or {}).get("teams") or []
    mappings = [
        safe_team_mapping(
            season=int(league["season"]),
            team_key=team.get("team_key"),
            team_name=team.get("team_name"),
            franchises=franchises,
        )
        for team in teams
    ]
    capabilities["standings"], _ = probe(client, f"league/{key}/standings", "team")

    start_week = league.get("start_week") or 1
    end_week = league.get("end_week") or start_week
    capabilities["weekly_matchups"], _ = probe(
        client, f"league/{key}/scoreboard;week={start_week}", "matchup"
    )
    capabilities["final_playoff_matchups"], _ = probe(
        client, f"league/{key}/scoreboard;week={end_week}", "matchup"
    )
    if teams:
        first_key = teams[0].get("team_key")
        capabilities["rosters"], _ = probe(
            client, f"team/{first_key}/roster;week={start_week}", "player"
        )
    else:
        capabilities["rosters"] = "unavailable"
    capabilities["draft_results"], _ = probe(client, f"league/{key}/draftresults", "draft_result")
    capabilities["transactions"], _ = probe(client, f"league/{key}/transactions", "transaction")
    return capabilities, mappings


def fetch_account_leagues(client: YahooDiscoveryClient) -> dict[str, dict[str, Any]]:
    games_payload = client.get("users;use_login=1/games;game_codes=nfl")
    games = [game for game in extract_games(games_payload) if game.get("game_code") in {None, "nfl"}]
    discovered: dict[str, dict[str, Any]] = {}
    keys = [game["game_key"] for game in games]
    for offset in range(0, len(keys), 10):
        batch = ",".join(keys[offset : offset + 10])
        payload = client.get(f"users;use_login=1/games;game_keys={batch}/leagues")
        for league in extract_leagues(payload):
            discovered[league["league_key"]] = league
    return discovered


def follow_renewals(
    client: YahooDiscoveryClient,
    discovered: dict[str, dict[str, Any]],
    anchor_key: str,
) -> tuple[list[str], list[str]]:
    queue = [anchor_key]
    attempted: set[str] = set()
    while queue and len(attempted) < 40:
        key = queue.pop(0)
        if not key or key in attempted:
            continue
        attempted.add(key)
        try:
            payload = client.get(f"league/{key}")
        except (requests.RequestException, ValueError, KeyError):
            continue
        rows = extract_leagues(payload)
        for row in rows:
            discovered[row["league_key"]] = row
            for linked in (row.get("previous_league_key"), row.get("next_league_key")):
                if linked and linked not in attempted:
                    queue.append(linked)
    return renewal_chain(discovered.values(), anchor_key)


def discover_live(request_delay: float) -> dict[str, Any]:
    environment = required_environment()
    token = refresh_access_token(
        environment["YAHOO_CLIENT_ID"],
        environment["YAHOO_CLIENT_SECRET"],
        environment["YAHOO_REFRESH_TOKEN"],
    )
    print("Yahoo authentication succeeded; beginning sanitized league discovery")
    client = YahooDiscoveryClient(token, request_delay=request_delay)
    franchises = load_franchises()
    discovered = fetch_account_leagues(client)

    anchor_payload = client.get(f"league/{environment['LEAGUE_KEY']}")
    anchors = extract_leagues(anchor_payload)
    if len(anchors) != 1:
        raise RuntimeError("Configured league alias did not resolve to exactly one league")
    anchor = anchors[0]
    if normalized_name(anchor.get("league_name")) != normalized_name(EXPECTED_LEAGUE_NAME):
        raise RuntimeError("Configured league alias does not match the expected public league name")
    discovered[anchor["league_key"]] = anchor
    linked_keys, missing_links = follow_renewals(client, discovered, anchor["league_key"])

    verified = []
    for key in linked_keys:
        league = discovered[key]
        if normalized_name(league.get("league_name")) != normalized_name(EXPECTED_LEAGUE_NAME):
            continue
        capabilities, mappings = probe_capabilities(client, league, franchises)
        league["capabilities"] = capabilities
        league["team_mappings"] = mappings
        verified.append(safe_league(league, verification_status="verified_renewal_chain"))

    candidates = []
    for row in discovered.values():
        if row["league_key"] in linked_keys:
            continue
        if normalized_name(row.get("league_name")) == normalized_name(EXPECTED_LEAGUE_NAME):
            candidates.append(safe_league(row, verification_status="unresolved_name_match"))

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "discovery_status": "complete" if not missing_links else "partial",
        "expected_league_name": EXPECTED_LEAGUE_NAME,
        "seasons": sorted(verified, key=lambda row: (row.get("season") or 0, row["league_key"])),
        "renew_chain": linked_keys,
        "unresolved_candidates": sorted(candidates, key=lambda row: (row.get("season") or 0, row["league_key"])),
        "missing_renewal_links": missing_links,
        "notes": [
            "Only the configured authenticated league and explicit renewal links are verified.",
            "Same-name leagues outside that chain remain unresolved candidates.",
            "Capability values report endpoint availability, not complete historical coverage.",
        ],
    }
    errors = validate_safe_output(payload)
    if errors:
        raise RuntimeError("Unsafe discovery output rejected: " + "; ".join(errors))
    return payload


def build_committed_baseline() -> dict[str, Any]:
    """Build the honest pre-live baseline from previously sanitized evidence."""

    franchises = load_franchises()
    mappings = []
    for franchise in franchises:
        yahoo = franchise.get("yahoo") or {}
        key = (yahoo.get("team_keys") or {}).get("2025")
        name = (yahoo.get("team_names") or {}).get("2025")
        if key:
            mappings.append(
                safe_team_mapping(
                    season=2025,
                    team_key=key,
                    team_name=name,
                    franchises=franchises,
                )
            )
    base_capabilities = {name: "not_probed" for name in CAPABILITY_NAMES}
    season_2024 = {
        "season": 2024,
        "game_key": "449",
        "league_key": "449.l.761310",
        "league_id": "761310",
        "league_name": EXPECTED_LEAGUE_NAME,
        "number_of_teams": None,
        "start_date": None,
        "end_date": None,
        "finished": True,
        "previous_league_key": None,
        "next_league_key": "461.l.103926",
        "verification_status": "verified_from_2025_renew_metadata",
        "capabilities": dict(base_capabilities),
        "team_mappings": [],
    }
    season_2025 = {
        "season": 2025,
        "game_key": "461",
        "league_key": "461.l.103926",
        "league_id": "103926",
        "league_name": EXPECTED_LEAGUE_NAME,
        "number_of_teams": 12,
        "start_date": "2025-09-04",
        "end_date": "2025-12-22",
        "finished": True,
        "previous_league_key": "449.l.761310",
        "next_league_key": None,
        "verification_status": "verified_from_sanitized_snapshot",
        "capabilities": {
            **base_capabilities,
            "league_metadata": "available_snapshot",
            "teams": "available_snapshot",
            "standings": "available_snapshot",
            "weekly_matchups": "single_week_snapshot_only",
            "final_playoff_matchups": "available_snapshot",
            "rosters": "single_week_snapshot_only",
        },
        "team_mappings": sorted(mappings, key=lambda row: row["yahoo_team_key"] or ""),
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": "2026-08-31T00:00:00Z",
        "discovery_status": "partial_authentication_required",
        "expected_league_name": EXPECTED_LEAGUE_NAME,
        "seasons": [season_2024, season_2025],
        "renew_chain": ["449.l.761310", "461.l.103926"],
        "unresolved_candidates": [
            {
                "season": 2026,
                "configured_alias": "nfl.l.26455",
                "verification_status": "authentication_required",
            }
        ],
        "missing_renewal_links": [],
        "notes": [
            "The committed baseline contains only previously sanitized repository evidence.",
            "A live authenticated discovery has not completed because Yahoo token refresh returns HTTP 400.",
            "Capability values marked not_probed are not evidence of unavailability.",
        ],
    }
    errors = validate_safe_output(payload)
    if errors:
        raise RuntimeError("Unsafe baseline output rejected: " + "; ".join(errors))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--request-delay", type=float, default=0.2)
    parser.add_argument("--dry-run", action="store_true", help="Use committed safe evidence and make no network calls")
    parser.add_argument("--check", action="store_true", help="Fail if the committed dry-run manifest is stale")
    args = parser.parse_args()
    if args.check and not args.dry_run:
        raise SystemExit("--check requires --dry-run")

    try:
        payload = build_committed_baseline() if args.dry_run else discover_live(args.request_delay)
    except Exception as error:
        print(
            f"Yahoo history discovery failed before writing output ({type(error).__name__}).",
            file=sys.stderr,
        )
        raise SystemExit(1) from error

    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != serialized:
            raise SystemExit("history manifest is stale; run discover_yahoo_history.py --dry-run")
        print(f"History manifest is current: {len(payload['seasons'])} verified seasons")
        return
    write_json_if_changed(args.output, payload)
    print(f"Sanitized discovery complete: {len(payload['seasons'])} verified seasons")


if __name__ == "__main__":
    main()
