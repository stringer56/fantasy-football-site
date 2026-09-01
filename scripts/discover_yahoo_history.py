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

from pull_yahoo import API, YahooApiError, get_json, refresh_access_token, write_json_if_changed
from yahoo_history_discovery import (
    CAPABILITY_NAMES,
    EXPECTED_LEAGUE_NAME,
    SCHEMA_VERSION,
    extract_games,
    extract_leagues,
    normalized_name,
    parse_league_key,
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
            except (requests.RequestException, YahooApiError) as error:
                status = (
                    error.status_code
                    if isinstance(error, YahooApiError)
                    else error.response.status_code if error.response is not None else None
                )
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


def local_archive_coverage(season: int | None) -> dict[str, Any] | None:
    if season is None:
        return None
    path = ROOT / "_data" / "generated" / "history" / str(season) / "playoffs.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    coverage = payload.get("coverage") or {}
    return {
        "playoffs": coverage.get("status"),
        "playoff_weeks": list(coverage.get("weeks") or []),
        "scored_playoff_games": coverage.get("scored_games"),
        "playoff_byes": coverage.get("byes"),
        "source_file": path.relative_to(ROOT).as_posix(),
    }


def entity_count(payload: Any, entity: str) -> int:
    return sum(1 for _ in walk_named(payload, entity))


def sanitized_failure_status(error: Exception) -> str:
    """Describe a failure without URLs, response bodies, or credential values."""

    if isinstance(error, YahooApiError):
        return f"http_{error.status_code}"
    if isinstance(error, requests.RequestException) and error.response is not None:
        return f"http_{error.response.status_code}"
    return f"error_{type(error).__name__.casefold()}"


def authorization_probe(
    client: YahooDiscoveryClient,
    operation: str,
    resource: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Run one ordered authorization probe and retain only safe diagnostics."""

    try:
        payload = client.get(resource)
    except (requests.RequestException, YahooApiError, ValueError, KeyError) as error:
        status_code = (
            error.status_code
            if isinstance(error, YahooApiError)
            else error.response.status_code
            if isinstance(error, requests.RequestException) and error.response is not None
            else None
        )
        return ({
            "operation": operation,
            "success": False,
            "http_status": status_code,
            "error_code": error.error_code if isinstance(error, YahooApiError) else None,
        }, None)
    return ({
        "operation": operation,
        "success": True,
        "http_status": 200,
        "error_code": None,
    }, payload)


def stopped_authorization_manifest(
    *,
    probes: list[dict[str, Any]],
    access_status: dict[str, str],
    failed_operation: str,
) -> dict[str, Any]:
    """Preserve repository evidence while honoring the no-enumeration stop rule."""

    payload = json.loads(json.dumps(build_committed_baseline()))
    payload["generated_at"] = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    payload["discovery_status"] = "authorization_blocked"
    payload["access_status"] = access_status
    payload["authorization_probes"] = probes
    for season in payload["seasons"]:
        season["verification_status"] = "verified_repository_evidence_live_retest_blocked"
        season["capabilities"] = {
            name: "not_tested_due_authorization_stop" for name in CAPABILITY_NAMES
        }
    payload["unresolved_candidates"] = [{
        "season": 2026,
        "configured_alias": "nfl.l.26455",
        "verification_status": "not_tested_due_authorization_stop",
    }]
    payload["notes"] = [
        f"Live retest stopped after {failed_operation} failed, as required by the authorization stop rule.",
        "No later Yahoo Fantasy resources or historical leagues were enumerated in this run.",
        "Only HTTP status and an allowlisted Yahoo error code, when available, were retained.",
        "Previously verified 2024 and 2025 repository evidence remains preserved.",
    ]
    errors = validate_safe_output(payload)
    if errors:
        raise RuntimeError("Unsafe stopped discovery output rejected: " + "; ".join(errors))
    return payload


def probe(
    client: YahooDiscoveryClient,
    resource: str,
    entity: str,
) -> tuple[str, dict[str, Any] | None]:
    try:
        payload = client.get(resource)
    except (requests.RequestException, YahooApiError, ValueError, KeyError) as error:
        return sanitized_failure_status(error), None
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
        except (requests.RequestException, YahooApiError, ValueError, KeyError):
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
    access_status: dict[str, str] = {"oauth_refresh": "succeeded"}
    authorization_probes: list[dict[str, Any]] = []

    user_probe, _ = authorization_probe(
        client,
        "authenticated_user_fantasy_resource",
        "users;use_login=1/games",
    )
    authorization_probes.append(user_probe)
    access_status["authenticated_user_fantasy_resource"] = (
        "succeeded" if user_probe["success"] else f"http_{user_probe['http_status']}"
    )
    if not user_probe["success"]:
        return stopped_authorization_manifest(
            probes=authorization_probes,
            access_status={
                **access_status,
                "nfl_fantasy_game_resource": "not_tested_due_stop_rule",
                "configured_alias_resolution": "not_tested_due_stop_rule",
                "historical_enumeration": "not_tested_due_stop_rule",
            },
            failed_operation="authenticated_user_fantasy_resource",
        )

    game_probe, _ = authorization_probe(
        client,
        "nfl_fantasy_game_resource",
        "game/nfl",
    )
    authorization_probes.append(game_probe)
    access_status["nfl_fantasy_game_resource"] = (
        "succeeded" if game_probe["success"] else f"http_{game_probe['http_status']}"
    )
    if not game_probe["success"]:
        return stopped_authorization_manifest(
            probes=authorization_probes,
            access_status={
                **access_status,
                "configured_alias_resolution": "not_tested_due_stop_rule",
                "historical_enumeration": "not_tested_due_stop_rule",
            },
            failed_operation="nfl_fantasy_game_resource",
        )

    ordered_league_probes = (
        ("configured_current_league", f"league/{environment['LEAGUE_KEY']}"),
        ("verified_2025_league", "league/461.l.103926"),
        ("verified_2024_league", "league/449.l.761310"),
    )
    for operation, resource in ordered_league_probes:
        result, _ = authorization_probe(client, operation, resource)
        authorization_probes.append(result)

    try:
        discovered = fetch_account_leagues(client)
        access_status["user_game_league_enumeration"] = "succeeded"
    except (requests.RequestException, YahooApiError, ValueError, KeyError) as error:
        discovered = {}
        access_status["user_game_league_enumeration"] = sanitized_failure_status(error)

    anchor: dict[str, Any] | None = None
    try:
        anchor_payload = client.get(f"league/{environment['LEAGUE_KEY']}")
        anchors = extract_leagues(anchor_payload)
        if len(anchors) == 1 and normalized_name(anchors[0].get("league_name")) == normalized_name(EXPECTED_LEAGUE_NAME):
            anchor = anchors[0]
            discovered[anchor["league_key"]] = anchor
            access_status["configured_alias_resolution"] = "succeeded"
        else:
            access_status["configured_alias_resolution"] = "unexpected_response"
    except (requests.RequestException, YahooApiError, ValueError, KeyError) as error:
        access_status["configured_alias_resolution"] = sanitized_failure_status(error)

    configured = parse_league_key(environment["LEAGUE_KEY"])
    configured_league_id = configured[1] if configured else None
    if anchor is None and configured_league_id:
        matching = [
            row for row in discovered.values()
            if row.get("league_id") == configured_league_id
            and normalized_name(row.get("league_name")) == normalized_name(EXPECTED_LEAGUE_NAME)
        ]
        if len(matching) == 1:
            anchor = matching[0]
            access_status["configured_alias_resolution"] = "resolved_via_user_league_enumeration"

    baseline = build_committed_baseline()
    known_access: dict[str, str] = {}
    for known in baseline["seasons"]:
        key = known["league_key"]
        if key in discovered:
            known_access[key] = "available_via_user_enumeration"
            continue
        try:
            rows = extract_leagues(client.get(f"league/{key}"))
            if len(rows) == 1:
                discovered[key] = rows[0]
                known_access[key] = "succeeded"
            else:
                known_access[key] = "unexpected_response"
        except (requests.RequestException, YahooApiError, ValueError, KeyError) as error:
            known_access[key] = sanitized_failure_status(error)
            discovered[key] = {
                field: known.get(field)
                for field in (
                    "season", "game_key", "league_key", "league_id", "league_name",
                    "number_of_teams", "draft_status", "current_week", "start_date",
                    "end_date", "start_week", "end_week", "finished",
                    "previous_league_key", "next_league_key",
                )
            }

    chain_anchor = anchor["league_key"] if anchor else "461.l.103926"
    linked_keys, missing_links = follow_renewals(client, discovered, chain_anchor)
    baseline_keys = {row["league_key"] for row in baseline["seasons"]}
    linked_keys = sorted(
        set(linked_keys) | baseline_keys,
        key=lambda key: ((discovered.get(key) or {}).get("season") or 0, key),
    )

    verified = []
    for key in linked_keys:
        league = discovered[key]
        if normalized_name(league.get("league_name")) != normalized_name(EXPECTED_LEAGUE_NAME):
            continue
        metadata_access = known_access.get(key)
        if metadata_access and metadata_access.startswith(("http_", "error_")):
            capabilities = {name: metadata_access for name in CAPABILITY_NAMES}
            mappings = list(
                next(
                    (row.get("team_mappings") or [] for row in baseline["seasons"] if row["league_key"] == key),
                    [],
                )
            )
        else:
            capabilities, mappings = probe_capabilities(client, league, franchises)
        league["capabilities"] = capabilities
        league["team_mappings"] = mappings
        league["archive_coverage"] = local_archive_coverage(league.get("season"))
        verification = "verified_renewal_chain" if key not in baseline_keys else "verified_repository_and_live_probe"
        verified.append(safe_league(league, verification_status=verification))

    candidates = []
    for row in discovered.values():
        if row["league_key"] in linked_keys:
            continue
        if normalized_name(row.get("league_name")) == normalized_name(EXPECTED_LEAGUE_NAME):
            candidates.append(safe_league(row, verification_status="unresolved_name_match"))
    if anchor is None:
        candidates.append({
            "season": 2026,
            "configured_alias": "nfl.l.26455",
            "verification_status": access_status.get("configured_alias_resolution", "unresolved"),
        })

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "discovery_status": (
            "complete"
            if anchor is not None and not missing_links
            else "partial_access_denied"
            if any(value == "http_403" for value in access_status.values())
            else "partial"
        ),
        "access_status": access_status,
        "authorization_probes": authorization_probes,
        "expected_league_name": EXPECTED_LEAGUE_NAME,
        "seasons": sorted(verified, key=lambda row: (row.get("season") or 0, row["league_key"])),
        "renew_chain": linked_keys,
        "unresolved_candidates": sorted(candidates, key=lambda row: (row.get("season") or 0, row["league_key"])),
        "missing_renewal_links": missing_links,
        "notes": [
            "Only the configured authenticated league and explicit renewal links are verified.",
            "Same-name leagues outside that chain remain unresolved candidates.",
            "Capability values report endpoint availability, not complete historical coverage.",
            "HTTP status labels are sanitized and contain no response body or request URL.",
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
    base_capabilities = {name: "http_403" for name in CAPABILITY_NAMES}
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
        "verification_status": "verified_repository_evidence_live_access_denied",
        "capabilities": dict(base_capabilities),
        "team_mappings": [],
        "archive_coverage": None,
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
        "verification_status": "verified_repository_evidence_live_access_denied",
        "capabilities": dict(base_capabilities),
        "team_mappings": sorted(mappings, key=lambda row: row["yahoo_team_key"] or ""),
        "archive_coverage": {
            "standings": "complete_snapshot",
            "playoffs": "complete_championship_bracket",
            "playoff_weeks": [14, 15, 16],
            "scored_playoff_games": 7,
            "playoff_byes": 2,
            "source_file": "_data/generated/history/2025/playoffs.json",
        },
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": "2026-09-01T03:21:01Z",
        "discovery_status": "partial_access_denied",
        "access_status": {
            "oauth_refresh": "succeeded",
            "user_game_league_enumeration": "http_403",
            "configured_alias_resolution": "http_403",
        },
        "authorization_probes": [
            {
                "operation": "authenticated_user_fantasy_resource",
                "success": False,
                "http_status": 403,
                "error_code": None,
            }
        ],
        "expected_league_name": EXPECTED_LEAGUE_NAME,
        "seasons": [season_2024, season_2025],
        "renew_chain": ["449.l.761310", "461.l.103926"],
        "unresolved_candidates": [
            {
                "season": 2026,
                "configured_alias": "nfl.l.26455",
                "verification_status": "http_403",
            }
        ],
        "missing_renewal_links": [],
        "notes": [
            "Yahoo OAuth refresh succeeds, but every tested Fantasy API resource returns HTTP 403.",
            "The committed league identities remain based on previously sanitized repository evidence.",
            "HTTP status labels contain no response body, request URL, or credential value.",
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
