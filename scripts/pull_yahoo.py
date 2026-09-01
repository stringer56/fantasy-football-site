"""Fetch Yahoo Fantasy Football data and publish sanitized Jekyll data."""

from __future__ import annotations

import base64
import json
import os
import pathlib
import sys
from typing import Any

import requests

from yahoo_normalize import build_public_payloads, normalize_matchups, normalize_teams


API = "https://fantasysports.yahooapis.com/fantasy/v2"
OUTPUT_DIRECTORY = pathlib.Path("_data/generated")


class YahooApiError(RuntimeError):
    """Sanitized Yahoo HTTP failure that never includes URLs or response bodies."""

    def __init__(self, operation: str, status_code: int) -> None:
        self.operation = operation
        self.status_code = status_code
        super().__init__(f"{operation} failed with HTTP {status_code}")


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        "https://api.login.yahoo.com/oauth2/get_token",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError:
        raise YahooApiError("Yahoo OAuth token refresh", response.status_code) from None
    return response.json()["access_token"]


def get_json(url: str, token: str) -> dict[str, Any]:
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError:
        raise YahooApiError("Yahoo Fantasy API request", response.status_code) from None
    if "application/json" not in response.headers.get("Content-Type", ""):
        raise ValueError("Yahoo returned a non-JSON response")
    return response.json()


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
        except (requests.RequestException, ValueError) as error:
            print(
                f"warning: roster unavailable for team {team.get('team_id')}: {error}",
                file=sys.stderr,
            )
    return payloads


def main() -> None:
    environment = required_environment()
    token = refresh_access_token(
        environment["YAHOO_CLIENT_ID"],
        environment["YAHOO_CLIENT_SECRET"],
        environment["YAHOO_REFRESH_TOKEN"],
    )
    league_alias = environment["LEAGUE_KEY"]
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

    changed = 0
    for filename, payload in public_payloads.items():
        changed += int(write_json_if_changed(OUTPUT_DIRECTORY / filename, payload))
    print(
        "Yahoo update complete: "
        f"{len(public_payloads['teams.json']['teams'])} teams, "
        f"{len(public_payloads['standings.json']['standings'])} standings rows, "
        f"{len(public_payloads['matchups.json']['matchups'])} matchups, "
        f"{changed} changed files"
    )


if __name__ == "__main__":
    main()
