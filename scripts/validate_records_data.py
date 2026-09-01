"""Validate generated records, provenance, references, ties, and empty categories."""

from __future__ import annotations

import json
from numbers import Real
from pathlib import Path
from typing import Any, Callable

import yaml

import build_records
from validate_public_data import validate_payload


ROOT = Path(__file__).resolve().parents[1]
RECORDS_PATH = ROOT / "_data" / "generated" / "records.json"
VALID_COVERAGE = {"complete", "partial", "unavailable"}


def numeric(value: object) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def expected_ranks(entries: list[dict[str, Any]], metric: Callable[[dict[str, Any]], Any]) -> list[int]:
    ranks: list[int] = []
    previous: Any = object()
    for position, entry in enumerate(entries, start=1):
        current = metric(entry)
        ranks.append(ranks[-1] if ranks and current == previous else position)
        previous = current
    return ranks


def main() -> None:
    errors: list[str] = []
    try:
        payload = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise SystemExit(f"Records validation failed: {error}") from error

    errors.extend(validate_payload(RECORDS_PATH, payload))
    franchises = yaml.safe_load((ROOT / "_data" / "franchises.yml").read_text(encoding="utf-8"))["franchises"]
    franchise_ids = {item["franchise_id"] for item in franchises}
    expected_paths = {
        item["franchise_id"]: f"/{'retired' if item['status'] == 'retired' else 'teams'}/{item['slug']}/"
        for item in franchises
    }

    if payload != build_records.generate():
        errors.append("generated records differ from deterministic source aggregation")
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    coverage = payload.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("source_years") != [2021, 2022, 2023, 2024]:
        errors.append("coverage must identify the verified 2021-2024 source period")

    published: list[dict[str, Any]] = []
    leaderboards = payload.get("leaderboards")
    records = payload.get("records")
    if not isinstance(leaderboards, dict) or not isinstance(records, dict):
        errors.append("leaderboards and records must be objects")
        leaderboards = leaderboards if isinstance(leaderboards, dict) else {}
        records = records if isinstance(records, dict) else {}
    published.extend(leaderboards.values())
    published.extend(records.values())

    for group in published:
        category_id = group.get("category_id", "unknown")
        provenance = group.get("provenance")
        if not isinstance(provenance, dict):
            errors.append(f"{category_id}: provenance is required")
            continue
        if provenance.get("coverage_status") not in VALID_COVERAGE - {"unavailable"}:
            errors.append(f"{category_id}: published coverage must be complete or partial")
        for field in ("source_type", "source_years", "source_files", "last_generated", "notes"):
            if field not in provenance:
                errors.append(f"{category_id}: provenance is missing {field}")
        if provenance.get("coverage_status") == "partial" and "all-time" in json.dumps(group).casefold():
            errors.append(f"{category_id}: partial records cannot claim all-time coverage")
        for source_file in provenance.get("source_files") or []:
            if not (ROOT / source_file).is_file():
                errors.append(f"{category_id}: source file does not resolve: {source_file}")
        if not isinstance(group.get("entries"), list):
            errors.append(f"{category_id}: entries must be an array")

    metrics: dict[str, Callable[[dict[str, Any]], Any]] = {
        "career_totals": lambda entry: entry["wins"],
        "championships": lambda entry: entry["championships"],
        "finals_appearances": lambda entry: entry["finals_appearances"],
        "playoff_results": lambda entry: (entry["wins"], entry["appearances"]),
        "playoff_appearance_streaks": lambda entry: entry["streak"],
    }
    for category_id, metric in metrics.items():
        group = leaderboards.get(category_id) or {}
        entries = group.get("entries") or []
        ranks = [entry.get("rank") for entry in entries]
        if ranks != expected_ranks(entries, metric):
            errors.append(f"{category_id}: ranks do not preserve competition ties")
        for entry in entries:
            franchise_id = entry.get("franchise_id")
            if franchise_id not in franchise_ids:
                errors.append(f"{category_id}: unknown franchise_id {franchise_id!r}")
            elif entry.get("path") != expected_paths[franchise_id]:
                errors.append(f"{category_id}: franchise route does not resolve for {franchise_id}")

    for category_id in ("career_totals", "playoff_results"):
        for entry in (leaderboards.get(category_id) or {}).get("entries") or []:
            for field in ("wins", "losses"):
                if not isinstance(entry.get(field), int) or entry[field] < 0:
                    errors.append(f"{category_id}: {field} must be a non-negative integer")
    for entry in (leaderboards.get("career_totals") or {}).get("entries") or []:
        for field in ("ties", "seasons_counted"):
            if not isinstance(entry.get(field), int) or entry[field] < 0:
                errors.append(f"career_totals: {field} must be a non-negative integer")
        for field in ("win_pct", "points_for", "points_against"):
            if not numeric(entry.get(field)):
                errors.append(f"career_totals: {field} must be numeric")

    for group in records.values():
        for record in group.get("entries") or []:
            holders = record.get("holders")
            if not isinstance(holders, list) or not holders:
                errors.append(f"{record.get('record_id')}: record holders are required")
                continue
            values = {holder.get("value") for holder in holders}
            if len(values) != 1 or not all(numeric(value) for value in values):
                errors.append(f"{record.get('record_id')}: tied holders must share one numeric value")
            for holder in holders:
                franchise_id = holder.get("franchise_id")
                path = holder.get("path")
                if franchise_id is None:
                    if path is not None:
                        errors.append(f"{record.get('record_id')}: unresolved holder cannot have a link")
                elif franchise_id not in franchise_ids or path != expected_paths.get(franchise_id):
                    errors.append(f"{record.get('record_id')}: invalid holder franchise reference")
                if not (ROOT / "_seasons" / f"{holder.get('year')}.md").is_file():
                    errors.append(f"{record.get('record_id')}: season route does not resolve")

    unavailable = payload.get("unavailable_categories")
    if not isinstance(unavailable, list) or not unavailable:
        errors.append("unavailable categories must be an intentional non-empty list")
        unavailable = []
    for category in unavailable:
        if category.get("entries") != []:
            errors.append(f"{category.get('category_id')}: unavailable category contains fabricated values")
        if not str(category.get("message") or "").strip():
            errors.append(f"{category.get('category_id')}: unavailable category needs a public message")
        provenance = category.get("provenance") or {}
        if provenance.get("coverage_status") != "unavailable":
            errors.append(f"{category.get('category_id')}: unavailable provenance is invalid")
        if "all-time" in json.dumps(category).casefold():
            errors.append(f"{category.get('category_id')}: unavailable category cannot claim all-time coverage")

    bench = payload.get("bench_blunders") or {}
    expected_bench_fields = {
        "rank", "franchise_id", "historical_team_name", "year", "week",
        "player_name", "points_missed", "source",
    }
    if set(bench.get("required_fields") or []) != expected_bench_fields:
        errors.append("bench-blunder schema is incomplete")
    if bench.get("entries") != []:
        errors.append("bench blunders must remain empty until verified source data exists")
    if (bench.get("provenance") or {}).get("coverage_status") != "unavailable":
        errors.append("bench blunders must be marked unavailable")

    if errors:
        raise SystemExit("Records validation failed:\n- " + "\n- ".join(errors))
    published_count = sum(len(group["entries"]) for group in published)
    print(
        f"Validated {len(published)} published record groups, {published_count} entries, "
        f"{len(unavailable)} unavailable categories, provenance, ties, and references"
    )


if __name__ == "__main__":
    main()
