"""Validate the public 2026 live hub, weekly snapshot, and League Wire."""

from __future__ import annotations

import json
from numbers import Real
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "_data" / "generated"
LIVE_PATH = GENERATED / "live_season.json"
WIRE_PATH = GENERATED / "league_wire.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def numeric(value: object) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def validate(live: dict, wire: dict) -> list[str]:
    errors: list[str] = []
    if live.get("schema_version") != 1 or live.get("season") != 2026:
        errors.append("live_season.json must be schema version 1 for 2026")
    status = live.get("data_status")
    if status not in {"ready", "stale", "unavailable"}:
        errors.append("live data_status must be ready, stale, or unavailable")
    freshness = live.get("freshness") or {}
    if freshness.get("status") not in {"current", "stale"}:
        errors.append("live freshness must explicitly be current or stale")
    if status == "stale" and freshness.get("status") != "stale":
        errors.append("stale data must carry a stale freshness label")

    standings = live.get("standings") or []
    matchups = live.get("matchups") or []
    summaries = live.get("franchise_summaries") or []
    if status == "unavailable":
        if standings or matchups or live.get("record_watch"):
            errors.append("unavailable live data must not publish synthetic results")
        return errors

    if len(standings) != 12:
        errors.append("a ready/stale 2026 hub must contain 12 standings rows")
    if len(matchups) != 6:
        errors.append("a ready/stale current week must contain 6 matchups")
    if len(summaries) != 12:
        errors.append("the live franchise integration must contain 12 summaries")
    franchise_ids = [row.get("franchise_id") for row in standings]
    if None in franchise_ids or len(franchise_ids) != len(set(franchise_ids)):
        errors.append("standings franchise IDs must resolve uniquely")
    if set(franchise_ids) != {row.get("franchise_id") for row in summaries}:
        errors.append("standings and franchise summaries must cover the same franchises")

    matchup_ids: set[str] = set()
    participants: list[str] = []
    for game in matchups:
        matchup_id = game.get("matchup_id")
        if not matchup_id or matchup_id in matchup_ids:
            errors.append("matchup IDs must be present and unique")
        matchup_ids.add(matchup_id)
        teams = game.get("teams") or []
        if len(teams) != 2:
            errors.append(f"{matchup_id}: matchup must contain exactly two teams")
            continue
        participants.extend(row.get("franchise_id") for row in teams)
        for team in teams:
            if team.get("franchise_id") not in franchise_ids:
                errors.append(f"{matchup_id}: unresolved franchise")
            for field in ("score", "projected_score"):
                if team.get(field) is not None and not numeric(team[field]):
                    errors.append(f"{matchup_id}: {field} must be numeric or null")
        if game.get("status") == "final":
            scores = [row.get("score") for row in teams]
            if not all(numeric(value) for value in scores):
                errors.append(f"{matchup_id}: final matchup needs numeric scores")
            elif scores[0] == scores[1]:
                if not game.get("is_tied") or game.get("winner_franchise_id") is not None:
                    errors.append(f"{matchup_id}: final tie is inconsistent")
            else:
                expected = teams[0]["franchise_id"] if scores[0] > scores[1] else teams[1]["franchise_id"]
                if game.get("winner_franchise_id") != expected:
                    errors.append(f"{matchup_id}: winner does not match the verified score")
        elif game.get("winner_franchise_id") is not None:
            errors.append(f"{matchup_id}: non-final matchup cannot publish a winner")
    if sorted(participants) != sorted(franchise_ids):
        errors.append("every franchise must appear exactly once in the current slate")

    event_ids: set[str] = set()
    for event in live.get("record_watch") or []:
        event_id = event.get("event_id")
        if not event_id or event_id in event_ids:
            errors.append("Record Watch event IDs must be stable and unique")
        event_ids.add(event_id)
        if not event.get("final") and event.get("level") != "Record Watch":
            errors.append(f"{event_id}: projections/live scores cannot promote historical records")

    if wire.get("schema_version") != 1 or wire.get("season") != 2026:
        errors.append("league_wire.json must be schema version 1 for 2026")
    if wire.get("items") != live.get("league_wire"):
        errors.append("standalone League Wire and live hub must agree")
    for item in wire.get("items") or []:
        if item.get("source") not in {"normalized_yahoo", "normalized_yahoo_and_verified_history"}:
            errors.append("League Wire items require deterministic source provenance")
        if not str(item.get("path") or "").startswith("/"):
            errors.append("League Wire items require a local source path")

    week = live.get("current_week")
    if not isinstance(week, int):
        errors.append("ready/stale live data requires an integer current week")
    else:
        snapshot = GENERATED / "live" / "2026" / f"week-{week:02d}.json"
        route = ROOT / "_live_weeks" / f"2026-week-{week:02d}.md"
        if not snapshot.is_file():
            errors.append(f"missing normalized current-week snapshot: {snapshot}")
        if not route.is_file():
            errors.append(f"missing current-week route: {route}")
    return errors


def main() -> None:
    live, wire = load(LIVE_PATH), load(WIRE_PATH)
    errors = validate(live, wire)
    if errors:
        raise SystemExit("Live-season validation failed:\n- " + "\n- ".join(errors))
    print(
        f"Validated 2026 live hub: {live['data_status']}, "
        f"{len(live.get('standings') or [])} teams, {len(live.get('matchups') or [])} matchups, "
        f"{len(live.get('record_watch') or [])} Record Watch events"
    )


if __name__ == "__main__":
    main()
