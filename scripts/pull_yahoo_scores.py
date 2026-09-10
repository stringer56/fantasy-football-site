"""Refresh only the current Yahoo fantasy scoreboard for near-live display."""

from __future__ import annotations

from datetime import datetime, timezone

from pull_yahoo import (
    API,
    OUTPUT_DIRECTORY,
    configured_yahoo_identity,
    get_json,
    refresh_access_token,
    required_environment,
    write_json_if_changed,
)
from yahoo_normalize import normalize_matchups


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
    scoreboard = get_json(
        f"{API}/league/{league_alias}/scoreboard?format=json", token
    )
    payload = normalize_matchups(scoreboard)
    expected_prefix = f"{configured['league_key']}.t."
    team_keys = [
        str(team.get("team_key") or "")
        for matchup in payload.get("matchups", [])
        for team in matchup.get("teams", [])
    ]
    if not payload.get("week") or not payload.get("matchups"):
        raise RuntimeError("Yahoo scoreboard did not contain a current matchup week")
    if not team_keys or any(not key.startswith(expected_prefix) for key in team_keys):
        raise RuntimeError("Yahoo scoreboard identity does not match this league")

    fetched_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    changed = int(write_json_if_changed(OUTPUT_DIRECTORY / "matchups.json", payload))
    changed += int(
        write_json_if_changed(
            OUTPUT_DIRECTORY / "live_sync.json",
            {
                "schema_version": 1,
                "status": "ready",
                "source": "official_yahoo_fantasy_api",
                "week": payload["week"],
                "fetched_at": fetched_at,
            },
        )
    )
    print(
        f"Yahoo live scoreboard refreshed: week {payload['week']}, "
        f"{len(payload['matchups'])} matchups, {changed} changed files"
    )


if __name__ == "__main__":
    main()
