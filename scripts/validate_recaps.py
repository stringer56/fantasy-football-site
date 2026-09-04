"""Validate deterministic recaps, canonical facts, provenance, and safety rules."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

import build_recaps
from validate_public_data import validate_payload


ROOT = Path(__file__).resolve().parents[1]
RECAPS_PATH = ROOT / "_data" / "generated" / "recaps.json"
VALID_COVERAGE = {"complete", "partial", "unavailable"}
REQUIRED_PROVENANCE = {
    "season", "source_files", "generated_at", "coverage_status", "facts_used", "warnings", "provenance_label"
}
FORBIDDEN_CLAIM_PATTERNS = {
    "winning streak": r"\bwinning streak\b",
    "losing streak": r"\blosing streak\b",
    "upset": r"\bupset\b",
    "comeback": r"\bcomeback\b",
    "bench blunder": r"\bbench blunder\b",
    "biggest blowout": r"\bbiggest blowout\b",
    "closest game": r"\bclosest game\b",
    "waiver activity": r"\bwaiver (?:claim|move|activity)\b",
    "trade story": r"\btrad(?:e|ed|ing) (?:for|away|changed|sparked)\b",
    "injury story": r"\binjur(?:y|ies)\b",
    "manager strategy": r"\bmanager strategy\b",
    "rivalry context": r"\brivalry\b",
    "dominance claim": r"\bdominant all season\b",
    "surprise claim": r"\bcame out of nowhere\b",
    "draft effect": r"\bdraft (?:effect|class|pick) (?:changed|sparked|powered|drove)\b",
}


def load_yaml(name: str) -> dict[str, Any]:
    value = yaml.safe_load((ROOT / "_data" / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"_data/{name}: root must be a mapping")
    return value


def score_pairs(text: str) -> list[tuple[float, float]]:
    matches = re.findall(r"(?<!\d)(\d{1,3}(?:,\d{3})*\.\d{2})–(\d{1,3}(?:,\d{3})*\.\d{2})(?!\d)", text)
    return [(float(left.replace(",", "")), float(right.replace(",", ""))) for left, right in matches]


def record_values(text: str) -> list[tuple[int, int, int]]:
    return [(int(wins), int(losses), int(ties)) for wins, losses, ties in re.findall(r"(\d+)–(\d+)–(\d+)", text)]


def check_provenance(
    label: str, entry: dict[str, Any], errors: list[str], *, requires_text: bool = True
) -> None:
    missing = REQUIRED_PROVENANCE - set(entry)
    if missing:
        errors.append(f"{label}: missing provenance fields {sorted(missing)}")
    if entry.get("coverage_status") not in VALID_COVERAGE:
        errors.append(f"{label}: invalid coverage_status")
    if not isinstance(entry.get("facts_used"), list) or not entry.get("facts_used"):
        errors.append(f"{label}: facts_used must be a non-empty array")
    if not isinstance(entry.get("warnings"), list):
        errors.append(f"{label}: warnings must be an array")
    for source_file in entry.get("source_files") or []:
        if not (ROOT / source_file).is_file():
            errors.append(f"{label}: source file does not resolve: {source_file}")
    for field in (("text", "generated_text") if requires_text else ()):
        prose = str(entry.get(field) or "")
        if not prose.strip():
            errors.append(f"{label}: {field} is required")
            continue
        if "all-time" in prose.casefold():
            errors.append(f"{label}: unsupported all-time language")
        for claim, pattern in FORBIDDEN_CLAIM_PATTERNS.items():
            if re.search(pattern, prose, flags=re.IGNORECASE):
                fact_types = {fact.get("fact_type") for fact in entry.get("facts_used") or []}
                if claim == "closest game" and fact_types & {"closest_game", "verified_weekly_metrics"}:
                    continue
                errors.append(f"{label}: unsupported {claim} language")


def main() -> None:
    errors: list[str] = []
    try:
        payload = json.loads(RECAPS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise SystemExit(f"Recap validation failed: {error}") from error

    errors.extend(validate_payload(RECAPS_PATH, payload))
    if payload != build_recaps.generate():
        errors.append("generated recaps differ from deterministic canonical aggregation")
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    engine = payload.get("engine") or {}
    if engine.get("type") != "deterministic_template_rules" or engine.get("external_ai_required") is not False:
        errors.append("recap engine must be deterministic and require no external AI")

    seasons_data = load_yaml("seasons.yml")["seasons"]
    playoffs_data = load_yaml("playoffs.yml")["playoffs"]
    champions_data = load_yaml("champions.yml")["champions"]
    franchises = load_yaml("franchises.yml")["franchises"]
    editorial = load_yaml("editorial/recaps.yml")
    season_by_year = {item["year"]: item for item in seasons_data}
    playoff_by_year = {item["season"]: item for item in playoffs_data}
    champion_by_year = {item["year"]: item for item in champions_data}
    franchise_by_id = {item["franchise_id"]: item for item in franchises}
    expected_years = set(season_by_year)

    collections = {
        "seasons": payload.get("seasons"),
        "team_recaps": payload.get("team_recaps"),
        "playoff_recaps": payload.get("playoff_recaps"),
        "championship_recaps": payload.get("championship_recaps"),
        "by_the_numbers": payload.get("by_the_numbers"),
    }
    for name, entries in collections.items():
        if not isinstance(entries, list):
            errors.append(f"{name} must be an array")
            collections[name] = []
            continue
        for entry in entries:
            if entry.get("season") not in expected_years:
                errors.append(f"{name}: unknown season {entry.get('season')!r}")
            check_provenance(
                f"{name}/{entry.get('recap_id') or entry.get('stat_id')}",
                entry,
                errors,
                requires_text=name != "by_the_numbers",
            )

    season_recaps = collections["seasons"]
    if {entry.get("season") for entry in season_recaps} != expected_years or len(season_recaps) != len(expected_years):
        errors.append("exactly one season recap is required for every canonical season")
    for recap in season_recaps:
        year = recap["season"]
        champion = champion_by_year[year]
        expected_pair = (float(champion["champion_score"]), float(champion["runner_up_score"]))
        if recap.get("facts_used", [{}])[0].get("champion_franchise_id") != champion["champion_franchise_id"]:
            errors.append(f"season-{year}: champion fact does not match canonical champion")
        valid_records = {
            (row["wins"], row["losses"], row["ties"])
            for row in season_by_year[year]["standings"]
        }
        valid_points = {
            float(value)
            for row in season_by_year[year]["standings"]
            for value in (row.get("points_for"), row.get("points_against"))
            if value is not None
        }
        for prose in (recap["generated_text"], recap["text"]):
            if any(pair != expected_pair for pair in score_pairs(prose)):
                errors.append(f"season-{year}: quoted championship score does not match canonical result")
            if any(value not in valid_records for value in record_values(prose)):
                errors.append(f"season-{year}: quoted W-L-T does not match canonical standings")
            quoted_points = [
                float(value.replace(",", ""))
                for value in re.findall(r"(\d{1,3}(?:,\d{3})*\.\d{2}) points (?:for|against)", prose)
            ]
            if any(value not in valid_points for value in quoted_points):
                errors.append(f"season-{year}: quoted PF/PA does not match canonical standings")

    expected_rows: dict[tuple[int, str], dict[str, Any]] = {}
    for season in seasons_data:
        for row in season["standings"]:
            key = row.get("franchise_id") or f"historical:{row['team_name'].casefold()}"
            expected_rows[(season["year"], key)] = row
    seen_rows: set[tuple[int, str]] = set()
    for recap in collections["team_recaps"]:
        key_value = recap.get("franchise_id") or f"historical:{recap.get('historical_team_name', '').casefold()}"
        key = (recap["season"], key_value)
        row = expected_rows.get(key)
        if row is None:
            errors.append(f"{recap.get('recap_id')}: team recap does not match a canonical standings row")
            continue
        seen_rows.add(key)
        expected_record = (row["wins"], row["losses"], row["ties"])
        if recap.get("record") != {"wins": row["wins"], "losses": row["losses"], "ties": row["ties"]}:
            errors.append(f"{recap['recap_id']}: structured record does not match standings")
        quoted_records = record_values(recap["generated_text"])
        if quoted_records != [expected_record]:
            errors.append(f"{recap['recap_id']}: quoted W-L-T does not match standings")
        if row.get("points_for") is not None and f"{build_recaps.format_points(row['points_for'])} points for" not in recap["generated_text"]:
            errors.append(f"{recap['recap_id']}: quoted PF is missing or incorrect")
        if row.get("points_against") is not None and f"{build_recaps.format_points(row['points_against'])} points against" not in recap["generated_text"]:
            errors.append(f"{recap['recap_id']}: quoted PA is missing or incorrect")
        for prose in (recap["text"], recap["generated_text"]):
            if any(value != expected_record for value in record_values(prose)):
                errors.append(f"{recap['recap_id']}: public W-L-T conflicts with standings")
            for field, label in (("points_for", "for"), ("points_against", "against")):
                quoted = [
                    float(value.replace(",", ""))
                    for value in re.findall(rf"(\d{{1,3}}(?:,\d{{3}})*\.\d{{2}}) points {label}", prose)
                ]
                if any(row.get(field) is None or value != float(row[field]) for value in quoted):
                    errors.append(f"{recap['recap_id']}: public points {label} conflicts with standings")
        if row.get("franchise_id"):
            franchise = franchise_by_id.get(row["franchise_id"])
            expected_path = f"/{'retired' if franchise and franchise['status'] == 'retired' else 'teams'}/{franchise['slug']}/" if franchise else None
            if recap.get("mapping_status") != "resolved" or recap.get("path") != expected_path:
                errors.append(f"{recap['recap_id']}: resolved franchise link is invalid")
        elif recap.get("mapping_status") != "unresolved" or recap.get("path") is not None:
            errors.append(f"{recap['recap_id']}: unresolved identity was mapped or linked")
    if seen_rows != set(expected_rows):
        errors.append("team recap coverage does not match all canonical standings rows")

    canonical_games = {
        game["game_id"]: (playoff["season"], game)
        for playoff in playoffs_data for game in playoff["games"]
    }
    seen_games: set[str] = set()
    for recap in collections["playoff_recaps"]:
        game_info = canonical_games.get(recap.get("game_id"))
        if not game_info:
            errors.append(f"{recap.get('recap_id')}: unknown playoff game")
            continue
        year, game = game_info
        seen_games.add(game["game_id"])
        one, two = build_recaps.game_participants(game)
        winner = one if one["franchise_id"] == game.get("winner_franchise_id") or (
            not game.get("winner_franchise_id") and one["name"] == game.get("winner_display_name")
        ) else two
        loser = two if winner is one else one
        if recap.get("winner_display_name") != winner["name"] or recap.get("loser_display_name") != loser["name"]:
            errors.append(f"{recap['recap_id']}: winner or loser does not match canonical game")
        if winner["score"] is None or loser["score"] is None:
            if score_pairs(recap["generated_text"]) or "does not publish a score" not in recap["generated_text"]:
                errors.append(f"{recap['recap_id']}: missing score was converted into a factual score")
            if score_pairs(recap["text"]):
                errors.append(f"{recap['recap_id']}: editorial prose invented a missing playoff score")
        else:
            expected_score = (float(winner["score"]), float(loser["score"]))
            if score_pairs(recap["generated_text"]) != [expected_score]:
                errors.append(f"{recap['recap_id']}: quoted playoff score does not match canonical game")
            if any(pair != expected_score for pair in score_pairs(recap["text"])):
                errors.append(f"{recap['recap_id']}: editorial playoff score conflicts with canonical game")
        if recap["season"] != year:
            errors.append(f"{recap['recap_id']}: game is assigned to the wrong season")
    if seen_games != set(canonical_games):
        errors.append("playoff recap coverage does not match every canonical game")

    championship_recaps = collections["championship_recaps"]
    if {entry.get("season") for entry in championship_recaps} != expected_years or len(championship_recaps) != len(expected_years):
        errors.append("exactly one championship recap is required for every canonical season")
    for recap in championship_recaps:
        champion = champion_by_year[recap["season"]]
        for field in (
            "champion_franchise_id", "runner_up_franchise_id", "champion_score", "runner_up_score"
        ):
            if recap.get(field) != champion.get(field):
                errors.append(f"{recap['recap_id']}: {field} does not match canonical championship")
        expected_pair = (float(champion["champion_score"]), float(champion["runner_up_score"]))
        if score_pairs(recap["generated_text"]) != [expected_pair]:
            errors.append(f"{recap['recap_id']}: quoted final score does not match canonical championship")
        if any(pair != expected_pair for pair in score_pairs(recap["text"])):
            errors.append(f"{recap['recap_id']}: editorial final score conflicts with canonical championship")
        season_rows = season_by_year[recap["season"]]["standings"]
        finalist_records = {
            (row["wins"], row["losses"], row["ties"])
            for row in season_rows
            if row.get("franchise_id") in {champion["champion_franchise_id"], champion["runner_up_franchise_id"]}
        }
        finalist_points = {
            float(value)
            for row in season_rows
            if row.get("franchise_id") in {champion["champion_franchise_id"], champion["runner_up_franchise_id"]}
            for value in (row.get("points_for"), row.get("points_against"))
            if value is not None
        }
        for prose in (recap["text"], recap["generated_text"]):
            if any(value not in finalist_records for value in record_values(prose)):
                errors.append(f"{recap['recap_id']}: finalist record conflicts with canonical standings")
            quoted_points = [
                float(value.replace(",", ""))
                for value in re.findall(r"(\d{1,3}(?:,\d{3})*\.\d{2}) points (?:for|against)", prose)
            ]
            if any(value not in finalist_points for value in quoted_points):
                errors.append(f"{recap['recap_id']}: finalist PF/PA conflicts with canonical standings")

    number_ids: dict[int, set[str]] = {year: set() for year in expected_years}
    for item in collections["by_the_numbers"]:
        if item.get("stat_id") in number_ids[item["season"]]:
            errors.append(f"by_the_numbers/{item['season']}: duplicate {item.get('stat_id')}")
        number_ids[item["season"]].add(item.get("stat_id"))
    required_numbers = {
        "champion", "runner_up", "best_record", "highest_pf", "lowest_pf", "most_wins",
        "fewest_wins", "championship_score", "team_count",
    }
    for year, stat_ids in number_ids.items():
        expected_numbers = set(required_numbers)
        if season_by_year[year].get("weeks_data_path"):
            expected_numbers.update({
                "highest_weekly_score", "lowest_weekly_score", "biggest_victory",
                "closest_game", "highest_combined_score", "longest_winning_streak",
            })
        if stat_ids != expected_numbers:
            errors.append(f"by_the_numbers/{year}: supported canonical fields are incomplete")

    detailed_years = sorted(
        year for year, season in season_by_year.items() if season.get("data_mode") == "detailed"
    )
    for detailed_year in detailed_years:
        season_recap = next((item for item in season_recaps if item.get("season") == detailed_year), None)
        if not season_recap:
            continue
        weekly = season_recap.get("weekly_archive") or {}
        if weekly.get("week_count") != 16 or weekly.get("matchup_count") != 92:
            errors.append(f"season-{detailed_year}: weekly archive must contain 16 weeks and 92 matchups")
        if len(weekly.get("weeks") or []) != 16:
            errors.append(f"season-{detailed_year}: every week must be represented")
        if len(season_recap.get("paragraphs") or []) < 3 or len(season_recap.get("paragraphs") or []) > 6:
            errors.append(f"season-{detailed_year}: season narrative must contain 3-6 paragraphs")
        team_recaps = [item for item in collections["team_recaps"] if item.get("season") == detailed_year]
        if len(team_recaps) != 12 or any(not item.get("weekly_metrics") for item in team_recaps):
            errors.append(f"{detailed_year}: all 12 franchises require verified weekly mini-recap metrics")

    override_keys: set[tuple[Any, ...]] = set()
    for kind in ("season_recaps", "team_recaps", "playoff_recaps", "championship_recaps"):
        if not isinstance(editorial.get(kind), list):
            errors.append(f"editorial recaps: {kind} must be an array")
            continue
        for item in editorial[kind]:
            key = (kind, item.get("season"), item.get("franchise_id"), item.get("historical_team_name"), item.get("game_id"))
            if key in override_keys:
                errors.append(f"editorial recaps: duplicate override {key}")
            override_keys.add(key)
            if item.get("status") != "approved" or not str(item.get("text") or "").strip():
                errors.append(f"editorial recaps: override {key} must be approved and contain text")

    if errors:
        raise SystemExit("Recap validation failed:\n- " + "\n- ".join(errors))
    print(
        f"Validated {len(season_recaps)} season recaps, {len(collections['team_recaps'])} team recaps, "
        f"{len(collections['playoff_recaps'])} playoff recaps, and {len(championship_recaps)} championships"
    )


if __name__ == "__main__":
    main()
