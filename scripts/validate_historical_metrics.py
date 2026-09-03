#!/usr/bin/env python3
"""Validate deterministic historical metrics, coverage, and references."""

from __future__ import annotations

import json
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
    if game.get("season") == 2021:
        errors.append(f"{location}: 2021 weekly contamination")
    if game.get("team_a") and game["team_a"].get("franchise_id") not in franchise_ids:
        errors.append(f"{location}: invalid team_a franchise")
    if game.get("team_b") and game["team_b"].get("franchise_id") not in franchise_ids:
        errors.append(f"{location}: invalid team_b franchise")
    if game.get("winner") and game["winner"].get("franchise_id") not in franchise_ids:
        errors.append(f"{location}: invalid winner franchise")
    if game.get("winner_score") is not None:
        expected = round(game["winner_score"] - game["loser_score"], 2)
        if expected != game.get("margin") or game["winner_score"] <= game["loser_score"]:
            errors.append(f"{location}: invalid winner/loser margin")


def ordered(entries: list[dict[str, Any]], field: str, reverse: bool) -> bool:
    values = [item[field] for item in entries]
    return values == sorted(values, reverse=reverse)


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
    validate_coverage(manifest.get("weekly_coverage"), builder.WEEKLY_LABEL, 2022, errors, "manifest weekly")
    if manifest.get("bench_records_enabled") is not False:
        errors.append("manifest: bench records must be disabled")

    for name in ("head_to_head", "biggest_wins", "closest_games", "weekly_scores", "streaks", "playoffs", "record_thresholds"):
        if name in payloads:
            validate_coverage(payloads[name].get("coverage"), builder.WEEKLY_LABEL, 2022, errors, name)

    biggest = payloads.get("biggest_wins", {})
    for group_name in ("overall", "regular_season", "championship_playoffs"):
        entries = biggest.get(group_name, [])
        if not ordered(entries, "margin", True):
            errors.append(f"biggest_wins.{group_name}: invalid ordering")
        if len({item.get("matchup_id") for item in entries}) != len(entries):
            errors.append(f"biggest_wins.{group_name}: duplicate matchup")
        for index, game in enumerate(entries):
            validate_game(game, franchise_ids, errors, f"biggest_wins.{group_name}[{index}]")
            if not game.get("winner") or not game.get("loser"):
                errors.append(f"biggest_wins.{group_name}[{index}]: resolved winner and loser required")
    if any(game.get("game_type") != "championship_playoff" for game in biggest.get("championship_playoffs", [])):
        errors.append("biggest_wins.championship_playoffs: unclassified postseason game")

    closest = payloads.get("closest_games", {})
    for group_name in ("overall", "championship_playoffs"):
        entries = closest.get(group_name, [])
        if not ordered(entries, "margin", False):
            errors.append(f"closest_games.{group_name}: invalid ordering")
        if any(item.get("tie") for item in entries):
            errors.append(f"closest_games.{group_name}: ties must be excluded")

    scores = payloads.get("weekly_scores", {})
    if not ordered(scores.get("highest_team_scores", []), "score", True):
        errors.append("weekly_scores: highest scores are not descending")
    if not ordered(scores.get("lowest_team_scores", []), "score", False):
        errors.append("weekly_scores: lowest scores are not ascending")

    h2h = payloads.get("head_to_head", {})
    pair_ids = set()
    for pair in h2h.get("pairs", []):
        if pair.get("pair_id") in pair_ids:
            errors.append(f"head_to_head: duplicate pair {pair.get('pair_id')}")
        pair_ids.add(pair.get("pair_id"))
        if pair.get("meetings") != pair.get("wins_a", 0) + pair.get("wins_b", 0) + pair.get("ties", 0):
            errors.append(f"head_to_head: totals disagree for {pair.get('pair_id')}")
        for side in ("franchise_a", "franchise_b"):
            if pair.get(side, {}).get("franchise_id") not in franchise_ids:
                errors.append(f"head_to_head: invalid {side} reference")
        for index, game in enumerate(pair.get("recent_meetings", [])):
            validate_game(game, franchise_ids, errors, f"head_to_head.{pair.get('pair_id')}[{index}]")

    playoffs = payloads.get("playoffs", {})
    for index, game in enumerate(playoffs.get("games", [])):
        validate_game(game, franchise_ids, errors, f"playoffs.games[{index}]")
        if game.get("game_type") != "championship_playoff" or not game.get("playoff_round"):
            errors.append(f"playoffs.games[{index}]: game is not independently classified")

    summaries = payloads.get("franchise_summaries", {})
    validate_coverage(summaries.get("season_level_coverage"), builder.SEASON_LABEL, 2021, errors, "franchise summaries season")
    validate_coverage(summaries.get("weekly_coverage"), builder.WEEKLY_LABEL, 2022, errors, "franchise summaries weekly")
    for summary in summaries.get("franchises", []):
        if summary.get("franchise_id") not in franchise_ids:
            errors.append("franchise_summaries: invalid franchise reference")
        if any(item.get("season") not in builder.SEASON_YEARS for item in summary.get("season_history", {}).get("seasons", [])):
            errors.append(f"franchise_summaries: invalid season for {summary.get('franchise_id')}")

    if errors:
        raise SystemExit("Historical metrics validation failed:\n- " + "\n- ".join(errors))
    print(
        f"Validated {len(payloads)} historical metric files, {len(h2h.get('pairs', []))} head-to-head pairs, "
        f"{len(playoffs.get('games', []))} classified playoff games, and separate coverage scopes"
    )


if __name__ == "__main__":
    main()
