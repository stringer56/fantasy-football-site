#!/usr/bin/env python3
"""Backfill sanitized Road to Glory history from official public Yahoo archives."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any

import yaml

from yahoo_archive import (
    ArchiveClient,
    parse_available_weeks,
    parse_draft,
    parse_matchups,
    parse_roster,
    parse_standings,
    parse_transactions,
    next_transaction_offset,
    write_json,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "_data" / "generated" / "history_manifest.json"
OUTPUT_ROOT = ROOT / "_data" / "generated" / "history"
CACHE_ROOT = ROOT / ".cache" / "yahoo-history"
FRANCHISES_PATH = ROOT / "_data" / "franchises.yml"
SEASONS_PATH = ROOT / "_data" / "seasons.yml"
PLAYOFFS_PATH = ROOT / "_data" / "playoffs.yml"
DRAFTS_PATH = ROOT / "_data" / "drafts.yml"
YAHOO_2021_SOURCE_PATH = ROOT / "_data" / "yahoo_history" / "2021.yml"
COMPLETED_SEASONS = {2021, 2022, 2023, 2024, 2025}
PLAYOFF_START = {2021: 15, 2022: 15, 2023: 14, 2024: 14, 2025: 14}
DEFAULT_SECTIONS = {"league", "standings", "matchups", "draft", "transactions"}
REMAPPABLE_FILES = ("teams.json", "standings.json", "weeks.json", "draft.json", "transactions.json", "rosters.json")


def coverage_scopes() -> dict[str, dict[str, Any]]:
    """Return the verified metric windows exposed to downstream builders."""
    return {
        "season_level_metrics": {
            "label": "Verified 2021–2025",
            "source_years": [2021, 2022, 2023, 2024, 2025],
            "coverage_status": "verified_with_mapping_exclusions",
            "allowed_metrics": [
                "final_standings",
                "season_wins_losses_ties",
                "season_points_for_against",
                "final_rank",
                "playoff_seed",
                "verified_championships",
                "resolved_franchise_season_summaries",
            ],
            "mapping_policy": (
                "Unresolved historical identities remain season-level rows but are excluded "
                "from franchise-level aggregation."
            ),
        },
        "weekly_derived_metrics": {
            "label": "Verified 2021–2025",
            "source_years": [2021, 2022, 2023, 2024, 2025],
            "coverage_status": "complete_weekly_results_for_listed_years",
            "allowed_metrics": [
                "head_to_head",
                "largest_margin",
                "smallest_winning_margin",
                "weekly_scoring_highs_lows",
                "matchup_margins",
                "weekly_win_loss_streaks",
                "detailed_playoff_matchup_metrics",
            ],
            "excluded_years": [],
            "exclusion_reason": None,
        },
    }


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_seasons(value: str, available: set[int]) -> list[int]:
    selected: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = (int(item) for item in part.split("-", 1))
            selected.update(range(min(start, end), max(start, end) + 1))
        else:
            selected.add(int(part))
    unknown = selected - available
    if unknown:
        raise ValueError(f"unknown season(s): {', '.join(map(str, sorted(unknown)))}")
    return sorted(selected)


def canonical_name_map() -> dict[str, str | None]:
    payload = yaml.safe_load(FRANCHISES_PATH.read_text(encoding="utf-8"))
    candidates: dict[str, set[str]] = {}
    for franchise in payload.get("franchises", []):
        franchise_id = franchise.get("franchise_id")
        for name in [franchise.get("name"), *(franchise.get("aliases") or [])]:
            if name:
                candidates.setdefault(str(name).casefold(), set()).add(franchise_id)
    seasons = yaml.safe_load(SEASONS_PATH.read_text(encoding="utf-8"))
    for season in seasons.get("seasons", []):
        for standing in season.get("standings", []):
            name, franchise_id = standing.get("team_name"), standing.get("franchise_id")
            if name and franchise_id:
                candidates.setdefault(str(name).casefold(), set()).add(franchise_id)
    return {name: next(iter(ids)) if len(ids) == 1 else None for name, ids in candidates.items()}


def mappings_for(season: dict[str, Any]) -> tuple[dict[str, str | None], dict[str, str | None]]:
    key_map: dict[str, str | None] = {}
    name_map = canonical_name_map()
    for item in season.get("team_mappings", []):
        key = item.get("yahoo_team_key")
        name = item.get("yahoo_team_name")
        franchise_id = item.get("candidate_franchise_id") if item.get("status") == "verified" else None
        if key:
            key_map[key] = franchise_id
        if name:
            name_map[name.casefold()] = franchise_id
    return key_map, name_map


def remap_payload(value: Any, mappings_by_name: dict[str, str | None]) -> int:
    """Apply only approved canonical aliases to an already normalized payload."""
    changes = 0
    if isinstance(value, list):
        return sum(remap_payload(item, mappings_by_name) for item in value)
    if not isinstance(value, dict):
        return 0
    for child in value.values():
        changes += remap_payload(child, mappings_by_name)

    historical_name = value.get("historical_team_name")
    if historical_name and "franchise_id" in value:
        franchise_id = mappings_by_name.get(str(historical_name).casefold())
        if franchise_id:
            if value.get("franchise_id") != franchise_id:
                value["franchise_id"] = franchise_id
                changes += 1
            if "mapping_status" in value and value.get("mapping_status") != "verified":
                value["mapping_status"] = "verified"
                changes += 1

    winner_name = value.get("winner_historical_name")
    if winner_name and "winner_franchise_id" in value:
        franchise_id = mappings_by_name.get(str(winner_name).casefold())
        if franchise_id and value.get("winner_franchise_id") != franchise_id:
            value["winner_franchise_id"] = franchise_id
            changes += 1
    return changes


def remap_committed_history(selected: list[int]) -> int:
    """Refresh canonical joins without refetching or changing Yahoo source facts."""
    mappings_by_name = canonical_name_map()
    changed_files = 0
    for year in selected:
        for filename in REMAPPABLE_FILES:
            path = OUTPUT_ROOT / str(year) / filename
            if not path.is_file():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if remap_payload(payload, mappings_by_name):
                write_json(path, payload)
                changed_files += 1

    completeness_path = OUTPUT_ROOT / "completeness.json"
    completeness = json.loads(completeness_path.read_text(encoding="utf-8"))
    completeness_changed = False
    if 2021 in selected:
        summary_2021 = next(
            item for item in completeness.get("seasons", []) if item.get("season") == 2021
        )
        source_2021 = yaml.safe_load(YAHOO_2021_SOURCE_PATH.read_text(encoding="utf-8"))
        generated_at_2021 = f"{source_2021['verified_on']}T00:00:00Z"
        apply_2021_canonical_fallback(
            summary_2021,
            generated_at_2021,
        )
        completeness["generated_at"] = max(
            str(completeness.get("generated_at") or generated_at_2021), generated_at_2021
        )
        completeness["coverage_scopes"] = coverage_scopes()
        completeness_changed = True
        changed_files += 3
    for summary in completeness.get("seasons", []):
        year = int(summary["season"])
        if year not in selected:
            continue
        standings_path = OUTPUT_ROOT / str(year) / "standings.json"
        if not standings_path.is_file():
            continue
        standings = json.loads(standings_path.read_text(encoding="utf-8")).get("standings", [])
        unresolved = sorted(
            row["historical_team_name"] for row in standings if not row.get("franchise_id")
        )
        mapping = summary.setdefault("franchise_mapping", {})
        replacement = "complete" if standings and not unresolved else ("partial" if standings else "unavailable")
        if mapping.get("status") != replacement:
            mapping["status"] = replacement
            completeness_changed = True
        if mapping.get("unresolved_names") != unresolved:
            mapping["unresolved_names"] = unresolved
            completeness_changed = True
        if "resolved" in mapping:
            resolved = len(standings) - len(unresolved)
            if mapping.get("resolved") != resolved:
                mapping["resolved"] = resolved
                completeness_changed = True
        if summary.get("unresolved_franchise_mappings") != unresolved:
            summary["unresolved_franchise_mappings"] = unresolved
            completeness_changed = True
        confidence = "high_results_partial_identity" if unresolved else "high_results_complete_identity"
        if summary.get("confidence") != confidence:
            summary["confidence"] = confidence
            completeness_changed = True
    if completeness_changed:
        write_json(completeness_path, completeness)
        changed_files += 1
    return changed_files


def payload_base(season: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "season": season["season"],
        "league_key": season["league_key"],
        "generated_at": generated_at,
        "source": {
            "type": "official_yahoo_public_archive",
            "url": f"https://football.fantasysports.yahoo.com/{season['season']}/f1/{season['league_id']}",
            "coverage_status": "verified_rows_only",
        },
    }


def safe_failure(season: int, section: str, error: Exception) -> dict[str, Any]:
    message = str(error)
    if "http" in message.lower():
        message = message.split("(", 1)[0].strip()
    return {"season": season, "section": section, "error_type": type(error).__name__, "message": message[:160]}


def build_2021_weeks(yahoo_source: dict[str, Any], standings: list[dict[str, Any]],
                     generated_at: str) -> dict[str, Any]:
    """Normalize the commissioner-authenticated Yahoo schedule transcription."""
    by_id = {row["yahoo_team_id"]: row for row in standings}
    weeks: dict[int, list[dict[str, Any]]] = {week: [] for week in range(1, 17)}
    seen: set[tuple[int, int, int]] = set()
    for raw in yahoo_source.get("matchups", []):
        week = int(raw["week"])
        team_a_id = int(raw["team_a_id"])
        team_b_id = int(raw["team_b_id"])
        pair = tuple(sorted((team_a_id, team_b_id)))
        key = (week, *pair)
        if key in seen:
            raise ValueError(f"2021 duplicate matchup: {key}")
        seen.add(key)
        if week not in weeks or team_a_id not in by_id or team_b_id not in by_id:
            raise ValueError(f"2021 invalid matchup reference: {key}")
        score_a = float(raw["team_a_score"])
        score_b = float(raw["team_b_score"])
        team_a = by_id[team_a_id]
        team_b = by_id[team_b_id]
        tie = score_a == score_b
        winner = None if tie else (team_a if score_a > score_b else team_b)

        def side(row: dict[str, Any], score: float) -> dict[str, Any]:
            return {
                "yahoo_team_key": row["yahoo_team_key"],
                "franchise_id": row["franchise_id"],
                "historical_team_name": row["historical_team_name"],
                "mapping_status": row["mapping_status"],
                "score": score,
            }

        bracket_type = raw.get("bracket_type")
        weeks[week].append({
            "season": 2021,
            "week": week,
            "matchup_id": f"2021-w{week:02d}-{pair[0]:02d}-{pair[1]:02d}",
            "status": "final",
            "is_playoffs": week >= PLAYOFF_START[2021],
            "is_consolation": (bracket_type == "placement") if week >= PLAYOFF_START[2021] else None,
            "team_a": side(team_a, score_a),
            "team_b": side(team_b, score_b),
            "winner_franchise_id": winner["franchise_id"] if winner else None,
            "winner_historical_name": winner["historical_team_name"] if winner else None,
            "tie": tie,
            "margin": round(abs(score_a - score_b), 2),
            "source": yahoo_source["source_type"],
            "verified": True,
        })
    recovered = [week for week, matchups in weeks.items() if matchups]
    if recovered != list(range(1, 17)) or len(seen) != 78:
        raise ValueError(f"2021 authenticated archive must contain 78 matchups across Weeks 1-16; got {len(seen)}")
    return {
        "schema_version": 1,
        "season": 2021,
        "league_key": "406.l.12928",
        "generated_at": generated_at,
        "source": {
            "type": yahoo_source["source_type"],
            "url": yahoo_source["source_url"],
            "coverage_status": "verified_complete_authenticated_archive",
            "verified_on": str(yahoo_source["verified_on"]),
        },
        "coverage": {
            "available_weeks": recovered,
            "recovered_weeks": recovered,
            "complete": True,
        },
        "weeks": [
            {"week": week, "matchups": sorted(matchups, key=lambda game: game["matchup_id"])}
            for week, matchups in weeks.items()
        ],
    }


def apply_2021_canonical_fallback(summary: dict[str, Any], generated_at: str,
                                  *, write_outputs: bool = True) -> dict[str, Any]:
    """Combine the commissioner-supplied Yahoo table with verified manual coverage."""
    season = next(
        item for item in yaml.safe_load(SEASONS_PATH.read_text(encoding="utf-8"))["seasons"]
        if item["year"] == 2021
    )
    playoffs = next(
        item for item in yaml.safe_load(PLAYOFFS_PATH.read_text(encoding="utf-8"))["playoffs"]
        if item["season"] == 2021
    )
    draft = next(
        item for item in yaml.safe_load(DRAFTS_PATH.read_text(encoding="utf-8"))["drafts"]
        if item["year"] == 2021
    )
    yahoo_source = yaml.safe_load(YAHOO_2021_SOURCE_PATH.read_text(encoding="utf-8"))
    source_rows = yahoo_source["standings"]
    canonical_by_rank = {row["rank"]: row for row in season["standings"]}
    standings = []
    for source_row in source_rows:
        canonical = canonical_by_rank[source_row["rank"]]
        row = {
            "rank": source_row["rank"],
            "yahoo_team_key": f"406.l.12928.t.{source_row['yahoo_team_id']}",
            "yahoo_team_id": source_row["yahoo_team_id"],
            "franchise_id": source_row.get("franchise_id"),
            "historical_team_name": source_row["yahoo_team_name"],
            "mapping_status": "verified" if source_row.get("franchise_id") else "unresolved",
            "wins": source_row["wins"],
            "losses": source_row["losses"],
            "ties": source_row["ties"],
            "win_percentage": round(
                (source_row["wins"] + 0.5 * source_row["ties"])
                / (source_row["wins"] + source_row["losses"] + source_row["ties"]),
                6,
            ),
            "points_for": source_row["points_for"],
            "points_against": source_row["points_against"],
            "streak": source_row["streak"],
            "playoff_seed": source_row.get("playoff_seed"),
            "playoff_finish": source_row.get("playoff_finish"),
        }
        for field in ("wins", "losses", "ties", "points_for", "points_against"):
            if source_row[field] != canonical[field]:
                raise ValueError(f"2021 Yahoo standings conflict at rank {source_row['rank']}: {field}")
        standings.append(row)
    unresolved = sorted(row["historical_team_name"] for row in standings if not row.get("franchise_id"))
    expected_weeks = 16
    scored_playoff_games = sum(
        game.get("team_one_score") is not None and game.get("team_two_score") is not None
        for game in playoffs["games"]
    )

    source = {
        "type": yahoo_source["source_type"],
        "url": yahoo_source["source_url"],
        "coverage_status": "complete_final_standings",
        "verified_on": str(yahoo_source["verified_on"]),
    }
    standings_payload = {
        "schema_version": 1,
        "season": 2021,
        "league_key": "406.l.12928",
        "generated_at": generated_at,
        "source": source,
        "standings": standings,
    }
    teams_payload = {
        "schema_version": 1,
        "season": 2021,
        "league_key": "406.l.12928",
        "generated_at": generated_at,
        "source": source,
        "teams": [
            {key: row[key] for key in (
                "yahoo_team_key", "yahoo_team_id", "franchise_id", "historical_team_name", "mapping_status"
            )}
            for row in sorted(standings, key=lambda item: item["yahoo_team_id"])
        ],
    }
    weeks_payload = build_2021_weeks(yahoo_source, standings, generated_at)
    if write_outputs:
        write_json(OUTPUT_ROOT / "2021" / "standings.json", standings_payload)
        write_json(OUTPUT_ROOT / "2021" / "teams.json", teams_payload)
        write_json(OUTPUT_ROOT / "2021" / "weeks.json", weeks_payload)

    summary["sections"].update({
        "standings": {
            "status": "complete",
            "coverage_type": "commissioner_supplied_yahoo_archive",
            "rows": len(standings),
            "expected": season["team_count"],
            "yahoo_rows": len(standings),
            "source_files": ["_data/yahoo_history/2021.yml", "_data/seasons.yml"],
        },
        "teams": {
            "status": "complete",
            "coverage_type": "commissioner_supplied_yahoo_archive",
            "rows": len(standings),
            "expected": season["team_count"],
            "resolved_franchises": len(standings) - len(unresolved),
            "source_files": ["_data/yahoo_history/2021.yml", "_data/franchises.yml"],
        },
        "weekly_matchups": {
            "status": "complete",
            "coverage_type": "commissioner_authenticated_yahoo_archive",
            "weeks": 16,
            "expected_weeks": expected_weeks,
            "games": 78,
            "all_scores_present": True,
            "expected_weeks_basis": "14 verified regular-season games plus two verified playoff rounds",
            "source_files": ["_data/yahoo_history/2021.yml"],
        },
        "playoffs": {
            "status": "complete",
            "coverage_type": "commissioner_authenticated_yahoo_archive",
            "games": len(playoffs["games"]),
            "scored_games": scored_playoff_games,
            "all_scores_present": scored_playoff_games == len(playoffs["games"]),
            "source_files": ["_data/yahoo_history/2021.yml", "_data/playoffs.yml", "_data/champions.yml"],
            "classification_note": "Yahoo verifies the championship and consolation brackets; structured seeds follow Yahoo where the preserved bracket image conflicts.",
        },
        "draft": {
            "status": "partial",
            "coverage_type": "google_site_verified_images",
            "picks": 0,
            "rounds_visible": draft["rounds"],
            "draft_order_slots": len(draft["draft_order"]),
            "result_assets": len(draft["results_assets"]),
            "pick_data_status": draft["pick_data_status"],
            "source_files": ["_data/drafts.yml", "assets/img/drafts/2021/"],
        },
    })
    summary["franchise_mapping"] = {
        "status": "partial",
        "resolved": len(standings) - len(unresolved),
        "unresolved_names": unresolved,
        "yahoo_team_keys_recovered": len(standings),
    }
    summary.update({
        "weeks_expected": expected_weeks,
        "weeks_fetched": 16,
        "matchups_expected": 78,
        "matchups_fetched": 78,
        "roster_weeks_fetched": 0,
        "unresolved_franchise_mappings": unresolved,
        "confidence": "high_results_complete_identity",
        "recovery_level": "A",
        "yahoo_route_status": "authenticated_archive_recovered",
        "routes_checked": [
            "https://football.fantasysports.yahoo.com/league/rtgffl264552026/2021",
            "https://football.fantasysports.yahoo.com/2021/f1/12928",
            "https://football.fantasysports.yahoo.com/2021/f1/12928/standings",
            "https://football.fantasysports.yahoo.com/archive/nfl/2021/12928",
        ],
        "route_observation": "The public route requires Yahoo authentication; the commissioner-authenticated archive supplied complete Weeks 1-16 results.",
    })
    return summary


def backfill_season(client: ArchiveClient, season: dict[str, Any], sections: set[str],
                    generated_at: str, refresh: bool, include_rosters: bool,
                    failures: list[dict[str, Any]]) -> dict[str, Any]:
    year = int(season["season"])
    game_key, league_id = str(season["game_key"]), str(season["league_id"])
    base_url = f"https://football.fantasysports.yahoo.com/{year}/f1/{league_id}"
    output_dir = OUTPUT_ROOT / str(year)
    key_map, name_map = mappings_for(season)
    summary: dict[str, Any] = {
        "season": year,
        "league_key": season["league_key"],
        "team_count_expected": season.get("number_of_teams"),
        "sections": {},
    }
    print(f"{year}: starting {', '.join(sorted(sections))}")

    if "league" in sections:
        league = payload_base(season, generated_at)
        league["league"] = {
            "name": season.get("league_name"),
            "game_key": game_key,
            "league_id": league_id,
            "team_count": season.get("number_of_teams"),
            "finished": season.get("finished"),
            "previous_league_key": season.get("previous_league_key"),
            "next_league_key": season.get("next_league_key"),
        }
        write_json(output_dir / "league.json", league)
        summary["sections"]["league"] = {"status": "complete", "rows": 1}

    home_page = None
    if sections & {"standings", "matchups", "rosters"}:
        try:
            home_page = client.get(
                f"{base_url}?matchup_week=1&module=matchups&lhst=matchups",
                pathlib.Path(str(year)) / "matchups-week-01.html",
                refresh=refresh,
            )
        except Exception as error:  # noqa: BLE001 - sanitized continuation is intentional
            failures.append(safe_failure(year, "archive_home", error))

    standings: list[dict[str, Any]] = []
    if "standings" in sections and home_page:
        try:
            standings = parse_standings(
                home_page, season=year, game_key=game_key, league_id=league_id, mappings=key_map
            )
            for row in standings:
                if row["yahoo_team_key"] not in key_map:
                    row["franchise_id"] = name_map.get(row["historical_team_name"].casefold())
                    row["mapping_status"] = "verified" if row["franchise_id"] else "unresolved"
                    key_map[row["yahoo_team_key"]] = row["franchise_id"]
            payload = payload_base(season, generated_at)
            payload["standings"] = standings
            write_json(output_dir / "standings.json", payload)
            teams_payload = payload_base(season, generated_at)
            teams_payload["teams"] = [
                {key: row[key] for key in (
                    "yahoo_team_key", "yahoo_team_id", "franchise_id", "historical_team_name", "mapping_status"
                )}
                for row in sorted(standings, key=lambda item: item["yahoo_team_id"])
            ]
            write_json(output_dir / "teams.json", teams_payload)
            expected = season.get("number_of_teams")
            status = "complete" if expected == len(standings) else "partial"
            summary["sections"]["standings"] = {"status": status, "rows": len(standings), "expected": expected}
            summary["sections"]["teams"] = {"status": status, "rows": len(standings), "expected": expected}
        except Exception as error:  # noqa: BLE001
            failures.append(safe_failure(year, "standings", error))
            summary["sections"]["standings"] = {"status": "unavailable", "rows": 0}
    elif "standings" in sections:
        summary["sections"]["standings"] = {"status": "unavailable", "rows": 0}
        summary["sections"]["teams"] = {"status": "unavailable", "rows": 0}

    if "matchups" in sections and home_page:
        weeks = parse_available_weeks(home_page)
        recovered: list[dict[str, Any]] = []
        for week in weeks:
            try:
                print(f"{year}: matchup week {week}/{weeks[-1]}")
                page = home_page if week == 1 and not refresh else client.get(
                    f"{base_url}?matchup_week={week}&module=matchups&lhst=matchups",
                    pathlib.Path(str(year)) / f"matchups-week-{week:02d}.html",
                    refresh=refresh,
                )
                games = parse_matchups(
                    page,
                    season=year,
                    week=week,
                    game_key=game_key,
                    league_id=league_id,
                    mappings=key_map,
                    playoff_start_week=PLAYOFF_START.get(year),
                )
                recovered.append({"week": week, "matchups": games})
            except Exception as error:  # noqa: BLE001
                failures.append(safe_failure(year, f"matchups_week_{week}", error))
        payload = payload_base(season, generated_at)
        payload["coverage"] = {
            "available_weeks": weeks,
            "recovered_weeks": [item["week"] for item in recovered],
            "complete": bool(weeks) and len(recovered) == len(weeks),
        }
        payload["weeks"] = recovered
        write_json(output_dir / "weeks.json", payload)
        game_count = sum(len(item["matchups"]) for item in recovered)
        summary["sections"]["weekly_matchups"] = {
            "status": "complete" if payload["coverage"]["complete"] else ("partial" if recovered else "unavailable"),
            "weeks": len(recovered),
            "expected_weeks": len(weeks),
            "games": game_count,
            "all_scores_present": all(
                game["team_a"]["score"] is not None and game["team_b"]["score"] is not None
                for item in recovered for game in item["matchups"]
            ),
        }
        playoff_games = [
            game for item in recovered for game in item["matchups"] if game["is_playoffs"]
        ]
        summary["sections"]["playoffs"] = {
            "status": "complete" if payload["coverage"]["complete"] and playoff_games else ("partial" if playoff_games else "unavailable"),
            "games": len(playoff_games),
            "all_scores_present": bool(playoff_games) and all(
                game["team_a"]["score"] is not None and game["team_b"]["score"] is not None for game in playoff_games
            ),
            "classification_note": "Yahoo weekly archive identifies playoff weeks; consolation classification is not inferred.",
        }
    elif "matchups" in sections:
        payload = payload_base(season, generated_at)
        payload["coverage"] = {"available_weeks": [], "recovered_weeks": [], "complete": False}
        payload["weeks"] = []
        write_json(output_dir / "weeks.json", payload)
        summary["sections"]["weekly_matchups"] = {
            "status": "unavailable", "weeks": 0, "expected_weeks": 0, "games": 0, "all_scores_present": False,
        }
        summary["sections"]["playoffs"] = {
            "status": "unavailable", "games": 0, "all_scores_present": False,
            "classification_note": "Yahoo weekly archive is unavailable without an accessible scoreboard.",
        }

    if "draft" in sections:
        try:
            print(f"{year}: draft")
            page = client.get(f"{base_url}/draftresults", pathlib.Path(str(year)) / "draft.html", refresh=refresh)
            picks = parse_draft(page, season=year, game_key=game_key, league_id=league_id, mappings_by_name=name_map)
            payload = payload_base(season, generated_at)
            payload["coverage"] = {"status": "complete_public_draft_board", "picks": len(picks)}
            payload["picks"] = picks
            write_json(output_dir / "draft.json", payload)
            summary["sections"]["draft"] = {"status": "complete", "picks": len(picks)}
        except Exception as error:  # noqa: BLE001
            failures.append(safe_failure(year, "draft", error))
            summary["sections"]["draft"] = {"status": "unavailable", "picks": 0}

    if "transactions" in sections:
        transactions: list[dict[str, Any]] = []
        seen_offsets: set[int] = set()
        offset: int | None = 0
        transaction_failed = False
        while offset is not None and offset not in seen_offsets and len(seen_offsets) < 100:
            seen_offsets.add(offset)
            try:
                print(f"{year}: transactions offset {offset}")
                cache_name = "transactions.html" if offset == 0 else f"transactions-{offset:04d}.html"
                url = f"{base_url}/transactions" if offset == 0 else f"{base_url}/transactions?transactionsfilter=all&count={offset}"
                page = client.get(url, pathlib.Path(str(year)) / cache_name, refresh=refresh)
                transactions.extend(parse_transactions(
                    page, season=year, game_key=game_key, league_id=league_id, mappings=key_map, offset=offset
                ))
                offset = next_transaction_offset(page)
            except Exception as error:  # noqa: BLE001
                failures.append(safe_failure(year, f"transactions_offset_{offset}", error))
                transaction_failed = True
                break
        payload = payload_base(season, generated_at)
        payload["coverage"] = {
            "status": "partial" if transaction_failed and transactions else ("unavailable" if transaction_failed else "complete"),
            "pages_fetched": len(seen_offsets),
            "transactions": len(transactions),
            "pagination_complete": not transaction_failed and offset is None,
        }
        payload["transactions"] = transactions
        write_json(output_dir / "transactions.json", payload)
        summary["sections"]["transactions"] = {
            "status": payload["coverage"]["status"],
            "rows": len(transactions),
            "pages": len(seen_offsets),
        }

    if include_rosters and standings:
        roster_rows: list[dict[str, Any]] = []
        weeks = parse_available_weeks(home_page or "")
        for week in weeks:
            for team in sorted(standings, key=lambda item: item["yahoo_team_id"]):
                try:
                    team_id = team["yahoo_team_id"]
                    page = client.get(
                        f"{base_url}/{team_id}/team?week={week}",
                        pathlib.Path(str(year)) / "rosters" / f"team-{team_id:02d}-week-{week:02d}.html",
                        refresh=refresh,
                    )
                    roster_rows.extend(parse_roster(
                        page,
                        season=year,
                        week=week,
                        team_key=team["yahoo_team_key"],
                        franchise_id=team["franchise_id"],
                        historical_team_name=team["historical_team_name"],
                    ))
                except Exception as error:  # noqa: BLE001
                    failures.append(safe_failure(year, f"roster_w{week}_t{team['yahoo_team_id']}", error))
        payload = payload_base(season, generated_at)
        payload["coverage"] = {
            "status": "complete" if len(roster_rows) and not any(
                item["season"] == year and item["section"].startswith("roster_") for item in failures
            ) else ("partial" if roster_rows else "unavailable"),
            "warning": "Public roster pages are archived only when their season/week identity is verified by the parser.",
        }
        payload["player_weeks"] = roster_rows
        write_json(output_dir / "rosters.json", payload)
        summary["sections"]["rosters"] = {"status": payload["coverage"]["status"], "player_rows": len(roster_rows)}
        summary["sections"]["player_weekly_points"] = {"status": payload["coverage"]["status"], "player_rows": len(roster_rows)}
    else:
        summary["sections"]["rosters"] = {"status": "not_requested", "player_rows": 0}
        summary["sections"]["player_weekly_points"] = {"status": "not_requested", "player_rows": 0}

    summary["sections"].setdefault("transactions", {"status": "not_requested", "rows": 0, "pages": 0})
    unresolved = sorted({
        row["historical_team_name"] for row in standings if row.get("mapping_status") == "unresolved"
    })
    summary["franchise_mapping"] = {
        "status": "complete" if standings and not unresolved else ("partial" if standings else "unavailable"),
        "unresolved_names": unresolved,
    }
    matchup_summary = summary["sections"].get("weekly_matchups", {})
    roster_summary = summary["sections"].get("rosters", {})
    matchups_complete = matchup_summary.get("status") == "complete"
    summary.update({
        "weeks_expected": matchup_summary.get("expected_weeks") or None,
        "weeks_fetched": matchup_summary.get("weeks", 0),
        "matchups_expected": matchup_summary.get("games") if matchups_complete else None,
        "matchups_fetched": matchup_summary.get("games", 0),
        "roster_weeks_fetched": roster_summary.get("weeks", 0),
        "unresolved_franchise_mappings": unresolved,
        "confidence": (
            "partial_manual_only" if year == 2021
            else "high_results_partial_identity" if unresolved
            else "high_results_complete_identity"
        ),
    })
    if year == 2021 and not standings:
        apply_2021_canonical_fallback(summary, generated_at)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", default="2021-2025", help="Comma-separated years or inclusive ranges")
    parser.add_argument("--sections", default=",".join(sorted(DEFAULT_SECTIONS)))
    parser.add_argument("--include-rosters", action="store_true")
    parser.add_argument("--refresh", action="store_true", help="Ignore cached HTML")
    parser.add_argument("--delay", type=float, default=2.5, help="Minimum seconds between Yahoo requests")
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--generated-at", default=None, help="ISO-8601 timestamp override for reproducible fixtures")
    parser.add_argument(
        "--remap-only",
        action="store_true",
        help="Reapply canonical aliases to committed normalized files without network requests",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    seasons_by_year = {int(item["season"]): item for item in manifest.get("seasons", [])}
    try:
        selected = parse_seasons(args.seasons, set(seasons_by_year))
    except ValueError as error:
        parser.error(str(error))
    sections = {item.strip() for item in args.sections.split(",") if item.strip()}
    unsupported = sections - {"league", "standings", "matchups", "draft", "transactions", "rosters"}
    if unsupported:
        parser.error(f"unsupported section(s): {', '.join(sorted(unsupported))}")
    if args.remap_only:
        changed = remap_committed_history(selected)
        print(f"Historical remap complete: {changed} file(s) updated")
        return
    include_rosters = args.include_rosters or "rosters" in sections
    generated_at = args.generated_at or utc_now()
    client = ArchiveClient(CACHE_ROOT, delay_seconds=max(0.5, args.delay), max_retries=max(0, args.max_retries))
    failures: list[dict[str, Any]] = []
    summaries = [
        backfill_season(client, seasons_by_year[year], sections, generated_at, args.refresh, include_rosters, failures)
        for year in selected
    ]
    completeness = {
        "schema_version": 1,
        "generated_at": generated_at,
        "source": "official_yahoo_public_archive",
        "scope": {"league_started": 2021, "completed_seasons": sorted(COMPLETED_SEASONS)},
        "coverage_scopes": coverage_scopes(),
        "seasons": summaries,
        "failures": failures,
        "publication_policy": "Only verified normalized rows may unlock derived records; partial and unavailable categories remain labeled.",
    }
    write_json(OUTPUT_ROOT / "completeness.json", completeness)
    print(f"Backfill complete: {len(summaries)} season(s), {len(failures)} sanitized failure(s)")
    for summary in summaries:
        weekly = summary["sections"].get("weekly_matchups", {})
        print(f"- {summary['season']}: {weekly.get('weeks', 0)} weeks, {weekly.get('games', 0)} matchups")
    if failures:
        print("Some sections remain partial; see history/completeness.json", file=sys.stderr)


if __name__ == "__main__":
    main()
