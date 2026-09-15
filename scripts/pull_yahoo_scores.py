"""Refresh only the current Yahoo fantasy scoreboard for near-live display."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

import requests

from pull_yahoo import (
    API,
    OUTPUT_DIRECTORY,
    configured_yahoo_identity,
    get_json,
    refresh_access_token,
    required_environment,
    write_json_if_changed,
)
from yahoo_client import YahooApiError, YahooTransportError
from yahoo_live import load_public_score_payloads
from yahoo_normalize import normalize_matchups


def retain_existing_records(payload: dict[str, Any], current_path: pathlib.Path) -> None:
    """Keep the last standings-derived record when a score response omits it."""

    try:
        current = json.loads(current_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return
    records = {
        team.get("team_key"): team.get("record")
        for matchup in current.get("matchups", [])
        for team in matchup.get("teams", [])
        if isinstance(team.get("record"), str)
    }
    for matchup in payload.get("matchups", []):
        for team in matchup.get("teams", []):
            if not team.get("record") and records.get(team.get("team_key")):
                team["record"] = records[team["team_key"]]


def validate_score_payload(payload: dict[str, Any], expected_prefix: str) -> None:
    matchups = payload.get("matchups")
    if not payload.get("week") or not isinstance(matchups, list) or not matchups:
        raise ValueError("Yahoo scoreboard did not contain a current matchup week")
    team_keys = [
        str(team.get("team_key") or "")
        for matchup in matchups
        for team in matchup.get("teams", [])
    ]
    if not team_keys or len(set(team_keys)) != len(team_keys):
        raise ValueError("Yahoo scoreboard contained incomplete team identities")
    if any(not key.startswith(expected_prefix) for key in team_keys):
        raise ValueError("Yahoo scoreboard identity does not match this league")
    for matchup in matchups:
        teams = matchup.get("teams")
        if not isinstance(teams, list) or len(teams) != 2:
            raise ValueError("Yahoo scoreboard contained an incomplete matchup")


def validate_sync_payload(sync: dict[str, Any], week: int) -> None:
    if sync.get("status") != "ready" or int(sync.get("week") or 0) != int(week):
        raise ValueError("Yahoo freshness metadata did not match the scoreboard")
    if sync.get("source") not in {
        "official_yahoo_fantasy_api",
        "official_yahoo_public_page_fallback",
    }:
        raise ValueError("Yahoo freshness metadata had an invalid source")
    timestamp = str(sync.get("fetched_at") or "")
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Yahoo freshness timestamp was invalid") from None


def authenticated_score_payloads(
    environment: dict[str, str], configured: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    league_alias = environment["LEAGUE_KEY"]
    token = refresh_access_token(
        environment["YAHOO_CLIENT_ID"],
        environment["YAHOO_CLIENT_SECRET"],
        environment["YAHOO_REFRESH_TOKEN"],
    )
    scoreboard = get_json(
        f"{API}/league/{league_alias}/scoreboard?format=json", token
    )
    payload = normalize_matchups(scoreboard)
    validate_score_payload(payload, f"{configured['league_key']}.t.")
    fetched_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return (
        payload,
        {
            "schema_version": 1,
            "status": "ready",
            "source": "official_yahoo_fantasy_api",
            "week": payload["week"],
            "fetched_at": fetched_at,
        },
    )


def fetch_score_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    environment = required_environment()
    configured = configured_yahoo_identity()
    league_alias = environment["LEAGUE_KEY"]
    if league_alias != str(configured["alias"]):
        raise RuntimeError("LEAGUE_KEY does not match the reviewed Yahoo configuration")

    try:
        return authenticated_score_payloads(environment, configured)
    except (
        YahooApiError,
        YahooTransportError,
        requests.RequestException,
        ValueError,
    ) as error:
        if isinstance(error, YahooApiError):
            detail = f"HTTP {error.status_code}"
        elif isinstance(error, YahooTransportError):
            detail = error.category
        else:
            detail = "invalid_or_unavailable_response"
        print(
            f"Yahoo authenticated scoreboard unavailable ({detail}); "
            "using official public fallback",
            file=sys.stderr,
        )
        payload, sync = load_public_score_payloads(refresh=True)
        validate_score_payload(payload, f"{configured['league_key']}.t.")
        return payload, sync


def refresh_once(output_directory: pathlib.Path = OUTPUT_DIRECTORY) -> dict[str, Any]:
    payload, sync = fetch_score_payloads()
    retain_existing_records(payload, output_directory / "matchups.json")
    configured = configured_yahoo_identity()
    validate_score_payload(payload, f"{configured['league_key']}.t.")
    validate_sync_payload(sync, int(payload["week"]))
    changed = int(write_json_if_changed(output_directory / "matchups.json", payload))
    changed += int(write_json_if_changed(output_directory / "live_sync.json", sync))
    print(
        f"Yahoo live scoreboard refreshed: week {payload['week']}, "
        f"{len(payload['matchups'])} matchups, {changed} changed files, "
        f"source {sync['source']}"
    )
    return sync


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stability-runs", type=int, default=1)
    parser.add_argument("--stability-delay", type=float, default=0.0)
    parser.add_argument(
        "--output-directory", type=pathlib.Path, default=OUTPUT_DIRECTORY
    )
    args = parser.parse_args()
    if not 1 <= args.stability_runs <= 3:
        raise ValueError("stability runs must be between 1 and 3")
    previous_timestamp: str | None = None
    for index in range(args.stability_runs):
        sync = refresh_once(args.output_directory)
        timestamp = str(sync["fetched_at"])
        if previous_timestamp is not None and timestamp <= previous_timestamp:
            raise RuntimeError("Yahoo live freshness timestamp did not advance")
        previous_timestamp = timestamp
        if index + 1 < args.stability_runs:
            time.sleep(max(1.0, args.stability_delay))


if __name__ == "__main__":
    main()
