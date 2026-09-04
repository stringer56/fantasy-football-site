"""Build deterministic, provenance-aware historical season recaps."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "_data"
OUTPUT_PATH = DATA_DIR / "generated" / "recaps.json"
SOURCE_FILES = [
    "_data/seasons.yml",
    "_data/playoffs.yml",
    "_data/champions.yml",
    "_data/franchises.yml",
    "_data/generated/record_book.json",
    "_data/editorial/recaps.yml",
]
ROUND_ORDER = {
    "Quarterfinal": 1,
    "Semifinal": 2,
    "Fifth Place Game": 3,
    "Championship": 4,
    "Third Place Game": 4,
}


def load_yaml(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"{relative_path}: expected a schema_version 1 mapping")
    return value


def load_json(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"{relative_path}: expected a schema_version 1 object")
    return value


def format_points(value: object) -> str:
    return f"{float(value):,.2f}"


def format_record(row: dict[str, Any]) -> str:
    return f"{row['wins']}–{row['losses']}–{row['ties']}"


def ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def join_names(names: Iterable[str]) -> str:
    values = list(names)
    if len(values) < 2:
        return "" if not values else values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return ", ".join(values[:-1]) + f", and {values[-1]}"


def win_pct(row: dict[str, Any]) -> float | None:
    games = row.get("wins", 0) + row.get("losses", 0) + row.get("ties", 0)
    return (row["wins"] + row["ties"] * 0.5) / games if games else None


def standings_complete(season: dict[str, Any], fields: Iterable[str]) -> bool:
    rows = season.get("standings") or []
    return len(rows) == season.get("team_count") and all(
        all(row.get(field) is not None for field in fields) for row in rows
    )


def tied_extreme(
    rows: list[dict[str, Any]], field: str, *, highest: bool = True
) -> list[dict[str, Any]]:
    if not rows or any(row.get(field) is None for row in rows):
        return []
    target = (max if highest else min)(row[field] for row in rows)
    return [row for row in rows if row[field] == target]


def best_record_rows(season: dict[str, Any]) -> list[dict[str, Any]]:
    rows = season.get("standings") or []
    if not standings_complete(season, ("wins", "losses", "ties")):
        return []
    percentages = [(row, win_pct(row)) for row in rows]
    target = max(value for _, value in percentages if value is not None)
    return [row for row, value in percentages if value == target]


def points_rank(rows: list[dict[str, Any]], row: dict[str, Any]) -> int | None:
    if any(item.get("points_for") is None for item in rows) or row.get("points_for") is None:
        return None
    return 1 + sum(item["points_for"] > row["points_for"] for item in rows)


def identity_index(franchises: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for franchise in franchises:
        result[franchise["franchise_id"]] = {
            "display_name": franchise["name"],
            "path": f"/{'retired' if franchise['status'] == 'retired' else 'teams'}/{franchise['slug']}/",
            "identity_image": (franchise.get("branding") or {}).get("identity_image"),
            "identity_alt": (franchise.get("branding") or {}).get("identity_alt"),
        }
    return result


def load_week_archive(season: dict[str, Any]) -> dict[str, Any] | None:
    relative_path = season.get("weeks_data_path")
    if not relative_path:
        return None
    payload = load_json(str(relative_path))
    coverage = payload.get("coverage") or {}
    expected = list(range(1, 17))
    if payload.get("season") != season["year"] or coverage.get("complete") is not True:
        raise ValueError(f"{relative_path}: complete season coverage is required")
    if coverage.get("recovered_weeks") != expected:
        raise ValueError(f"{relative_path}: expected verified weeks 1-16")
    return payload


def derive_weekly_archive(
    season: dict[str, Any], playoff: dict[str, Any], identities: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    payload = load_week_archive(season)
    if payload is None:
        return None

    playoff_games: dict[tuple[int, frozenset[str]], dict[str, Any]] = {}
    for game in playoff.get("games") or []:
        if game.get("week") is None:
            continue
        playoff_games[(game["week"], frozenset((game["team_one_franchise_id"], game["team_two_franchise_id"])))] = game

    team_games: dict[str, list[dict[str, Any]]] = {row["franchise_id"]: [] for row in season["standings"]}
    week_summaries: list[dict[str, Any]] = []
    all_games: list[dict[str, Any]] = []
    all_scores: list[dict[str, Any]] = []

    def side(raw: dict[str, Any]) -> dict[str, Any]:
        identity = identities[raw["franchise_id"]]
        return {
            "franchise_id": raw["franchise_id"],
            "name": raw["historical_team_name"],
            "score": float(raw["score"]),
            "path": identity["path"],
        }

    for week in payload["weeks"]:
        normalized: list[dict[str, Any]] = []
        for raw in week["matchups"]:
            one = side(raw["team_a"])
            two = side(raw["team_b"])
            classification = playoff_games.get(
                (week["week"], frozenset((one["franchise_id"], two["franchise_id"])))
            )
            game = {
                "matchup_id": raw["matchup_id"],
                "week": week["week"],
                "team_one": one,
                "team_two": two,
                "winner_franchise_id": raw.get("winner_franchise_id"),
                "winner_name": raw.get("winner_historical_name"),
                "tie": raw.get("tie") is True,
                "margin": float(raw["margin"]),
                "combined_score": round(one["score"] + two["score"], 2),
                "playoff_round": classification.get("round") if classification else None,
                "bracket_type": classification.get("bracket_type") if classification else None,
                "notable_labels": [],
            }
            normalized.append(game)
            all_games.append(game)
            all_scores.extend(
                ({"week": week["week"], **one}, {"week": week["week"], **two})
            )
            for current, opponent in ((one, two), (two, one)):
                result = "T" if game["tie"] else (
                    "W" if game["winner_franchise_id"] == current["franchise_id"] else "L"
                )
                team_games[current["franchise_id"]].append({
                    "week": week["week"],
                    "score": current["score"],
                    "opponent_franchise_id": opponent["franchise_id"],
                    "opponent_name": opponent["name"],
                    "opponent_score": opponent["score"],
                    "margin": game["margin"],
                    "result": result,
                    "playoff_round": game["playoff_round"],
                })

        highest_score = max(max(game["team_one"]["score"], game["team_two"]["score"]) for game in normalized)
        closest_margin = min(game["margin"] for game in normalized)
        biggest_margin = max(game["margin"] for game in normalized)
        for game in normalized:
            if highest_score in (game["team_one"]["score"], game["team_two"]["score"]):
                game["notable_labels"].append("Highest score of the week")
            if game["margin"] == closest_margin:
                game["notable_labels"].append("Closest matchup")
            if game["margin"] == biggest_margin:
                game["notable_labels"].append("Biggest margin")
            if game["playoff_round"]:
                game["notable_labels"].append(game["playoff_round"])
        week_summaries.append({"week": week["week"], "matchups": normalized})

    def score_label(item: dict[str, Any]) -> str:
        return f"{item['name']} · {format_points(item['score'])} · Week {item['week']}"

    highest_score = max(all_scores, key=lambda item: (item["score"], -item["week"]))
    lowest_score = min(all_scores, key=lambda item: (item["score"], item["week"]))
    biggest_game = max(all_games, key=lambda item: (item["margin"], -item["week"]))
    closest_game = min(all_games, key=lambda item: (item["margin"], item["week"]))
    combined_game = max(all_games, key=lambda item: (item["combined_score"], -item["week"]))

    team_metrics: dict[str, dict[str, Any]] = {}
    league_streaks: list[dict[str, Any]] = []
    for franchise_id, games in team_games.items():
        high = max(games, key=lambda item: (item["score"], -item["week"]))
        wins = [item for item in games if item["result"] == "W"]
        closest = min(games, key=lambda item: (item["margin"], item["week"]))
        biggest = max(wins, key=lambda item: (item["margin"], -item["week"])) if wins else None
        longest_win = longest_loss = current_win = current_loss = 0
        for game in sorted((item for item in games if item["week"] <= 13), key=lambda item: item["week"]):
            if game["result"] == "W":
                current_win += 1
                current_loss = 0
            elif game["result"] == "L":
                current_loss += 1
                current_win = 0
            else:
                current_win = current_loss = 0
            longest_win = max(longest_win, current_win)
            longest_loss = max(longest_loss, current_loss)
        name = next(row["team_name"] for row in season["standings"] if row["franchise_id"] == franchise_id)
        league_streaks.append({"franchise_id": franchise_id, "name": name, "wins": longest_win})
        team_metrics[franchise_id] = {
            "highest_score": {"week": high["week"], "score": high["score"]},
            "biggest_win": ({
                "week": biggest["week"], "opponent_name": biggest["opponent_name"], "margin": biggest["margin"]
            } if biggest else None),
            "closest_game": {
                "week": closest["week"], "opponent_name": closest["opponent_name"],
                "margin": closest["margin"], "result": closest["result"],
            },
            "longest_regular_season_win_streak": longest_win,
            "longest_regular_season_loss_streak": longest_loss,
        }

    best_streak = max(item["wins"] for item in league_streaks)
    streak_holders = [item for item in league_streaks if item["wins"] == best_streak]

    def matchup_label(game: dict[str, Any], value: float) -> str:
        return (
            f"{game['team_one']['name']} vs. {game['team_two']['name']} · "
            f"{format_points(value)} · Week {game['week']}"
        )

    return {
        "coverage_label": "Verified Weeks 1–16",
        "week_count": len(week_summaries),
        "matchup_count": len(all_games),
        "weeks": week_summaries,
        "team_metrics": team_metrics,
        "season_metrics": {
            "highest_weekly_score": {**highest_score, "display": score_label(highest_score)},
            "lowest_weekly_score": {**lowest_score, "display": score_label(lowest_score)},
            "biggest_victory": {**biggest_game, "display": matchup_label(biggest_game, biggest_game["margin"])},
            "closest_game": {**closest_game, "display": matchup_label(closest_game, closest_game["margin"])},
            "highest_combined_score": {**combined_game, "display": matchup_label(combined_game, combined_game["combined_score"])},
            "longest_winning_streak": {
                "games": best_streak,
                "holders": streak_holders,
                "display": f"{join_names(item['name'] for item in streak_holders)} · {best_streak} games",
            },
        },
    }


def generated_timestamp(champions: list[dict[str, Any]]) -> str:
    dates = sorted(str(item["verified_on"]) for item in champions if item.get("verified_on"))
    if not dates:
        raise ValueError("championship provenance must include verified_on")
    return f"{dates[-1]}T00:00:00Z"


def override_for(
    editorial: dict[str, Any], kind: str, *, season: int, franchise_id: str | None = None,
    historical_team_name: str | None = None, game_id: str | None = None
) -> dict[str, Any] | None:
    for item in editorial.get(kind) or []:
        if item.get("status") != "approved" or not str(item.get("text") or "").strip():
            continue
        if item.get("season") != season:
            continue
        if kind == "team_recaps":
            if item.get("franchise_id") != franchise_id:
                continue
            if franchise_id is None and item.get("historical_team_name") != historical_team_name:
                continue
        if kind == "playoff_recaps" and item.get("game_id") != game_id:
            continue
        return item
    return None


def apply_override(entry: dict[str, Any], paragraphs: list[str], override: dict[str, Any] | None) -> None:
    generated_text = "\n\n".join(paragraphs)
    entry["generated_text"] = generated_text
    entry["generated_paragraphs"] = paragraphs
    if override:
        text = str(override["text"]).strip()
        entry["text"] = text
        entry["paragraphs"] = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        entry["content_source"] = "editorial_override"
        if "_data/editorial/recaps.yml" not in entry["source_files"]:
            entry["source_files"].append("_data/editorial/recaps.yml")
    else:
        entry["text"] = generated_text
        entry["paragraphs"] = paragraphs
        entry["content_source"] = "deterministic_generated"


def provenance(
    season: int,
    generated_at: str,
    coverage_status: str,
    facts_used: list[dict[str, Any]],
    warnings: list[str] | None = None,
    source_files: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "season": season,
        "source_files": source_files or SOURCE_FILES[:4],
        "generated_at": generated_at,
        "coverage_status": coverage_status,
        "facts_used": facts_used,
        "warnings": warnings or [],
        "provenance_label": "Generated from verified league results.",
    }


def participant_key(franchise_id: str | None, display_name: str) -> str:
    return franchise_id or f"historical:{display_name.casefold()}"


def playoff_participants(playoff: dict[str, Any]) -> set[str]:
    participants: set[str] = set()
    for game in playoff.get("games") or []:
        for side in ("team_one", "team_two"):
            participants.add(participant_key(game.get(f"{side}_franchise_id"), game[f"{side}_display_name"]))
    return participants


def row_in_game(row: dict[str, Any], game: dict[str, Any], side: str) -> bool:
    franchise_id = row.get("franchise_id")
    side_id = game.get(f"{side}_franchise_id")
    if franchise_id is not None:
        return franchise_id == side_id
    return side_id is None and row["team_name"].casefold() == game[f"{side}_display_name"].casefold()


def game_side_for_row(row: dict[str, Any], game: dict[str, Any]) -> str | None:
    for side in ("team_one", "team_two"):
        if row_in_game(row, game, side):
            return side
    return None


def playoff_status(row: dict[str, Any], playoff: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    games = [game for game in playoff.get("games") or [] if game_side_for_row(row, game)]
    name = row["team_name"]
    finish = row.get("playoff_finish")
    if finish is not None:
        labels = {1: "won the Brew Crew Cup", 2: "finished as the Brew Crew Cup runner-up",
                  3: "won the third-place game", 4: "finished fourth",
                  5: "won the fifth-place game", 6: "finished sixth"}
        return (
            f"{name} reached the postseason and {labels[finish]}.",
            {"fact_type": "playoff_status", "status": f"finished_{finish}",
             "playoff_finish": finish, "games": [game["game_id"] for game in games]},
        )
    if not games:
        return (
            f"The structured playoff bracket does not list {name} among the verified postseason participants.",
            {"fact_type": "playoff_status", "status": "not_listed", "games": []},
        )
    games.sort(key=lambda game: (ROUND_ORDER.get(game["round"], 0), game["order"]))
    loss = next((game for game in reversed(games) if game.get("winner_franchise_id") != row.get("franchise_id")
                 or (row.get("franchise_id") is None and game.get("winner_display_name", "").casefold() != name.casefold())), None)
    if loss is None:
        return (
            f"{name} reached the postseason and won the Brew Crew Cup.",
            {"fact_type": "playoff_status", "status": "champion", "games": [game["game_id"] for game in games]},
        )
    if loss["round"] == "Championship":
        return (
            f"{name} reached the championship and finished as the Brew Crew Cup runner-up.",
            {"fact_type": "playoff_status", "status": "runner_up", "games": [game["game_id"] for game in games]},
        )
    return (
        f"{name} reached the {loss['round'].lower()} before {loss['winner_display_name']} advanced.",
        {
            "fact_type": "playoff_status",
            "status": f"eliminated_{loss['round'].casefold()}",
            "elimination_game_id": loss["game_id"],
            "games": [game["game_id"] for game in games],
        },
    )


def record_reference(records: dict[str, Any], year: int) -> tuple[str | None, dict[str, Any] | None]:
    priority = ("best_win_pct", "highest_points_for", "most_wins")
    candidates: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for group in (records.get("records") or {}).values():
        provenance_data = group.get("provenance") or {}
        for record in group.get("entries") or []:
            for holder in record.get("holders") or []:
                if holder.get("year") == year and holder.get("franchise_id"):
                    candidates[record["record_id"]] = (record, provenance_data)
                    break
    for record_id in priority:
        if record_id not in candidates:
            continue
        record, source = candidates[record_id]
        holder = next(item for item in record["holders"] if item["year"] == year and item.get("franchise_id"))
        period = source.get("source_years") or records.get("coverage", {}).get("source_years") or []
        period_label = f"{min(period)}–{max(period)}" if period else "verified"
        value = holder["value"]
        if record_id == "best_win_pct":
            sentence = (
                f"The record book lists {holder['historical_team_name']}'s {float(value):.3f} winning percentage "
                f"as the best verified mark in the {period_label} archive."
            )
        elif record_id == "highest_points_for":
            sentence = (
                f"The record book lists {holder['historical_team_name']}'s {format_points(value)} points for "
                f"as the highest verified total in the {period_label} archive."
            )
            if source.get("coverage_status") == "partial":
                sentence += " That archive category remains partial because of the documented 2024 PF/PA source conflict."
        else:
            sentence = (
                f"The record book lists {holder['historical_team_name']}'s {int(value)} wins "
                f"as the highest verified total in the {period_label} archive."
            )
        return sentence, {
            "fact_type": "archive_record",
            "record_id": record_id,
            "holder_franchise_id": holder["franchise_id"],
            "holder_name": holder["historical_team_name"],
            "value": value,
            "coverage_status": source.get("coverage_status"),
            "source_years": period,
        }
    return None, None


def build_season_recap(
    season: dict[str, Any], champion: dict[str, Any], playoff: dict[str, Any], records: dict[str, Any],
    generated_at: str, editorial: dict[str, Any], weekly: dict[str, Any] | None = None
) -> dict[str, Any]:
    year = season["year"]
    rows = season["standings"]
    best = best_record_rows(season)
    highest_pf = tied_extreme(rows, "points_for") if standings_complete(season, ("points_for",)) else []
    participants = playoff_participants(playoff)
    facts: list[dict[str, Any]] = [
        {
            "fact_type": "championship_result",
            "champion_franchise_id": champion["champion_franchise_id"],
            "champion_name": champion["champion_display_name"],
            "runner_up_franchise_id": champion["runner_up_franchise_id"],
            "runner_up_name": champion["runner_up_display_name"],
            "champion_score": champion["champion_score"],
            "runner_up_score": champion["runner_up_score"],
        },
        {"fact_type": "playoff_field_size", "value": len(participants)},
    ]
    opening = (
        f"The {year} Road to Glory season ended with {champion['champion_display_name']} defeating "
        f"{champion['runner_up_display_name']} {format_points(champion['champion_score'])}–"
        f"{format_points(champion['runner_up_score'])} to win the Brew Crew Cup."
    )
    details: list[str] = []
    if best:
        best_names = join_names(row["team_name"] for row in best)
        details.append(f"{best_names} posted the strongest verified record at {format_record(best[0])}.")
        facts.append({
            "fact_type": "best_record", "team_names": [row["team_name"] for row in best],
            "records": [format_record(row) for row in best],
        })
    if highest_pf:
        pf_names = join_names(row["team_name"] for row in highest_pf)
        details.append(f"{pf_names} led the {season['team_count']}-team field with {format_points(highest_pf[0]['points_for'])} points for.")
        facts.append({
            "fact_type": "highest_points_for", "team_names": [row["team_name"] for row in highest_pf],
            "value": highest_pf[0]["points_for"],
        })
    details.append(f"The verified bracket contains {len(participants)} postseason participants and preserves every advancing team.")
    record_sentence, record_fact = record_reference(records, year)
    if record_sentence and record_fact:
        facts.append(record_fact)
    paragraphs = [opening]
    if weekly:
        paragraphs.append(" ".join(details))
        metrics = weekly["season_metrics"]
        high = metrics["highest_weekly_score"]
        low = metrics["lowest_weekly_score"]
        biggest = metrics["biggest_victory"]
        closest = metrics["closest_game"]
        combined = metrics["highest_combined_score"]
        streak = metrics["longest_winning_streak"]
        paragraphs.append(
            f"Across all 16 verified weeks, {high['name']} recorded the season's highest weekly score at "
            f"{format_points(high['score'])} in Week {high['week']}, while {low['name']} posted the lowest at "
            f"{format_points(low['score'])} in Week {low['week']}. The largest victory margin was "
            f"{format_points(biggest['margin'])} points in Week {biggest['week']}, and the closest game was decided "
            f"by {format_points(closest['margin'])} points in Week {closest['week']}."
        )
        paragraphs.append(
            f"The highest combined score reached {format_points(combined['combined_score'])} in Week "
            f"{combined['week']}. {join_names(item['name'] for item in streak['holders'])} produced the longest "
            f"verified regular-season run at {streak['games']} consecutive wins. The six-team championship field "
            "was seeded from the verified final standings, with Greendale Human Beings and Albany Kneelers earning "
            "the two first-round byes."
        )
        facts.extend([
            {"fact_type": "weekly_archive_coverage", "weeks": weekly["week_count"], "matchups": weekly["matchup_count"]},
            {"fact_type": "highest_weekly_score", "franchise_id": high["franchise_id"], "week": high["week"], "value": high["score"]},
            {"fact_type": "lowest_weekly_score", "franchise_id": low["franchise_id"], "week": low["week"], "value": low["score"]},
            {"fact_type": "biggest_victory", "matchup_id": biggest["matchup_id"], "value": biggest["margin"]},
            {"fact_type": "closest_game", "matchup_id": closest["matchup_id"], "value": closest["margin"]},
            {"fact_type": "highest_combined_score", "matchup_id": combined["matchup_id"], "value": combined["combined_score"]},
        ])
    else:
        paragraphs[0] += " " + " ".join(details)
    if record_sentence:
        paragraphs.append(record_sentence)
    summary = (
        f"{champion['champion_display_name']} won the {year} Brew Crew Cup "
        f"{format_points(champion['champion_score'])}–{format_points(champion['runner_up_score'])} over "
        f"{champion['runner_up_display_name']}."
    )
    best_display = join_names(row["team_name"] for row in best)
    if best:
        best_display += f" · {format_record(best[0])}"
    entry = {
        "recap_id": f"season-{year}",
        **provenance(year, generated_at, "complete", facts, source_files=SOURCE_FILES[:5]),
        "headline": f"{champion['champion_display_name']} Takes the Cup",
        "summary": summary,
        "best_record_display": best_display or None,
        "weekly_archive": weekly,
    }
    apply_override(entry, paragraphs, override_for(editorial, "season_recaps", season=year))
    return entry


def build_by_the_numbers(
    season: dict[str, Any], champion: dict[str, Any], generated_at: str,
    weekly: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    year = season["year"]
    rows = season["standings"]
    best = best_record_rows(season)
    highest_pf = tied_extreme(rows, "points_for")
    lowest_pf = tied_extreme(rows, "points_for", highest=False)
    most_wins = tied_extreme(rows, "wins")
    fewest_wins = tied_extreme(rows, "wins", highest=False)
    point_warnings = ["2024_pf_pa_source_conflict"] if year == 2024 else []
    point_coverage = "partial" if point_warnings else "complete"

    def card(stat_id: str, label: str, display_value: str, facts: list[dict[str, Any]], *,
             coverage: str = "complete", warnings: list[str] | None = None) -> dict[str, Any]:
        return {
            "stat_id": stat_id,
            "label": label,
            "display_value": display_value,
            **provenance(year, generated_at, coverage, facts, warnings, SOURCE_FILES[:3]),
        }

    cards = [
        card("champion", "Champion", champion["champion_display_name"], [{"fact_type": "champion", "franchise_id": champion["champion_franchise_id"]}]),
        card("runner_up", "Runner-Up", champion["runner_up_display_name"], [{"fact_type": "runner_up", "franchise_id": champion["runner_up_franchise_id"]}]),
        card("most_wins", "Most Wins", f"{join_names(row['team_name'] for row in most_wins)} · {most_wins[0]['wins']}", [{"fact_type": "most_wins", "team_names": [row["team_name"] for row in most_wins], "value": most_wins[0]["wins"]}]),
        card("fewest_wins", "Fewest Wins", f"{join_names(row['team_name'] for row in fewest_wins)} · {fewest_wins[0]['wins']}", [{"fact_type": "fewest_wins", "team_names": [row["team_name"] for row in fewest_wins], "value": fewest_wins[0]["wins"]}]),
        card("championship_score", "Championship Final", f"{format_points(champion['champion_score'])}–{format_points(champion['runner_up_score'])}", [{"fact_type": "championship_score", "winner": champion["champion_score"], "runner_up": champion["runner_up_score"]}]),
        card("team_count", "Teams", str(season["team_count"]), [{"fact_type": "team_count", "value": season["team_count"]}]),
    ]
    if best:
        cards.insert(2, card("best_record", "Best Record", f"{join_names(row['team_name'] for row in best)} · {format_record(best[0])}", [{"fact_type": "best_record", "team_names": [row["team_name"] for row in best], "record": format_record(best[0])}]))
    point_cards = []
    if highest_pf:
        point_cards.append(card("highest_pf", "Highest PF", f"{join_names(row['team_name'] for row in highest_pf)} · {format_points(highest_pf[0]['points_for'])}", [{"fact_type": "highest_points_for", "team_names": [row["team_name"] for row in highest_pf], "value": highest_pf[0]["points_for"]}], coverage=point_coverage, warnings=point_warnings))
    if lowest_pf:
        point_cards.append(card("lowest_pf", "Lowest PF", f"{join_names(row['team_name'] for row in lowest_pf)} · {format_points(lowest_pf[0]['points_for'])}", [{"fact_type": "lowest_points_for", "team_names": [row["team_name"] for row in lowest_pf], "value": lowest_pf[0]["points_for"]}], coverage=point_coverage, warnings=point_warnings))
    insertion = 3 if best else 2
    cards[insertion:insertion] = point_cards
    if weekly:
        metrics = weekly["season_metrics"]
        weekly_source = [str(season["weeks_data_path"])]

        def weekly_card(stat_id: str, label: str, display: str, fact: dict[str, Any]) -> dict[str, Any]:
            item = card(stat_id, label, display, [fact])
            item["source_files"] = weekly_source
            return item

        cards.extend([
            weekly_card("highest_weekly_score", "Highest Weekly Score", metrics["highest_weekly_score"]["display"], {"fact_type": "highest_weekly_score", "value": metrics["highest_weekly_score"]["score"]}),
            weekly_card("lowest_weekly_score", "Lowest Weekly Score", metrics["lowest_weekly_score"]["display"], {"fact_type": "lowest_weekly_score", "value": metrics["lowest_weekly_score"]["score"]}),
            weekly_card("biggest_victory", "Biggest Victory", metrics["biggest_victory"]["display"], {"fact_type": "biggest_victory", "value": metrics["biggest_victory"]["margin"]}),
            weekly_card("closest_game", "Closest Game", metrics["closest_game"]["display"], {"fact_type": "closest_game", "value": metrics["closest_game"]["margin"]}),
            weekly_card("highest_combined_score", "Highest Combined Score", metrics["highest_combined_score"]["display"], {"fact_type": "highest_combined_score", "value": metrics["highest_combined_score"]["combined_score"]}),
            weekly_card("longest_winning_streak", "Longest Winning Streak", metrics["longest_winning_streak"]["display"], {"fact_type": "longest_regular_season_winning_streak", "value": metrics["longest_winning_streak"]["games"]}),
        ])
    return cards


def build_team_recap(
    season: dict[str, Any], row: dict[str, Any], playoff: dict[str, Any], identities: dict[str, dict[str, Any]],
    generated_at: str, editorial: dict[str, Any], weekly: dict[str, Any] | None = None
) -> dict[str, Any]:
    year = season["year"]
    identity = identities.get(row.get("franchise_id"))
    mapping_status = "resolved" if identity else "unresolved"
    warnings: list[str] = []
    coverage = "complete"
    if not identity:
        warnings.append("unresolved_franchise_mapping")
        coverage = "partial"
    if year == 2024 and row.get("franchise_id") == "turnbull-acs":
        warnings.append("2024_pf_pa_source_conflict")
        coverage = "partial"
    facts: list[dict[str, Any]] = [{
        "fact_type": "standing",
        "rank": row["rank"],
        "wins": row["wins"],
        "losses": row["losses"],
        "ties": row["ties"],
        "points_for": row.get("points_for"),
        "points_against": row.get("points_against"),
    }]
    sentences = [
        f"{row['team_name']} finished {ordinal(row['rank'])} in the {year} final standings with a final record of {format_record(row)}."
    ]
    pf_rank = points_rank(season["standings"], row)
    if row.get("points_for") is not None and row.get("points_against") is not None:
        point_sentence = (
            f"The team posted {format_points(row['points_for'])} points for and "
            f"{format_points(row['points_against'])} points against."
        )
        if pf_rank is not None:
            point_sentence += f" Its points-for total ranked {ordinal(pf_rank)} in the {season['team_count']}-team field."
            facts.append({"fact_type": "points_for_rank", "rank": pf_rank, "team_count": season["team_count"]})
        sentences.append(point_sentence)
    else:
        coverage = "partial"
        warnings.append("missing_pf_or_pa")
    status_sentence, status_fact = playoff_status(row, playoff)
    sentences.append(status_sentence)
    facts.append(status_fact)
    weekly_metrics = weekly["team_metrics"].get(row.get("franchise_id")) if weekly and row.get("franchise_id") else None
    if weekly_metrics:
        high = weekly_metrics["highest_score"]
        biggest = weekly_metrics.get("biggest_win")
        closest = weekly_metrics["closest_game"]
        weekly_sentence = (
            f"Its highest verified weekly score was {format_points(high['score'])} in Week {high['week']}. "
        )
        if biggest:
            weekly_sentence += (
                f"Its largest win came by {format_points(biggest['margin'])} points over "
                f"{biggest['opponent_name']} in Week {biggest['week']}. "
            )
        weekly_sentence += (
            f"Its closest game was a {format_points(closest['margin'])}-point decision against "
            f"{closest['opponent_name']} in Week {closest['week']}; its longest regular-season runs were "
            f"{weekly_metrics['longest_regular_season_win_streak']} consecutive wins and "
            f"{weekly_metrics['longest_regular_season_loss_streak']} consecutive losses."
        )
        sentences.append(weekly_sentence)
        facts.append({"fact_type": "verified_weekly_metrics", **weekly_metrics})
    if not identity:
        sentences.append(
            "This historical identity remains unresolved, so the season result is not assigned to a current or retired franchise profile."
        )
    if weekly_metrics:
        sentences.append(
            "The recap uses the verified final standings, classified playoff results, and complete 16-week matchup archive; no transaction or player-level detail is inferred."
        )
    else:
        sentences.append(
            "The recap uses only the verified final standings and structured playoff bracket; no weekly, transaction, or player-level detail is inferred."
        )
    entry = {
        "recap_id": f"team-{year}-{row.get('franchise_id') or re.sub(r'[^a-z0-9]+', '-', row['team_name'].casefold()).strip('-')}",
        **provenance(year, generated_at, coverage, facts, warnings, SOURCE_FILES[:4]),
        "franchise_id": row.get("franchise_id"),
        "mapping_status": mapping_status,
        "historical_team_name": row["team_name"],
        "rank": row["rank"],
        "record": {"wins": row["wins"], "losses": row["losses"], "ties": row["ties"]},
        "points_for": row.get("points_for"),
        "points_against": row.get("points_against"),
        "path": identity["path"] if identity else None,
        "identity_image": identity["identity_image"] if identity else None,
        "identity_alt": identity["identity_alt"] if identity else None,
        "weekly_metrics": weekly_metrics,
    }
    override = override_for(
        editorial,
        "team_recaps",
        season=year,
        franchise_id=row.get("franchise_id"),
        historical_team_name=row["team_name"],
    )
    apply_override(entry, [" ".join(sentences)], override)
    return entry


def game_participants(game: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    one = {
        "franchise_id": game.get("team_one_franchise_id"),
        "name": game["team_one_display_name"],
        "score": game.get("team_one_score"),
    }
    two = {
        "franchise_id": game.get("team_two_franchise_id"),
        "name": game["team_two_display_name"],
        "score": game.get("team_two_score"),
    }
    return one, two


def build_playoff_recap(
    year: int, game: dict[str, Any], generated_at: str, editorial: dict[str, Any]
) -> dict[str, Any]:
    one, two = game_participants(game)
    winner = one if (
        (game.get("winner_franchise_id") and one["franchise_id"] == game["winner_franchise_id"])
        or (not game.get("winner_franchise_id") and one["name"] == game.get("winner_display_name"))
    ) else two
    loser = two if winner is one else one
    scores_available = winner["score"] is not None and loser["score"] is not None
    facts = [{
        "fact_type": "playoff_result",
        "game_id": game["game_id"],
        "round": game["round"],
        "winner_franchise_id": game.get("winner_franchise_id"),
        "winner_name": winner["name"],
        "loser_franchise_id": loser["franchise_id"],
        "loser_name": loser["name"],
        "winner_score": winner["score"],
        "loser_score": loser["score"],
    }]
    warnings: list[str] = []
    if scores_available:
        if game["round"] == "Championship":
            action = "to win the Brew Crew Cup"
        elif game["round"] in {"Third Place Game", "Fifth Place Game"}:
            action = f"in the {year} {game['round'].lower()}"
        else:
            action = f"in the {year} {game['round'].lower()}"
        text = (
            f"{winner['name']} defeated {loser['name']} {format_points(winner['score'])}–"
            f"{format_points(loser['score'])} {action}."
        )
        coverage = "complete"
    else:
        next_round = {"Quarterfinal": "semifinal", "Semifinal": "championship"}.get(game["round"])
        destination = f" to advance to the {next_round}" if next_round else ""
        text = (
            f"{winner['name']} advanced past {loser['name']} in the {year} {game['round'].lower()}{destination}. "
            "The source bracket verifies the winner but does not publish a score."
        )
        coverage = "partial"
        warnings.append("score_unavailable")
    if "opposite semifinal lanes" in str(game.get("notes") or ""):
        warnings.append("source_bracket_lane_ambiguity")
    entry = {
        "recap_id": f"playoff-{game['game_id']}",
        **provenance(year, generated_at, coverage, facts, warnings, SOURCE_FILES[1:3]),
        "game_id": game["game_id"],
        "round": game["round"],
        "order": game["order"],
        "winner_display_name": winner["name"],
        "loser_display_name": loser["name"],
        "winner_score": winner["score"],
        "loser_score": loser["score"],
    }
    apply_override(
        entry,
        [text],
        override_for(editorial, "playoff_recaps", season=year, game_id=game["game_id"]),
    )
    return entry


def path_sentence(team_name: str, franchise_id: str, playoff: dict[str, Any]) -> tuple[str | None, list[str]]:
    wins: list[tuple[str, str, str]] = []
    for game in playoff.get("games") or []:
        if game["round"] == "Championship" or game.get("bracket_type") == "placement" or game.get("winner_franchise_id") != franchise_id:
            continue
        one, two = game_participants(game)
        opponent = two if one["franchise_id"] == franchise_id else one
        wins.append((game["game_id"], opponent["name"], game["round"].lower()))
    wins.sort(key=lambda item: ROUND_ORDER.get(item[2].title(), 0))
    if not wins:
        return None, []
    segments = [f"{opponent} in the {round_name}" for _, opponent, round_name in wins]
    return f"{team_name} reached the final by advancing past {join_names(segments)}.", [item[0] for item in wins]


def build_championship_recap(
    season: dict[str, Any], champion: dict[str, Any], playoff: dict[str, Any], all_champions: list[dict[str, Any]],
    generated_at: str, editorial: dict[str, Any]
) -> dict[str, Any]:
    year = season["year"]
    rows_by_id = {row.get("franchise_id"): row for row in season["standings"] if row.get("franchise_id")}
    champion_row = rows_by_id[champion["champion_franchise_id"]]
    runner_row = rows_by_id[champion["runner_up_franchise_id"]]
    champion_path, champion_games = path_sentence(
        champion["champion_display_name"], champion["champion_franchise_id"], playoff
    )
    runner_path, runner_games = path_sentence(
        champion["runner_up_display_name"], champion["runner_up_franchise_id"], playoff
    )
    title_count = sum(
        item["year"] <= year and item["champion_franchise_id"] == champion["champion_franchise_id"]
        for item in all_champions
    )
    first = (
        f"The {year} Brew Crew Cup championship ended with {champion['champion_display_name']} defeating "
        f"{champion['runner_up_display_name']} {format_points(champion['champion_score'])}–"
        f"{format_points(champion['runner_up_score'])}."
    )
    second = (
        f"The final standings list {champion['champion_display_name']} {ordinal(champion_row['rank'])} at "
        f"{format_record(champion_row)} with {format_points(champion_row['points_for'])} points for, while "
        f"{champion['runner_up_display_name']} finished {ordinal(runner_row['rank'])} at {format_record(runner_row)} "
        f"with {format_points(runner_row['points_for'])} points for."
    )
    path_parts = [item for item in (champion_path, runner_path) if item]
    third = " ".join(path_parts)
    archive_start = min(item["year"] for item in all_champions)
    fourth = (
        f"The victory marked championship No. {title_count} for {champion['champion_display_name']} within the verified "
        f"{archive_start}–{year} archive through that season. The available sources do not establish player-level events, "
        "so this recap is limited to verified standings, playoff results, and the final score."
    )
    paragraphs = [first + " " + second, " ".join(part for part in (third, fourth) if part)]
    facts = [
        {
            "fact_type": "championship_result",
            "champion_franchise_id": champion["champion_franchise_id"],
            "runner_up_franchise_id": champion["runner_up_franchise_id"],
            "champion_score": champion["champion_score"],
            "runner_up_score": champion["runner_up_score"],
        },
        {
            "fact_type": "final_standing_positions",
            "champion_rank": champion_row["rank"],
            "runner_up_rank": runner_row["rank"],
            "champion_record": format_record(champion_row),
            "runner_up_record": format_record(runner_row),
        },
        {"fact_type": "verified_playoff_path", "champion_games": champion_games, "runner_up_games": runner_games},
        {"fact_type": "verified_archive_title_count", "value": title_count, "source_years": list(range(archive_start, year + 1))},
    ]
    entry = {
        "recap_id": f"championship-{year}",
        **provenance(year, generated_at, "complete", facts, source_files=SOURCE_FILES[:5]),
        "champion_franchise_id": champion["champion_franchise_id"],
        "champion_display_name": champion["champion_display_name"],
        "runner_up_franchise_id": champion["runner_up_franchise_id"],
        "runner_up_display_name": champion["runner_up_display_name"],
        "champion_score": champion["champion_score"],
        "runner_up_score": champion["runner_up_score"],
        "verified_archive_title_count": title_count,
    }
    apply_override(entry, paragraphs, override_for(editorial, "championship_recaps", season=year))
    return entry


def generate(
    *,
    seasons_data: dict[str, Any] | None = None,
    playoffs_data: dict[str, Any] | None = None,
    champions_data: dict[str, Any] | None = None,
    franchises_data: dict[str, Any] | None = None,
    records_data: dict[str, Any] | None = None,
    editorial_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seasons_data = seasons_data or load_yaml("_data/seasons.yml")
    playoffs_data = playoffs_data or load_yaml("_data/playoffs.yml")
    champions_data = champions_data or load_yaml("_data/champions.yml")
    franchises_data = franchises_data or load_yaml("_data/franchises.yml")
    records_data = records_data or load_json("_data/generated/record_book.json")
    editorial_data = editorial_data or load_yaml("_data/editorial/recaps.yml")

    seasons = seasons_data["seasons"]
    playoffs = {item["season"]: item for item in playoffs_data["playoffs"]}
    champions = {item["year"]: item for item in champions_data["champions"]}
    identities = identity_index(franchises_data["franchises"])
    generated_at = generated_timestamp(champions_data["champions"])

    season_recaps: list[dict[str, Any]] = []
    team_recaps: list[dict[str, Any]] = []
    playoff_recaps: list[dict[str, Any]] = []
    championship_recaps: list[dict[str, Any]] = []
    by_the_numbers: list[dict[str, Any]] = []
    for season in sorted(seasons, key=lambda item: item["year"], reverse=True):
        year = season["year"]
        playoff = playoffs[year]
        champion = champions[year]
        weekly = derive_weekly_archive(season, playoff, identities)
        season_recaps.append(build_season_recap(
            season, champion, playoff, records_data, generated_at, editorial_data, weekly
        ))
        by_the_numbers.extend(build_by_the_numbers(season, champion, generated_at, weekly))
        team_recaps.extend(
            build_team_recap(season, row, playoff, identities, generated_at, editorial_data, weekly)
            for row in season["standings"]
        )
        playoff_recaps.extend(
            build_playoff_recap(year, game, generated_at, editorial_data)
            for game in playoff["games"]
        )
        championship_recaps.append(
            build_championship_recap(
                season, champion, playoff, champions_data["champions"], generated_at, editorial_data
            )
        )

    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "engine": {
            "type": "deterministic_template_rules",
            "external_ai_required": False,
            "override_priority": ["approved_editorial_override", "deterministic_generated", "unavailable"],
        },
        "coverage": {
            "label": f"Verified {min(item['year'] for item in seasons)}–{max(item['year'] for item in seasons)} archive",
            "source_years": sorted(item["year"] for item in seasons),
            "source_files": SOURCE_FILES,
            "season_recaps": len(season_recaps),
            "team_recaps": len(team_recaps),
            "playoff_recaps": len(playoff_recaps),
            "championship_recaps": len(championship_recaps),
            "unresolved_team_recaps": sum(item["mapping_status"] == "unresolved" for item in team_recaps),
        },
        "seasons": season_recaps,
        "team_recaps": team_recaps,
        "playoff_recaps": playoff_recaps,
        "championship_recaps": championship_recaps,
        "by_the_numbers": by_the_numbers,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--check", action="store_true", help="Fail when committed output differs")
    args = parser.parse_args()
    payload = generate()
    if args.check:
        current = json.loads(args.output.read_text(encoding="utf-8"))
        if current != payload:
            raise SystemExit("Generated recaps are stale; run python scripts/build_recaps.py")
        print(
            f"Verified {len(payload['seasons'])} deterministic season recaps and "
            f"{len(payload['team_recaps'])} team recaps"
        )
        return
    write_json(args.output, payload)
    print(
        f"Wrote {args.output}: {len(payload['seasons'])} seasons, "
        f"{len(payload['team_recaps'])} teams, {len(payload['playoff_recaps'])} playoff games"
    )


if __name__ == "__main__":
    main()
