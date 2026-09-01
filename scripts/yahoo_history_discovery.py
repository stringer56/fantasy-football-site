"""Pure helpers for safe Yahoo Fantasy historical league discovery."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict, deque
from typing import Any, Iterable, Mapping

from yahoo_normalize import as_mapping


SCHEMA_VERSION = 1
EXPECTED_LEAGUE_NAME = "Road To Glory FFL"
CAPABILITY_NAMES = (
    "league_metadata",
    "teams",
    "standings",
    "weekly_matchups",
    "final_playoff_matchups",
    "rosters",
    "draft_results",
    "transactions",
)
FORBIDDEN_PUBLIC_KEYS = {
    "access_token",
    "account_id",
    "authorization",
    "client_id",
    "client_secret",
    "edit_url",
    "email",
    "email_address",
    "guid",
    "ip",
    "ip_address",
    "iris_group_chat_id",
    "manager_id",
    "password",
    "refresh_token",
    "short_invitation_url",
}
FORBIDDEN_TEXT = ("authorization:", "/invitation?key=", "&ikey=", "bearer ")


def text(value: Any) -> str | None:
    if value is None:
        return None
    candidate = str(value).strip()
    return candidate or None


def integer(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def boolean(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    return None


def normalized_name(value: Any) -> str:
    candidate = unicodedata.normalize("NFKC", text(value) or "")
    candidate = candidate.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", candidate).strip().casefold()


def parse_league_key(value: Any) -> tuple[str, str] | None:
    """Return (game_key, league_id) for a Yahoo global league key."""

    candidate = text(value)
    if not candidate:
        return None
    match = re.fullmatch(r"([A-Za-z0-9]+)\.l\.(\d+)", candidate)
    return (match.group(1), match.group(2)) if match else None


def parse_renewal_key(value: Any) -> str | None:
    """Convert Yahoo's ``gameKey_leagueId`` renewal value to a league key."""

    candidate = text(value)
    if not candidate:
        return None
    if parse_league_key(candidate):
        return candidate
    match = re.fullmatch(r"([A-Za-z0-9]+)_(\d+)", candidate)
    return f"{match.group(1)}.l.{match.group(2)}" if match else None


def walk_named(value: Any, name: str) -> Iterable[Any]:
    """Yield named Yahoo resources through numbered/list response wrappers."""

    if isinstance(value, dict):
        for key, child in value.items():
            if key == name:
                yield child
            else:
                yield from walk_named(child, name)
    elif isinstance(value, list):
        for child in value:
            yield from walk_named(child, name)


def normalize_game(node: Any) -> dict[str, Any] | None:
    game = as_mapping(node)
    game_key = text(game.get("game_key"))
    if not game_key:
        return None
    return {
        "game_key": game_key,
        "game_code": text(game.get("code")),
        "season": integer(game.get("season")),
    }


def extract_games(payload: Any) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for node in walk_named(payload, "game"):
        game = normalize_game(node)
        if game:
            by_key[game["game_key"]] = game
    return sorted(by_key.values(), key=lambda row: (row.get("season") or 0, row["game_key"]))


def normalize_league(node: Any) -> dict[str, Any] | None:
    league = as_mapping(node)
    league_key = text(league.get("league_key"))
    parsed = parse_league_key(league_key)
    if not parsed:
        return None
    game_key, league_id = parsed
    return {
        "season": integer(league.get("season")),
        "game_key": game_key,
        "league_key": league_key,
        "league_id": text(league.get("league_id")) or league_id,
        "league_name": text(league.get("name")),
        "number_of_teams": integer(league.get("num_teams")),
        "draft_status": text(league.get("draft_status")),
        "current_week": integer(league.get("current_week")),
        "start_date": text(league.get("start_date")),
        "end_date": text(league.get("end_date")),
        "start_week": integer(league.get("start_week")),
        "end_week": integer(league.get("end_week")),
        "finished": boolean(league.get("is_finished")),
        "previous_league_key": parse_renewal_key(league.get("renew")),
        "next_league_key": parse_renewal_key(league.get("renewed")),
    }


def extract_leagues(payload: Any) -> list[dict[str, Any]]:
    """Extract and de-duplicate safe league metadata."""

    by_key: dict[str, dict[str, Any]] = {}
    for node in walk_named(payload, "league"):
        league = normalize_league(node)
        if league:
            existing = by_key.get(league["league_key"], {})
            by_key[league["league_key"]] = {
                key: value if value is not None else existing.get(key)
                for key, value in {**existing, **league}.items()
            }
    return sorted(by_key.values(), key=lambda row: (row.get("season") or 0, row["league_key"]))


def renewal_chain(
    leagues: Iterable[Mapping[str, Any]], anchor_key: str
) -> tuple[list[str], list[str]]:
    """Return linked keys and missing links reachable from an authenticated anchor."""

    by_key = {str(row["league_key"]): row for row in leagues if row.get("league_key")}
    linked: set[str] = set()
    missing: set[str] = set()
    queue: deque[str] = deque([anchor_key])
    while queue:
        key = queue.popleft()
        if key in linked:
            continue
        row = by_key.get(key)
        if row is None:
            missing.add(key)
            continue
        linked.add(key)
        for field in ("previous_league_key", "next_league_key"):
            relation = text(row.get(field))
            if relation and relation not in linked:
                queue.append(relation)
    ordered = sorted(linked, key=lambda key: (by_key[key].get("season") or 0, key))
    return ordered, sorted(missing)


def franchise_alias_index(franchises: Iterable[Mapping[str, Any]]) -> dict[str, set[str]]:
    index: defaultdict[str, set[str]] = defaultdict(set)
    for franchise in franchises:
        franchise_id = text(franchise.get("franchise_id"))
        if not franchise_id:
            continue
        names = [franchise.get("name"), *(franchise.get("aliases") or [])]
        names.extend(((franchise.get("yahoo") or {}).get("team_names") or {}).values())
        for name in names:
            if text(name):
                index[normalized_name(name)].add(franchise_id)
    return dict(index)


def map_team(
    *,
    season: int,
    team_key: str | None,
    team_name: str | None,
    franchises: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Resolve only a season key or one unambiguous approved public alias."""

    franchise_list = list(franchises)
    for franchise in franchise_list:
        known_keys = ((franchise.get("yahoo") or {}).get("team_keys") or {})
        if team_key and known_keys.get(str(season)) == team_key:
            return {
                "candidate_franchise_id": franchise["franchise_id"],
                "status": "verified",
                "basis": "season_team_key",
            }
    matches = franchise_alias_index(franchise_list).get(normalized_name(team_name), set())
    if len(matches) == 1:
        return {
            "candidate_franchise_id": next(iter(matches)),
            "status": "verified",
            "basis": "unique_canonical_name_or_alias",
        }
    return {
        "candidate_franchise_id": None,
        "status": "unresolved",
        "basis": None,
    }


def safe_team_mapping(
    *,
    season: int,
    team_key: str | None,
    team_name: str | None,
    franchises: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    mapping = map_team(
        season=season,
        team_key=team_key,
        team_name=team_name,
        franchises=franchises,
    )
    return {
        "season": season,
        "yahoo_team_key": team_key,
        "yahoo_team_name": team_name,
        **mapping,
    }


def safe_league(row: Mapping[str, Any], *, verification_status: str) -> dict[str, Any]:
    return {
        "season": row.get("season"),
        "game_key": row.get("game_key"),
        "league_key": row.get("league_key"),
        "league_id": row.get("league_id"),
        "league_name": row.get("league_name"),
        "number_of_teams": row.get("number_of_teams"),
        "draft_status": row.get("draft_status"),
        "current_week": row.get("current_week"),
        "start_week": row.get("start_week"),
        "end_week": row.get("end_week"),
        "start_date": row.get("start_date"),
        "end_date": row.get("end_date"),
        "finished": row.get("finished"),
        "previous_league_key": row.get("previous_league_key"),
        "next_league_key": row.get("next_league_key"),
        "verification_status": verification_status,
        "capabilities": {
            name: (row.get("capabilities") or {}).get(name, "not_probed")
            for name in CAPABILITY_NAMES
        },
        "team_mappings": list(row.get("team_mappings") or []),
        "archive_coverage": row.get("archive_coverage"),
    }


def validate_safe_output(payload: Any) -> list[str]:
    """Reject private field names and common credential-bearing text."""

    errors: list[str] = []

    def inspect(value: Any, location: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.casefold() in FORBIDDEN_PUBLIC_KEYS:
                    errors.append(f"forbidden key at {location}.{key}")
                inspect(child, f"{location}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, f"{location}[{index}]")
        elif isinstance(value, str):
            lowered = value.casefold()
            if any(fragment in lowered for fragment in FORBIDDEN_TEXT):
                errors.append(f"forbidden private text at {location}")

    inspect(payload, "root")
    return errors
