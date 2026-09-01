"""Backfill sanitized Yahoo weekly history for verified Road to Glory leagues."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from pull_yahoo import refresh_access_token
from yahoo_history import (
    SCHEMA_VERSION,
    YahooHistoryClient,
    build_bench_scores,
    build_head_to_head,
    build_team_weeks,
    calculate_margins,
    calculate_streaks,
    extract_leagues,
    load_yaml,
    normalize_history_matchups,
    normalize_history_roster,
    resolve_franchise,
    write_json_if_changed,
)
from yahoo_normalize import normalize_teams


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data"
DEFAULT_HISTORY_ROOT = DATA / "generated" / "history"
DEFAULT_HEAD_TO_HEAD = DATA / "generated" / "head_to_head.json"


def required_environment() -> dict[str, str]:
    names = ("YAHOO_CLIENT_ID", "YAHOO_CLIENT_SECRET", "YAHOO_REFRESH_TOKEN")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    return {name: os.environ[name] for name in names}


def read_existing(path: Path, key: str) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return payload.get(key) or [] if isinstance(payload, dict) else []


def matchup_payload(
    *,
    season: int,
    league_key: str,
    expected_weeks: list[int],
    playoff_start_week: int | None,
    matchups: list[dict[str, Any]],
    failed_weeks: list[int],
) -> dict[str, Any]:
    fetched_weeks = sorted({row["week"] for row in matchups})
    missing_weeks = sorted(set(expected_weeks) - set(fetched_weeks))
    regular = [row for row in matchups if not row.get("is_playoffs")]
    scores_complete = bool(matchups) and all(
        row["team_a"].get("score") is not None and row["team_b"].get("score") is not None
        for row in matchups
    )
    mappings_complete = bool(matchups) and all(
        row[side].get("franchise_id") for row in matchups for side in ("team_a", "team_b")
    )
    expected_regular = [
        week for week in expected_weeks
        if playoff_start_week is None or week < playoff_start_week
    ]
    regular_weeks = {row["week"] for row in regular}
    regular_complete = bool(expected_regular) and set(expected_regular).issubset(regular_weeks) and all(
        row["team_a"].get("score") is not None and row["team_b"].get("score") is not None
        for row in regular
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "season": season,
        "league_key": league_key,
        "coverage": {
            "expected_weeks": expected_weeks,
            "fetched_weeks": fetched_weeks,
            "missing_weeks": missing_weeks,
            "failed_weeks": sorted(set(failed_weeks)),
            "playoff_start_week": playoff_start_week,
            "weekly_scores_complete": scores_complete,
            "franchise_mappings_complete": mappings_complete,
            "regular_season_complete": regular_complete,
            "playoff_scores_complete": bool(matchups) and scores_complete and any(row.get("is_playoffs") for row in matchups),
        },
        "matchups": sorted(matchups, key=lambda row: (row["week"], row["matchup_id"])),
    }


def roster_payload(
    *,
    season: int,
    league_key: str,
    expected_requests: int,
    completed_requests: int,
    player_weeks: list[dict[str, Any]],
    include_player_stats: bool,
) -> dict[str, Any]:
    bench_players = [row for row in player_weeks if row.get("starter_or_bench") == "bench"]
    selected_positions_complete = bool(player_weeks) and all(row.get("selected_position") for row in player_weeks)
    player_points_complete = include_player_stats and bool(player_weeks) and all(
        row.get("fantasy_points") is not None for row in player_weeks
    )
    bench_possible = (
        expected_requests > 0
        and completed_requests == expected_requests
        and selected_positions_complete
        and player_points_complete
        and bool(bench_players)
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "season": season,
        "league_key": league_key,
        "coverage": {
            "expected_team_weeks": expected_requests,
            "fetched_team_weeks": completed_requests,
            "rosters_complete": expected_requests > 0 and completed_requests == expected_requests,
            "selected_positions_complete": selected_positions_complete,
            "player_weekly_points_complete": player_points_complete,
            "bench_reconstruction_possible": bench_possible,
        },
        "player_weeks": sorted(
            player_weeks,
            key=lambda row: (row["week"], row.get("yahoo_team_key") or "", row.get("player_key") or ""),
        ),
        "bench_scores": build_bench_scores(player_weeks) if bench_possible else [],
    }


def fact_payload(
    season: int,
    matchups_document: dict[str, Any],
    team_weeks: list[dict[str, Any]],
) -> dict[str, Any]:
    complete = bool((matchups_document.get("coverage") or {}).get("regular_season_complete"))
    regular_scores = [row for row in team_weeks if not row.get("playoff") and row.get("score") is not None]
    facts: dict[str, Any] = {}
    if complete and regular_scores:
        highest = max(regular_scores, key=lambda row: (row["score"], row.get("historical_team_name") or ""))
        lowest = min(regular_scores, key=lambda row: (row["score"], row.get("historical_team_name") or ""))
        facts = {
            "highest_weekly_score": highest,
            "lowest_weekly_score": lowest,
            "margins": calculate_margins(matchups_document["matchups"]),
            "streaks": calculate_streaks(team_weeks),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "season": season,
        "coverage_status": "complete" if complete else "unavailable",
        "facts": facts,
        "notes": [] if complete else ["Weekly facts remain unpublished until regular-season coverage is complete."],
    }


def build_head_to_head_document(
    season_documents: list[dict[str, Any]],
) -> dict[str, Any]:
    complete_seasons = [
        doc["season"] for doc in season_documents
        if doc["coverage"].get("regular_season_complete") and doc["coverage"].get("franchise_mappings_complete")
    ]
    matchups = [row for doc in season_documents for row in doc.get("matchups") or [] if not row.get("is_playoffs")]
    pairs = build_head_to_head(matchups) if complete_seasons else []
    status = "complete" if season_documents and len(complete_seasons) == len(season_documents) else ("partial" if pairs else "unavailable")
    source_years = sorted(doc["season"] for doc in season_documents)
    label = (
        f"Verified Yahoo history: {min(source_years)}–{max(source_years)}"
        if status == "complete" and source_years
        else "Awaiting complete Yahoo weekly matchup history"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": None,
        "coverage": {
            "status": status,
            "label": label,
            "source_years": source_years,
            "complete_regular_seasons": sorted(complete_seasons),
            "games_counted": sum(pair["games"] for pair in pairs),
            "notes": [] if status == "complete" else [
                "No head-to-head result is published until complete weekly coverage and franchise mappings pass validation."
            ],
        },
        "pairs": pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-season", type=int, required=True)
    parser.add_argument("--end-season", type=int, required=True)
    parser.add_argument("--include-rosters", action="store_true")
    parser.add_argument("--include-player-stats", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--request-delay", type=float, default=0.25)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_HISTORY_ROOT)
    parser.add_argument("--head-to-head-output", type=Path, default=DEFAULT_HEAD_TO_HEAD)
    args = parser.parse_args()
    if args.start_season > args.end_season:
        raise SystemExit("start season must not be after end season")
    if args.include_player_stats:
        args.include_rosters = True

    environment = required_environment()
    token = refresh_access_token(
        environment["YAHOO_CLIENT_ID"],
        environment["YAHOO_CLIENT_SECRET"],
        environment["YAHOO_REFRESH_TOKEN"],
    )
    client = YahooHistoryClient(token, request_delay=args.request_delay)
    leagues = [
        row for row in load_yaml(DATA / "yahoo_leagues.yml")["leagues"]
        if row.get("verified") and args.start_season <= row["season"] <= args.end_season
    ]
    franchises = load_yaml(DATA / "franchises.yml")["franchises"]
    if not leagues:
        raise SystemExit("No verified Yahoo leagues exist in the requested range")

    season_documents: list[dict[str, Any]] = []
    for league in sorted(leagues, key=lambda row: row["season"]):
        season = league["season"]
        league_key = league["league_key"]
        season_dir = args.output_root / str(season)
        matchups_path = season_dir / "matchups.json"
        team_weeks_path = season_dir / "team_weeks.json"
        rosters_path = season_dir / "rosters.json"
        player_weeks_path = season_dir / "player_weeks.json"
        facts_path = season_dir / "facts.json"

        metadata_payload = client.get_json(f"league/{league_key}")
        metadata_rows = extract_leagues(metadata_payload)
        metadata = next((row for row in metadata_rows if row.get("league_key") == league_key), None)
        if not metadata:
            raise RuntimeError(f"Yahoo did not return metadata for verified league {season}")
        start_week = metadata.get("start_week") or 1
        end_week = metadata.get("end_week") or metadata.get("current_week")
        if not end_week or end_week < start_week:
            raise RuntimeError(f"Yahoo did not provide a usable week range for verified league {season}")
        expected_weeks = list(range(start_week, end_week + 1))

        teams_payload = client.get_json(f"league/{league_key}/teams")
        yahoo_teams = normalize_teams(teams_payload)["teams"]
        team_identities = []
        for team in yahoo_teams:
            mapping = resolve_franchise(
                season=season,
                team_key=team.get("team_key"),
                team_name=team.get("team_name"),
                franchises=franchises,
            )
            team_identities.append({
                "yahoo_team_key": team.get("team_key"),
                "historical_team_name": team.get("team_name"),
                **mapping,
            })

        existing = read_existing(matchups_path, "matchups") if args.resume else []
        by_week: dict[int, list[dict[str, Any]]] = {}
        for row in existing:
            by_week.setdefault(row["week"], []).append(row)
        failed_weeks: list[int] = []
        for week in expected_weeks:
            if args.resume and week in by_week:
                continue
            try:
                payload = client.get_json(f"league/{league_key}/scoreboard;week={week}")
                by_week[week] = normalize_history_matchups(
                    payload,
                    season=season,
                    league_key=league_key,
                    franchises=franchises,
                )
            except Exception as error:
                failed_weeks.append(week)
                print(f"warning: {season} week {week} scoreboard unavailable: {type(error).__name__}")
            checkpoint = matchup_payload(
                season=season,
                league_key=league_key,
                expected_weeks=expected_weeks,
                playoff_start_week=metadata.get("playoff_start_week"),
                matchups=[row for rows in by_week.values() for row in rows],
                failed_weeks=failed_weeks,
            )
            write_json_if_changed(matchups_path, checkpoint)

        matchups_document = matchup_payload(
            season=season,
            league_key=league_key,
            expected_weeks=expected_weeks,
            playoff_start_week=metadata.get("playoff_start_week"),
            matchups=[row for rows in by_week.values() for row in rows],
            failed_weeks=failed_weeks,
        )
        write_json_if_changed(matchups_path, matchups_document)
        team_weeks = build_team_weeks(matchups_document["matchups"])
        write_json_if_changed(team_weeks_path, {
            "schema_version": SCHEMA_VERSION,
            "season": season,
            "league_key": league_key,
            "coverage": matchups_document["coverage"],
            "team_weeks": team_weeks,
        })
        write_json_if_changed(facts_path, fact_payload(season, matchups_document, team_weeks))
        season_documents.append(matchups_document)

        if args.include_rosters:
            existing_players = read_existing(player_weeks_path, "player_weeks") if args.resume else []
            player_rows: dict[tuple[int, str], list[dict[str, Any]]] = {}
            for row in existing_players:
                player_rows.setdefault((row["week"], row.get("yahoo_team_key") or ""), []).append(row)
            completed_requests = len(player_rows)
            expected_requests = len(expected_weeks) * len(team_identities)
            for week in expected_weeks:
                for identity in team_identities:
                    team_key = identity.get("yahoo_team_key")
                    request_key = (week, team_key or "")
                    if not team_key or (args.resume and request_key in player_rows):
                        continue
                    resource = f"team/{team_key}/roster;week={week}"
                    if args.include_player_stats:
                        resource += f"/players/stats;type=week;week={week}"
                    try:
                        payload = client.get_json(resource)
                        player_rows[request_key] = normalize_history_roster(
                            payload,
                            season=season,
                            week=week,
                            team_identity=identity,
                        )
                        completed_requests += 1
                    except Exception as error:
                        print(f"warning: {season} week {week} roster unavailable: {type(error).__name__}")
                flattened = [row for rows in player_rows.values() for row in rows]
                document = roster_payload(
                    season=season,
                    league_key=league_key,
                    expected_requests=expected_requests,
                    completed_requests=completed_requests,
                    player_weeks=flattened,
                    include_player_stats=args.include_player_stats,
                )
                write_json_if_changed(player_weeks_path, document)
                grouped_rosters = []
                for (week_number, roster_team_key), rows in sorted(player_rows.items()):
                    identity = next(
                        (item for item in team_identities if item.get("yahoo_team_key") == roster_team_key),
                        {},
                    )
                    grouped_rosters.append({
                        "season": season,
                        "week": week_number,
                        "yahoo_team_key": roster_team_key,
                        "franchise_id": identity.get("franchise_id"),
                        "historical_team_name": identity.get("historical_team_name"),
                        "mapping_status": identity.get("mapping_status"),
                        "players": [{
                            "player_key": row.get("player_key"),
                            "player_name": row.get("player_name"),
                            "nfl_team": row.get("nfl_team"),
                            "primary_position": row.get("primary_position"),
                            "selected_position": row.get("selected_position"),
                            "status": row.get("status"),
                        } for row in rows],
                    })
                write_json_if_changed(rosters_path, {
                    "schema_version": SCHEMA_VERSION,
                    "season": season,
                    "league_key": league_key,
                    "coverage": document["coverage"],
                    "rosters": grouped_rosters,
                })

    head_to_head = build_head_to_head_document(season_documents)
    write_json_if_changed(args.head_to_head_output, head_to_head)
    print(
        f"Historical backfill complete: {len(season_documents)} seasons, "
        f"{sum(len(doc['matchups']) for doc in season_documents)} matchups, "
        f"{len(head_to_head['pairs'])} head-to-head pairs"
    )


if __name__ == "__main__":
    main()
