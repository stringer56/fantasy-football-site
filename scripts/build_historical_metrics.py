#!/usr/bin/env python3
"""Build deterministic, coverage-gated historical Road to Glory metrics."""

from __future__ import annotations

import argparse
import difflib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
HISTORY_ROOT = ROOT / "_data" / "generated" / "history"
OUTPUT_ROOT = ROOT / "_data" / "generated" / "records"
WEEKLY_YEARS = [2022, 2023, 2024, 2025]
SEASON_YEARS = [2021, 2022, 2023, 2024, 2025]
WEEKLY_LABEL = "Verified 2022–2025"
SEASON_LABEL = "Verified 2021–2025"
OUTPUT_NAMES = (
    "manifest", "head_to_head", "biggest_wins", "closest_games", "weekly_scores",
    "streaks", "playoffs", "franchise_summaries", "record_thresholds",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def coverage(kind: str, source_files: list[str]) -> dict[str, Any]:
    years, label = (WEEKLY_YEARS, WEEKLY_LABEL) if kind == "weekly" else (SEASON_YEARS, SEASON_LABEL)
    return {
        "class": f"{kind}_derived" if kind == "weekly" else "season_level",
        "label": label,
        "start_season": years[0],
        "end_season": years[-1],
        "source_years": years,
        "source_files": source_files,
    }


def rounded(value: float, digits: int = 2) -> float:
    return round(value + 0.0, digits)


def identity_index(franchises: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for item in franchises:
        prefix = "retired" if item["status"] == "retired" else "teams"
        result[item["franchise_id"]] = {
            "franchise_id": item["franchise_id"],
            "display_name": item["name"],
            "short_name": item["short_name"],
            "path": f"/{prefix}/{item['slug']}/",
            "identity_image": item["branding"]["identity_image"],
        }
    return result


def compact_identity(franchise_id: str, identities: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return dict(identities[franchise_id])


def load_weekly_games() -> tuple[list[dict[str, Any]], list[str]]:
    games, source_files = [], []
    seen: set[str] = set()
    for year in WEEKLY_YEARS:
        relative = f"_data/generated/history/{year}/weeks.json"
        payload = load_json(ROOT / relative)
        if payload.get("season") != year or not payload.get("coverage", {}).get("complete"):
            raise ValueError(f"{year}: weekly archive is not complete")
        source_files.append(relative)
        for block in payload.get("weeks", []):
            for game in block.get("matchups", []):
                matchup_id = game.get("matchup_id")
                if matchup_id in seen:
                    raise ValueError(f"duplicate matchup_id: {matchup_id}")
                seen.add(matchup_id)
                if game.get("status") != "final" or not game.get("verified"):
                    raise ValueError(f"{matchup_id}: weekly input is not verified final data")
                if not isinstance(game.get("team_a", {}).get("score"), (int, float)) or not isinstance(
                    game.get("team_b", {}).get("score"), (int, float)
                ):
                    raise ValueError(f"{matchup_id}: final scores are required")
                games.append(game)
    return games, source_files


def classified_playoff_games(games: list[dict[str, Any]]) -> tuple[dict[str, str], list[str]]:
    """Map weekly matchup IDs to independently verified championship-bracket rounds."""
    lookup = {
        (game["season"], game["week"], frozenset((game["team_a"]["franchise_id"], game["team_b"]["franchise_id"]))): game
        for game in games
        if game["team_a"].get("franchise_id") and game["team_b"].get("franchise_id")
    }
    classified: dict[str, str] = {}
    source_files = ["_data/playoffs.yml", "_data/generated/history/2025/playoffs.json"]
    canonical = load_yaml(ROOT / "_data" / "playoffs.yml")
    round_week = {
        2022: {"Semifinal": 15, "Championship": 16},
        2023: {"Quarterfinal": 14, "Semifinal": 15, "Championship": 16},
        2024: {"Quarterfinal": 14, "Semifinal": 15, "Championship": 16},
    }
    for season in canonical.get("playoffs", []):
        year = season["season"]
        if year not in round_week:
            continue
        for item in season.get("games", []):
            pair = frozenset((item.get("team_one_franchise_id"), item.get("team_two_franchise_id")))
            game = lookup.get((year, round_week[year][item["round"]], pair))
            if not game or game.get("winner_franchise_id") != item.get("winner_franchise_id"):
                # Conflicting bracket lanes stay unclassified rather than being forced.
                continue
            classified[game["matchup_id"]] = item["round"]
    playoffs_2025 = load_json(ROOT / "_data" / "generated" / "history" / "2025" / "playoffs.json")
    for item in playoffs_2025.get("games", []):
        if item.get("bracket_type") != "championship":
            continue
        pair = frozenset((item["team_one"]["franchise_id"], item["team_two"]["franchise_id"]))
        game = lookup.get((2025, item["week"], pair))
        if not game or game.get("winner_franchise_id") != item.get("winner_franchise_id"):
            raise ValueError(f"{item['game_id']}: 2025 playoff game did not match weekly archive")
        classified[game["matchup_id"]] = item["round"]
    return classified, source_files


def game_entry(game: dict[str, Any], identities: dict[str, dict[str, Any]], playoff_rounds: dict[str, str]) -> dict[str, Any]:
    a, b = game["team_a"], game["team_b"]
    a_id, b_id = a.get("franchise_id"), b.get("franchise_id")
    if game.get("tie"):
        winner, loser = None, None
    elif a["score"] > b["score"]:
        winner, loser = a, b
    else:
        winner, loser = b, a
    playoff_round = playoff_rounds.get(game["matchup_id"])
    if not game.get("is_playoffs"):
        game_type = "regular_season"
    elif playoff_round:
        game_type = "championship_playoff"
    else:
        game_type = "postseason_unclassified"
    entry = {
        "matchup_id": game["matchup_id"],
        "season": game["season"],
        "week": game["week"],
        "game_type": game_type,
        "playoff_round": playoff_round,
        "tie": bool(game.get("tie")),
        "team_a": {**compact_identity(a_id, identities), "score": a["score"]} if a_id else None,
        "team_b": {**compact_identity(b_id, identities), "score": b["score"]} if b_id else None,
        "historical_team_a": a["historical_team_name"],
        "historical_team_b": b["historical_team_name"],
        "team_a_score": a["score"],
        "team_b_score": b["score"],
        "combined_score": rounded(a["score"] + b["score"]),
        "margin": rounded(abs(a["score"] - b["score"])),
    }
    entry["winner"] = compact_identity(winner["franchise_id"], identities) if winner and winner.get("franchise_id") else None
    entry["loser"] = compact_identity(loser["franchise_id"], identities) if loser and loser.get("franchise_id") else None
    if winner:
        entry["winner_score"], entry["loser_score"] = winner["score"], loser["score"]
    else:
        entry["winner_score"], entry["loser_score"] = None, None
    return entry


def ranked(entries: Iterable[dict[str, Any]], key, *, reverse: bool = True, limit: int | None = None) -> list[dict[str, Any]]:
    ordered = sorted(entries, key=lambda item: (key(item), item["season"], item["week"], item["matchup_id"]), reverse=reverse)
    result, previous = [], object()
    for position, item in enumerate(ordered, start=1):
        value = key(item)
        rank = result[-1]["rank"] if result and value == previous else position
        result.append({"rank": rank, **item})
        previous = value
        if limit and len(result) >= limit:
            break
    return result


def current_series_streak(meetings: list[dict[str, Any]], a_id: str, b_id: str) -> dict[str, Any] | None:
    ordered = sorted(meetings, key=lambda game: (game["season"], game["week"]), reverse=True)
    if not ordered or ordered[0]["tie"]:
        return None
    winner_id = ordered[0]["winner"]["franchise_id"]
    length = 0
    for game in ordered:
        if game["tie"] or game["winner"]["franchise_id"] != winner_id:
            break
        length += 1
    return {"franchise_id": winner_id, "wins": length, "against_franchise_id": b_id if winner_id == a_id else a_id}


def meeting_view(game: dict[str, Any]) -> dict[str, Any]:
    """Keep the comparison payload small while retaining display-ready facts."""
    def side_view(side: dict[str, Any]) -> dict[str, Any]:
        return {
            "franchise_id": side["franchise_id"], "display_name": side["display_name"],
            "path": side["path"], "score": side["score"],
        }

    return {
        "matchup_id": game["matchup_id"], "season": game["season"], "week": game["week"],
        "game_type": game["game_type"], "playoff_round": game["playoff_round"], "tie": game["tie"],
        "team_a": side_view(game["team_a"]), "team_b": side_view(game["team_b"]),
        "winner": (
            {"franchise_id": game["winner"]["franchise_id"], "display_name": game["winner"]["display_name"]}
            if game["winner"] else None
        ),
        "margin": game["margin"], "combined_score": game["combined_score"],
    }


def build_head_to_head(games: list[dict[str, Any]], identities: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for game in games:
        if game["team_a"] and game["team_b"]:
            pair = tuple(sorted((game["team_a"]["franchise_id"], game["team_b"]["franchise_id"])))
            pairs[pair].append(game)
    output = []
    for (a_id, b_id), meetings in sorted(pairs.items()):
        wins_a = sum(bool(game["winner"] and game["winner"]["franchise_id"] == a_id) for game in meetings)
        wins_b = sum(bool(game["winner"] and game["winner"]["franchise_id"] == b_id) for game in meetings)
        ties = sum(game["tie"] for game in meetings)
        points_a = sum(game["team_a"]["score"] if game["team_a"]["franchise_id"] == a_id else game["team_b"]["score"] for game in meetings)
        points_b = sum(game["team_a"]["score"] if game["team_a"]["franchise_id"] == b_id else game["team_b"]["score"] for game in meetings)
        wins_by_a = [game for game in meetings if game["winner"] and game["winner"]["franchise_id"] == a_id]
        wins_by_b = [game for game in meetings if game["winner"] and game["winner"]["franchise_id"] == b_id]
        decided = [game for game in meetings if not game["tie"]]
        playoff_meetings = [game for game in meetings if game["game_type"] == "championship_playoff"]
        recent = sorted(meetings, key=lambda game: (game["season"], game["week"]), reverse=True)
        output.append({
            "pair_id": f"{a_id}--{b_id}",
            "franchise_a": compact_identity(a_id, identities),
            "franchise_b": compact_identity(b_id, identities),
            "meetings": len(meetings), "wins_a": wins_a, "wins_b": wins_b, "ties": ties,
            "points_a": rounded(points_a), "points_b": rounded(points_b),
            "average_score_a": rounded(points_a / len(meetings), 3),
            "average_score_b": rounded(points_b / len(meetings), 3),
            "average_margin": rounded(sum(game["margin"] for game in meetings) / len(meetings), 3),
            "largest_win_a": meeting_view(max(wins_by_a, key=lambda game: game["margin"])) if wins_by_a else None,
            "largest_win_b": meeting_view(max(wins_by_b, key=lambda game: game["margin"])) if wins_by_b else None,
            "closest_meeting": meeting_view(min(decided, key=lambda game: (game["margin"], game["season"], game["week"]))) if decided else None,
            "highest_scoring_meeting": meeting_view(max(meetings, key=lambda game: (game["combined_score"], game["season"], game["week"]))),
            "most_recent_meeting": meeting_view(recent[0]),
            "current_series_streak": current_series_streak(meetings, a_id, b_id),
            "playoff_meetings": len(playoff_meetings),
            "playoff_wins_a": sum(bool(game["winner"] and game["winner"]["franchise_id"] == a_id) for game in playoff_meetings),
            "playoff_wins_b": sum(bool(game["winner"] and game["winner"]["franchise_id"] == b_id) for game in playoff_meetings),
            "recent_meetings": [meeting_view(game) for game in recent[:10]],
        })
    return output


def outcome_for(game: dict[str, Any], franchise_id: str) -> str:
    if game["tie"]:
        return "T"
    return "W" if game["winner"] and game["winner"]["franchise_id"] == franchise_id else "L"


def best_streak(sequence: list[tuple[int, int, str]], accepted: set[str], *, cross_season: bool) -> dict[str, Any] | None:
    best: list[tuple[int, int, str]] = []
    current: list[tuple[int, int, str]] = []
    for item in sequence:
        if current and item[0] != current[-1][0] and not cross_season:
            current = []
        if current and item[0] > current[-1][0] + 1:
            current = []
        if item[2] in accepted:
            current.append(item)
            if len(current) > len(best):
                best = list(current)
        else:
            current = []
    if not best:
        return None
    return {"games": len(best), "start_season": best[0][0], "start_week": best[0][1], "end_season": best[-1][0], "end_week": best[-1][1]}


def build_streaks(games: list[dict[str, Any]], identities: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_team: defaultdict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for game in games:
        if game["game_type"] != "regular_season":
            continue
        for side in (game["team_a"], game["team_b"]):
            if side:
                by_team[side["franchise_id"]].append((game["season"], game["week"], outcome_for(game, side["franchise_id"])))
    output = {"single_season_wins": [], "single_season_losses": [], "single_season_unbeaten": [], "cross_season_wins": [], "cross_season_losses": []}
    for franchise_id, sequence in by_team.items():
        sequence.sort()
        for key, accepted, cross in (
            ("single_season_wins", {"W"}, False), ("single_season_losses", {"L"}, False),
            ("single_season_unbeaten", {"W", "T"}, False), ("cross_season_wins", {"W"}, True),
            ("cross_season_losses", {"L"}, True),
        ):
            result = best_streak(sequence, accepted, cross_season=cross)
            if result:
                output[key].append({**compact_identity(franchise_id, identities), **result})
    for key in output:
        output[key] = sorted(output[key], key=lambda item: (-item["games"], item["franchise_id"]))
        for index, item in enumerate(output[key], start=1):
            item["rank"] = index
    return output


def championship_facts() -> list[dict[str, Any]]:
    facts = [{"season": item["year"], "champion_franchise_id": item["champion_franchise_id"], "runner_up_franchise_id": item["runner_up_franchise_id"]} for item in load_yaml(ROOT / "_data" / "champions.yml")["champions"]]
    placements = load_json(ROOT / "_data" / "generated" / "history" / "2025" / "playoffs.json")["final_placements"]
    by_place = {item["place"]: item for item in placements}
    facts.append({"season": 2025, "champion_franchise_id": by_place[1]["franchise_id"], "runner_up_franchise_id": by_place[2]["franchise_id"]})
    return sorted(facts, key=lambda item: item["season"])


def build_playoff_metrics(games: list[dict[str, Any]], identities: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    playoff_games = [game for game in games if game["game_type"] == "championship_playoff"]
    championships = championship_facts()
    rows = []
    for franchise_id in sorted(identities):
        team_games = [game for game in playoff_games if game["team_a"]["franchise_id"] == franchise_id or game["team_b"]["franchise_id"] == franchise_id]
        titles = sum(item["champion_franchise_id"] == franchise_id for item in championships)
        finals = sum(franchise_id in (item["champion_franchise_id"], item["runner_up_franchise_id"]) for item in championships)
        if not team_games and not titles and not finals:
            continue
        wins = [game for game in team_games if game["winner"]["franchise_id"] == franchise_id]
        scores = [side["score"] for game in team_games for side in (game["team_a"], game["team_b"]) if side["franchise_id"] == franchise_id]
        rows.append({
            **compact_identity(franchise_id, identities), "playoff_games": len(team_games), "playoff_wins": len(wins),
            "playoff_losses": len(team_games) - len(wins), "championship_appearances": finals, "championships": titles,
            "largest_playoff_win": max(wins, key=lambda game: game["margin"]) if wins else None,
            "closest_playoff_win": min(wins, key=lambda game: game["margin"]) if wins else None,
            "highest_playoff_score": max(scores) if scores else None,
        })
    rows.sort(key=lambda item: (-item["championships"], -item["playoff_wins"], item["franchise_id"]))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def build_franchise_summaries(games: list[dict[str, Any]], identities: dict[str, dict[str, Any]], streaks: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    standings_by_team: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for year in SEASON_YEARS:
        payload = load_json(HISTORY_ROOT / str(year) / "standings.json")
        for row in payload["standings"]:
            if row.get("franchise_id"):
                standings_by_team[row["franchise_id"]].append({"season": year, **row})
    championships = championship_facts()
    playoff_rows = {row["franchise_id"]: row for row in build_playoff_metrics(games, identities)}
    win_streaks = {row["franchise_id"]: row for row in streaks["single_season_wins"]}
    output = []
    for franchise_id in sorted(set(standings_by_team) | {side["franchise_id"] for game in games for side in (game["team_a"], game["team_b"]) if side}):
        seasons = standings_by_team.get(franchise_id, [])
        team_games = [game for game in games if (game["team_a"] and game["team_a"]["franchise_id"] == franchise_id) or (game["team_b"] and game["team_b"]["franchise_id"] == franchise_id)]
        outcomes = [outcome_for(game, franchise_id) for game in team_games]
        scores_for, scores_against = [], []
        wins = []
        for game in team_games:
            mine = game["team_a"] if game["team_a"] and game["team_a"]["franchise_id"] == franchise_id else game["team_b"]
            other = game["team_b"] if mine is game["team_a"] else game["team_a"]
            scores_for.append(mine["score"])
            scores_against.append(
                other["score"] if other else (
                    game["team_b_score"] if mine is game["team_a"] else game["team_a_score"]
                )
            )
            if outcome_for(game, franchise_id) == "W" and game["winner"] and game["loser"]:
                wins.append(game)
        season_history = {
            "coverage": coverage("season", [f"_data/generated/history/{year}/standings.json" for year in SEASON_YEARS] + ["_data/champions.yml", "_data/generated/history/2025/playoffs.json"]),
            "seasons_represented": [row["season"] for row in seasons],
            "season_count": len(seasons),
            "wins": sum(row["wins"] for row in seasons), "losses": sum(row["losses"] for row in seasons), "ties": sum(row["ties"] for row in seasons),
            "points_for": rounded(sum(row["points_for"] for row in seasons)), "points_against": rounded(sum(row["points_against"] for row in seasons)),
            "average_final_rank": rounded(sum(row["rank"] for row in seasons) / len(seasons), 3) if seasons else None,
            "championships": sum(item["champion_franchise_id"] == franchise_id for item in championships),
            "seasons": [{"season": row["season"], "historical_team_name": row["historical_team_name"], "rank": row["rank"], "wins": row["wins"], "losses": row["losses"], "ties": row["ties"], "points_for": row["points_for"], "points_against": row["points_against"], "playoff_seed": row.get("playoff_seed"), "playoff_finish": row.get("playoff_finish")} for row in seasons],
        }
        weekly = {
            "coverage": coverage("weekly", [f"_data/generated/history/{year}/weeks.json" for year in WEEKLY_YEARS]),
            "games": len(team_games), "wins": outcomes.count("W"), "losses": outcomes.count("L"), "ties": outcomes.count("T"),
            "win_percentage": rounded((outcomes.count("W") + outcomes.count("T") * 0.5) / len(outcomes), 6) if outcomes else None,
            "points_for": rounded(sum(scores_for)) if scores_for else None, "points_against": rounded(sum(scores_against)) if scores_against else None,
            "average_score": rounded(sum(scores_for) / len(scores_for), 3) if scores_for else None,
            "highest_score": max(scores_for) if scores_for else None, "lowest_score": min(scores_for) if scores_for else None,
            "biggest_win": max(wins, key=lambda game: game["margin"]) if wins else None,
            "closest_win": min(wins, key=lambda game: game["margin"]) if wins else None,
            "longest_winning_streak": win_streaks.get(franchise_id),
            "playoff_record": playoff_rows.get(franchise_id),
            "head_to_head_available": any(game["team_a"] and game["team_b"] for game in team_games),
        }
        output.append({**compact_identity(franchise_id, identities), "season_history": season_history, "weekly_performance": weekly})
    return sorted(output, key=lambda item: (-item["season_history"]["wins"], item["franchise_id"]))


def build_payloads() -> dict[str, dict[str, Any]]:
    completeness = load_json(HISTORY_ROOT / "completeness.json")
    scopes = completeness.get("coverage_scopes", {})
    if scopes.get("season_level_metrics", {}).get("label") != SEASON_LABEL or scopes.get("weekly_derived_metrics", {}).get("label") != WEEKLY_LABEL:
        raise ValueError("historical coverage scopes do not match the required contract")
    identities = identity_index(load_yaml(ROOT / "_data" / "franchises.yml")["franchises"])
    raw_games, weekly_sources = load_weekly_games()
    playoff_rounds, playoff_sources = classified_playoff_games(raw_games)
    games = [game_entry(game, identities, playoff_rounds) for game in raw_games]
    resolved_games = [game for game in games if game["team_a"] and game["team_b"]]
    decided = [game for game in resolved_games if not game["tie"]]
    regular = [game for game in decided if game["game_type"] == "regular_season"]
    playoffs = [game for game in decided if game["game_type"] == "championship_playoff"]
    ties = [game for game in resolved_games if game["tie"]]
    streaks = build_streaks(games, identities)
    scores = [{"matchup_id": game["matchup_id"], "season": game["season"], "week": game["week"], "game_type": game["game_type"], **compact_identity(side["franchise_id"], identities), "score": side["score"]} for game in games for side in (game["team_a"], game["team_b"]) if side]
    combined = [game for game in resolved_games]
    by_season = []
    for year in WEEKLY_YEARS:
        year_scores = [item for item in scores if item["season"] == year]
        by_season.append({"season": year, "highest": max(year_scores, key=lambda item: (item["score"], item["franchise_id"])), "lowest": min(year_scores, key=lambda item: (item["score"], item["franchise_id"]))})
    weekly_coverage = coverage("weekly", weekly_sources)
    season_sources = [f"_data/generated/history/{year}/standings.json" for year in SEASON_YEARS]
    generated_at = completeness["generated_at"]
    h2h = build_head_to_head(games, identities)
    franchise_summaries = build_franchise_summaries(games, identities, streaks)
    playoff_metrics = build_playoff_metrics(games, identities)
    biggest_overall = ranked(decided, lambda game: game["margin"], limit=10)
    biggest_regular = ranked(regular, lambda game: game["margin"], limit=10)
    biggest_playoffs = ranked(playoffs, lambda game: game["margin"], limit=10)
    closest_overall = ranked(decided, lambda game: game["margin"], reverse=False, limit=10)
    closest_playoffs = ranked(playoffs, lambda game: game["margin"], reverse=False, limit=10)
    highest_scores = ranked(scores, lambda item: item["score"], limit=10)
    lowest_scores = ranked(scores, lambda item: item["score"], reverse=False, limit=10)
    highest_combined = ranked(combined, lambda game: game["combined_score"], limit=10)
    lowest_combined = ranked(combined, lambda game: game["combined_score"], reverse=False, limit=10)
    base = {"schema_version": 1, "generated_at": generated_at}
    payloads = {
        "head_to_head": {**base, "coverage": weekly_coverage, "pairs": h2h},
        "biggest_wins": {**base, "coverage": weekly_coverage, "overall": biggest_overall, "regular_season": biggest_regular, "championship_playoffs": biggest_playoffs},
        "closest_games": {**base, "coverage": weekly_coverage, "overall": closest_overall, "championship_playoffs": closest_playoffs, "ties": ties},
        "weekly_scores": {**base, "coverage": weekly_coverage, "highest_team_scores": highest_scores, "lowest_team_scores": lowest_scores, "by_season": by_season, "highest_combined_matchups": highest_combined, "lowest_combined_matchups": lowest_combined},
        "streaks": {**base, "coverage": weekly_coverage, "scope_note": "Regular-season games only; ties break win/loss streaks and extend unbeaten streaks.", **streaks},
        "playoffs": {**base, "coverage": coverage("weekly", weekly_sources + playoff_sources), "classification": "Only independently matched championship-bracket games; placement and ambiguous postseason games are excluded.", "franchises": playoff_metrics, "games": playoffs},
        "franchise_summaries": {**base, "season_level_coverage": coverage("season", season_sources + ["_data/champions.yml", "_data/generated/history/2025/playoffs.json"]), "weekly_coverage": weekly_coverage, "franchises": franchise_summaries},
        "record_thresholds": {**base, "coverage": weekly_coverage, "thresholds": {
            "highest_weekly_score": highest_scores[0]["score"], "tenth_highest_weekly_score": highest_scores[-1]["score"],
            "largest_margin": biggest_overall[0]["margin"], "tenth_largest_margin": biggest_overall[-1]["margin"],
            "highest_combined_matchup_score": highest_combined[0]["combined_score"], "lowest_combined_matchup_score": lowest_combined[0]["combined_score"],
        }},
    }
    payloads["manifest"] = {**base, "season_level_coverage": coverage("season", season_sources), "weekly_coverage": weekly_coverage, "files": [f"{name}.json" for name in OUTPUT_NAMES if name != "manifest"], "counts": {"weekly_matchups_input": len(games), "resolved_matchups": len(resolved_games), "excluded_unresolved_matchups": len(games) - len(resolved_games), "head_to_head_pairs": len(h2h), "classified_championship_playoff_games": len(playoffs), "franchise_summaries": len(franchise_summaries)}, "unresolved_identity_policy": "Unresolved historical identities are never assigned to canonical franchises. Their games are excluded from pair and opponent-dependent records.", "bench_records_enabled": False}
    return payloads


def serialized(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if committed outputs differ from deterministic aggregation")
    args = parser.parse_args()
    payloads = build_payloads()
    if args.check:
        stale = [name for name, payload in payloads.items() if not (OUTPUT_ROOT / f"{name}.json").is_file() or (OUTPUT_ROOT / f"{name}.json").read_text(encoding="utf-8") != serialized(payload)]
        if stale:
            for name in stale:
                path = OUTPUT_ROOT / f"{name}.json"
                committed = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
                expected = serialized(payloads[name]).splitlines()
                preview = list(difflib.unified_diff(committed, expected, fromfile=f"committed/{name}.json", tofile=f"generated/{name}.json", lineterm=""))[:24]
                if preview:
                    print("\n".join(preview))
            raise SystemExit(f"Historical metrics are stale: {', '.join(stale)}")
        print(f"Historical metrics are current: {len(payloads)} files")
        return
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (OUTPUT_ROOT / f"{name}.json").write_text(serialized(payload), encoding="utf-8")
    print(f"Wrote {len(payloads)} historical metric files to {OUTPUT_ROOT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
