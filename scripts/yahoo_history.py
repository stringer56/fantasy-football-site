"""Pure helpers for sanitized Yahoo historical discovery and aggregation."""

from __future__ import annotations

import json
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import requests
import yaml

from yahoo_normalize import (
    as_mapping,
    entity_nodes,
    nested_section,
    normalize_matchups,
)


SCHEMA_VERSION = 1
API_ROOT = "https://fantasysports.yahooapis.com/fantasy/v2"
COMPLETED_STATUSES = {"postevent", "complete", "completed"}
BENCH_POSITIONS = {"BN", "BE", "BENCH"}


def text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def integer(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def normalize_identity(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKC", value or "")
    normalized = normalized.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def parse_renewal_key(value: Any) -> str | None:
    """Convert Yahoo's renewal shorthand to a global league key."""

    candidate = text(value)
    if not candidate:
        return None
    if re.fullmatch(r"\d+\.l\.\d+", candidate):
        return candidate
    match = re.fullmatch(r"(\d+)_(\d+)", candidate)
    return f"{match.group(1)}.l.{match.group(2)}" if match else None


def walk_named_entities(value: Any, entity_name: str) -> Iterable[Any]:
    """Yield Yahoo resources from deeply numbered user/game collections."""

    if isinstance(value, dict):
        for key, child in value.items():
            if key == entity_name:
                yield child
            else:
                yield from walk_named_entities(child, entity_name)
    elif isinstance(value, list):
        for child in value:
            yield from walk_named_entities(child, entity_name)


def normalize_league_metadata(node: Any) -> dict[str, Any] | None:
    league = as_mapping(node)
    league_key = text(league.get("league_key"))
    league_id = text(league.get("league_id"))
    season = integer(league.get("season"))
    if not league_key and not league_id:
        return None
    game_key = league_key.split(".l.", 1)[0] if league_key and ".l." in league_key else None
    return {
        "season": season,
        "game_key": game_key,
        "league_key": league_key,
        "league_id": league_id,
        "league_name": text(league.get("name")),
        "number_of_teams": integer(league.get("num_teams")),
        "start_week": integer(league.get("start_week")),
        "end_week": integer(league.get("end_week")),
        "current_week": integer(league.get("current_week")),
        "playoff_start_week": integer(league.get("playoff_start_week")),
        "previous_league_key": parse_renewal_key(league.get("renew")),
        "next_league_key": parse_renewal_key(league.get("renewed")),
    }


def extract_leagues(payload: Any) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for node in walk_named_entities(payload, "league"):
        normalized = normalize_league_metadata(node)
        if normalized and normalized.get("league_key"):
            records[normalized["league_key"]] = normalized
    return sorted(records.values(), key=lambda row: (row.get("season") or 0, row["league_key"]))


def extract_games(payload: Any) -> list[dict[str, Any]]:
    games: dict[str, dict[str, Any]] = {}
    for node in walk_named_entities(payload, "game"):
        game = as_mapping(node)
        game_key = text(game.get("game_key"))
        if not game_key:
            continue
        games[game_key] = {
            "game_key": game_key,
            "game_code": text(game.get("code")),
            "season": integer(game.get("season")),
            "name": text(game.get("name")),
        }
    return sorted(games.values(), key=lambda row: (row.get("season") or 0, row["game_key"]))


def classify_discovery(
    discovered: Iterable[dict[str, Any]],
    canonical: Iterable[dict[str, Any]],
    *,
    expected_name: str = "Road To Glory FFL",
) -> dict[str, list[dict[str, Any]]]:
    """Separate verified, candidate, and ambiguous league results."""

    canonical_by_key = {row["league_key"]: row for row in canonical if row.get("verified")}
    expected = normalize_identity(expected_name)
    candidates_by_season: defaultdict[int | None, list[dict[str, Any]]] = defaultdict(list)
    verified: list[dict[str, Any]] = []

    for row in discovered:
        key = row.get("league_key")
        name_matches = normalize_identity(row.get("league_name")) == expected
        linked = (
            key in canonical_by_key
            or row.get("previous_league_key") in canonical_by_key
            or row.get("next_league_key") in canonical_by_key
        )
        candidate = {**row, "name_matches": name_matches, "renewal_link_matches": linked}
        if key in canonical_by_key:
            verified.append(candidate)
        elif name_matches or linked:
            candidates_by_season[row.get("season")].append(candidate)

    unverified: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    for season, rows in candidates_by_season.items():
        target = ambiguous if len(rows) > 1 else unverified
        target.extend({**row, "season": season} for row in rows)
    return {
        "verified": sorted(verified, key=lambda row: (row.get("season") or 0, row["league_key"])),
        "unverified": sorted(unverified, key=lambda row: (row.get("season") or 0, row["league_key"])),
        "ambiguous": sorted(ambiguous, key=lambda row: (row.get("season") or 0, row["league_key"])),
    }


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path}: expected a schema_version 1 mapping")
    return payload


def build_committed_manifest(
    yahoo_leagues: dict[str, Any], site: dict[str, Any]
) -> dict[str, Any]:
    verified = sorted(
        (row for row in yahoo_leagues.get("leagues") or [] if row.get("verified")),
        key=lambda row: row["season"],
    )
    verified_dates = [
        str((row.get("source") or {}).get("verified_on"))
        for row in verified
        if (row.get("source") or {}).get("verified_on")
    ]
    generated_at = f"{max(verified_dates)}T00:00:00Z" if verified_dates else None
    public_verified = [
        {
            "season": row["season"],
            "game_key": str(row["game_key"]),
            "league_key": row["league_key"],
            "league_id": str(row["league_id"]),
            "previous_league_key": row.get("previous_league_key"),
            "next_league_key": row.get("next_league_key"),
            "source_type": (row.get("source") or {}).get("type"),
        }
        for row in verified
    ]
    current_season = int(site["current_season"])
    current_verified = any(row["season"] == current_season for row in verified)
    configured = site.get("yahoo") or {}
    unverified = [] if current_verified else [{
        "season": current_season,
        "configured_alias": configured.get("league_alias"),
        "league_id": str(configured.get("league_alias") or "").rsplit(".", 1)[-1] or None,
        "status": "authentication_required",
        "source": "_data/site.yml",
    }]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "partial" if public_verified else "unavailable",
        "verified_leagues": public_verified,
        "unverified_candidates": unverified,
        "ambiguous_candidates": [],
        "archive_coverage": {
            "matchup_seasons": [],
            "roster_seasons": [],
            "player_point_seasons": [],
            "complete_weekly_matchups": 0,
        },
        "notes": [
            "Verified league identity does not imply that weekly Yahoo archives have been recovered.",
            "The configured 2026 alias is not a resolved season-specific league key.",
            "No ambiguous candidate is promoted into the verified renewal chain.",
        ],
    }


def franchise_alias_index(franchises: Iterable[dict[str, Any]]) -> dict[str, set[str]]:
    index: defaultdict[str, set[str]] = defaultdict(set)
    for franchise in franchises:
        names = [franchise.get("name"), *(franchise.get("aliases") or [])]
        names.extend(((franchise.get("yahoo") or {}).get("team_names") or {}).values())
        for name in names:
            if text(name):
                index[normalize_identity(str(name))].add(franchise["franchise_id"])
    return dict(index)


def resolve_franchise(
    *,
    season: int,
    team_key: str | None,
    team_name: str | None,
    franchises: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    franchise_list = list(franchises)
    for franchise in franchise_list:
        keys = ((franchise.get("yahoo") or {}).get("team_keys") or {})
        if team_key and keys.get(str(season)) == team_key:
            return {
                "franchise_id": franchise["franchise_id"],
                "mapping_status": "resolved",
                "mapping_basis": "season_team_key",
            }
    matches = franchise_alias_index(franchise_list).get(normalize_identity(team_name), set())
    if len(matches) == 1:
        return {
            "franchise_id": next(iter(matches)),
            "mapping_status": "resolved",
            "mapping_basis": "verified_canonical_alias",
        }
    return {
        "franchise_id": None,
        "mapping_status": "ambiguous" if len(matches) > 1 else "unresolved",
        "mapping_basis": None,
    }


def _matchup_id(season: int, week: int, teams: list[dict[str, Any]]) -> str:
    tokens = []
    for team in teams:
        value = team.get("team_id") or team.get("team_key") or team.get("team_name") or "unknown"
        tokens.append(re.sub(r"[^a-zA-Z0-9]+", "-", str(value)).strip("-").lower())
    return f"{season}-w{week:02d}-{'-'.join(sorted(tokens))}"


def normalize_history_matchups(
    payload: Any,
    *,
    season: int,
    league_key: str,
    franchises: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized = normalize_matchups(payload)
    week = normalized.get("week")
    if week is None:
        return []
    output: list[dict[str, Any]] = []
    for matchup in normalized.get("matchups") or []:
        teams = matchup.get("teams") or []
        if len(teams) != 2:
            continue
        public_teams = []
        for team in teams:
            mapping = resolve_franchise(
                season=season,
                team_key=team.get("team_key"),
                team_name=team.get("team_name"),
                franchises=franchises,
            )
            public_teams.append({
                "yahoo_team_key": team.get("team_key"),
                "franchise_id": mapping["franchise_id"],
                "historical_team_name": team.get("team_name"),
                "score": team.get("score"),
                "mapping_status": mapping["mapping_status"],
                "mapping_basis": mapping["mapping_basis"],
            })
        winner_key = matchup.get("winner_team_key")
        winner = next((team for team in public_teams if team["yahoo_team_key"] == winner_key), None)
        tied = bool(matchup.get("is_tied"))
        status = (matchup.get("status") or "").lower()
        output.append({
            "season": season,
            "week": int(week),
            "matchup_id": _matchup_id(season, int(week), teams),
            "status": matchup.get("status"),
            "is_playoffs": bool(matchup.get("is_playoffs")),
            "is_consolation": bool(matchup.get("is_consolation")),
            "team_a": public_teams[0],
            "team_b": public_teams[1],
            "winner_yahoo_team_key": winner_key,
            "winner_franchise_id": winner.get("franchise_id") if winner else None,
            "winner_historical_name": winner.get("historical_team_name") if winner else None,
            "tie": tied,
            "source": {
                "type": "yahoo_fantasy_api",
                "league_key": league_key,
                "resource": f"scoreboard;week={week}",
            },
            "verified": status in COMPLETED_STATUSES and (tied or winner is not None),
        })
    return sorted(output, key=lambda row: row["matchup_id"])


def build_team_weeks(matchups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for matchup in matchups:
        teams = [matchup["team_a"], matchup["team_b"]]
        for index, team in enumerate(teams):
            opponent = teams[1 - index]
            score = team.get("score")
            opponent_score = opponent.get("score")
            if matchup.get("tie"):
                result = "tie"
            elif matchup.get("winner_yahoo_team_key"):
                result = "win" if team.get("yahoo_team_key") == matchup["winner_yahoo_team_key"] else "loss"
            else:
                result = None
            margin = round(score - opponent_score, 2) if score is not None and opponent_score is not None else None
            output.append({
                "season": matchup["season"],
                "week": matchup["week"],
                "matchup_id": matchup["matchup_id"],
                "yahoo_team_key": team.get("yahoo_team_key"),
                "franchise_id": team.get("franchise_id"),
                "historical_team_name": team.get("historical_team_name"),
                "score": score,
                "opponent_franchise_id": opponent.get("franchise_id"),
                "opponent_name": opponent.get("historical_team_name"),
                "result": result,
                "margin": margin,
                "playoff": matchup.get("is_playoffs"),
                "source": matchup.get("source"),
            })
    return sorted(output, key=lambda row: (row["season"], row["week"], row["matchup_id"], row.get("historical_team_name") or ""))


def build_head_to_head(matchups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: dict[tuple[str, str], dict[str, Any]] = {}
    for matchup in matchups:
        a = matchup["team_a"]
        b = matchup["team_b"]
        if not matchup.get("verified") or not a.get("franchise_id") or not b.get("franchise_id"):
            continue
        if a.get("score") is None or b.get("score") is None:
            continue
        by_id = {a["franchise_id"]: a, b["franchise_id"]: b}
        franchise_a, franchise_b = sorted(by_id)
        left, right = by_id[franchise_a], by_id[franchise_b]
        key = (franchise_a, franchise_b)
        pair = pairs.setdefault(key, {
            "franchise_a": franchise_a,
            "franchise_b": franchise_b,
            "games": 0,
            "wins_a": 0,
            "wins_b": 0,
            "ties": 0,
            "points_a": 0.0,
            "points_b": 0.0,
            "largest_win_a": None,
            "largest_win_b": None,
            "last_meeting": None,
            "season_breakdown": {},
        })
        pair["games"] += 1
        pair["points_a"] = round(pair["points_a"] + left["score"], 2)
        pair["points_b"] = round(pair["points_b"] + right["score"], 2)
        season = str(matchup["season"])
        breakdown = pair["season_breakdown"].setdefault(season, {"games": 0, "wins_a": 0, "wins_b": 0, "ties": 0})
        breakdown["games"] += 1
        if matchup.get("tie"):
            pair["ties"] += 1
            breakdown["ties"] += 1
        elif matchup.get("winner_franchise_id") == franchise_a:
            pair["wins_a"] += 1
            breakdown["wins_a"] += 1
            margin = round(left["score"] - right["score"], 2)
            pair["largest_win_a"] = max(pair["largest_win_a"] or margin, margin)
        elif matchup.get("winner_franchise_id") == franchise_b:
            pair["wins_b"] += 1
            breakdown["wins_b"] += 1
            margin = round(right["score"] - left["score"], 2)
            pair["largest_win_b"] = max(pair["largest_win_b"] or margin, margin)
        meeting = {"season": matchup["season"], "week": matchup["week"], "matchup_id": matchup["matchup_id"]}
        if not pair["last_meeting"] or (meeting["season"], meeting["week"]) > (pair["last_meeting"]["season"], pair["last_meeting"]["week"]):
            pair["last_meeting"] = meeting
    return [pairs[key] for key in sorted(pairs)]


def calculate_streaks(team_weeks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: defaultdict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in team_weeks:
        if row.get("playoff") or not row.get("franchise_id"):
            continue
        groups[(row["season"], row["franchise_id"])].append(row)
    output = []
    for (season, franchise_id), rows in sorted(groups.items()):
        current_win = current_loss = best_win = best_loss = 0
        for row in sorted(rows, key=lambda item: item["week"]):
            result = row.get("result")
            if result == "win":
                current_win += 1
                current_loss = 0
            elif result == "loss":
                current_loss += 1
                current_win = 0
            else:
                current_win = current_loss = 0
            best_win = max(best_win, current_win)
            best_loss = max(best_loss, current_loss)
        output.append({
            "season": season,
            "franchise_id": franchise_id,
            "longest_win_streak": best_win,
            "longest_loss_streak": best_loss,
        })
    return output


def calculate_margins(matchups: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {"regular_season": [], "playoffs": []}
    for matchup in matchups:
        a, b = matchup["team_a"], matchup["team_b"]
        if not matchup.get("verified") or matchup.get("tie") or a.get("score") is None or b.get("score") is None:
            continue
        winner = a if a.get("yahoo_team_key") == matchup.get("winner_yahoo_team_key") else b
        loser = b if winner is a else a
        entry = {
            "season": matchup["season"],
            "week": matchup["week"],
            "matchup_id": matchup["matchup_id"],
            "winner_franchise_id": winner.get("franchise_id"),
            "winner_historical_name": winner.get("historical_team_name"),
            "loser_franchise_id": loser.get("franchise_id"),
            "loser_historical_name": loser.get("historical_team_name"),
            "winner_score": winner["score"],
            "loser_score": loser["score"],
            "margin": round(winner["score"] - loser["score"], 2),
        }
        groups["playoffs" if matchup.get("is_playoffs") else "regular_season"].append(entry)
    return {
        name: sorted(rows, key=lambda row: (-row["margin"], row["season"], row["week"], row["matchup_id"]))
        for name, rows in groups.items()
    }


def normalize_history_roster(
    payload: Any,
    *,
    season: int,
    week: int,
    team_identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    fantasy = as_mapping(payload.get("fantasy_content") if isinstance(payload, dict) else None)
    team = as_mapping(fantasy.get("team"))
    roster = as_mapping(team.get("roster"))
    players_container = nested_section(roster, "players")
    players: list[dict[str, Any]] = []
    for node in entity_nodes(players_container, "player"):
        player = as_mapping(node)
        name = as_mapping(player.get("name"))
        selected = as_mapping(player.get("selected_position"))
        points = as_mapping(player.get("player_points"))
        player_key = text(player.get("player_key"))
        player_name = text(name.get("full") or player.get("name"))
        if not player_key and not player_name:
            continue
        position = text(selected.get("position"))
        players.append({
            "season": season,
            "week": week,
            "franchise_id": team_identity.get("franchise_id"),
            "historical_team_name": team_identity.get("historical_team_name"),
            "yahoo_team_key": team_identity.get("yahoo_team_key"),
            "player_key": player_key,
            "player_name": player_name,
            "nfl_team": text(player.get("editorial_team_abbr") or player.get("editorial_team_full_name")),
            "primary_position": text(player.get("primary_position") or player.get("display_position")),
            "selected_position": position,
            "starter_or_bench": "bench" if (position or "").upper() in BENCH_POSITIONS else "starter",
            "status": text(player.get("status")),
            "fantasy_points": number(points.get("total") or points.get("value")),
            "source": {
                "type": "yahoo_fantasy_api",
                "resource": f"roster;week={week}/players/stats;type=week;week={week}",
            },
        })
    return sorted(players, key=lambda row: (row.get("player_key") or "", row.get("player_name") or ""))


def build_bench_scores(player_weeks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [row for row in player_weeks if row.get("starter_or_bench") == "bench" and row.get("fantasy_points") is not None]
    ordered = sorted(eligible, key=lambda row: (-row["fantasy_points"], row["season"], row["week"], row.get("player_name") or ""))
    output = []
    previous_value: float | None = None
    previous_rank = 0
    for position, row in enumerate(ordered, start=1):
        rank = previous_rank if previous_value == row["fantasy_points"] else position
        output.append({
            "rank": rank,
            "franchise_id": row.get("franchise_id"),
            "historical_team_name": row.get("historical_team_name"),
            "year": row["season"],
            "week": row["week"],
            "player_name": row.get("player_name"),
            "points_missed": row["fantasy_points"],
            "source": row.get("source"),
        })
        previous_value = row["fantasy_points"]
        previous_rank = rank
    return output


class YahooHistoryClient:
    """Authenticated GET client with bounded retries, delay, and memory cache."""

    def __init__(
        self,
        token: str,
        *,
        session: requests.Session | None = None,
        request_delay: float = 0.25,
        max_retries: int = 4,
        backoff_base: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.token = token
        self.session = session or requests.Session()
        self.request_delay = max(0.0, request_delay)
        self.max_retries = max(0, max_retries)
        self.backoff_base = max(0.0, backoff_base)
        self.sleep = sleep
        self.cache: dict[str, dict[str, Any]] = {}

    def get_json(self, resource: str) -> dict[str, Any]:
        resource = resource.lstrip("/")
        if resource in self.cache:
            return self.cache[resource]
        url = f"{API_ROOT}/{resource}"
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}format=json"
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
                    timeout=30,
                )
                retryable = response.status_code == 429 or response.status_code >= 500
                if retryable and attempt < self.max_retries:
                    retry_after = number(response.headers.get("Retry-After"))
                    self.sleep(retry_after if retry_after is not None else self.backoff_base * (2**attempt))
                    continue
                response.raise_for_status()
                if "application/json" not in response.headers.get("Content-Type", ""):
                    raise ValueError("Yahoo returned a non-JSON response")
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("Yahoo returned a non-object JSON response")
                self.cache[resource] = payload
                if self.request_delay:
                    self.sleep(self.request_delay)
                return payload
            except requests.RequestException as error:
                last_error = error
                status = getattr(getattr(error, "response", None), "status_code", None)
                if status is not None and status != 429 and status < 500:
                    raise
                if attempt >= self.max_retries:
                    raise
                self.sleep(self.backoff_base * (2**attempt))
        raise RuntimeError("Yahoo request failed") from last_error


def write_json_if_changed(path: Path, payload: Any) -> bool:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.is_file() and path.read_text(encoding="utf-8") == serialized:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(path)
    return True
