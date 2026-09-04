"""Build the sanitized 2026 live-season experience from normalized Yahoo data."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "_data" / "generated"
OUTPUT = GENERATED / "live_season.json"
WIRE_OUTPUT = GENERATED / "league_wire.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected an object")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a mapping")
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == serialized:
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(path)


def iso_timestamp(value: object) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if text.isdigit():
        return datetime.fromtimestamp(int(text), tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def franchise_indexes(franchises_data: dict[str, Any], season: int) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_id: dict[str, dict[str, Any]] = {}
    by_key: dict[str, dict[str, Any]] = {}
    for franchise in franchises_data.get("franchises", []):
        if franchise.get("status") != "active":
            continue
        by_id[franchise["franchise_id"]] = franchise
        key = ((franchise.get("yahoo") or {}).get("team_keys") or {}).get(str(season))
        if key:
            by_key[str(key)] = franchise
    return by_id, by_key


def identity(franchise: dict[str, Any], display_name: str | None = None) -> dict[str, Any]:
    branding = franchise.get("branding") or {}
    return {
        "franchise_id": franchise["franchise_id"],
        "display_name": display_name or franchise["name"],
        "canonical_name": franchise["name"],
        "short_name": franchise.get("short_name") or franchise["name"],
        "path": f"/teams/{franchise['slug']}/",
        "identity_image": branding.get("identity_image"),
        "identity_alt": branding.get("identity_alt"),
        "primary_color": branding.get("primary_color"),
    }


def _record_text(row: dict[str, Any] | None) -> str:
    if not row:
        return "0–0–0"
    return f"{row.get('wins', 0)}–{row.get('losses', 0)}–{row.get('ties', 0)}"


def _status(value: object) -> str:
    normalized = str(value or "").casefold()
    if normalized in {"postevent", "final", "complete", "completed"}:
        return "final"
    if normalized in {"midevent", "in_progress", "in progress", "live"}:
        return "live"
    return "upcoming"


def normalize_matchups(
    matchups_data: dict[str, Any],
    standings_data: dict[str, Any],
    rosters_data: dict[str, Any],
    by_key: dict[str, dict[str, Any]],
    h2h_data: dict[str, Any],
) -> list[dict[str, Any]]:
    standings = {row.get("team_key"): row for row in standings_data.get("standings", [])}
    rosters = {row.get("team_key"): row.get("players", []) for row in rosters_data.get("teams", [])}
    h2h = {row.get("pair_id"): row for row in h2h_data.get("pairs", [])}
    normalized: list[dict[str, Any]] = []
    for raw in matchups_data.get("matchups", []):
        if not isinstance(raw.get("teams"), list) or len(raw["teams"]) != 2:
            continue
        teams = []
        for source in raw["teams"]:
            franchise = by_key.get(source.get("team_key"))
            if not franchise:
                teams = []
                break
            standing = standings.get(source.get("team_key"))
            team = identity(franchise, source.get("team_name"))
            team.update(
                {
                    "team_key": source.get("team_key"),
                    "team_id": source.get("team_id"),
                    "record": source.get("record") or _record_text(standing),
                    "score": source.get("score"),
                    "projected_score": source.get("projected_score"),
                    "roster": rosters.get(source.get("team_key"), []),
                }
            )
            teams.append(team)
        if len(teams) != 2:
            continue
        week = int(raw.get("week") or matchups_data.get("week") or 0)
        ordered_ids = sorted(team["franchise_id"] for team in teams)
        pair_id = "--".join(ordered_ids)
        series = h2h.get(pair_id)
        status = _status(raw.get("status"))
        winner_key = raw.get("winner_team_key") if status == "final" else None
        normalized.append(
            {
                "matchup_id": f"2026-w{week:02d}-{ordered_ids[0]}--{ordered_ids[1]}",
                "week": week,
                "status": status,
                "status_label": {"final": "Final", "live": "In Progress", "upcoming": "Upcoming"}[status],
                "is_playoffs": bool(raw.get("is_playoffs")),
                "is_consolation": bool(raw.get("is_consolation")),
                "is_tied": bool(raw.get("is_tied")) if status == "final" else False,
                "winner_franchise_id": next((team["franchise_id"] for team in teams if team["team_key"] == winner_key), None),
                "teams": teams,
                "historical_context": (
                    {
                        "series_path": series.get("share_path"),
                        "meetings": series.get("meetings"),
                        "wins_a": series.get("wins_a"),
                        "wins_b": series.get("wins_b"),
                        "ties": series.get("ties"),
                        "franchise_a_id": (series.get("franchise_a") or {}).get("franchise_id"),
                        "most_recent_meeting": series.get("most_recent_meeting"),
                        "current_series_streak": series.get("current_series_streak"),
                    }
                    if series
                    else None
                ),
            }
        )
    return sorted(normalized, key=lambda row: row["matchup_id"])


def weekly_facts(matchups: list[dict[str, Any]], standings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = [
        row
        for row in matchups
        if row["status"] in {"live", "final"}
        and all(isinstance(team.get("score"), (int, float)) for team in row["teams"])
        and any(team["score"] > 0 for team in row["teams"])
    ]
    if not scored:
        return []
    team_scores = [(team["score"], team, game) for game in scored for team in game["teams"]]
    highest = max(team_scores, key=lambda item: (item[0], item[1]["franchise_id"]))
    lowest = min(team_scores, key=lambda item: (item[0], item[1]["franchise_id"]))
    decided = [game for game in scored if game["teams"][0]["score"] != game["teams"][1]["score"]]
    biggest = max(decided, key=lambda game: abs(game["teams"][0]["score"] - game["teams"][1]["score"])) if decided else None
    closest = min(decided, key=lambda game: abs(game["teams"][0]["score"] - game["teams"][1]["score"])) if decided else None
    combined = max(scored, key=lambda game: sum(team["score"] for team in game["teams"]))
    facts = [
        {"fact_id": "highest-score", "label": "Highest score", "value": highest[0], "franchise_id": highest[1]["franchise_id"], "display_name": highest[1]["display_name"]},
        {"fact_id": "lowest-score", "label": "Lowest score", "value": lowest[0], "franchise_id": lowest[1]["franchise_id"], "display_name": lowest[1]["display_name"]},
        {"fact_id": "highest-combined", "label": "Highest combined score", "value": round(sum(team["score"] for team in combined["teams"]), 2), "matchup_id": combined["matchup_id"]},
    ]
    if biggest:
        facts.append({"fact_id": "biggest-win", "label": "Biggest lead", "value": round(abs(biggest["teams"][0]["score"] - biggest["teams"][1]["score"]), 2), "matchup_id": biggest["matchup_id"]})
    if closest:
        facts.append({"fact_id": "closest-game", "label": "Closest game", "value": round(abs(closest["teams"][0]["score"] - closest["teams"][1]["score"]), 2), "matchup_id": closest["matchup_id"]})
    streak_rows = [row for row in standings if isinstance((row.get("streak") or {}).get("value"), int)]
    if streak_rows:
        longest = max(streak_rows, key=lambda row: ((row.get("streak") or {}).get("value", 0), str(row.get("franchise_id"))))
        facts.append({"fact_id": "longest-active-streak", "label": "Longest active streak", "value": (longest.get("streak") or {}).get("value"), "streak_type": (longest.get("streak") or {}).get("type"), "franchise_id": longest.get("franchise_id"), "display_name": longest.get("display_name")})
    return facts


def record_watch_events(matchups: list[dict[str, Any]], thresholds_data: dict[str, Any]) -> list[dict[str, Any]]:
    thresholds = thresholds_data.get("thresholds") or {}
    franchise_thresholds = {row.get("franchise_id"): row for row in thresholds_data.get("franchises", [])}
    events: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(event: dict[str, Any]) -> None:
        if event["event_id"] not in seen:
            seen.add(event["event_id"])
            events.append(event)

    for game in matchups:
        if game["status"] == "upcoming":
            continue
        final = game["status"] == "final"
        scores = [team.get("score") for team in game["teams"]]
        if not all(isinstance(score, (int, float)) for score in scores) or not any(score > 0 for score in scores):
            continue
        for team in game["teams"]:
            score = team["score"]
            level = None
            threshold = None
            if final and score > thresholds.get("highest_weekly_score", math.inf):
                level, threshold = "New verified league record", thresholds["highest_weekly_score"]
            elif final and score >= thresholds.get("tenth_highest_weekly_score", math.inf):
                level, threshold = "Top-10 performance", thresholds["tenth_highest_weekly_score"]
            elif final and score >= thresholds.get("twenty_fifth_highest_weekly_score", math.inf):
                level, threshold = "Top-25 performance", thresholds["twenty_fifth_highest_weekly_score"]
            elif not final and score > 0:
                target = thresholds.get("twenty_fifth_highest_weekly_score")
                if isinstance(target, (int, float)) and 0 < target - score <= 20:
                    level, threshold = "Record Watch", target
            if level:
                difference = round(threshold - score, 2) if not final else None
                add({
                    "event_id": f"{game['matchup_id']}:{team['franchise_id']}:weekly-score:{level.casefold().replace(' ', '-')}",
                    "type": "weekly_score",
                    "level": level,
                    "final": final,
                    "franchise_id": team["franchise_id"],
                    "display_name": team["display_name"],
                    "value": score,
                    "threshold": threshold,
                    "difference": difference,
                    "message": (f"{team['display_name']} posted {score:.2f}, clearing the verified 2021–2025 benchmark of {threshold:.2f}." if final else f"{team['display_name']} is {difference:.2f} points from the verified Top-25 cutoff."),
                })
            personal = franchise_thresholds.get(team["franchise_id"], {}).get("highest_weekly_score")
            if final and isinstance(personal, (int, float)) and score > personal:
                add({"event_id": f"{game['matchup_id']}:{team['franchise_id']}:franchise-high", "type": "franchise_weekly_high", "level": "New franchise high", "final": True, "franchise_id": team["franchise_id"], "display_name": team["display_name"], "value": score, "threshold": personal, "difference": None, "message": f"{team['display_name']} set a verified franchise weekly high at {score:.2f}."})

        if not final:
            continue
        high, low = max(scores), min(scores)
        margin, combined = round(high - low, 2), round(high + low, 2)
        winner = next((team for team in game["teams"] if team["score"] == high), None)
        loser = next((team for team in game["teams"] if team["score"] == low), None)
        if winner and margin > thresholds.get("largest_margin", math.inf):
            add({"event_id": f"{game['matchup_id']}:league-margin", "type": "victory_margin", "level": "New verified margin record", "final": True, "franchise_id": winner["franchise_id"], "display_name": winner["display_name"], "value": margin, "threshold": thresholds["largest_margin"], "difference": None, "message": f"{winner['display_name']} won by {margin:.2f}, a new verified league margin record."})
        elif winner and margin >= thresholds.get("tenth_largest_margin", math.inf):
            add({"event_id": f"{game['matchup_id']}:top-ten-margin", "type": "victory_margin", "level": "Top-10 margin", "final": True, "franchise_id": winner["franchise_id"], "display_name": winner["display_name"], "value": margin, "threshold": thresholds["tenth_largest_margin"], "difference": None, "message": f"{winner['display_name']}'s {margin:.2f}-point win reached the verified Top-10 margin range."})
        if combined > thresholds.get("highest_combined_matchup_score", math.inf):
            add({"event_id": f"{game['matchup_id']}:combined-score", "type": "combined_score", "level": "New verified combined-score record", "final": True, "franchise_id": None, "display_name": None, "value": combined, "threshold": thresholds["highest_combined_matchup_score"], "difference": None, "message": f"The matchup combined for {combined:.2f}, a new verified league record."})
        if loser and loser["score"] > thresholds.get("highest_losing_score", math.inf):
            add({"event_id": f"{game['matchup_id']}:{loser['franchise_id']}:losing-score", "type": "highest_losing_score", "level": "New verified losing-score record", "final": True, "franchise_id": loser["franchise_id"], "display_name": loser["display_name"], "value": loser["score"], "threshold": thresholds["highest_losing_score"], "difference": None, "message": f"{loser['display_name']}'s {loser['score']:.2f} became the highest verified losing score."})
    return sorted(events, key=lambda event: (not event["final"], event["event_id"]))


def build_league_wire(week: int | None, matchups: list[dict[str, Any]], facts: list[dict[str, Any]], record_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for event in record_events[:2]:
        items.append({"headline_id": f"record:{event['event_id']}", "category": "Record Watch", "headline": event["level"], "detail": event["message"], "week": week, "source": "normalized_yahoo_and_verified_history", "path": "/records/"})
    fact_by_id = {row["fact_id"]: row for row in facts}
    highest = fact_by_id.get("highest-score")
    if highest:
        items.append({"headline_id": f"week-{week}:high-score", "category": "Week in Review", "headline": f"{highest['display_name']} leads Week {week} scoring", "detail": f"The week's current high is {highest['value']:.2f} points.", "week": week, "source": "normalized_yahoo", "path": f"/2026/week/{week}/"})
    if not items and matchups:
        projected = [game for game in matchups if all(isinstance(team.get("projected_score"), (int, float)) for team in game["teams"])]
        featured = min(projected, key=lambda game: abs(game["teams"][0]["projected_score"] - game["teams"][1]["projected_score"])) if projected else matchups[0]
        names = [team["display_name"] for team in featured["teams"]]
        items.append({"headline_id": f"week-{week}:slate", "category": "League Wire", "headline": f"Week {week} slate is set", "detail": f"{names[0]} meets {names[1]} in the featured matchup.", "week": week, "source": "normalized_yahoo", "path": f"/2026/week/{week}/"})
    return items[:5]


def franchise_summaries(by_id: dict[str, dict[str, Any]], standings: list[dict[str, Any]], matchups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    standings_by_id = {row.get("franchise_id"): row for row in standings}
    summaries = []
    for franchise_id, franchise in sorted(by_id.items()):
        standing = standings_by_id.get(franchise_id)
        game = next((row for row in matchups if any(team["franchise_id"] == franchise_id for team in row["teams"])), None)
        opponent = None
        if game:
            opponent = next(team for team in game["teams"] if team["franchise_id"] != franchise_id)
        row = identity(franchise)
        row.update({
            "rank": standing.get("rank") if standing else None,
            "record": _record_text(standing),
            "points_for": standing.get("points_for") if standing else None,
            "points_against": standing.get("points_against") if standing else None,
            "streak": standing.get("streak") if standing else None,
            "current_matchup": ({"matchup_id": game["matchup_id"], "status": game["status"], "opponent": opponent, "week": game["week"]} if game and game["status"] != "upcoming" else None),
            "next_opponent": ({"franchise_id": opponent["franchise_id"], "display_name": opponent["display_name"], "path": opponent["path"], "week": game["week"]} if game and game["status"] == "upcoming" else None),
        })
        summaries.append(row)
    return summaries


def build_live_payload(*, stale: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    site = load_yaml(ROOT / "_data" / "site.yml")
    season = int(site["current_season"])
    manifest = load_json(GENERATED / "manifest.json")
    source_current = manifest.get("status") == "ready" and manifest.get("season") == season
    source_timestamp = iso_timestamp(manifest.get("source_update_timestamp"))
    base = {
        "schema_version": 1,
        "season": season,
        "generated_at": source_timestamp,
        "data_status": "stale" if stale and source_current else ("ready" if source_current else "unavailable"),
        "freshness": {
            "status": "stale" if stale or not source_current else "current",
            "source_updated_at": source_timestamp if source_current else None,
            "label": "Last valid Yahoo snapshot" if stale and source_current else ("Updated from Yahoo" if source_current else "Live Yahoo data unavailable"),
        },
        "source": {
            "type": manifest.get("source") or "yahoo_fantasy_api",
            "normalized": True,
            "historical_archive_modified": False,
        },
        "current_week": None,
        "available_weeks": [],
        "league": None,
        "standings": [],
        "matchups": [],
        "featured_matchup": None,
        "weekly_facts": [],
        "record_watch": [],
        "league_wire": [],
        "franchise_summaries": [],
        "playoff_race": {"status": "not_calculated", "teams": [], "reason": "League tiebreakers and clinching rules are not yet fully deterministic."},
        "power_rankings": {"status": "unavailable", "week": None, "top_three": [], "biggest_riser": None, "biggest_faller": None},
        "picks": {"status": "unavailable", "week": None},
        "season_milestones": [],
    }
    if not source_current:
        return base, {"schema_version": 1, "season": season, "week": None, "generated_at": None, "coverage_status": "unavailable", "items": []}

    league_data = load_json(GENERATED / "league.json")
    standings_data = load_json(GENERATED / "standings.json")
    matchups_data = load_json(GENERATED / "matchups.json")
    rosters_data = load_json(GENERATED / "rosters.json")
    franchises_data = load_yaml(ROOT / "_data" / "franchises.yml")
    thresholds = load_json(GENERATED / "records" / "record_thresholds.json")
    h2h = load_json(GENERATED / "records" / "head_to_head.json")
    power = load_json(GENERATED / "power_rankings.json")
    picks = load_json(GENERATED / "picks.json")
    by_id, by_key = franchise_indexes(franchises_data, season)
    if len(by_id) != 12 or len(by_key) != 12:
        raise ValueError("all 12 active franchises require verified 2026 Yahoo team keys")

    standings = []
    for raw in standings_data.get("standings", []):
        franchise = by_key.get(raw.get("team_key"))
        if not franchise:
            raise ValueError(f"unresolved current Yahoo team key: {raw.get('team_key')}")
        row = identity(franchise, raw.get("team_name"))
        row.update({key: raw.get(key) for key in ("team_key", "team_id", "rank", "wins", "losses", "ties", "winning_percentage", "points_for", "points_against", "streak", "playoff_seed")})
        standings.append(row)
    standings.sort(key=lambda row: (row.get("rank") is None, row.get("rank") or 999, row["franchise_id"]))

    matchups = normalize_matchups(matchups_data, standings_data, rosters_data, by_key, h2h)
    facts = weekly_facts(matchups, standings)
    events = record_watch_events(matchups, thresholds)
    week = int(matchups_data.get("week") or (league_data.get("league") or {}).get("current_week") or 0) or None
    wire = build_league_wire(week, matchups, facts, events)
    projected_matchups = [game for game in matchups if all(isinstance(team.get("projected_score"), (int, float)) for team in game["teams"])]
    featured_matchup = min(projected_matchups, key=lambda game: (abs(game["teams"][0]["projected_score"] - game["teams"][1]["projected_score"]), game["matchup_id"])) if projected_matchups else (matchups[0] if matchups else None)

    power_current = power if power.get("season") == season and power.get("rankings") else None
    power_rankings = {
        "status": "ready" if power_current else "unavailable",
        "week": power_current.get("week") if power_current else None,
        "top_three": (power_current.get("rankings") or [])[:3] if power_current else [],
        "biggest_riser": None,
        "biggest_faller": None,
    }
    if power_current:
        movements = [row for row in power_current["rankings"] if isinstance(row.get("movement"), int)]
        if movements:
            power_rankings["biggest_riser"] = max(movements, key=lambda row: (row["movement"], row["franchise_id"]))
            power_rankings["biggest_faller"] = min(movements, key=lambda row: (row["movement"], row["franchise_id"]))

    league = league_data.get("league") or {}
    end_week = league.get("end_week")
    base.update({
        "current_week": week,
        "available_weeks": list(range(int(league.get("start_week") or 1), int(end_week or week or 1) + 1)),
        "league": league,
        "standings": standings,
        "matchups": matchups,
        "featured_matchup": featured_matchup,
        "weekly_facts": facts,
        "record_watch": events,
        "league_wire": wire,
        "franchise_summaries": franchise_summaries(by_id, standings, matchups),
        "power_rankings": power_rankings,
        "picks": {"status": "ready" if picks.get("season") == season and picks.get("current_week") else "unavailable", "week": (picks.get("current_week") or {}).get("week")},
        "season_milestones": ([{"milestone_id": f"week-{week}-opened", "label": f"Week {week} slate published", "week": week}] if week else []) + [{"milestone_id": event["event_id"], "label": event["level"], "week": week} for event in events if event["final"]],
    })
    wire_payload = {"schema_version": 1, "season": season, "week": week, "generated_at": source_timestamp, "coverage_status": "ready" if wire else "unavailable", "items": wire}
    return base, wire_payload


def persist_week(payload: dict[str, Any]) -> Path | None:
    week = payload.get("current_week")
    if payload.get("data_status") not in {"ready", "stale"} or not isinstance(week, int):
        return None
    snapshot = {
        "schema_version": 1,
        "season": payload["season"],
        "week": week,
        "generated_at": payload.get("generated_at"),
        "data_status": payload.get("data_status"),
        "freshness": payload.get("freshness"),
        "matchups": payload.get("matchups", []),
        "weekly_facts": payload.get("weekly_facts", []),
        "record_watch": payload.get("record_watch", []),
        "power_rankings": payload.get("power_rankings"),
    }
    path = GENERATED / "live" / str(payload["season"]) / f"week-{week:02d}.json"
    write_json(path, snapshot)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stale", action="store_true", help="Preserve current data but mark the source stale")
    parser.add_argument("--no-persist-week", action="store_true")
    args = parser.parse_args()
    payload, wire = build_live_payload(stale=args.stale)
    write_json(OUTPUT, payload)
    write_json(WIRE_OUTPUT, wire)
    week_path = None if args.no_persist_week else persist_week(payload)
    print(f"Built {payload['season']} live hub: {payload['data_status']}, {len(payload['matchups'])} matchups, {len(payload['record_watch'])} record alerts")
    if week_path:
        print(f"Updated {week_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
