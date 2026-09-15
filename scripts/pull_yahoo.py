"""Fetch Yahoo Fantasy Football data and publish sanitized Jekyll data."""

from __future__ import annotations

import json
import os
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

import requests
import yaml

try:
    from .yahoo_client import YahooApiError, YahooTransportError, get_json, refresh_access_token
    from .yahoo_normalize import build_public_payloads, normalize_matchups, normalize_teams
except ImportError:
    from yahoo_client import YahooApiError, YahooTransportError, get_json, refresh_access_token
    from yahoo_normalize import build_public_payloads, normalize_matchups, normalize_teams


API = "https://fantasysports.yahooapis.com/fantasy/v2"
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "_data" / "generated"
SITE_CONFIG = ROOT / "_data" / "site.yml"


def write_json_if_changed(path: pathlib.Path, data: Any) -> bool:
    serialized = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == serialized:
        print(f"unchanged {path}")
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(path)
    print(f"wrote {path}")
    return True


def required_environment() -> dict[str, str]:
    names = (
        "YAHOO_CLIENT_ID",
        "YAHOO_CLIENT_SECRET",
        "YAHOO_REFRESH_TOKEN",
        "LEAGUE_KEY",
    )
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    return {name: os.environ[name] for name in names}


def configured_yahoo_identity() -> dict[str, Any]:
    config = yaml.safe_load(SITE_CONFIG.read_text(encoding="utf-8"))
    yahoo = config.get("yahoo") or {}
    required = ("season", "game_key", "league_id", "league_key", "alias")
    missing = [field for field in required if yahoo.get(field) in (None, "")]
    if missing:
        raise RuntimeError("Canonical Yahoo configuration is incomplete")
    return yahoo


def validate_requested_and_normalized_identity(
    configured: dict[str, Any], requested_alias: str, league_payload: dict[str, Any]
) -> None:
    """Fail safely if the secret or Yahoo response points at another league."""
    if requested_alias != str(configured["alias"]):
        raise RuntimeError("LEAGUE_KEY does not match the reviewed Yahoo configuration")
    league = league_payload.get("league") or {}
    expected = {
        "season": int(configured["season"]),
        "league_key": str(configured["league_key"]),
        "league_id": str(configured["league_id"]),
    }
    actual = {
        "season": league.get("season"),
        "league_key": str(league.get("league_key") or ""),
        "league_id": str(league.get("league_id") or ""),
    }
    if actual != expected:
        raise RuntimeError("Yahoo response identity does not match the reviewed configuration")


def fetch_rosters(
    *,
    token: str,
    teams: list[dict[str, Any]],
    week: int | None,
) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for team in teams:
        team_key = team.get("team_key")
        if not team_key:
            continue
        url = f"{API}/team/{team_key}/roster?format=json"
        if week is not None:
            url += f"&week={week}"
        try:
            payloads[team_key] = get_json(url, token)
            print(f"fetched roster for team {team.get('team_id')}")
        except (
            requests.RequestException,
            YahooApiError,
            YahooTransportError,
            ValueError,
        ) as error:
            print(
                f"warning: roster unavailable for team {team.get('team_id')}: {error}",
                file=sys.stderr,
            )
    return payloads


def main() -> None:
    environment = required_environment()
    configured = configured_yahoo_identity()
    league_alias = environment["LEAGUE_KEY"]
    if league_alias != str(configured["alias"]):
        raise RuntimeError("LEAGUE_KEY does not match the reviewed Yahoo configuration")
    token = refresh_access_token(
        environment["YAHOO_CLIENT_ID"],
        environment["YAHOO_CLIENT_SECRET"],
        environment["YAHOO_REFRESH_TOKEN"],
    )
    print("Yahoo authentication succeeded; fetching public league data")

    league_data = get_json(f"{API}/league/{league_alias}?format=json", token)
    standings_data = get_json(
        f"{API}/league/{league_alias}/standings?format=json", token
    )
    scoreboard_data = get_json(
        f"{API}/league/{league_alias}/scoreboard?format=json", token
    )
    teams_data = get_json(f"{API}/league/{league_alias}/teams?format=json", token)

    teams = normalize_teams(teams_data)["teams"]
    week = normalize_matchups(scoreboard_data)["week"]
    roster_payloads = fetch_rosters(token=token, teams=teams, week=week)
    public_payloads = build_public_payloads(
        league_data=league_data,
        teams_data=teams_data,
        standings_data=standings_data,
        scoreboard_data=scoreboard_data,
        roster_payloads=roster_payloads,
    )
    validate_requested_and_normalized_identity(
        configured, league_alias, public_payloads["league.json"]
    )

    changed = 0
    for filename, payload in public_payloads.items():
        changed += int(write_json_if_changed(OUTPUT_DIRECTORY / filename, payload))
    fetched_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    changed += int(
        write_json_if_changed(
            OUTPUT_DIRECTORY / "live_sync.json",
            {
                "schema_version": 1,
                "status": "ready",
                "source": "official_yahoo_fantasy_api",
                "week": public_payloads["matchups.json"]["week"],
                "fetched_at": fetched_at,
            },
        )
    )
    print(
        "Yahoo update complete: "
        f"{len(public_payloads['teams.json']['teams'])} teams, "
        f"{len(public_payloads['standings.json']['standings'])} standings rows, "
        f"{len(public_payloads['matchups.json']['matchups'])} matchups, "
        f"{changed} changed files"
    )


if __name__ == "__main__":
    main()
