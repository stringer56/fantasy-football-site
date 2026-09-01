"""Validate the canonical Yahoo league map and sanitized history archives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_public_data import validate_payload
from yahoo_history import load_yaml, parse_renewal_key


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data"
PRIVATE_KEYS = {
    "access_token", "refresh_token", "client_secret", "guid", "manager_id",
    "email", "email_address", "ip", "ip_address", "account_id", "auth_token",
    "edit_url", "short_invitation_url", "iris_group_chat_id", "xoauth_yahoo_guid",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError(f"{path}: expected a schema_version 1 object")
    return payload


def inspect_private(value: Any, path: Path, location: str = "root") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in PRIVATE_KEYS:
                errors.append(f"{path}: forbidden private key at {location}.{key}")
            errors.extend(inspect_private(child, path, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(inspect_private(child, path, f"{location}[{index}]"))
    return errors


def validate_league_map(payload: dict[str, Any]) -> tuple[list[str], dict[int, dict[str, Any]]]:
    errors: list[str] = []
    by_season: dict[int, dict[str, Any]] = {}
    by_key: dict[str, dict[str, Any]] = {}
    for row in payload.get("leagues") or []:
        season = row.get("season")
        key = row.get("league_key")
        if not isinstance(season, int) or season in by_season:
            errors.append(f"_data/yahoo_leagues.yml: duplicate or invalid season {season!r}")
            continue
        if parse_renewal_key(key) != key or key in by_key:
            errors.append(f"_data/yahoo_leagues.yml: invalid or duplicate league key {key!r}")
        if not row.get("verified"):
            errors.append(f"_data/yahoo_leagues.yml: unverified candidates do not belong in canonical leagues ({season})")
        source = row.get("source") or {}
        if not source.get("type") or not source.get("evidence") or not source.get("verified_on"):
            errors.append(f"_data/yahoo_leagues.yml: season {season} lacks source provenance")
        if str(row.get("game_key")) != str(key).split(".l.", 1)[0]:
            errors.append(f"_data/yahoo_leagues.yml: season {season} game key does not match league key")
        if str(row.get("league_id")) != str(key).split(".l.", 1)[1]:
            errors.append(f"_data/yahoo_leagues.yml: season {season} league ID does not match league key")
        by_season[season] = row
        by_key[key] = row
    for season, row in by_season.items():
        previous = row.get("previous_league_key")
        next_key = row.get("next_league_key")
        if previous in by_key and by_key[previous].get("next_league_key") != row["league_key"]:
            errors.append(f"_data/yahoo_leagues.yml: season {season} previous link is not reciprocal")
        if next_key in by_key and by_key[next_key].get("previous_league_key") != row["league_key"]:
            errors.append(f"_data/yahoo_leagues.yml: season {season} next link is not reciprocal")
    return errors, by_season


def validate_matchups(path: Path, payload: dict[str, Any], franchise_ids: set[str]) -> list[str]:
    errors = inspect_private(payload, path)
    season = payload.get("season")
    coverage = payload.get("coverage") or {}
    expected = set(coverage.get("expected_weeks") or [])
    fetched = set(coverage.get("fetched_weeks") or [])
    missing = set(coverage.get("missing_weeks") or [])
    if fetched | missing != expected or fetched & missing:
        errors.append(f"{path}: fetched/missing week coverage does not partition expected weeks")
    seen_ids: set[str] = set()
    for row in payload.get("matchups") or []:
        matchup_id = row.get("matchup_id")
        if not matchup_id or matchup_id in seen_ids:
            errors.append(f"{path}: duplicate or empty matchup ID {matchup_id!r}")
        seen_ids.add(matchup_id)
        if row.get("season") != season or not isinstance(row.get("week"), int):
            errors.append(f"{path}: matchup {matchup_id} has invalid season/week")
        sides = [row.get("team_a") or {}, row.get("team_b") or {}]
        keys = {side.get("yahoo_team_key") for side in sides}
        for side in sides:
            score = side.get("score")
            if score is not None and not isinstance(score, (int, float)):
                errors.append(f"{path}: matchup {matchup_id} has a nonnumeric score")
            franchise_id = side.get("franchise_id")
            if franchise_id is not None and franchise_id not in franchise_ids:
                errors.append(f"{path}: matchup {matchup_id} references unknown franchise {franchise_id}")
            if franchise_id is None and side.get("mapping_status") not in {"unresolved", "ambiguous"}:
                errors.append(f"{path}: matchup {matchup_id} hides an unresolved mapping")
        winner_key = row.get("winner_yahoo_team_key")
        if row.get("tie") and (winner_key or row.get("winner_franchise_id")):
            errors.append(f"{path}: tied matchup {matchup_id} has a winner")
        if winner_key and winner_key not in keys:
            errors.append(f"{path}: matchup {matchup_id} winner does not participate")
        a_score, b_score = sides[0].get("score"), sides[1].get("score")
        if row.get("verified") and a_score is not None and b_score is not None:
            if row.get("tie") != (a_score == b_score):
                errors.append(f"{path}: matchup {matchup_id} tie flag conflicts with scores")
            if not row.get("tie"):
                expected_key = sides[0].get("yahoo_team_key") if a_score > b_score else sides[1].get("yahoo_team_key")
                if winner_key != expected_key:
                    errors.append(f"{path}: matchup {matchup_id} winner conflicts with scores")
    return errors


def validate_team_weeks(path: Path, payload: dict[str, Any], matchup_ids: set[str], franchise_ids: set[str]) -> list[str]:
    errors = inspect_private(payload, path)
    seen: set[tuple[str, str]] = set()
    for row in payload.get("team_weeks") or []:
        matchup_id = row.get("matchup_id")
        key = (matchup_id, row.get("yahoo_team_key"))
        if matchup_id not in matchup_ids or key in seen:
            errors.append(f"{path}: duplicate or unknown team-week reference {key}")
        seen.add(key)
        if row.get("franchise_id") is not None and row["franchise_id"] not in franchise_ids:
            errors.append(f"{path}: unknown franchise {row['franchise_id']}")
        if row.get("score") is not None and not isinstance(row["score"], (int, float)):
            errors.append(f"{path}: team-week score is not numeric")
        if row.get("margin") is not None and not isinstance(row["margin"], (int, float)):
            errors.append(f"{path}: team-week margin is not numeric")
    return errors


def validate_player_weeks(path: Path, payload: dict[str, Any], franchise_ids: set[str]) -> list[str]:
    errors = inspect_private(payload, path)
    coverage = payload.get("coverage") or {}
    players = payload.get("player_weeks") or []
    player_index = {}
    for row in players:
        key = (row.get("season"), row.get("week"), row.get("yahoo_team_key"), row.get("player_key"))
        if key in player_index:
            errors.append(f"{path}: duplicate player-week {key}")
        player_index[key] = row
        if row.get("franchise_id") is not None and row["franchise_id"] not in franchise_ids:
            errors.append(f"{path}: unknown player-week franchise {row['franchise_id']}")
        if row.get("fantasy_points") is not None and not isinstance(row["fantasy_points"], (int, float)):
            errors.append(f"{path}: player fantasy points are not numeric")
        expected_role = "bench" if str(row.get("selected_position") or "").upper() in {"BN", "BE", "BENCH"} else "starter"
        if row.get("starter_or_bench") != expected_role:
            errors.append(f"{path}: player bench classification conflicts with selected position")
    bench = payload.get("bench_scores") or []
    if bench and not coverage.get("bench_reconstruction_possible"):
        errors.append(f"{path}: bench scores exist without complete bench coverage")
    for entry in bench:
        matches = [row for row in players if row.get("season") == entry.get("year") and row.get("week") == entry.get("week") and row.get("player_name") == entry.get("player_name")]
        if not matches or matches[0].get("starter_or_bench") != "bench" or matches[0].get("fantasy_points") != entry.get("points_missed"):
            errors.append(f"{path}: bench entry is not supported by a verified player-week")
    return errors


def validate_rosters(path: Path, payload: dict[str, Any], franchise_ids: set[str]) -> list[str]:
    errors = inspect_private(payload, path)
    seen: set[tuple[int, str]] = set()
    for roster in payload.get("rosters") or []:
        key = (roster.get("week"), roster.get("yahoo_team_key"))
        if not isinstance(key[0], int) or not key[1] or key in seen:
            errors.append(f"{path}: duplicate or invalid roster reference {key}")
        seen.add(key)
        franchise_id = roster.get("franchise_id")
        if franchise_id is not None and franchise_id not in franchise_ids:
            errors.append(f"{path}: unknown roster franchise {franchise_id}")
        if franchise_id is None and roster.get("mapping_status") not in {"unresolved", "ambiguous"}:
            errors.append(f"{path}: roster hides an unresolved franchise mapping")
        player_keys: set[str] = set()
        for player in roster.get("players") or []:
            player_key = player.get("player_key")
            if not player_key or player_key in player_keys or not player.get("player_name"):
                errors.append(f"{path}: duplicate or invalid player in roster {key}")
            player_keys.add(player_key)
    return errors


def validate_head_to_head(path: Path, payload: dict[str, Any], franchise_ids: set[str]) -> list[str]:
    errors = inspect_private(payload, path)
    coverage = payload.get("coverage") or {}
    pairs = payload.get("pairs") or []
    if coverage.get("status") == "unavailable" and pairs:
        errors.append(f"{path}: unavailable head-to-head coverage contains values")
    if coverage.get("status") != "complete" and "all-time" in str(coverage.get("label") or "").lower():
        errors.append(f"{path}: partial head-to-head coverage claims all-time")
    seen: set[tuple[str, str]] = set()
    games = 0
    for pair in pairs:
        key = (pair.get("franchise_a"), pair.get("franchise_b"))
        if key[0] not in franchise_ids or key[1] not in franchise_ids or key[0] >= key[1] or key in seen:
            errors.append(f"{path}: invalid or duplicate franchise pair {key}")
        seen.add(key)
        if pair.get("games") != pair.get("wins_a", 0) + pair.get("wins_b", 0) + pair.get("ties", 0):
            errors.append(f"{path}: pair {key} totals do not reconcile")
        games += pair.get("games", 0)
    if games != coverage.get("games_counted"):
        errors.append(f"{path}: head-to-head games_counted does not reconcile")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DATA / "generated" / "yahoo_history_manifest.json")
    parser.add_argument("--history-root", type=Path, default=DATA / "generated" / "history")
    parser.add_argument("--head-to-head", type=Path, default=DATA / "generated" / "head_to_head.json")
    args = parser.parse_args()
    errors: list[str] = []
    yahoo_leagues = load_yaml(DATA / "yahoo_leagues.yml")
    map_errors, leagues_by_season = validate_league_map(yahoo_leagues)
    errors.extend(map_errors)
    franchises = load_yaml(DATA / "franchises.yml")["franchises"]
    franchise_ids = {row["franchise_id"] for row in franchises}

    manifest = load_json(args.manifest)
    errors.extend(validate_payload(args.manifest, manifest))
    errors.extend(inspect_private(manifest, args.manifest))
    manifest_seasons = {row.get("season") for row in manifest.get("verified_leagues") or []}
    if manifest_seasons != set(leagues_by_season):
        errors.append(f"{args.manifest}: verified seasons do not match canonical Yahoo league map")
    for row in manifest.get("verified_leagues") or []:
        canonical = leagues_by_season.get(row.get("season"))
        if canonical and row.get("league_key") != canonical.get("league_key"):
            errors.append(f"{args.manifest}: season {row.get('season')} league key conflicts with canonical map")

    matchup_count = 0
    archived_seasons = 0
    if args.history_root.exists():
        for matchups_path in sorted(args.history_root.glob("*/matchups.json")):
            archived_seasons += 1
            matchups = load_json(matchups_path)
            if matchups.get("season") not in leagues_by_season:
                errors.append(f"{matchups_path}: archive season is not a verified Yahoo league")
            errors.extend(validate_matchups(matchups_path, matchups, franchise_ids))
            matchup_ids = {row["matchup_id"] for row in matchups.get("matchups") or []}
            matchup_count += len(matchup_ids)
            team_weeks_path = matchups_path.with_name("team_weeks.json")
            if team_weeks_path.is_file():
                team_weeks = load_json(team_weeks_path)
                errors.extend(validate_team_weeks(team_weeks_path, team_weeks, matchup_ids, franchise_ids))
            player_weeks_path = matchups_path.with_name("player_weeks.json")
            if player_weeks_path.is_file():
                player_weeks = load_json(player_weeks_path)
                errors.extend(validate_player_weeks(player_weeks_path, player_weeks, franchise_ids))
            rosters_path = matchups_path.with_name("rosters.json")
            if rosters_path.is_file():
                rosters = load_json(rosters_path)
                errors.extend(validate_rosters(rosters_path, rosters, franchise_ids))

    head_to_head = load_json(args.head_to_head)
    errors.extend(validate_payload(args.head_to_head, head_to_head))
    errors.extend(validate_head_to_head(args.head_to_head, head_to_head, franchise_ids))
    if errors:
        print("Yahoo history validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(
        f"Validated {len(leagues_by_season)} verified Yahoo league keys, "
        f"{archived_seasons} archived seasons, {matchup_count} weekly matchups, "
        f"and {len(head_to_head.get('pairs') or [])} head-to-head pairs"
    )


if __name__ == "__main__":
    main()
