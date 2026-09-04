#!/usr/bin/env python3
"""Validate deterministic historical metrics, coverage, and references."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

import build_historical_metrics as builder
from validate_public_data import validate_payload


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "_data" / "generated" / "records"


def load(name: str) -> dict[str, Any]:
    return json.loads((OUTPUT_ROOT / f"{name}.json").read_text(encoding="utf-8"))


def validate_coverage(value: Any, expected_label: str, expected_start: int, errors: list[str], location: str) -> None:
    if not isinstance(value, dict):
        errors.append(f"{location}: coverage object is required")
        return
    if value.get("label") != expected_label or value.get("start_season") != expected_start or value.get("end_season") != 2025:
        errors.append(f"{location}: invalid coverage window")
    if "all-time" in json.dumps(value).casefold():
        errors.append(f"{location}: cannot claim all-time coverage")


def validate_game(game: dict[str, Any], franchise_ids: set[str], errors: list[str], location: str) -> None:
    if game.get("season") not in builder.WEEKLY_YEARS:
        errors.append(f"{location}: weekly metric contains non-weekly season")
    if game.get("team_a") and game["team_a"].get("franchise_id") not in franchise_ids:
        errors.append(f"{location}: invalid team_a franchise")
    if game.get("team_b") and game["team_b"].get("franchise_id") not in franchise_ids:
        errors.append(f"{location}: invalid team_b franchise")
    if game.get("winner") and game["winner"].get("franchise_id") not in franchise_ids:
        errors.append(f"{location}: invalid winner franchise")
    a = game.get("team_a")
    b = game.get("team_b")
    if a and b:
        if not isinstance(a.get("score"), (int, float)) or not isinstance(b.get("score"), (int, float)):
            errors.append(f"{location}: both numeric scores are required")
        else:
            expected_margin = round(abs(a["score"] - b["score"]), 2)
            expected_tie = a["score"] == b["score"]
            if game.get("margin") != expected_margin or bool(game.get("tie")) != expected_tie:
                errors.append(f"{location}: score, tie, and margin fields disagree")
            expected_winner = None if expected_tie else (a if a["score"] > b["score"] else b)
            if (game.get("winner") or {}).get("franchise_id") != (expected_winner or {}).get("franchise_id"):
                errors.append(f"{location}: winner does not match the final score")
    if game.get("winner_score") is not None:
        expected = round(game["winner_score"] - game["loser_score"], 2)
        if expected != game.get("margin") or game["winner_score"] <= game["loser_score"]:
            errors.append(f"{location}: invalid winner/loser margin")


def ordered(entries: list[dict[str, Any]], field: str, reverse: bool) -> bool:
    values = [item[field] for item in entries]
    return values == sorted(values, reverse=reverse)


def validate_franchise_references(value: Any, franchise_ids: set[str], errors: list[str], location: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if (key == "franchise_id" or key.endswith("_franchise_id")) and child is not None:
                if child not in franchise_ids:
                    errors.append(f"{location}.{key}: invalid franchise reference {child}")
            else:
                validate_franchise_references(child, franchise_ids, errors, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_franchise_references(child, franchise_ids, errors, f"{location}[{index}]")


def validate_ranked(entries: list[dict[str, Any]], field: str, reverse: bool, errors: list[str], location: str) -> None:
    if not ordered(entries, field, reverse):
        errors.append(f"{location}: invalid {field} ordering")
    previous_value: Any = object()
    previous_rank = 0
    for position, entry in enumerate(entries, start=1):
        expected_rank = previous_rank if position > 1 and entry[field] == previous_value else position
        if entry.get("rank") != expected_rank:
            errors.append(f"{location}[{position - 1}]: invalid competition rank")
        previous_value = entry[field]
        previous_rank = expected_rank


def main() -> None:
    errors: list[str] = []
    expected = builder.build_payloads()
    payloads: dict[str, dict[str, Any]] = {}
    for name in builder.OUTPUT_NAMES:
        path = OUTPUT_ROOT / f"{name}.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{name}: {error}")
            continue
        payloads[name] = payload
        errors.extend(validate_payload(path, payload))
        if payload.get("schema_version") != 1:
            errors.append(f"{name}: schema_version must be 1")
        if payload != expected.get(name):
            errors.append(f"{name}: output differs from deterministic aggregation")
        if "bench" in name.casefold() or "bench_blunder" in json.dumps(payload).casefold():
            if name != "manifest":
                errors.append(f"{name}: bench records must remain disabled")

    franchises = yaml.safe_load((ROOT / "_data" / "franchises.yml").read_text(encoding="utf-8"))
    franchise_ids = {item["franchise_id"] for item in franchises["franchises"]}
    manifest = payloads.get("manifest", {})
    validate_coverage(manifest.get("season_level_coverage"), builder.SEASON_LABEL, 2021, errors, "manifest season")
    validate_coverage(manifest.get("weekly_coverage"), builder.WEEKLY_LABEL, 2021, errors, "manifest weekly")
    if manifest.get("bench_records_enabled") is not False:
        errors.append("manifest: bench records must be disabled")

    for name in ("head_to_head", "biggest_wins", "closest_games", "weekly_scores", "streaks", "playoffs", "record_thresholds"):
        if name in payloads:
            validate_coverage(payloads[name].get("coverage"), builder.WEEKLY_LABEL, 2021, errors, name)
    for name in ("championships", "season_leaders"):
        if name in payloads:
            validate_coverage(payloads[name].get("coverage"), builder.SEASON_LABEL, 2021, errors, name)
    for name in ("franchise_career", "franchise_summaries"):
        if name in payloads:
            validate_coverage(payloads[name].get("season_level_coverage"), builder.SEASON_LABEL, 2021, errors, f"{name} season")
            validate_coverage(payloads[name].get("weekly_coverage"), builder.WEEKLY_LABEL, 2021, errors, f"{name} weekly")

    expected_counts = {
        "weekly_matchups_input": 446,
        "resolved_matchups": 446,
        "excluded_unresolved_matchups": 0,
        "head_to_head_pairs": 78,
        "classified_championship_playoff_games": 21,
        "franchise_career_rows": 13,
        "championships": 5,
    }
    if manifest.get("counts") != expected_counts:
        errors.append(f"manifest: expected canonical counts {expected_counts}, found {manifest.get('counts')}")
    expected_files = {f"{name}.json" for name in builder.OUTPUT_NAMES if name != "manifest"}
    if set(manifest.get("files", [])) != expected_files:
        errors.append("manifest: generated file inventory is incomplete")

    biggest = payloads.get("biggest_wins", {})
    for group_name in ("overall", "regular_season", "championship_playoffs"):
        entries = biggest.get(group_name, [])
        validate_ranked(entries, "margin", True, errors, f"biggest_wins.{group_name}")
        if len({item.get("matchup_id") for item in entries}) != len(entries):
            errors.append(f"biggest_wins.{group_name}: duplicate matchup")
        for index, game in enumerate(entries):
            validate_game(game, franchise_ids, errors, f"biggest_wins.{group_name}[{index}]")
            if not game.get("winner") or not game.get("loser"):
                errors.append(f"biggest_wins.{group_name}[{index}]: resolved winner and loser required")
    if any(game.get("game_type") != "championship_playoff" for game in biggest.get("championship_playoffs", [])):
        errors.append("biggest_wins.championship_playoffs: unclassified postseason game")
    if len(biggest.get("overall", [])) != 25 or len(biggest.get("regular_season", [])) != 10:
        errors.append("biggest_wins: expected Top 25 overall and Top 10 regular-season rankings")
    if any(game.get("playoff_round") != "Championship" for game in biggest.get("championships", [])):
        errors.append("biggest_wins.championships: non-championship game")

    closest = payloads.get("closest_games", {})
    for group_name in ("overall", "championship_playoffs"):
        entries = closest.get(group_name, [])
        validate_ranked(entries, "margin", False, errors, f"closest_games.{group_name}")
        if any(item.get("tie") for item in entries):
            errors.append(f"closest_games.{group_name}: ties must be excluded")
    if len(closest.get("overall", [])) != 25:
        errors.append("closest_games: expected Top 25 decided-game ranking")
    if any(not item.get("tie") for item in closest.get("ties", [])):
        errors.append("closest_games.ties: decided game was published as a tie")
    if any(game.get("playoff_round") != "Championship" for game in closest.get("championships", [])):
        errors.append("closest_games.championships: non-championship game")

    scores = payloads.get("weekly_scores", {})
    for group, field, reverse in (
        ("highest_team_scores", "score", True),
        ("lowest_team_scores", "score", False),
        ("highest_combined_matchups", "combined_score", True),
        ("lowest_combined_matchups", "combined_score", False),
        ("highest_losing_scores", "score", True),
        ("lowest_winning_scores", "score", False),
    ):
        entries = scores.get(group, [])
        validate_ranked(entries, field, reverse, errors, f"weekly_scores.{group}")
        if len(entries) != 25:
            errors.append(f"weekly_scores.{group}: expected Top 25")
    if any(item.get("result") != "L" for item in scores.get("highest_losing_scores", [])):
        errors.append("weekly_scores.highest_losing_scores: non-loss included")
    if any(item.get("result") != "W" for item in scores.get("lowest_winning_scores", [])):
        errors.append("weekly_scores.lowest_winning_scores: non-win included")
    if {item.get("season") for item in scores.get("by_season", [])} != set(builder.WEEKLY_YEARS):
        errors.append("weekly_scores.by_season: not every verified season is represented")

    h2h = payloads.get("head_to_head", {})
    pair_ids = set()
    h2h_matchup_ids: list[str] = []
    regular_outcomes: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for pair in h2h.get("pairs", []):
        if pair.get("pair_id") in pair_ids:
            errors.append(f"head_to_head: duplicate pair {pair.get('pair_id')}")
        pair_ids.add(pair.get("pair_id"))
        meetings = pair.get("all_meetings", [])
        if pair.get("meetings") != len(meetings) or pair.get("meetings") != pair.get("wins_a", 0) + pair.get("wins_b", 0) + pair.get("ties", 0):
            errors.append(f"head_to_head: totals disagree for {pair.get('pair_id')}")
        for side in ("franchise_a", "franchise_b"):
            if pair.get(side, {}).get("franchise_id") not in franchise_ids:
                errors.append(f"head_to_head: invalid {side} reference")
        a_id = pair.get("franchise_a", {}).get("franchise_id")
        b_id = pair.get("franchise_b", {}).get("franchise_id")
        computed_wins = {a_id: 0, b_id: 0}
        computed_ties = 0
        computed_points = {a_id: 0.0, b_id: 0.0}
        for index, game in enumerate(meetings):
            validate_game(game, franchise_ids, errors, f"head_to_head.{pair.get('pair_id')}[{index}]")
            h2h_matchup_ids.append(game.get("matchup_id"))
            for side in (game["team_a"], game["team_b"]):
                computed_points[side["franchise_id"]] += side["score"]
            if game.get("tie"):
                computed_ties += 1
            else:
                computed_wins[game["winner"]["franchise_id"]] += 1
            if game.get("game_type") == "regular_season":
                for side in (game["team_a"], game["team_b"]):
                    bucket = regular_outcomes[side["franchise_id"]]
                    if game.get("tie"):
                        bucket[2] += 1
                    elif game["winner"]["franchise_id"] == side["franchise_id"]:
                        bucket[0] += 1
                    else:
                        bucket[1] += 1
        if (computed_wins.get(a_id), computed_wins.get(b_id), computed_ties) != (pair.get("wins_a"), pair.get("wins_b"), pair.get("ties")):
            errors.append(f"head_to_head: win reconciliation failed for {pair.get('pair_id')}")
        if round(computed_points.get(a_id, 0), 2) != pair.get("points_a") or round(computed_points.get(b_id, 0), 2) != pair.get("points_b"):
            errors.append(f"head_to_head: point reconciliation failed for {pair.get('pair_id')}")
        if pair.get("rivalry_title") is not None or pair.get("editorial_history") is not None:
            errors.append(f"head_to_head: unapproved rivalry editorial data for {pair.get('pair_id')}")

    if len(h2h_matchup_ids) != 446 or len(set(h2h_matchup_ids)) != 446:
        errors.append("head_to_head: all 446 resolved matchups must appear exactly once across pair histories")

    playoffs = payloads.get("playoffs", {})
    playoff_outcomes: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    for index, game in enumerate(playoffs.get("games", [])):
        validate_game(game, franchise_ids, errors, f"playoffs.games[{index}]")
        if game.get("game_type") != "championship_playoff" or not game.get("playoff_round"):
            errors.append(f"playoffs.games[{index}]: game is not independently classified")
        for side in (game["team_a"], game["team_b"]):
            bucket = playoff_outcomes[side["franchise_id"]]
            bucket[0 if game["winner"]["franchise_id"] == side["franchise_id"] else 1] += 1
    if len({game.get("matchup_id") for game in playoffs.get("games", [])}) != len(playoffs.get("games", [])):
        errors.append("playoffs: duplicate classified matchup")
    for row in playoffs.get("franchises", []):
        expected_record = playoff_outcomes[row["franchise_id"]]
        if expected_record != [row["playoff_wins"], row["playoff_losses"]]:
            errors.append(f"playoffs: W-L reconciliation failed for {row['franchise_id']}")

    career = payloads.get("franchise_career", {})
    career_sort_keys = [
        (
            -(row["season_history"]["win_percentage"] or 0),
            -row["season_history"]["wins"],
            -row["season_history"]["points_for"],
            row["franchise_id"],
        )
        for row in career.get("franchises", [])
    ]
    if career_sort_keys != sorted(career_sort_keys):
        errors.append("franchise_career: default ranking order is invalid")
    for summary in career.get("franchises", []):
        if summary.get("franchise_id") not in franchise_ids:
            errors.append("franchise_career: invalid franchise reference")
        if any(item.get("season") not in builder.SEASON_YEARS for item in summary.get("season_history", {}).get("seasons", [])):
            errors.append(f"franchise_career: invalid season for {summary.get('franchise_id')}")
        season_record = summary.get("season_history", {})
        if regular_outcomes[summary["franchise_id"]] != [season_record.get("wins"), season_record.get("losses"), season_record.get("ties")]:
            errors.append(f"franchise_career: regular-season W-L-T mismatch for {summary['franchise_id']}")
        if len({row["opponent"]["franchise_id"] for row in summary.get("head_to_head", [])}) != len(summary.get("head_to_head", [])):
            errors.append(f"franchise_career: duplicate opponent for {summary['franchise_id']}")

    championships = payloads.get("championships", {})
    canonical_champions = yaml.safe_load((ROOT / "_data" / "champions.yml").read_text(encoding="utf-8"))["champions"]
    generated_finals = championships.get("championships", [])
    if len(generated_finals) != len(canonical_champions):
        errors.append("championships: canonical final count mismatch")
    title_counts: defaultdict[str, int] = defaultdict(int)
    for final in generated_finals:
        title_counts[final["champion"]["franchise_id"]] += 1
        if round(final["champion_score"] - final["runner_up_score"], 2) != final.get("margin"):
            errors.append(f"championships: invalid margin for {final.get('season')}")
    career_titles = {row["franchise_id"]: row["season_history"]["championships"] for row in career.get("franchises", [])}
    for franchise_id, count in career_titles.items():
        if count != title_counts[franchise_id]:
            errors.append(f"championships: title reconciliation failed for {franchise_id}")
    if [row["season"] for row in generated_finals] != sorted((row["season"] for row in generated_finals), reverse=True):
        errors.append("championships: finals are not in descending season order")
    for key, primary, secondary in (
        ("most_championships", "championships", "appearances"),
        ("most_appearances", "appearances", "championships"),
        ("best_championship_record", "win_percentage", "appearances"),
        ("most_runner_up_finishes", "runner_up_finishes", "appearances"),
    ):
        rows = championships.get("leaderboards", {}).get(key, [])
        ordering = [(-row[primary], -row[secondary], row["franchise_id"]) for row in rows]
        if ordering != sorted(ordering):
            errors.append(f"championships.{key}: invalid ordering")

    streaks = payloads.get("streaks", {})
    for key in (
        "single_season_wins", "single_season_losses", "single_season_unbeaten",
        "cross_season_wins", "cross_season_losses", "cross_season_unbeaten",
        "playoff_wins", "playoff_losses", "championship_appearance_streaks",
    ):
        rows = streaks.get(key, [])
        if [(-row["games"], row["franchise_id"]) for row in rows] != sorted(
            (-row["games"], row["franchise_id"]) for row in rows
        ):
            errors.append(f"streaks.{key}: invalid ordering")
        if [row.get("rank") for row in rows] != list(range(1, len(rows) + 1)):
            errors.append(f"streaks.{key}: ranks must be deterministic ordinals")

    comparisons = payloads.get("season_leaders", {}).get("comparisons", {})
    for key, field, reverse in (
        ("best_single_season_records", "win_percentage", True),
        ("highest_single_season_pf", "points_for", True),
        ("lowest_single_season_pa", "points_against", False),
        ("best_point_differential", "point_differential", True),
        ("most_dominant_champions", "margin", True),
        ("closest_championships", "margin", False),
        ("highest_scoring_championships", "combined_score", True),
        ("lowest_scoring_championships", "combined_score", False),
    ):
        values = [row[field] for row in comparisons.get(key, [])]
        if values != sorted(values, reverse=reverse):
            errors.append(f"season_leaders.{key}: invalid ordering")

    thresholds = payloads.get("record_thresholds", {}).get("thresholds", {})
    expected_thresholds = {
        "highest_weekly_score": scores["highest_team_scores"][0]["score"],
        "tenth_highest_weekly_score": scores["highest_team_scores"][9]["score"],
        "twenty_fifth_highest_weekly_score": scores["highest_team_scores"][24]["score"],
        "largest_margin": biggest["overall"][0]["margin"],
        "tenth_largest_margin": biggest["overall"][9]["margin"],
        "highest_combined_matchup_score": scores["highest_combined_matchups"][0]["combined_score"],
        "lowest_combined_matchup_score": scores["lowest_combined_matchups"][0]["combined_score"],
        "highest_losing_score": scores["highest_losing_scores"][0]["score"],
        "lowest_winning_score": scores["lowest_winning_scores"][0]["score"],
    }
    if thresholds != expected_thresholds:
        errors.append("record_thresholds: archive benchmarks do not match ranked records")
    threshold_rows = payloads.get("record_thresholds", {}).get("franchises", [])
    if len(threshold_rows) != len({row["franchise_id"] for row in threshold_rows}):
        errors.append("record_thresholds: duplicate franchise threshold")

    for name, payload in payloads.items():
        validate_franchise_references(payload, franchise_ids, errors, name)

    events_path = ROOT / "_data" / "generated" / "history" / "events.json"
    if events_path.exists():
        errors.append("history/events.json: exact matchup dates are unavailable; event dates must not be inferred from weeks")

    if errors:
        raise SystemExit("Historical metrics validation failed:\n- " + "\n- ".join(errors))
    print(
        f"Validated {len(payloads)} historical metric files, {len(h2h.get('pairs', []))} head-to-head pairs, "
        f"{len(playoffs.get('games', []))} classified playoff games, and separate coverage scopes"
    )


if __name__ == "__main__":
    main()
