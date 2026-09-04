#!/usr/bin/env python3
"""Build deterministic, coverage-gated historical Road to Glory metrics."""

from __future__ import annotations

import argparse
import difflib
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
HISTORY_ROOT = ROOT / "_data" / "generated" / "history"
OUTPUT_ROOT = ROOT / "_data" / "generated" / "records"
WEEKLY_YEARS = [2021, 2022, 2023, 2024, 2025]
SEASON_YEARS = [2021, 2022, 2023, 2024, 2025]
WEEKLY_LABEL = "Verified 2021–2025"
SEASON_LABEL = "Verified 2021–2025"
OUTPUT_NAMES = (
    "manifest", "franchise_career", "head_to_head", "biggest_wins", "closest_games",
    "weekly_scores", "streaks", "playoffs", "championships", "season_leaders",
    "record_thresholds", "franchise_summaries",
)
RANKING_LIMIT = 25


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
    quantum = Decimal("1").scaleb(-digits)
    return float(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP))


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
        2021: {"Semifinal": 15, "Championship": 16},
        2022: {"Semifinal": 15, "Championship": 16},
        2023: {"Quarterfinal": 14, "Semifinal": 15, "Championship": 16},
        2024: {"Quarterfinal": 14, "Semifinal": 15, "Championship": 16},
    }
    for season in canonical.get("playoffs", []):
        year = season["season"]
        if year not in round_week:
            continue
        for item in season.get("games", []):
            if item.get("bracket_type") == "placement":
                continue
            week = round_week[year].get(item["round"])
            if week is None:
                continue
            pair = frozenset((item.get("team_one_franchise_id"), item.get("team_two_franchise_id")))
            game = lookup.get((year, week, pair))
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


def series_streak(meetings: list[dict[str, Any]], a_id: str, b_id: str, *, current: bool) -> dict[str, Any] | None:
    """Return a current or longest winning run within one head-to-head series."""
    ordered = sorted(meetings, key=lambda game: (game["season"], game["week"], game["matchup_id"]))
    runs: list[list[dict[str, Any]]] = []
    active: list[dict[str, Any]] = []
    for game in ordered:
        winner_id = game["winner"]["franchise_id"] if game.get("winner") else None
        if not winner_id:
            if active:
                runs.append(active)
            active = []
        elif active and active[-1]["winner"]["franchise_id"] == winner_id:
            active.append(game)
        else:
            if active:
                runs.append(active)
            active = [game]
    if active:
        runs.append(active)
    if not runs or (current and ordered[-1].get("tie")):
        return None
    run = runs[-1] if current else max(
        runs,
        key=lambda value: (len(value), value[-1]["season"], value[-1]["week"], value[-1]["matchup_id"]),
    )
    winner_id = run[-1]["winner"]["franchise_id"]
    return {
        "franchise_id": winner_id,
        "wins": len(run),
        "against_franchise_id": b_id if winner_id == a_id else a_id,
        "start_season": run[0]["season"],
        "start_week": run[0]["week"],
        "end_season": run[-1]["season"],
        "end_week": run[-1]["week"],
    }


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
        points_a = sum((
            Decimal(str(game["team_a"]["score"] if game["team_a"]["franchise_id"] == a_id else game["team_b"]["score"]))
            for game in meetings
        ), Decimal("0"))
        points_b = sum((
            Decimal(str(game["team_a"]["score"] if game["team_a"]["franchise_id"] == b_id else game["team_b"]["score"]))
            for game in meetings
        ), Decimal("0"))
        total_margin = sum((Decimal(str(game["margin"])) for game in meetings), Decimal("0"))
        wins_by_a = [game for game in meetings if game["winner"] and game["winner"]["franchise_id"] == a_id]
        wins_by_b = [game for game in meetings if game["winner"] and game["winner"]["franchise_id"] == b_id]
        decided = [game for game in meetings if not game["tie"]]
        playoff_meetings = [game for game in meetings if game["game_type"] == "championship_playoff"]
        championship_meetings = [game for game in playoff_meetings if game["playoff_round"] == "Championship"]
        recent = sorted(meetings, key=lambda game: (game["season"], game["week"]), reverse=True)
        output.append({
            "pair_id": f"{a_id}--{b_id}",
            "share_path": f"/head-to-head/?a={a_id}&b={b_id}",
            "rivalry_title": None,
            "editorial_history": None,
            "franchise_a": compact_identity(a_id, identities),
            "franchise_b": compact_identity(b_id, identities),
            "meetings": len(meetings), "wins_a": wins_a, "wins_b": wins_b, "ties": ties,
            "points_a": rounded(points_a), "points_b": rounded(points_b),
            "average_score_a": rounded(points_a / Decimal(len(meetings)), 3),
            "average_score_b": rounded(points_b / Decimal(len(meetings)), 3),
            "average_margin": rounded(total_margin / Decimal(len(meetings)), 3),
            "largest_win_a": meeting_view(max(wins_by_a, key=lambda game: game["margin"])) if wins_by_a else None,
            "largest_win_b": meeting_view(max(wins_by_b, key=lambda game: game["margin"])) if wins_by_b else None,
            "closest_meeting": meeting_view(min(decided, key=lambda game: (game["margin"], game["season"], game["week"]))) if decided else None,
            "highest_scoring_meeting": meeting_view(max(meetings, key=lambda game: (game["combined_score"], game["season"], game["week"]))),
            "lowest_scoring_meeting": meeting_view(min(meetings, key=lambda game: (game["combined_score"], game["season"], game["week"]))),
            "most_recent_meeting": meeting_view(recent[0]),
            "first_meeting": meeting_view(recent[-1]),
            "current_series_streak": series_streak(meetings, a_id, b_id, current=True),
            "longest_series_streak": series_streak(meetings, a_id, b_id, current=False),
            "playoff_meetings": len(playoff_meetings),
            "playoff_wins_a": sum(bool(game["winner"] and game["winner"]["franchise_id"] == a_id) for game in playoff_meetings),
            "playoff_wins_b": sum(bool(game["winner"] and game["winner"]["franchise_id"] == b_id) for game in playoff_meetings),
            "championship_meetings": len(championship_meetings),
            "championship_wins_a": sum(bool(game["winner"] and game["winner"]["franchise_id"] == a_id) for game in championship_meetings),
            "championship_wins_b": sum(bool(game["winner"] and game["winner"]["franchise_id"] == b_id) for game in championship_meetings),
            "recent_meetings": [meeting_view(game) for game in recent[:10]],
            "all_meetings": [meeting_view(game) for game in recent],
            "memorable_meetings": {
                "closest": meeting_view(min(decided, key=lambda game: (game["margin"], game["season"], game["week"]))) if decided else None,
                "highest_scoring": meeting_view(max(meetings, key=lambda game: (game["combined_score"], game["season"], game["week"]))),
                "largest_win_a": meeting_view(max(wins_by_a, key=lambda game: game["margin"])) if wins_by_a else None,
                "largest_win_b": meeting_view(max(wins_by_b, key=lambda game: game["margin"])) if wins_by_b else None,
            },
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
    playoff_by_team: defaultdict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for game in games:
        for side in (game["team_a"], game["team_b"]):
            if side and game["game_type"] == "regular_season":
                by_team[side["franchise_id"]].append((game["season"], game["week"], outcome_for(game, side["franchise_id"])))
            elif side and game["game_type"] == "championship_playoff":
                playoff_by_team[side["franchise_id"]].append((game["season"], game["week"], outcome_for(game, side["franchise_id"])))
    output = {
        "single_season_wins": [], "single_season_losses": [], "single_season_unbeaten": [],
        "cross_season_wins": [], "cross_season_losses": [], "cross_season_unbeaten": [],
        "playoff_wins": [], "playoff_losses": [], "championship_appearance_streaks": [],
    }
    for franchise_id, sequence in by_team.items():
        sequence.sort()
        for key, accepted, cross in (
            ("single_season_wins", {"W"}, False), ("single_season_losses", {"L"}, False),
            ("single_season_unbeaten", {"W", "T"}, False), ("cross_season_wins", {"W"}, True),
            ("cross_season_losses", {"L"}, True), ("cross_season_unbeaten", {"W", "T"}, True),
        ):
            result = best_streak(sequence, accepted, cross_season=cross)
            if result:
                output[key].append({**compact_identity(franchise_id, identities), **result})
    for franchise_id, sequence in playoff_by_team.items():
        sequence.sort()
        for key, accepted in (("playoff_wins", {"W"}), ("playoff_losses", {"L"})):
            result = best_streak(sequence, accepted, cross_season=True)
            if result:
                output[key].append({**compact_identity(franchise_id, identities), **result})
    for key in output:
        output[key] = sorted(output[key], key=lambda item: (-item["games"], item["franchise_id"]))
        for index, item in enumerate(output[key], start=1):
            item["rank"] = index
    return output


def championship_facts() -> list[dict[str, Any]]:
    facts_by_season = {
        item["year"]: {
            "season": item["year"],
            "champion_franchise_id": item["champion_franchise_id"],
            "runner_up_franchise_id": item["runner_up_franchise_id"],
        }
        for item in load_yaml(ROOT / "_data" / "champions.yml")["champions"]
    }

    # The generated playoff archive remains a fallback while a season is being
    # backfilled. Once that season has a canonical champions.yml entry, do not
    # count the same championship a second time.
    if 2025 not in facts_by_season:
        placements = load_json(ROOT / "_data" / "generated" / "history" / "2025" / "playoffs.json")["final_placements"]
        by_place = {item["place"]: item for item in placements}
        facts_by_season[2025] = {
            "season": 2025,
            "champion_franchise_id": by_place[1]["franchise_id"],
            "runner_up_franchise_id": by_place[2]["franchise_id"],
        }
    return [facts_by_season[season] for season in sorted(facts_by_season)]


def build_championship_appearance_streaks(
    championships: list[dict[str, Any]], identities: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    years_by_team: defaultdict[str, list[int]] = defaultdict(list)
    for item in championships:
        years_by_team[item["champion_franchise_id"]].append(item["season"])
        years_by_team[item["runner_up_franchise_id"]].append(item["season"])
    rows = []
    for franchise_id, years in years_by_team.items():
        best: list[int] = []
        active: list[int] = []
        for year in sorted(set(years)):
            if active and year != active[-1] + 1:
                active = []
            active.append(year)
            if len(active) > len(best):
                best = list(active)
        if len(best) > 1:
            rows.append({
                **compact_identity(franchise_id, identities),
                "games": len(best),
                "start_season": best[0],
                "start_week": None,
                "end_season": best[-1],
                "end_week": None,
            })
    rows.sort(key=lambda item: (-item["games"], item["franchise_id"]))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def build_playoff_metrics(games: list[dict[str, Any]], identities: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    playoff_games = [game for game in games if game["game_type"] == "championship_playoff"]
    championships = championship_facts()
    rows = []
    for franchise_id in sorted(identities):
        team_games = [game for game in playoff_games if game["team_a"]["franchise_id"] == franchise_id or game["team_b"]["franchise_id"] == franchise_id]
        titles = sum(item["champion_franchise_id"] == franchise_id for item in championships)
        finals = sum(franchise_id in (item["champion_franchise_id"], item["runner_up_franchise_id"]) for item in championships)
        runner_ups = sum(item["runner_up_franchise_id"] == franchise_id for item in championships)
        if not team_games and not titles and not finals:
            continue
        wins = [game for game in team_games if game["winner"]["franchise_id"] == franchise_id]
        scores = [side["score"] for game in team_games for side in (game["team_a"], game["team_b"]) if side["franchise_id"] == franchise_id]
        rows.append({
            **compact_identity(franchise_id, identities),
            "playoff_appearances": len({game["season"] for game in team_games}),
            "playoff_games": len(team_games),
            "playoff_wins": len(wins),
            "playoff_losses": len(team_games) - len(wins),
            "playoff_win_percentage": rounded(len(wins) / len(team_games), 6) if team_games else None,
            "semifinal_appearances": sum(game["playoff_round"] == "Semifinal" for game in team_games),
            "championship_appearances": finals,
            "championships": titles,
            "runner_up_finishes": runner_ups,
            "championship_record": {
                "wins": titles,
                "losses": runner_ups,
                "win_percentage": rounded(titles / finals, 6) if finals else None,
            },
            "largest_playoff_win": meeting_view(max(wins, key=lambda game: game["margin"])) if wins else None,
            "closest_playoff_win": meeting_view(min(wins, key=lambda game: game["margin"])) if wins else None,
            "highest_playoff_score": max(scores) if scores else None,
            "lowest_playoff_score": min(scores) if scores else None,
        })
    rows.sort(key=lambda item: (-item["championships"], -item["playoff_wins"], item["franchise_id"]))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def build_franchise_summaries(
    games: list[dict[str, Any]],
    identities: dict[str, dict[str, Any]],
    streaks: dict[str, list[dict[str, Any]]],
    head_to_head: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    standings_by_team: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for year in SEASON_YEARS:
        payload = load_json(HISTORY_ROOT / str(year) / "standings.json")
        for row in payload["standings"]:
            if row.get("franchise_id"):
                standings_by_team[row["franchise_id"]].append({"season": year, **row})
    championships = championship_facts()
    playoff_rows = {row["franchise_id"]: row for row in build_playoff_metrics(games, identities)}
    win_streaks = {row["franchise_id"]: row for row in streaks["single_season_wins"]}
    loss_streaks = {row["franchise_id"]: row for row in streaks["single_season_losses"]}
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
        season_rows = [{
            "season": row["season"],
            "historical_team_name": row["historical_team_name"],
            "rank": row["rank"],
            "wins": row["wins"],
            "losses": row["losses"],
            "ties": row["ties"],
            "win_percentage": rounded((row["wins"] + row["ties"] * 0.5) / (row["wins"] + row["losses"] + row["ties"]), 6),
            "points_for": row["points_for"],
            "points_against": row["points_against"],
            "point_differential": rounded(row["points_for"] - row["points_against"]),
            "playoff_seed": row.get("playoff_seed"),
            "playoff_finish": row.get("playoff_finish"),
            "season_path": f"/history/{row['season']}/",
        } for row in seasons]
        best_season = max(season_rows, key=lambda row: (row["win_percentage"], row["wins"], row["points_for"], -row["season"])) if season_rows else None
        worst_season = min(season_rows, key=lambda row: (row["win_percentage"], row["wins"], row["points_for"], row["season"])) if season_rows else None
        high_pf_season = max(season_rows, key=lambda row: (row["points_for"], -row["season"])) if season_rows else None
        low_pf_season = min(season_rows, key=lambda row: (row["points_for"], row["season"])) if season_rows else None
        total_wins = sum(row["wins"] for row in seasons)
        total_losses = sum(row["losses"] for row in seasons)
        total_ties = sum(row["ties"] for row in seasons)
        total_games = total_wins + total_losses + total_ties
        season_history = {
            "coverage": coverage("season", [f"_data/generated/history/{year}/standings.json" for year in SEASON_YEARS] + ["_data/champions.yml", "_data/generated/history/2025/playoffs.json"]),
            "seasons_represented": [row["season"] for row in seasons],
            "season_count": len(seasons),
            "games": total_games,
            "wins": total_wins, "losses": total_losses, "ties": total_ties,
            "win_percentage": rounded((total_wins + total_ties * 0.5) / total_games, 6) if total_games else None,
            "points_for": rounded(sum(row["points_for"] for row in seasons)), "points_against": rounded(sum(row["points_against"] for row in seasons)),
            "point_differential": rounded(sum(row["points_for"] - row["points_against"] for row in seasons)),
            "average_final_rank": rounded(sum(row["rank"] for row in seasons) / len(seasons), 3) if seasons else None,
            "championships": sum(item["champion_franchise_id"] == franchise_id for item in championships),
            "best_season_record": best_season,
            "worst_season_record": worst_season,
            "highest_single_season_pf": high_pf_season,
            "lowest_single_season_pf": low_pf_season,
            "seasons": season_rows,
        }
        playoff_record = playoff_rows.get(franchise_id)
        h2h_rows = []
        for pair in head_to_head:
            if franchise_id not in (pair["franchise_a"]["franchise_id"], pair["franchise_b"]["franchise_id"]):
                continue
            as_a = franchise_id == pair["franchise_a"]["franchise_id"]
            h2h_rows.append({
                "pair_id": pair["pair_id"],
                "share_path": pair["share_path"],
                "opponent": pair["franchise_b"] if as_a else pair["franchise_a"],
                "meetings": pair["meetings"],
                "wins": pair["wins_a"] if as_a else pair["wins_b"],
                "losses": pair["wins_b"] if as_a else pair["wins_a"],
                "ties": pair["ties"],
                "points_for": pair["points_a"] if as_a else pair["points_b"],
                "points_against": pair["points_b"] if as_a else pair["points_a"],
                "playoff_meetings": pair["playoff_meetings"],
                "championship_meetings": pair["championship_meetings"],
            })
        h2h_rows.sort(key=lambda row: (-row["meetings"], row["opponent"]["display_name"]))
        championship_history = []
        for item in championships:
            if franchise_id in (item["champion_franchise_id"], item["runner_up_franchise_id"]):
                championship_history.append({
                    "season": item["season"],
                    "result": "Champion" if item["champion_franchise_id"] == franchise_id else "Runner-up",
                    "opponent_franchise_id": item["runner_up_franchise_id"] if item["champion_franchise_id"] == franchise_id else item["champion_franchise_id"],
                    "season_path": f"/history/{item['season']}/",
                })
        timeline = []
        if season_rows:
            timeline.append({"season": season_rows[0]["season"], "week": None, "event_type": "first_verified_season", "label": f"First verified league season as {season_rows[0]['historical_team_name']}"})
            previous_name = season_rows[0]["historical_team_name"]
            for row in season_rows[1:]:
                if row["historical_team_name"] != previous_name:
                    timeline.append({"season": row["season"], "week": None, "event_type": "name_change", "label": f"Historical display name changed from {previous_name} to {row['historical_team_name']}"})
                    previous_name = row["historical_team_name"]
        for item in championship_history:
            timeline.append({"season": item["season"], "week": None, "event_type": "championship" if item["result"] == "Champion" else "championship_appearance", "label": item["result"]})
        playoff_seasons = sorted({
            game["season"] for game in team_games if game["game_type"] == "championship_playoff"
        })
        for season in playoff_seasons:
            timeline.append({"season": season, "week": None, "event_type": "playoff_appearance", "label": "Playoff appearance"})
        if scores_for:
            high_game = max(team_games, key=lambda game: next(side["score"] for side in (game["team_a"], game["team_b"]) if side and side["franchise_id"] == franchise_id))
            timeline.append({"season": high_game["season"], "week": high_game["week"], "event_type": "franchise_record", "label": f"Franchise-high verified score: {max(scores_for):.2f}"})
        timeline.sort(key=lambda item: (item["season"], item["week"] or 0, item["event_type"]))
        weekly = {
            "coverage": coverage("weekly", [f"_data/generated/history/{year}/weeks.json" for year in WEEKLY_YEARS]),
            "games": len(team_games), "wins": outcomes.count("W"), "losses": outcomes.count("L"), "ties": outcomes.count("T"),
            "win_percentage": rounded((outcomes.count("W") + outcomes.count("T") * 0.5) / len(outcomes), 6) if outcomes else None,
            "points_for": rounded(sum(scores_for)) if scores_for else None, "points_against": rounded(sum(scores_against)) if scores_against else None,
            "average_score": rounded(sum(scores_for) / len(scores_for), 3) if scores_for else None,
            "average_points_allowed": rounded(sum(scores_against) / len(scores_against), 3) if scores_against else None,
            "highest_score": max(scores_for) if scores_for else None, "lowest_score": min(scores_for) if scores_for else None,
            "biggest_win": meeting_view(max(wins, key=lambda game: game["margin"])) if wins else None,
            "closest_win": meeting_view(min(wins, key=lambda game: game["margin"])) if wins else None,
            "longest_winning_streak": win_streaks.get(franchise_id),
            "longest_losing_streak": loss_streaks.get(franchise_id),
            "playoff_record": playoff_record,
            "head_to_head_available": any(game["team_a"] and game["team_b"] for game in team_games),
        }
        output.append({
            **compact_identity(franchise_id, identities),
            "season_history": season_history,
            "weekly_performance": weekly,
            "playoff_history": playoff_record,
            "championship_history": championship_history,
            "head_to_head": h2h_rows,
            "timeline_events": timeline,
        })
    output.sort(key=lambda item: (-(item["season_history"]["win_percentage"] or 0), -item["season_history"]["wins"], -item["season_history"]["points_for"], item["franchise_id"]))
    for index, row in enumerate(output, start=1):
        row["rank"] = index
    return output


def standing_rows(identities: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for year in SEASON_YEARS:
        payload = load_json(HISTORY_ROOT / str(year) / "standings.json")
        for item in payload["standings"]:
            franchise_id = item.get("franchise_id")
            if not franchise_id:
                continue
            games = item["wins"] + item["losses"] + item["ties"]
            rows.append({
                "season": year,
                "season_path": f"/history/{year}/",
                "historical_team_name": item["historical_team_name"],
                **compact_identity(franchise_id, identities),
                "rank": item["rank"],
                "wins": item["wins"],
                "losses": item["losses"],
                "ties": item["ties"],
                "win_percentage": rounded((item["wins"] + item["ties"] * 0.5) / games, 6),
                "points_for": item["points_for"],
                "points_against": item["points_against"],
                "point_differential": rounded(item["points_for"] - item["points_against"]),
                "playoff_seed": item.get("playoff_seed"),
                "playoff_finish": item.get("playoff_finish"),
            })
    return rows


def championship_payload(
    identities: dict[str, dict[str, Any]], standings: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    seeds = {(row["season"], row["franchise_id"]): row.get("playoff_seed") for row in standings}
    entries = []
    for item in load_yaml(ROOT / "_data" / "champions.yml")["champions"]:
        champion_id = item["champion_franchise_id"]
        runner_id = item["runner_up_franchise_id"]
        entries.append({
            "season": item["year"],
            "season_path": item["season_path"],
            "champion": compact_identity(champion_id, identities),
            "runner_up": compact_identity(runner_id, identities),
            "champion_score": item["champion_score"],
            "runner_up_score": item["runner_up_score"],
            "margin": rounded(item["champion_score"] - item["runner_up_score"]),
            "combined_score": rounded(item["champion_score"] + item["runner_up_score"]),
            "champion_seed": seeds.get((item["year"], champion_id)),
            "runner_up_seed": seeds.get((item["year"], runner_id)),
        })
    entries.sort(key=lambda row: row["season"], reverse=True)
    rows = []
    for franchise_id in sorted(identities):
        appearances = [entry for entry in entries if franchise_id in (entry["champion"]["franchise_id"], entry["runner_up"]["franchise_id"])]
        if not appearances:
            continue
        wins = sum(entry["champion"]["franchise_id"] == franchise_id for entry in appearances)
        rows.append({
            **compact_identity(franchise_id, identities),
            "appearances": len(appearances),
            "championships": wins,
            "runner_up_finishes": len(appearances) - wins,
            "win_percentage": rounded(wins / len(appearances), 6),
        })

    def leaderboard(key) -> list[dict[str, Any]]:
        ordered_rows = sorted(rows, key=key)
        for index, row in enumerate(ordered_rows, start=1):
            row = row.copy()
            row["rank"] = index
            ordered_rows[index - 1] = row
        return ordered_rows

    leaders = {
        "most_championships": leaderboard(lambda row: (-row["championships"], -row["appearances"], row["franchise_id"])),
        "most_appearances": leaderboard(lambda row: (-row["appearances"], -row["championships"], row["franchise_id"])),
        "best_championship_record": leaderboard(lambda row: (-row["win_percentage"], -row["appearances"], row["franchise_id"])),
        "most_runner_up_finishes": leaderboard(lambda row: (-row["runner_up_finishes"], -row["appearances"], row["franchise_id"])),
    }
    return entries, leaders


def ranked_seasons(entries: list[dict[str, Any]], field: str, *, reverse: bool) -> list[dict[str, Any]]:
    ordered_rows = sorted(
        entries,
        key=lambda row: (row[field], row["wins"], row["points_for"], -row["season"], row["franchise_id"]),
        reverse=reverse,
    )
    result = []
    previous = object()
    for position, row in enumerate(ordered_rows, start=1):
        value = row[field]
        rank = result[-1]["record_rank"] if result and value == previous else position
        result.append({"record_rank": rank, **row})
        previous = value
    return result


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
    championship_games = [game for game in playoffs if game["playoff_round"] == "Championship"]
    ties = [game for game in resolved_games if game["tie"]]
    streaks = build_streaks(games, identities)
    championship_finals = championship_facts()
    streaks["championship_appearance_streaks"] = build_championship_appearance_streaks(championship_finals, identities)
    scores = []
    for game in resolved_games:
        for side, opponent in ((game["team_a"], game["team_b"]), (game["team_b"], game["team_a"])):
            scores.append({
                "matchup_id": game["matchup_id"],
                "season": game["season"],
                "week": game["week"],
                "game_type": game["game_type"],
                "playoff_round": game["playoff_round"],
                **compact_identity(side["franchise_id"], identities),
                "score": side["score"],
                "opponent": compact_identity(opponent["franchise_id"], identities),
                "opponent_score": opponent["score"],
                "result": outcome_for(game, side["franchise_id"]),
                "margin": game["margin"],
                "combined_score": game["combined_score"],
            })
    combined = [game for game in resolved_games]
    by_season = []
    for year in WEEKLY_YEARS:
        year_scores = [item for item in scores if item["season"] == year]
        by_season.append({"season": year, "highest": max(year_scores, key=lambda item: (item["score"], item["franchise_id"])), "lowest": min(year_scores, key=lambda item: (item["score"], item["franchise_id"]))})
    weekly_coverage = coverage("weekly", weekly_sources)
    season_sources = [f"_data/generated/history/{year}/standings.json" for year in SEASON_YEARS]
    season_coverage = coverage("season", season_sources + ["_data/champions.yml"])
    generated_at = completeness["generated_at"]
    h2h = build_head_to_head(games, identities)
    franchise_summaries = build_franchise_summaries(games, identities, streaks, h2h)
    playoff_metrics = build_playoff_metrics(games, identities)
    standings = standing_rows(identities)
    championship_entries, championship_leaders = championship_payload(identities, standings)
    biggest_overall = ranked(decided, lambda game: game["margin"], limit=RANKING_LIMIT)
    biggest_regular = ranked(regular, lambda game: game["margin"], limit=10)
    biggest_playoffs = ranked(playoffs, lambda game: game["margin"], limit=10)
    biggest_championship = ranked(championship_games, lambda game: game["margin"], limit=10)
    closest_overall = ranked(decided, lambda game: game["margin"], reverse=False, limit=RANKING_LIMIT)
    closest_playoffs = ranked(playoffs, lambda game: game["margin"], reverse=False, limit=10)
    closest_championship = ranked(championship_games, lambda game: game["margin"], reverse=False, limit=10)
    highest_scores = ranked(scores, lambda item: item["score"], limit=RANKING_LIMIT)
    lowest_scores = ranked(scores, lambda item: item["score"], reverse=False, limit=RANKING_LIMIT)
    highest_combined = ranked(combined, lambda game: game["combined_score"], limit=RANKING_LIMIT)
    lowest_combined = ranked(combined, lambda game: game["combined_score"], reverse=False, limit=RANKING_LIMIT)
    highest_losing_scores = ranked([item for item in scores if item["result"] == "L"], lambda item: item["score"], limit=RANKING_LIMIT)
    lowest_winning_scores = ranked([item for item in scores if item["result"] == "W"], lambda item: item["score"], reverse=False, limit=RANKING_LIMIT)
    biggest_by_franchise = []
    closest_by_franchise = []
    score_by_franchise = []
    threshold_by_franchise = []
    for franchise_id in sorted(identities):
        franchise_wins = [game for game in decided if game["winner"]["franchise_id"] == franchise_id]
        franchise_scores = [item for item in scores if item["franchise_id"] == franchise_id]
        if franchise_wins:
            biggest_game = max(franchise_wins, key=lambda game: (game["margin"], game["season"], game["week"]))
            closest_game = min(franchise_wins, key=lambda game: (game["margin"], game["season"], game["week"]))
            biggest_by_franchise.append({**compact_identity(franchise_id, identities), "game": meeting_view(biggest_game)})
            closest_by_franchise.append({**compact_identity(franchise_id, identities), "game": meeting_view(closest_game)})
        if franchise_scores:
            high = max(franchise_scores, key=lambda item: (item["score"], item["season"], item["week"]))
            low = min(franchise_scores, key=lambda item: (item["score"], item["season"], item["week"]))
            score_by_franchise.append({**compact_identity(franchise_id, identities), "highest": high, "lowest": low})
            threshold_by_franchise.append({
                **compact_identity(franchise_id, identities),
                "highest_weekly_score": high["score"],
                "largest_win_margin": max((game["margin"] for game in franchise_wins), default=None),
                "highest_combined_matchup_score": max(item["combined_score"] for item in franchise_scores),
            })
    season_leaders = {
        "best_single_season_records": ranked_seasons(standings, "win_percentage", reverse=True),
        "highest_single_season_pf": ranked_seasons(standings, "points_for", reverse=True),
        "lowest_single_season_pa": ranked_seasons(standings, "points_against", reverse=False),
        "best_point_differential": ranked_seasons(standings, "point_differential", reverse=True),
        "most_dominant_champions": sorted(championship_entries, key=lambda row: (-row["margin"], -row["season"])),
        "closest_championships": sorted(championship_entries, key=lambda row: (row["margin"], -row["season"])),
        "highest_scoring_championships": sorted(championship_entries, key=lambda row: (-row["combined_score"], -row["season"])),
        "lowest_scoring_championships": sorted(championship_entries, key=lambda row: (row["combined_score"], -row["season"])),
    }
    base = {"schema_version": 1, "generated_at": generated_at}
    career_base = {
        **base,
        "season_level_coverage": season_coverage,
        "weekly_coverage": weekly_coverage,
        "ranking_rule": "Ranked by season-level win percentage, then total wins, then points for.",
        "franchises": franchise_summaries,
    }
    payloads = {
        "head_to_head": {**base, "coverage": weekly_coverage, "pairs": h2h},
        "biggest_wins": {**base, "coverage": weekly_coverage, "overall": biggest_overall, "regular_season": biggest_regular, "championship_playoffs": biggest_playoffs, "championships": biggest_championship, "by_franchise": biggest_by_franchise},
        "closest_games": {**base, "coverage": weekly_coverage, "overall": closest_overall, "championship_playoffs": closest_playoffs, "championships": closest_championship, "by_franchise": closest_by_franchise, "ties": ties},
        "weekly_scores": {**base, "coverage": weekly_coverage, "highest_team_scores": highest_scores, "lowest_team_scores": lowest_scores, "by_franchise": score_by_franchise, "by_season": by_season, "highest_combined_matchups": highest_combined, "lowest_combined_matchups": lowest_combined, "highest_losing_scores": highest_losing_scores, "lowest_winning_scores": lowest_winning_scores},
        "streaks": {**base, "coverage": weekly_coverage, "scope_note": "Single-season runs reset at each season boundary. Cross-season regular-season and classified-playoff runs may continue only into the immediately adjacent represented season; ties break win/loss runs and extend unbeaten runs.", **streaks},
        "playoffs": {**base, "coverage": coverage("weekly", weekly_sources + playoff_sources), "classification": "Only independently matched championship-bracket games; placement and ambiguous postseason games are excluded.", "franchises": playoff_metrics, "games": playoffs},
        "championships": {**base, "coverage": season_coverage, "championships": championship_entries, "leaderboards": championship_leaders},
        "season_leaders": {**base, "coverage": season_coverage, "comparisons": season_leaders},
        "franchise_career": career_base,
        "franchise_summaries": {**career_base, "compatibility_note": "Compatibility alias; new pages use franchise_career.json."},
        "record_thresholds": {**base, "coverage": weekly_coverage, "thresholds": {
            "highest_weekly_score": highest_scores[0]["score"], "tenth_highest_weekly_score": highest_scores[9]["score"],
            "twenty_fifth_highest_weekly_score": highest_scores[24]["score"],
            "largest_margin": biggest_overall[0]["margin"], "tenth_largest_margin": biggest_overall[9]["margin"],
            "highest_combined_matchup_score": highest_combined[0]["combined_score"], "lowest_combined_matchup_score": lowest_combined[0]["combined_score"],
            "highest_losing_score": highest_losing_scores[0]["score"], "lowest_winning_score": lowest_winning_scores[0]["score"],
        }, "franchises": threshold_by_franchise, "live_data_dependency": False},
    }
    payloads["manifest"] = {**base, "season_level_coverage": coverage("season", season_sources), "weekly_coverage": weekly_coverage, "files": [f"{name}.json" for name in OUTPUT_NAMES if name != "manifest"], "counts": {"weekly_matchups_input": len(games), "resolved_matchups": len(resolved_games), "excluded_unresolved_matchups": len(games) - len(resolved_games), "head_to_head_pairs": len(h2h), "classified_championship_playoff_games": len(playoffs), "franchise_career_rows": len(franchise_summaries), "championships": len(championship_entries)}, "unresolved_identity_policy": "Unresolved historical identities are never assigned to canonical franchises. Their games are excluded from pair and opponent-dependent records.", "postseason_policy": "Placement and unclassified postseason games remain in general matchup history but are excluded from championship-bracket playoff totals.", "bench_records_enabled": False}
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
