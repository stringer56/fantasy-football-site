"""Pure normalization helpers for Yahoo Fantasy Football JSON responses.

Yahoo represents entities as a mixture of numbered dictionaries, metadata
lists, and nested lists. These helpers intentionally understand those shapes
without searching arbitrary response keys or publishing the original payload.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


SCHEMA_VERSION = 1


def as_mapping(value: Any) -> dict[str, Any]:
    """Merge Yahoo metadata lists into one shallow mapping."""

    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, list):
        return {}

    merged: dict[str, Any] = {}
    for part in value:
        if isinstance(part, dict):
            merged.update(part)
        elif isinstance(part, list):
            merged.update(as_mapping(part))
    return merged


def indexed_values(value: Any) -> list[Any]:
    """Return values from a Yahoo numbered collection in numeric order."""

    if isinstance(value, list):
        return list(value)
    if not isinstance(value, dict):
        return []

    numbered: list[tuple[int, Any]] = []
    for key, item in value.items():
        if str(key).isdigit():
            numbered.append((int(key), item))
    return [item for _, item in sorted(numbered, key=lambda pair: pair[0])]


def entity_nodes(container: Any, entity_name: str) -> Iterable[Any]:
    """Yield named entities from a Yahoo numbered collection."""

    direct = as_mapping(container)
    if entity_name in direct:
        yield direct[entity_name]
        return

    for item in indexed_values(container):
        wrapper = as_mapping(item)
        if entity_name in wrapper:
            yield wrapper[entity_name]


def nested_section(value: Any, section_name: str) -> Any:
    """Find a section directly or below one numbered Yahoo wrapper."""

    root = as_mapping(value)
    if section_name in root:
        return root[section_name]

    for item in indexed_values(root):
        wrapper = as_mapping(item)
        if section_name in wrapper:
            return wrapper[section_name]
    return None


def _fantasy_content(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    return as_mapping(data.get("fantasy_content"))


def _league_payload(data: Any) -> dict[str, Any]:
    return as_mapping(_fantasy_content(data).get("league"))


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _integer(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _points(value: Any) -> float | None:
    number = _number(value)
    return round(number, 2) if number is not None else None


def _boolean(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    return None


def _first_logo_url(team: Mapping[str, Any]) -> str | None:
    logos = team.get("team_logos")
    candidates = indexed_values(logos) if isinstance(logos, dict) else (logos or [])
    if not isinstance(candidates, list):
        return None

    for candidate in candidates:
        wrapper = as_mapping(candidate)
        logo = as_mapping(wrapper.get("team_logo", wrapper))
        url = _text(logo.get("url"))
        if url:
            return url
    return None


def _safe_managers(team: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return public display names only; omit Yahoo account identifiers."""

    managers = team.get("managers")
    candidates = indexed_values(managers) if isinstance(managers, dict) else (managers or [])
    if not isinstance(candidates, list):
        return []

    public: list[dict[str, str]] = []
    for candidate in candidates:
        wrapper = as_mapping(candidate)
        manager = as_mapping(wrapper.get("manager", wrapper))
        display_name = _text(manager.get("nickname") or manager.get("name"))
        if display_name:
            public.append({"display_name": display_name})
    return public


def normalize_team(team_node: Any) -> dict[str, Any] | None:
    team = as_mapping(team_node)
    team_key = _text(team.get("team_key"))
    team_name = _text(team.get("name") or team.get("nickname"))
    if not team_key and not team_name:
        return None

    return {
        "team_key": team_key,
        "team_id": _integer(team.get("team_id")),
        "team_name": team_name,
        "managers": _safe_managers(team),
        "team_logo_url": _first_logo_url(team),
        "waiver_priority": _integer(team.get("waiver_priority")),
        "number_of_moves": _integer(team.get("number_of_moves")),
        "number_of_trades": _integer(team.get("number_of_trades")),
    }


def normalize_league(data: Any) -> dict[str, Any]:
    league = _league_payload(data)
    normalized = {
        "league_key": _text(league.get("league_key")),
        "league_id": _text(league.get("league_id")),
        "league_name": _text(league.get("name")),
        "season": _integer(league.get("season")),
        "number_of_teams": _integer(league.get("num_teams")),
        "current_week": _integer(league.get("current_week")),
        "matchup_week": _integer(league.get("matchup_week")),
        "start_date": _text(league.get("start_date")),
        "end_date": _text(league.get("end_date")),
        "is_finished": _boolean(league.get("is_finished")),
        "league_logo_url": _text(league.get("logo_url")),
        "source_update_timestamp": _text(league.get("league_update_timestamp")),
    }
    return {"schema_version": SCHEMA_VERSION, "league": normalized}


def normalize_teams(data: Any) -> dict[str, Any]:
    league = _league_payload(data)
    container = league.get("teams")
    teams: list[dict[str, Any]] = []
    for node in entity_nodes(container, "team"):
        normalized = normalize_team(node)
        if normalized:
            teams.append(normalized)
    return {"schema_version": SCHEMA_VERSION, "teams": teams}


def normalize_standings(data: Any) -> dict[str, Any]:
    league = _league_payload(data)
    standings_section = league.get("standings")
    teams_container = nested_section(standings_section, "teams")
    standings: list[dict[str, Any]] = []

    for node in entity_nodes(teams_container, "team"):
        team = as_mapping(node)
        public_team = normalize_team(node)
        if not public_team:
            continue

        team_standings = as_mapping(team.get("team_standings"))
        outcomes = as_mapping(team_standings.get("outcome_totals"))
        streak = as_mapping(team_standings.get("streak"))
        standings.append(
            {
                "rank": _integer(team_standings.get("rank")),
                "team_key": public_team["team_key"],
                "team_id": public_team["team_id"],
                "team_name": public_team["team_name"],
                "wins": _integer(outcomes.get("wins")) or 0,
                "losses": _integer(outcomes.get("losses")) or 0,
                "ties": _integer(outcomes.get("ties")) or 0,
                "winning_percentage": _number(outcomes.get("percentage")),
                "points_for": _points(team_standings.get("points_for")),
                "points_against": _points(team_standings.get("points_against")),
                "streak": {
                    "type": _text(streak.get("type")),
                    "value": _integer(streak.get("value")),
                }
                if streak
                else None,
                "playoff_seed": _integer(team_standings.get("playoff_seed")),
            }
        )

    standings.sort(
        key=lambda record: (
            record["rank"] is None,
            record["rank"] if record["rank"] is not None else 10_000,
        )
    )
    return {"schema_version": SCHEMA_VERSION, "standings": standings}


def _matchup_team(team_node: Any) -> dict[str, Any] | None:
    team = as_mapping(team_node)
    public_team = normalize_team(team_node)
    if not public_team:
        return None

    points = as_mapping(team.get("team_points"))
    projected = as_mapping(team.get("team_projected_points"))
    return {
        "team_key": public_team["team_key"],
        "team_id": public_team["team_id"],
        "team_name": public_team["team_name"],
        "score": _points(points.get("total") or points.get("value")),
        "projected_score": _points(projected.get("total") or projected.get("value")),
    }


def normalize_matchups(data: Any) -> dict[str, Any]:
    league = _league_payload(data)
    scoreboard = as_mapping(league.get("scoreboard"))
    matchups_container = nested_section(scoreboard, "matchups")
    normalized_matchups: list[dict[str, Any]] = []

    for node in entity_nodes(matchups_container, "matchup"):
        matchup = as_mapping(node)
        teams_container = nested_section(matchup, "teams")
        teams: list[dict[str, Any]] = []
        for team_node in entity_nodes(teams_container, "team"):
            team = _matchup_team(team_node)
            if team:
                teams.append(team)

        if not teams:
            continue
        normalized_matchups.append(
            {
                "week": _integer(matchup.get("week")),
                "status": _text(matchup.get("status")),
                "is_playoffs": _boolean(matchup.get("is_playoffs")),
                "is_consolation": _boolean(matchup.get("is_consolation")),
                "is_tied": _boolean(matchup.get("is_tied")),
                "winner_team_key": _text(matchup.get("winner_team_key")),
                "teams": teams,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "week": _integer(scoreboard.get("week") or league.get("matchup_week")),
        "matchups": normalized_matchups,
    }


def normalize_player(player_node: Any) -> dict[str, Any] | None:
    player = as_mapping(player_node)
    name = as_mapping(player.get("name"))
    selected_position = as_mapping(player.get("selected_position"))
    player_key = _text(player.get("player_key"))
    player_name = _text(name.get("full") or player.get("name"))
    if not player_key and not player_name:
        return None

    return {
        "player_key": player_key,
        "player_name": player_name,
        "nfl_team": _text(
            player.get("editorial_team_abbr") or player.get("editorial_team_full_name")
        ),
        "primary_position": _text(
            player.get("primary_position") or player.get("display_position")
        ),
        "selected_position": _text(selected_position.get("position")),
        "status": _text(player.get("status")),
    }


def normalize_roster(
    data: Any,
    *,
    fallback_team: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    fantasy_content = _fantasy_content(data)
    team_node = fantasy_content.get("team")
    team = as_mapping(team_node)
    public_team = normalize_team(team_node) or dict(fallback_team or {})
    roster = as_mapping(team.get("roster"))
    players_container = nested_section(roster, "players")
    players: list[dict[str, Any]] = []

    for node in entity_nodes(players_container, "player"):
        player = normalize_player(node)
        if player:
            players.append(player)

    return {
        "team_key": public_team.get("team_key"),
        "team_id": public_team.get("team_id"),
        "team_name": public_team.get("team_name"),
        "players": players,
    }


def normalize_rosters(
    roster_payloads: Mapping[str, Any] | None,
    teams: Iterable[Mapping[str, Any]],
    *,
    week: int | None,
) -> dict[str, Any]:
    payloads = roster_payloads or {}
    normalized: list[dict[str, Any]] = []
    for team in teams:
        team_key = _text(team.get("team_key"))
        payload = payloads.get(team_key) if team_key else None
        if payload is None:
            normalized.append(
                {
                    "team_key": team_key,
                    "team_id": team.get("team_id"),
                    "team_name": team.get("team_name"),
                    "players": [],
                }
            )
        else:
            normalized.append(normalize_roster(payload, fallback_team=team))

    return {"schema_version": SCHEMA_VERSION, "week": week, "teams": normalized}


def build_public_payloads(
    *,
    league_data: Any,
    teams_data: Any,
    standings_data: Any,
    scoreboard_data: Any,
    roster_payloads: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build every allowlisted public file from Yahoo API responses."""

    league = normalize_league(league_data)
    teams = normalize_teams(teams_data)
    standings = normalize_standings(standings_data)
    matchups = normalize_matchups(scoreboard_data)
    rosters = normalize_rosters(
        roster_payloads,
        teams["teams"],
        week=matchups["week"],
    )
    league_record = league["league"]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "season": league_record.get("season"),
        "source_update_timestamp": league_record.get("source_update_timestamp"),
        "status": "ready" if teams["teams"] and standings["standings"] else "unavailable",
    }
    return {
        "manifest.json": manifest,
        "league.json": league,
        "teams.json": teams,
        "standings.json": standings,
        "matchups.json": matchups,
        "rosters.json": rosters,
    }
