#!/usr/bin/env python3
"""Validate normalized Yahoo public-archive backfill data and completeness claims."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
HISTORY_ROOT = ROOT / "_data" / "generated" / "history"
COMPLETENESS_PATH = HISTORY_ROOT / "completeness.json"
FRANCHISES_PATH = ROOT / "_data" / "franchises.yml"
CHAMPIONS_PATH = ROOT / "_data" / "champions.yml"
YAHOO_2021_SOURCE_PATH = ROOT / "_data" / "yahoo_history" / "2021.yml"
FORBIDDEN_KEYS = {
    "access_token", "refresh_token", "client_secret", "authorization", "email",
    "guid", "account_id", "manager_id", "invitation_key", "auth_token", "edit_url",
}
SEASON_LEVEL_METRICS = {
    "final_standings", "season_wins_losses_ties", "season_points_for_against",
    "final_rank", "playoff_seed", "verified_championships",
    "resolved_franchise_season_summaries",
}
WEEKLY_DERIVED_METRICS = {
    "head_to_head", "largest_margin", "smallest_winning_margin",
    "weekly_scoring_highs_lows", "matchup_margins", "weekly_win_loss_streaks",
    "detailed_playoff_matchup_metrics",
}


def load_json(path: pathlib.Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("root must be an object")
    return payload


def inspect_private(value: Any, location: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in FORBIDDEN_KEYS:
                errors.append(f"{location}: forbidden field {key}")
            inspect_private(child, f"{location}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            inspect_private(child, f"{location}[{index}]", errors)
    elif isinstance(value, str) and ("authorization:" in value.casefold() or "/invitation?key=" in value.casefold()):
        errors.append(f"{location}: private text pattern")


def validate_standings(path: pathlib.Path, payload: dict[str, Any], valid_franchises: set[str], errors: list[str]) -> set[str]:
    rows = payload.get("standings")
    if not isinstance(rows, list) or not rows:
        errors.append(f"{path}: standings must be a non-empty array")
        return set()
    ranks, team_keys = set(), set()
    for index, row in enumerate(rows):
        prefix = f"{path}: standings[{index}]"
        rank, team_key = row.get("rank"), row.get("yahoo_team_key")
        if not isinstance(rank, int) or rank < 1 or rank in ranks:
            errors.append(f"{prefix}: rank must be a unique positive integer")
        ranks.add(rank)
        if not isinstance(team_key, str) or team_key in team_keys:
            errors.append(f"{prefix}: yahoo_team_key must be unique")
        team_keys.add(team_key)
        for field in ("wins", "losses", "ties"):
            if not isinstance(row.get(field), int) or row[field] < 0:
                errors.append(f"{prefix}: {field} must be a non-negative integer")
        for field in ("points_for", "points_against"):
            if row.get(field) is not None and not isinstance(row[field], (int, float)):
                errors.append(f"{prefix}: {field} must be numeric or null")
        mapping = row.get("mapping_status")
        if mapping == "verified" and not row.get("franchise_id"):
            errors.append(f"{prefix}: verified mapping requires franchise_id")
        if row.get("franchise_id") and row.get("franchise_id") not in valid_franchises:
            errors.append(f"{prefix}: unknown franchise_id {row.get('franchise_id')}")
        if mapping == "unresolved" and row.get("franchise_id") is not None:
            errors.append(f"{prefix}: unresolved mapping must keep franchise_id null")
    return team_keys


def validate_weeks(path: pathlib.Path, payload: dict[str, Any], team_keys: set[str], errors: list[str]) -> tuple[int, int]:
    weeks = payload.get("weeks")
    if not isinstance(weeks, list):
        errors.append(f"{path}: weeks must be an array")
        return 0, 0
    week_numbers, matchup_ids = set(), set()
    games_count = 0
    for week_block in weeks:
        week = week_block.get("week")
        if not isinstance(week, int) or week in week_numbers:
            errors.append(f"{path}: week values must be unique integers")
        week_numbers.add(week)
        for game in week_block.get("matchups", []):
            games_count += 1
            game_id = game.get("matchup_id")
            if not game_id or game_id in matchup_ids:
                errors.append(f"{path}: matchup IDs must be non-empty and unique")
            matchup_ids.add(game_id)
            if game.get("season") != payload.get("season") or game.get("week") != week:
                errors.append(f"{path}: {game_id} season/week mismatch")
            team_a, team_b = game.get("team_a", {}), game.get("team_b", {})
            if team_a.get("yahoo_team_key") == team_b.get("yahoo_team_key"):
                errors.append(f"{path}: {game_id} cannot match a team against itself")
            for team in (team_a, team_b):
                if team_keys and team.get("yahoo_team_key") not in team_keys:
                    errors.append(f"{path}: {game_id} references unknown team key")
                if team.get("score") is not None and not isinstance(team["score"], (int, float)):
                    errors.append(f"{path}: {game_id} score must be numeric or null")
                if team.get("mapping_status") == "unresolved" and team.get("franchise_id") is not None:
                    errors.append(f"{path}: {game_id} unresolved team has franchise_id")
            a_score, b_score = team_a.get("score"), team_b.get("score")
            if a_score is not None and b_score is not None and game.get("status") == "final":
                expected_margin = round(abs(a_score - b_score), 2)
                if game.get("margin") != expected_margin:
                    errors.append(f"{path}: {game_id} margin disagrees with scores")
                expected_tie = a_score == b_score
                if game.get("tie") != expected_tie:
                    errors.append(f"{path}: {game_id} tie flag disagrees with scores")
                if not expected_tie:
                    winner = team_a if a_score > b_score else team_b
                    if game.get("winner_historical_name") != winner.get("historical_team_name"):
                        errors.append(f"{path}: {game_id} winner name disagrees with scores")
                    if winner.get("franchise_id") and game.get("winner_franchise_id") != winner.get("franchise_id"):
                        errors.append(f"{path}: {game_id} winner franchise disagrees with scores")
    coverage = payload.get("coverage", {})
    if coverage.get("complete"):
        if sorted(coverage.get("available_weeks", [])) != sorted(coverage.get("recovered_weeks", [])):
            errors.append(f"{path}: complete coverage requires every available week")
        if sorted(week_numbers) != sorted(coverage.get("recovered_weeks", [])):
            errors.append(f"{path}: coverage recovered_weeks disagrees with week blocks")
    return len(week_numbers), games_count


def validate_draft(path: pathlib.Path, payload: dict[str, Any], errors: list[str]) -> int:
    picks = payload.get("picks")
    if not isinstance(picks, list) or not picks:
        errors.append(f"{path}: picks must be a non-empty array")
        return 0
    overall = [pick.get("overall_pick") for pick in picks]
    if overall != list(range(1, len(picks) + 1)):
        errors.append(f"{path}: overall picks must be unique and sequential")
    round_slots: set[tuple[int, int]] = set()
    for pick in picks:
        key = (pick.get("round"), pick.get("round_pick"))
        if key in round_slots:
            errors.append(f"{path}: duplicate round/slot {key}")
        round_slots.add(key)
        if pick.get("mapping_status") == "unresolved" and pick.get("franchise_id") is not None:
            errors.append(f"{path}: unresolved draft identity must remain null")
        if not pick.get("player_name") or not pick.get("historical_team_name"):
            errors.append(f"{path}: each draft pick requires player and team names")
    return len(picks)


def validate_transactions(path: pathlib.Path, payload: dict[str, Any], team_keys: set[str],
                          valid_franchises: set[str], errors: list[str]) -> int:
    rows = payload.get("transactions")
    if not isinstance(rows, list):
        errors.append(f"{path}: transactions must be an array")
        return 0
    ids: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"{path}: transactions[{index}]"
        transaction_id = row.get("transaction_id")
        if not transaction_id or transaction_id in ids:
            errors.append(f"{prefix}: transaction_id must be non-empty and unique")
        ids.add(transaction_id)
        if row.get("transaction_type") not in {"add", "drop", "add_drop", "trade"}:
            errors.append(f"{prefix}: invalid transaction_type")
        if team_keys and row.get("yahoo_team_key") not in team_keys:
            errors.append(f"{prefix}: unknown yahoo_team_key")
        if row.get("franchise_id") and row.get("franchise_id") not in valid_franchises:
            errors.append(f"{prefix}: unknown franchise_id")
        if row.get("mapping_status") == "unresolved" and row.get("franchise_id") is not None:
            errors.append(f"{prefix}: unresolved mapping must remain null")
        if not isinstance(row.get("players"), list):
            errors.append(f"{prefix}: players must be an array")
        for player in row.get("players", []):
            if player.get("action") not in {"add", "drop", "trade"} or not player.get("player_name"):
                errors.append(f"{prefix}: invalid player action")
    coverage = payload.get("coverage", {})
    if coverage.get("status") == "complete" and not coverage.get("pagination_complete"):
        errors.append(f"{path}: complete transactions require complete pagination")
    if coverage.get("transactions") != len(rows):
        errors.append(f"{path}: transaction coverage count disagrees")
    return len(rows)


def main() -> None:
    errors: list[str] = []
    if not COMPLETENESS_PATH.exists():
        raise SystemExit("Yahoo history backfill validation failed:\n- missing completeness.json")
    completeness = load_json(COMPLETENESS_PATH)
    franchise_payload = yaml.safe_load(FRANCHISES_PATH.read_text(encoding="utf-8"))
    valid_franchises = {item["franchise_id"] for item in franchise_payload.get("franchises", [])}
    if completeness.get("schema_version") != 1:
        errors.append("completeness.json: schema_version must be 1")
    season_summaries = completeness.get("seasons", [])
    years = [item.get("season") for item in season_summaries]
    if len(years) != len(set(years)):
        errors.append("completeness.json: seasons must be unique")
    league_keys = [item.get("league_key") for item in season_summaries]
    if len(league_keys) != len(set(league_keys)):
        errors.append("completeness.json: league keys must be unique")
    if any(isinstance(year, int) and year < 2021 for year in years):
        errors.append("completeness.json: Road to Glory did not exist before 2021")

    coverage_scopes = completeness.get("coverage_scopes", {})
    season_scope = coverage_scopes.get("season_level_metrics", {})
    weekly_scope = coverage_scopes.get("weekly_derived_metrics", {})
    if season_scope.get("label") != "Verified 2021–2025":
        errors.append("completeness.json: season-level coverage label must be Verified 2021–2025")
    if season_scope.get("source_years") != [2021, 2022, 2023, 2024, 2025]:
        errors.append("completeness.json: season-level coverage must span 2021–2025")
    if set(season_scope.get("allowed_metrics", [])) != SEASON_LEVEL_METRICS:
        errors.append("completeness.json: season-level metric allowlist is incomplete")
    if not season_scope.get("mapping_policy"):
        errors.append("completeness.json: season-level mapping exclusions must be documented")
    if weekly_scope.get("label") != "Verified 2021–2025":
        errors.append("completeness.json: weekly-derived coverage label must be Verified 2021–2025")
    if weekly_scope.get("source_years") != [2021, 2022, 2023, 2024, 2025]:
        errors.append("completeness.json: weekly-derived coverage must span 2021–2025")
    if set(weekly_scope.get("allowed_metrics", [])) != WEEKLY_DERIVED_METRICS:
        errors.append("completeness.json: weekly-derived metric allowlist is incomplete")
    if weekly_scope.get("excluded_years") != [] or weekly_scope.get("exclusion_reason") is not None:
        errors.append("completeness.json: weekly-derived coverage must include every 2021-2025 season")
    for scope_name, scope in coverage_scopes.items():
        if "all-time" in str(scope.get("label", "")).casefold():
            errors.append(f"completeness.json: {scope_name} cannot use an all-time label")
    summaries_by_year = {item.get("season"): item for item in season_summaries}
    for year in season_scope.get("source_years", []):
        standings_status = summaries_by_year.get(year, {}).get("sections", {}).get("standings", {}).get("status")
        if standings_status != "complete":
            errors.append(f"completeness.json: season-level scope requires complete {year} standings")
    for year in weekly_scope.get("source_years", []):
        weekly_status = summaries_by_year.get(year, {}).get("sections", {}).get("weekly_matchups", {}).get("status")
        if weekly_status != "complete":
            errors.append(f"completeness.json: weekly-derived scope requires complete {year} matchups")

    totals = {"standings": 0, "weeks": 0, "matchups": 0, "draft_picks": 0, "transactions": 0}
    weeks_by_year: dict[int, dict[str, Any]] = {}
    for summary in season_summaries:
        year = summary.get("season")
        season_dir = HISTORY_ROOT / str(year)
        team_keys: set[str] = set()
        declared_matchups = summary.get("sections", {}).get("weekly_matchups", {})
        if summary.get("weeks_expected") != (declared_matchups.get("expected_weeks") or None):
            errors.append(f"{year}: weeks_expected disagrees with weekly_matchups summary")
        if summary.get("weeks_fetched") != declared_matchups.get("weeks", 0):
            errors.append(f"{year}: weeks_fetched disagrees with weekly_matchups summary")
        if summary.get("matchups_fetched") != declared_matchups.get("games", 0):
            errors.append(f"{year}: matchups_fetched disagrees with weekly_matchups summary")
        expected_matchups = declared_matchups.get("games") if declared_matchups.get("status") == "complete" else None
        if summary.get("matchups_expected") != expected_matchups:
            errors.append(f"{year}: matchups_expected disagrees with coverage status")
        unresolved = summary.get("franchise_mapping", {}).get("unresolved_names", [])
        if summary.get("unresolved_franchise_mappings") != unresolved:
            errors.append(f"{year}: unresolved mapping aliases disagree")
        if not isinstance(summary.get("roster_weeks_fetched"), int) or summary["roster_weeks_fetched"] < 0:
            errors.append(f"{year}: roster_weeks_fetched must be a non-negative integer")
        if summary.get("confidence") not in {
            "partial_manual_only", "partial_mixed_verified_sources",
            "high_results_partial_identity", "high_results_complete_identity",
        }:
            errors.append(f"{year}: invalid confidence label")
        if year == 2021:
            if summary.get("recovery_level") != "A":
                errors.append("2021: authenticated complete recovery must be Level A")
            if summary.get("yahoo_route_status") != "authenticated_archive_recovered":
                errors.append("2021: Yahoo route status must record authenticated recovery")
            if declared_matchups.get("status") != "complete" or summary.get("weeks_fetched") != 16:
                errors.append("2021: authenticated Yahoo weekly data must be complete")
            if summary.get("sections", {}).get("standings", {}).get("coverage_type") != "commissioner_supplied_yahoo_archive":
                errors.append("2021: standings must retain their commissioner-supplied Yahoo provenance")
            if summary.get("sections", {}).get("standings", {}).get("yahoo_rows") != 10:
                errors.append("2021: all ten supplied Yahoo standings rows must be represented")
            if summary.get("franchise_mapping", {}).get("yahoo_team_keys_recovered") != 10:
                errors.append("2021: all ten supplied Yahoo team keys must be represented")
        standings_path = season_dir / "standings.json"
        if standings_path.exists():
            payload = load_json(standings_path)
            if payload.get("season") != year or payload.get("league_key") != summary.get("league_key"):
                errors.append(f"{standings_path}: season/league mismatch")
            team_keys = validate_standings(standings_path, payload, valid_franchises, errors)
            totals["standings"] += len(payload.get("standings", []))
            expected = summary.get("team_count_expected")
            if summary.get("sections", {}).get("standings", {}).get("status") == "complete" and len(team_keys) != expected:
                errors.append(f"{standings_path}: complete standings must match expected team count")
            if year == 2021:
                source = yaml.safe_load(YAHOO_2021_SOURCE_PATH.read_text(encoding="utf-8"))
                source_by_rank = {row["rank"]: row for row in source.get("standings", [])}
                for row in payload.get("standings", []):
                    source_row = source_by_rank.get(row.get("rank"), {})
                    expected_key = f"406.l.12928.t.{source_row.get('yahoo_team_id')}"
                    if row.get("yahoo_team_key") != expected_key:
                        errors.append(f"{standings_path}: rank {row.get('rank')} Yahoo team key disagrees with source")
                    for generated_field, source_field in (
                        ("historical_team_name", "yahoo_team_name"), ("wins", "wins"),
                        ("losses", "losses"), ("ties", "ties"), ("points_for", "points_for"),
                        ("points_against", "points_against"), ("playoff_seed", "playoff_seed"),
                        ("playoff_finish", "playoff_finish"),
                    ):
                        if row.get(generated_field) != source_row.get(source_field):
                            errors.append(
                                f"{standings_path}: rank {row.get('rank')} {generated_field} disagrees with source"
                            )
        weeks_path = season_dir / "weeks.json"
        if weeks_path.exists():
            payload = load_json(weeks_path)
            week_count, game_count = validate_weeks(weeks_path, payload, team_keys, errors)
            totals["weeks"] += week_count
            totals["matchups"] += game_count
            weeks_by_year[year] = payload
            declared = summary.get("sections", {}).get("weekly_matchups", {})
            if declared.get("weeks") != week_count or declared.get("games") != game_count:
                errors.append(f"{weeks_path}: completeness counts disagree with normalized data")
        draft_path = season_dir / "draft.json"
        if draft_path.exists():
            payload = load_json(draft_path)
            pick_count = validate_draft(draft_path, payload, errors)
            totals["draft_picks"] += pick_count
            if summary.get("sections", {}).get("draft", {}).get("picks") != pick_count:
                errors.append(f"{draft_path}: completeness draft count disagrees")
        transactions_path = season_dir / "transactions.json"
        if transactions_path.exists():
            payload = load_json(transactions_path)
            transaction_count = validate_transactions(transactions_path, payload, team_keys, valid_franchises, errors)
            totals["transactions"] += transaction_count
            if summary.get("sections", {}).get("transactions", {}).get("rows") != transaction_count:
                errors.append(f"{transactions_path}: completeness transaction count disagrees")

    champions = yaml.safe_load(CHAMPIONS_PATH.read_text(encoding="utf-8")).get("champions", [])
    for champion in champions:
        year = champion.get("year")
        if year not in weeks_by_year:
            continue
        games = [game for block in weeks_by_year[year].get("weeks", []) for game in block.get("matchups", [])]
        if not games:
            continue
        champion_id, runner_up_id = champion.get("champion_franchise_id"), champion.get("runner_up_franchise_id")
        matching = [game for game in games if {
            game.get("team_a", {}).get("franchise_id"), game.get("team_b", {}).get("franchise_id")
        } == {champion_id, runner_up_id} and game.get("is_playoffs")]
        final_game = max(matching, key=lambda game: game.get("week", 0)) if matching else None
        if not final_game or final_game.get("winner_franchise_id") != champion_id:
            errors.append(f"{year}: normalized Yahoo championship result disagrees with canonical champion")
            continue
        winner = final_game["team_a"] if final_game["team_a"]["franchise_id"] == champion_id else final_game["team_b"]
        runner_up = final_game["team_b"] if winner is final_game["team_a"] else final_game["team_a"]
        if winner.get("score") != champion.get("champion_score") or runner_up.get("score") != champion.get("runner_up_score"):
            errors.append(f"{year}: normalized Yahoo championship score disagrees with canonical result")

    for path in sorted(HISTORY_ROOT.rglob("*.json")):
        try:
            payload = load_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            errors.append(f"{path}: {error}")
            continue
        if payload.get("schema_version") != 1:
            errors.append(f"{path}: schema_version must be 1")
        inspect_private(payload, str(path), errors)

    if errors:
        print("Yahoo history backfill validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print(
        "Validated Yahoo history backfill: "
        f"{len(season_summaries)} seasons, {totals['weeks']} weeks, "
        f"{totals['matchups']} matchups, {totals['draft_picks']} draft picks, "
        f"{totals['transactions']} transactions"
    )


if __name__ == "__main__":
    main()
