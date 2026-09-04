"""Validate the canonical season, champion, playoff, asset, and route records."""

from __future__ import annotations

import json
from numbers import Real
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_YEARS = {2021, 2022, 2023, 2024, 2025}
VALID_ROUNDS = {
    "Quarterfinal", "Semifinal", "Consolation Semifinal", "Championship",
    "Third Place Game", "Fifth Place Game", "Seventh Place Game",
}


def load(name: str) -> dict:
    value = yaml.safe_load((ROOT / "_data" / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"_data/{name}: expected a schema_version 1 mapping")
    return value


def local_asset(raw_path: object) -> bool:
    if not isinstance(raw_path, str) or not raw_path.startswith("/assets/img/history/"):
        return False
    path = (ROOT / raw_path.lstrip("/")).resolve()
    return ROOT.resolve() in path.parents and path.is_file() and path.stat().st_size > 1024


def numeric(value: object) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def main() -> None:
    errors: list[str] = []
    seasons_data = load("seasons.yml")
    champions_data = load("champions.yml")
    playoffs_data = load("playoffs.yml")
    franchises_data = load("franchises.yml")
    seasons = seasons_data.get("seasons")
    champions = champions_data.get("champions")
    playoffs = playoffs_data.get("playoffs")
    franchises = franchises_data.get("franchises")
    if not all(isinstance(items, list) for items in (seasons, champions, playoffs, franchises)):
        raise SystemExit("History validation failed: canonical arrays are missing")

    franchise_by_id = {item["franchise_id"]: item for item in franchises}
    valid_names: dict[str, set[str]] = {
        item["franchise_id"]: {
            str(item["name"]).casefold(),
            *(str(alias).casefold() for alias in item.get("aliases") or []),
        }
        for item in franchises
    }
    season_by_year = {item.get("year"): item for item in seasons}
    champion_by_year = {item.get("year"): item for item in champions}
    playoff_by_year = {item.get("season"): item for item in playoffs}

    for label, values in (
        ("season", [item.get("year") for item in seasons]),
        ("champion", [item.get("year") for item in champions]),
        ("playoff", [item.get("season") for item in playoffs]),
    ):
        if set(values) != EXPECTED_YEARS or len(values) != len(set(values)):
            errors.append(f"{label} years must contain 2021-2025 exactly once")

    for year in sorted(EXPECTED_YEARS):
        season = season_by_year.get(year) or {}
        champion = champion_by_year.get(year) or {}
        playoff = playoff_by_year.get(year) or {}
        route = ROOT / "_seasons" / f"{year}.md"
        if not route.is_file() or f"permalink: /history/{year}/" not in route.read_text(encoding="utf-8"):
            errors.append(f"{year}: collection route /history/{year}/ is missing")

        for field in ("champion_franchise_id", "runner_up_franchise_id"):
            franchise_id = season.get(field)
            if franchise_id not in franchise_by_id:
                errors.append(f"{year}: unknown {field} {franchise_id!r}")
            if champion.get(field) != franchise_id:
                errors.append(f"{year}: {field} differs between season and champion records")
        if season.get("champion_display_name") != champion.get("champion_display_name"):
            errors.append(f"{year}: champion display names do not agree")
        if season.get("runner_up_display_name") != champion.get("runner_up_display_name"):
            errors.append(f"{year}: runner-up display names do not agree")

        asset_fields = (
            "standings_asset", "bracket_asset", "championship_portrait_asset", "championship_matchup_asset"
        )
        if season.get("data_mode") == "detailed":
            if season.get("status_label") != "Complete":
                errors.append(f"{year}: detailed season must be labelled Complete")
            expected_regular_season_weeks = 14 if year in {2021, 2022} else 13
            if season.get("regular_season_weeks", 13) != expected_regular_season_weeks:
                errors.append(
                    f"{year}: regular-season boundary must be Week {expected_regular_season_weeks}"
                )
            if season.get("bracket_asset"):
                if not local_asset(season.get("bracket_asset")):
                    errors.append(f"{year}: detailed season bracket_asset is missing or invalid")
            elif season.get("bracket_path") != f"/history/{year}/#bracket":
                errors.append(f"{year}: data-driven bracket path must resolve to the season bracket")
            week_path = ROOT / str(season.get("weeks_data_path") or "")
            if not week_path.is_file():
                errors.append(f"{year}: detailed season weeks_data_path is missing")
            for field in asset_fields:
                if season.get(field) and not local_asset(season.get(field)):
                    errors.append(f"{year}: missing or invalid optional {field}: {season.get(field)!r}")
        else:
            for field in asset_fields:
                if not local_asset(season.get(field)):
                    errors.append(f"{year}: missing or invalid {field}: {season.get(field)!r}")
        season_bracket = season.get("bracket_path") or season.get("bracket_asset")
        if champion.get("bracket_path") != season_bracket:
            errors.append(f"{year}: champion bracket path differs from season record")
        if playoff.get("bracket_path") != season_bracket:
            errors.append(f"{year}: playoff bracket path differs from season record")
        if champion.get("season_path") != f"/history/{year}/":
            errors.append(f"{year}: champion season_path must be /history/{year}/")

        standings = season.get("standings")
        if not isinstance(standings, list) or len(standings) != season.get("team_count"):
            errors.append(f"{year}: standings length must match team_count")
            standings = standings if isinstance(standings, list) else []
        ranks = [row.get("rank") for row in standings]
        if ranks != list(range(1, len(standings) + 1)):
            errors.append(f"{year}: standings ranks must be complete and ordered")
        for row in standings:
            label = f"{year} rank {row.get('rank')}"
            franchise_id = row.get("franchise_id")
            if franchise_id == 0:
                errors.append(f"{label}: unknown franchise must be null, never zero")
            elif franchise_id is not None:
                if franchise_id not in franchise_by_id:
                    errors.append(f"{label}: unknown franchise_id {franchise_id!r}")
                elif str(row.get("team_name") or "").casefold() not in valid_names[franchise_id]:
                    errors.append(f"{label}: team name is not canonical or a verified alias")
            if not str(row.get("team_name") or "").strip():
                errors.append(f"{label}: team_name is required")
            for field in ("wins", "losses", "ties"):
                if not isinstance(row.get(field), int) or row[field] < 0:
                    errors.append(f"{label}: {field} must be a non-negative integer")
            for field in ("points_for", "points_against"):
                if not numeric(row.get(field)) or row[field] <= 0:
                    errors.append(f"{label}: {field} must be a positive number")

        games = playoff.get("games")
        if not isinstance(games, list) or not games:
            errors.append(f"{year}: playoff games are required")
            games = []
        game_ids: set[str] = set()
        finals: list[dict] = []
        for game in games:
            game_id = game.get("game_id")
            if not isinstance(game_id, str) or game_id in game_ids:
                errors.append(f"{year}: invalid or duplicate playoff game_id {game_id!r}")
            game_ids.add(game_id)
            if game.get("round") not in VALID_ROUNDS:
                errors.append(f"{game_id}: invalid playoff round")
            if game.get("round") == "Championship":
                finals.append(game)
            for side in ("team_one", "team_two"):
                franchise_id = game.get(f"{side}_franchise_id")
                if franchise_id == 0:
                    errors.append(f"{game_id}: unknown franchise must be null, never zero")
                elif franchise_id is not None and franchise_id not in franchise_by_id:
                    errors.append(f"{game_id}: unknown {side}_franchise_id {franchise_id!r}")
                if not str(game.get(f"{side}_display_name") or "").strip():
                    errors.append(f"{game_id}: {side}_display_name is required")
            winner_id = game.get("winner_franchise_id")
            if winner_id not in {game.get("team_one_franchise_id"), game.get("team_two_franchise_id")}:
                errors.append(f"{game_id}: winner must be one of the participating franchises")
            scores = (game.get("team_one_score"), game.get("team_two_score"))
            if (scores[0] is None) != (scores[1] is None):
                errors.append(f"{game_id}: both scores must be known or both null")
            if any(score == 0 for score in scores):
                errors.append(f"{game_id}: unknown scores must be null, never zero")
            if any(score is not None and (not numeric(score) or score <= 0) for score in scores):
                errors.append(f"{game_id}: published scores must be positive numbers")

        if len(finals) != 1:
            errors.append(f"{year}: exactly one championship game is required")
        else:
            final = finals[0]
            if final.get("winner_franchise_id") != champion.get("champion_franchise_id"):
                errors.append(f"{year}: champion does not match playoff winner")
            expected_scores = {champion.get("champion_score"), champion.get("runner_up_score")}
            if {final.get("team_one_score"), final.get("team_two_score")} != expected_scores:
                errors.append(f"{year}: championship scores do not match playoff final")

        if season.get("data_mode") == "detailed":
            source_standings = json.loads((ROOT / f"_data/generated/history/{year}/standings.json").read_text(encoding="utf-8"))
            source_rows = {row["franchise_id"]: row for row in source_standings["standings"]}
            if len(standings) != season.get("team_count") or set(source_rows) != {row.get("franchise_id") for row in standings}:
                errors.append(f"{year}: standings must contain every verified Yahoo franchise")
            for row in standings:
                source = source_rows.get(row.get("franchise_id"), {})
                fields = ("rank", "wins", "losses", "ties", "win_percentage", "points_for", "points_against")
                if year == 2025:
                    fields += ("playoff_seed",)
                for field in fields:
                    if row.get(field) != source.get(field):
                        errors.append(f"{year} {row.get('franchise_id')}: {field} differs from Yahoo standings")
            field = playoff.get("playoff_field") or []
            seeded_rows = sorted(
                (row for row in standings if row.get("playoff_seed") is not None),
                key=lambda row: row["playoff_seed"],
            )
            expected_seeds = list(range(1, len(seeded_rows) + 1))
            if not seeded_rows or [row.get("playoff_seed") for row in seeded_rows] != expected_seeds:
                errors.append(f"{year}: standings playoff seeds must be complete and sequential")
            if len(field) != len(seeded_rows) or [item.get("seed") for item in field] != expected_seeds:
                errors.append(f"{year}: playoff field must match the verified seeded standings")
            elif [item.get("franchise_id") for item in field] != [row.get("franchise_id") for row in seeded_rows]:
                errors.append(f"{year}: playoff field franchises must match the verified seed order")
            weeks = json.loads((ROOT / f"_data/generated/history/{year}/weeks.json").read_text(encoding="utf-8"))
            if weeks.get("coverage", {}).get("recovered_weeks") != list(range(1, 17)):
                errors.append(f"{year}: all 16 verified weeks are required")
            matchups = [game for week in weeks.get("weeks") or [] for game in week.get("matchups") or []]
            expected_matchups = 78 if year == 2021 else 92
            if len(matchups) != expected_matchups:
                errors.append(f"{year}: expected {expected_matchups} verified matchup rows")
            if any(game.get("verified") is not True or game.get("team_a", {}).get("score") is None or game.get("team_b", {}).get("score") is None for game in matchups):
                errors.append(f"{year}: every matchup must be verified with both final scores")
            source_by_week_pair = {
                (game["week"], frozenset((game["team_a"].get("franchise_id"), game["team_b"].get("franchise_id")))): game
                for game in matchups
            }
            for game in games:
                if game.get("bracket_type") not in {"championship", "placement"}:
                    errors.append(f"{game.get('game_id')}: detailed playoff game requires a bracket_type")
                if game.get("week") is None:
                    errors.append(f"{game.get('game_id')}: detailed playoff game requires a verified week")
                    continue
                pair = frozenset((game.get("team_one_franchise_id"), game.get("team_two_franchise_id")))
                source_game = source_by_week_pair.get((game["week"], pair))
                if not source_game:
                    errors.append(f"{game.get('game_id')}: playoff game does not match the weekly archive")
                    continue
                source_scores = {
                    source_game["team_a"]["franchise_id"]: source_game["team_a"]["score"],
                    source_game["team_b"]["franchise_id"]: source_game["team_b"]["score"],
                }
                if game.get("team_one_score") != source_scores.get(game.get("team_one_franchise_id")) or game.get("team_two_score") != source_scores.get(game.get("team_two_franchise_id")):
                    errors.append(f"{game.get('game_id')}: playoff score differs from the weekly archive")
                if game.get("winner_franchise_id") != source_game.get("winner_franchise_id"):
                    errors.append(f"{game.get('game_id')}: playoff winner differs from the weekly archive")
        elif season.get("data_mode") == "season_level":
            if season.get("status_label") != "Complete":
                errors.append(f"{year}: season-level archive must be labelled Complete")
            if season.get("coverage_label") != f"Season Data — Verified {year}":
                errors.append(f"{year}: season-level coverage label is missing or incorrect")
            if season.get("weeks_data_path"):
                errors.append(f"{year}: unavailable weekly history must not define weeks_data_path")
            source_standings = json.loads(
                (ROOT / f"_data/generated/history/{year}/standings.json").read_text(encoding="utf-8")
            )
            source_rows = {row["franchise_id"]: row for row in source_standings["standings"]}
            if len(standings) != 10 or set(source_rows) != {row.get("franchise_id") for row in standings}:
                errors.append(f"{year}: standings must contain the 10 verified Yahoo franchises")
            for row in standings:
                source = source_rows.get(row.get("franchise_id"), {})
                for field in (
                    "rank", "wins", "losses", "ties", "win_percentage", "points_for",
                    "points_against", "streak", "playoff_seed", "playoff_finish",
                ):
                    if row.get(field) != source.get(field):
                        errors.append(f"{year} {row.get('franchise_id')}: {field} differs from verified source")
            field = playoff.get("playoff_field") or []
            seeded_rows = sorted(
                (row for row in standings if row.get("playoff_seed") is not None),
                key=lambda row: row["playoff_seed"],
            )
            expected_seeds = list(range(1, len(seeded_rows) + 1))
            if [row.get("playoff_seed") for row in seeded_rows] != expected_seeds:
                errors.append(f"{year}: playoff seeds must be complete and sequential")
            if [item.get("seed") for item in field] != expected_seeds:
                errors.append(f"{year}: playoff field must preserve the verified bracket seeds")
            elif [item.get("franchise_id") for item in field] != [row.get("franchise_id") for row in seeded_rows]:
                errors.append(f"{year}: playoff field franchises must match the verified seed order")
            weeks = json.loads(
                (ROOT / f"_data/generated/history/{year}/weeks.json").read_text(encoding="utf-8")
            )
            if weeks.get("coverage", {}).get("complete") is not False or weeks.get("weeks") != []:
                errors.append(f"{year}: unavailable weekly data must remain explicitly empty")
            if len(games) != 3 or sum(game.get("round") == "Championship" for game in games) != 1:
                errors.append(f"{year}: expected two verified semifinals and one championship")
            if any(game.get("bracket_type") != "championship" for game in games):
                errors.append(f"{year}: all verified playoff games belong to the championship bracket")
            if sum(game.get("team_one_score") is not None for game in games) != 1:
                errors.append(f"{year}: only the championship may contain a verified score")

    if errors:
        raise SystemExit("History validation failed:\n- " + "\n- ".join(errors))
    standings_count = sum(len(item["standings"]) for item in seasons)
    game_count = sum(len(item["games"]) for item in playoffs)
    print(f"Validated 5 seasons, 5 championship results, {standings_count} standings rows, {game_count} playoff games, routes, references, scores, and approved presentation assets")


if __name__ == "__main__":
    main()
