"""Build the public, provenance-carrying Road to Glory record book."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "_data"
OUTPUT_PATH = DATA_DIR / "generated" / "records.json"


def load_yaml(name: str) -> dict[str, Any]:
    value = yaml.safe_load((DATA_DIR / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"_data/{name}: expected a schema_version 1 mapping")
    return value


def calculate_win_pct(wins: int, losses: int, ties: int) -> float | None:
    games = wins + losses + ties
    return round((wins + ties * 0.5) / games, 3) if games else None


def rank_entries(
    entries: Iterable[dict[str, Any]],
    value: Callable[[dict[str, Any]], Any],
    *,
    reverse: bool = True,
) -> list[dict[str, Any]]:
    """Apply competition ranks (1, 1, 3) without breaking tied values."""
    ordered = sorted(entries, key=lambda entry: (value(entry), entry.get("display_name", "")), reverse=reverse)
    ranked: list[dict[str, Any]] = []
    previous: Any = object()
    for position, entry in enumerate(ordered, start=1):
        current = value(entry)
        rank = ranked[-1]["rank"] if ranked and current == previous else position
        ranked.append({"rank": rank, **entry})
        previous = current
    return ranked


def franchise_index(franchises: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for franchise in franchises:
        franchise_id = franchise["franchise_id"]
        status = franchise["status"]
        slug = franchise["slug"]
        index[franchise_id] = {
            "display_name": franchise["name"],
            "short_name": franchise.get("short_name") or franchise["name"],
            "path": f"/{'retired' if status == 'retired' else 'teams'}/{slug}/",
            "identity_image": (franchise.get("branding") or {}).get("identity_image"),
        }
    return index


def identity_fields(franchise_id: str, identities: dict[str, dict[str, Any]]) -> dict[str, Any]:
    identity = identities[franchise_id]
    return {"franchise_id": franchise_id, **identity}


def build_career_totals(
    seasons: list[dict[str, Any]],
    champions: list[dict[str, Any]],
    identities: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    totals: dict[str, dict[str, Any]] = {}
    unresolved_rows = 0
    for season in seasons:
        year = season["year"]
        for row in season.get("standings") or []:
            franchise_id = row.get("franchise_id")
            if not franchise_id:
                unresolved_rows += 1
                continue
            total = totals.setdefault(
                franchise_id,
                {
                    **identity_fields(franchise_id, identities),
                    "seasons": [],
                    "wins": 0,
                    "losses": 0,
                    "ties": 0,
                    "points_for": 0.0,
                    "points_against": 0.0,
                    "championships": 0,
                    "runner_up_finishes": 0,
                },
            )
            total["seasons"].append(year)
            for field in ("wins", "losses", "ties"):
                total[field] += int(row[field])
            if row.get("points_for") is not None:
                total["points_for"] += float(row["points_for"])
            if row.get("points_against") is not None:
                total["points_against"] += float(row["points_against"])

    for champion in champions:
        champion_id = champion.get("champion_franchise_id")
        runner_up_id = champion.get("runner_up_franchise_id")
        if champion_id in totals:
            totals[champion_id]["championships"] += 1
        if runner_up_id in totals:
            totals[runner_up_id]["runner_up_finishes"] += 1

    entries = []
    for total in totals.values():
        total["seasons"].sort()
        total["seasons_counted"] = len(total["seasons"])
        total["points_for"] = round(total["points_for"], 2)
        total["points_against"] = round(total["points_against"], 2)
        total["win_pct"] = calculate_win_pct(total["wins"], total["losses"], total["ties"])
        entries.append(total)
    return rank_entries(entries, lambda item: item["wins"]), unresolved_rows


def season_entry(year: int, row: dict[str, Any], identities: dict[str, dict[str, Any]]) -> dict[str, Any]:
    franchise_id = row.get("franchise_id")
    identity = identities.get(franchise_id) if franchise_id else None
    return {
        "year": year,
        "season_path": f"/history/{year}/",
        "franchise_id": franchise_id,
        "historical_team_name": row["team_name"],
        "display_name": identity["display_name"] if identity else row["team_name"],
        "path": identity["path"] if identity else None,
        "identity_image": identity["identity_image"] if identity else None,
        "source": {"file": "_data/seasons.yml", "year": year},
    }


def record_holders(
    rows: list[tuple[int, dict[str, Any]]],
    field: str,
    identities: dict[str, dict[str, Any]],
    *,
    highest: bool,
    transform: Callable[[dict[str, Any]], Any] | None = None,
) -> list[dict[str, Any]]:
    available = [(year, row) for year, row in rows if row.get(field) is not None]
    if not available:
        return []
    get_value = transform or (lambda row: row[field])
    target = (max if highest else min)(get_value(row) for _, row in available)
    holders = []
    for year, row in available:
        value = get_value(row)
        if value == target:
            holders.append({**season_entry(year, row, identities), "value": round(value, 3)})
    return sorted(holders, key=lambda item: (item["year"], item["historical_team_name"]), reverse=True)


def build_season_records(
    seasons: list[dict[str, Any]], identities: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = [(season["year"], row) for season in seasons for row in season.get("standings") or []]
    win_pct = lambda row: calculate_win_pct(row["wins"], row["losses"], row["ties"])
    result_records = [
        ("most_wins", "Most regular-season wins", "wins", True, None, "wins"),
        ("fewest_wins", "Fewest regular-season wins", "wins", False, None, "wins"),
        ("best_win_pct", "Best regular-season win percentage", "wins", True, win_pct, "percentage"),
    ]
    point_records = [
        ("highest_points_for", "Highest points for", "points_for", True, None, "points"),
        ("lowest_points_for", "Lowest points for", "points_for", False, None, "points"),
        ("highest_points_against", "Highest points against", "points_against", True, None, "points"),
        ("lowest_points_against", "Lowest points against", "points_against", False, None, "points"),
    ]

    def assemble(definitions: list[tuple[str, str, str, bool, Any, str]]) -> list[dict[str, Any]]:
        return [
            {
                "record_id": record_id,
                "label": label,
                "format": value_format,
                "holders": record_holders(rows, field, identities, highest=highest, transform=transform),
            }
            for record_id, label, field, highest, transform, value_format in definitions
        ]

    return assemble(result_records), assemble(point_records)


def count_leaderboard(
    counts: dict[str, int], identities: dict[str, dict[str, Any]], value_field: str
) -> list[dict[str, Any]]:
    entries = [
        {**identity_fields(franchise_id, identities), value_field: count}
        for franchise_id, count in counts.items()
        if count > 0 and franchise_id in identities
    ]
    return rank_entries(entries, lambda item: item[value_field])


def build_championship_leaderboards(
    champions: list[dict[str, Any]], identities: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    titles: defaultdict[str, int] = defaultdict(int)
    finals: defaultdict[str, int] = defaultdict(int)
    for season in champions:
        titles[season["champion_franchise_id"]] += 1
        finals[season["champion_franchise_id"]] += 1
        finals[season["runner_up_franchise_id"]] += 1
    return (
        count_leaderboard(titles, identities, "championships"),
        count_leaderboard(finals, identities, "finals_appearances"),
    )


def build_playoff_results(
    playoffs: list[dict[str, Any]], identities: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    results: dict[str, dict[str, Any]] = {}
    unresolved_participants: set[tuple[int, str]] = set()
    for playoff in playoffs:
        year = playoff["season"]
        season_participants: set[str] = set()
        for game in playoff.get("games") or []:
            winner_id = game.get("winner_franchise_id")
            for side in ("team_one", "team_two"):
                franchise_id = game.get(f"{side}_franchise_id")
                display_name = game.get(f"{side}_display_name")
                if not franchise_id:
                    unresolved_participants.add((year, display_name))
                    continue
                season_participants.add(franchise_id)
                result = results.setdefault(
                    franchise_id,
                    {**identity_fields(franchise_id, identities), "seasons": set(), "wins": 0, "losses": 0},
                )
                if franchise_id == winner_id:
                    result["wins"] += 1
                else:
                    result["losses"] += 1
        for franchise_id in season_participants:
            results[franchise_id]["seasons"].add(year)

    entries = []
    for result in results.values():
        result["seasons"] = sorted(result["seasons"])
        result["appearances"] = len(result["seasons"])
        entries.append(result)
    entries = rank_entries(entries, lambda item: (item["wins"], item["appearances"]))
    return entries, len(unresolved_participants)


def build_playoff_streaks(
    playoffs: list[dict[str, Any]], identities: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    years_by_franchise: defaultdict[str, set[int]] = defaultdict(set)
    for playoff in playoffs:
        for game in playoff.get("games") or []:
            for side in ("team_one", "team_two"):
                franchise_id = game.get(f"{side}_franchise_id")
                if franchise_id:
                    years_by_franchise[franchise_id].add(playoff["season"])

    entries = []
    for franchise_id, year_set in years_by_franchise.items():
        years = sorted(year_set)
        best: list[int] = []
        current: list[int] = []
        for year in years:
            if current and year != current[-1] + 1:
                if len(current) > len(best):
                    best = current
                current = []
            current.append(year)
        if len(current) > len(best):
            best = current
        entries.append(
            {
                **identity_fields(franchise_id, identities),
                "streak": len(best),
                "start_year": best[0],
                "end_year": best[-1],
            }
        )
    return rank_entries(entries, lambda item: item["streak"])


def provenance(category: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        "source_type": category["source_type"],
        "source_years": category.get("source_years") or [],
        "source_files": category.get("source_files") or [],
        "coverage_status": category["coverage_status"],
        "last_generated": generated_at,
        "notes": category.get("notes") or [],
    }


def build_payload(
    seasons_data: dict[str, Any],
    champions_data: dict[str, Any],
    playoffs_data: dict[str, Any],
    franchises_data: dict[str, Any],
    records_config: dict[str, Any],
) -> dict[str, Any]:
    seasons = seasons_data["seasons"]
    champions = champions_data["champions"]
    playoffs = playoffs_data["playoffs"]
    identities = franchise_index(franchises_data["franchises"])
    categories = {item["category_id"]: item for item in records_config["categories"]}
    verified_dates = [str(item["verified_on"]) for item in champions if item.get("verified_on")]
    generated_at = f"{max(verified_dates)}T00:00:00Z"

    career, unresolved_standings = build_career_totals(seasons, champions, identities)
    season_results, season_points = build_season_records(seasons, identities)
    championships, finals = build_championship_leaderboards(champions, identities)
    playoff_results, unresolved_playoffs = build_playoff_results(playoffs, identities)
    playoff_streaks = build_playoff_streaks(playoffs, identities)

    def group(category_id: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
        category = categories[category_id]
        if not category.get("public_calculation_allowed") or category.get("coverage_status") == "unavailable":
            raise ValueError(f"{category_id}: configuration does not allow public calculation")
        return {
            "category_id": category_id,
            "label": category["label"],
            "provenance": provenance(category, generated_at),
            "entries": entries,
        }

    unavailable = []
    for category in records_config["categories"]:
        if category["coverage_status"] == "unavailable":
            unavailable.append(
                {
                    "category_id": category["category_id"],
                    "label": category["label"],
                    "message": category["public_message"],
                    "provenance": provenance(category, generated_at),
                    "entries": [],
                }
            )

    archive = records_config["archive"]
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "coverage": {
            "label": archive["label"],
            "source_years": archive["source_years"],
            "unresolved_standings_rows": unresolved_standings,
            "unresolved_playoff_participants": unresolved_playoffs,
            "notes": archive["notes"],
        },
        "leaderboards": {
            "career_totals": group("career_totals", career),
            "championships": group("championships", championships),
            "finals_appearances": group("finals_appearances", finals),
            "playoff_results": group("playoff_results", playoff_results),
            "playoff_appearance_streaks": group("playoff_appearance_streaks", playoff_streaks),
        },
        "records": {
            "season_results": group("season_wins", season_results),
            "season_points": group("season_points", season_points),
        },
        "unavailable_categories": unavailable,
        "bench_blunders": {
            "category_id": "bench_blunders",
            "label": categories["bench_blunders"]["label"],
            "required_fields": records_config["bench_blunder_schema"]["required_fields"],
            "provenance": provenance(categories["bench_blunders"], generated_at),
            "entries": records_config["bench_blunder_schema"]["entries"],
        },
    }


def generate() -> dict[str, Any]:
    return build_payload(
        load_yaml("seasons.yml"),
        load_yaml("champions.yml"),
        load_yaml("playoffs.yml"),
        load_yaml("franchises.yml"),
        load_yaml("records.yml"),
    )


def serialized(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when the committed output is stale")
    args = parser.parse_args()
    content = serialized(generate())
    if args.check:
        if not OUTPUT_PATH.is_file() or OUTPUT_PATH.read_text(encoding="utf-8") != content:
            raise SystemExit("Generated records are stale; run python scripts/build_records.py")
        print("Generated records are current")
        return
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
