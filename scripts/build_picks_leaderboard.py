"""Validate weekly matchup picks and build the season Picks Leaderboard."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from .voting_common import (
        BallotError,
        ROOT,
        generated_at_from_rows,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        public_aggregate_fingerprint,
        select_latest_valid,
        write_json,
    )
except ImportError:
    from voting_common import (
        BallotError,
        ROOT,
        generated_at_from_rows,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        public_aggregate_fingerprint,
        select_latest_valid,
        write_json,
    )


OUTPUT_PATH = ROOT / "_data" / "generated" / "picks.json"
ARCHIVE_ROOT = ROOT / "_data" / "picks"


def canonical_matchups_from_yahoo(
    matchups_data: dict[str, Any],
    manifest: dict[str, Any],
    season: int,
    franchises_data: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    if manifest.get("status") != "ready" or manifest.get("season") != season:
        return [], "stale_yahoo_data"
    week = matchups_data.get("week")
    if not isinstance(week, int):
        return [], "missing_yahoo_week"
    team_key_to_franchise: dict[str, dict[str, Any]] = {}
    for franchise in franchises_data.get("franchises") or []:
        team_key = ((franchise.get("yahoo") or {}).get("team_keys") or {}).get(str(season))
        if team_key:
            team_key_to_franchise[team_key] = franchise

    canonical = []
    for source in matchups_data.get("matchups") or []:
        teams = source.get("teams") or []
        if len(teams) != 2:
            continue
        resolved = [team_key_to_franchise.get(team.get("team_key")) for team in teams]
        if any(item is None for item in resolved):
            continue
        first, second = resolved
        participants = [first["franchise_id"], second["franchise_id"]]
        winner_key = source.get("winner_team_key")
        winner = team_key_to_franchise.get(winner_key) if winner_key else None
        is_tied = bool(source.get("is_tied"))
        complete = source.get("status") == "postevent"
        matchup_slug = "-vs-".join(sorted(participants))
        canonical.append(
            {
                "matchup_id": f"{season}-week-{week:02d}-{matchup_slug}",
                "season": season,
                "week": week,
                "status": source.get("status"),
                "participants": [
                    {
                        "franchise_id": franchise["franchise_id"],
                        "display_name": franchise["name"],
                        "path": f"/teams/{franchise['slug']}/",
                        "identity_image": (franchise.get("branding") or {}).get("identity_image"),
                    }
                    for franchise in resolved
                ],
                "winner_franchise_id": winner["franchise_id"] if complete and winner and not is_tied else None,
                "winner_status": "verified" if complete and winner and not is_tied else ("no_contest" if complete and is_tied else "pending"),
            }
        )
    return canonical, "ready" if canonical else "unresolved_yahoo_matchups"


def rows_to_ballots(imported: dict[str, Any], matchup_ids: set[str]) -> list[dict[str, Any]]:
    if isinstance(imported.get("ballots"), list):
        return imported["ballots"]
    ballots = []
    metadata = {"owner_id", "submitted_at", "season", "week", "exported_at", "generated_at"}
    for row in imported.get("rows") or []:
        picks = [
            {"matchup_id": key, "franchise_id": value}
            for key, value in row.items()
            if key not in metadata and value not in (None, "")
        ]
        ballots.append(
            {
                "owner_id": row.get("owner_id"),
                "submitted_at": row.get("submitted_at"),
                "season": row.get("season"),
                "week": row.get("week"),
                "picks": picks,
            }
        )
    return ballots


def validate_pick_ballot(ballot: dict[str, Any], matchup_by_id: dict[str, dict[str, Any]]) -> None:
    picks = ballot.get("picks")
    if not isinstance(picks, list):
        raise BallotError("matchup ballot must contain picks")
    matchup_ids = [pick.get("matchup_id") for pick in picks if isinstance(pick, dict)]
    if len(matchup_ids) != len(picks) or len(set(matchup_ids)) != len(matchup_ids):
        raise BallotError("matchup ballot contains duplicate or malformed picks")
    if set(matchup_ids) != set(matchup_by_id):
        raise BallotError("matchup ballot must select every required matchup exactly once")
    for pick in picks:
        matchup = matchup_by_id.get(pick.get("matchup_id"))
        if matchup is None:
            raise BallotError("unknown matchup_id")
        participants = {item["franchise_id"] for item in matchup["participants"]}
        if pick.get("franchise_id") not in participants:
            raise BallotError("pick is not a participant in the matchup")


def aggregate_week(
    ballots: list[dict[str, Any]],
    matchups: list[dict[str, Any]],
    owners: dict[str, dict[str, Any]],
    *,
    deadline: object = None,
    results_visible: bool = False,
    publish_manager_picks: bool = False,
) -> tuple[dict[str, Any], int, int]:
    matchup_by_id = {item["matchup_id"]: item for item in matchups}
    selected, rejected = select_latest_valid(
        ballots,
        set(owners),
        lambda ballot: validate_pick_ballot(ballot, matchup_by_id),
        parse_deadline(deadline),
    )
    votes: defaultdict[str, Counter[str]] = defaultdict(Counter)
    manager_results = []
    for ballot in selected:
        correct = incorrect = no_contests = pending = 0
        public_picks = []
        for pick in ballot["picks"]:
            matchup = matchup_by_id[pick["matchup_id"]]
            votes[pick["matchup_id"]][pick["franchise_id"]] += 1
            if matchup["winner_status"] == "verified":
                result = "correct" if pick["franchise_id"] == matchup["winner_franchise_id"] else "incorrect"
                correct += int(result == "correct")
                incorrect += int(result == "incorrect")
            elif matchup["winner_status"] == "no_contest":
                result = "no_contest"
                no_contests += 1
            else:
                result = "pending"
                pending += 1
            if publish_manager_picks:
                public_picks.append({**pick, "result": result})
        decided = correct + incorrect
        manager_results.append(
            {
                "owner_id": ballot["owner_id"],
                "display_name": owners[ballot["owner_id"]]["display_name"],
                "correct": correct,
                "incorrect": incorrect,
                "no_contests": no_contests,
                "pending": pending,
                "total_picks": decided,
                "accuracy": round(correct / decided, 3) if decided else None,
                "weekly_win": False,
                "picks": public_picks,
            }
        )
    eligible = [item for item in manager_results if item["total_picks"]]
    if eligible:
        best = max(item["correct"] for item in eligible)
        for item in eligible:
            item["weekly_win"] = item["correct"] == best
    manager_results.sort(key=lambda item: (-item["correct"], -(item["accuracy"] or 0), item["display_name"].casefold()))

    rendered_matchups = []
    for matchup in matchups:
        item = dict(matchup)
        total_votes = sum(votes[matchup["matchup_id"]].values())
        if results_visible:
            item["pick_results"] = [
                {
                    "franchise_id": participant["franchise_id"],
                    "vote_count": votes[matchup["matchup_id"]][participant["franchise_id"]],
                    "percentage": round(votes[matchup["matchup_id"]][participant["franchise_id"]] / total_votes, 3) if total_votes else 0.0,
                }
                for participant in matchup["participants"]
            ]
        else:
            item["pick_results"] = []
        item["ballots_counted"] = total_votes
        rendered_matchups.append(item)
    week = matchups[0]["week"] if matchups else None
    season = matchups[0]["season"] if matchups else None
    selection_totals = [
        {
            "matchup_id": matchup["matchup_id"],
            "picks": [
                {
                    "franchise_id": participant["franchise_id"],
                    "vote_count": votes[matchup["matchup_id"]][participant["franchise_id"]],
                }
                for participant in matchup["participants"]
            ],
        }
        for matchup in matchups
    ]
    return (
        {
            "season": season,
            "week": week,
            "matchups": rendered_matchups,
            "manager_results": manager_results,
            "selection_totals": selection_totals,
        },
        len(selected),
        rejected,
    )


def build_leaderboard(weekly_results: list[dict[str, Any]], owners: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    for week in weekly_results:
        for result in week.get("manager_results") or []:
            owner_id = result["owner_id"]
            total = totals.setdefault(
                owner_id,
                {
                    "owner_id": owner_id,
                    "display_name": owners[owner_id]["display_name"],
                    "correct": 0,
                    "incorrect": 0,
                    "no_contests": 0,
                    "total_picks": 0,
                    "weekly_wins": 0,
                },
            )
            for field in ("correct", "incorrect", "no_contests", "total_picks"):
                total[field] += int(result.get(field) or 0)
            total["weekly_wins"] += int(bool(result.get("weekly_win")))
    entries = []
    for total in totals.values():
        total["accuracy"] = round(total["correct"] / total["total_picks"], 3) if total["total_picks"] else None
        entries.append(total)
    entries.sort(key=lambda item: (-item["correct"], -(item["accuracy"] or 0), item["display_name"].casefold()))
    for rank, item in enumerate(entries, start=1):
        item["rank"] = rank
    return entries


def build_output(
    imported: dict[str, Any] | None,
    matchups_data: dict[str, Any],
    manifest: dict[str, Any],
    site_data: dict[str, Any],
    franchises_data: dict[str, Any],
    owners_data: dict[str, Any],
    *,
    existing: dict[str, Any] | None = None,
    deadline: object = None,
    community_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    imported = imported or {}
    season = int(imported.get("season") or site_data["current_season"])
    matchups, matchup_status = canonical_matchups_from_yahoo(matchups_data, manifest, season, franchises_data)
    owners = owner_index(owners_data)
    ballots = rows_to_ballots(imported, {item["matchup_id"] for item in matchups})
    current = None
    accepted = rejected = 0
    if matchups:
        current, accepted, rejected = aggregate_week(
            ballots,
            matchups,
            owners,
            deadline=deadline or imported.get("closes_at"),
            results_visible=bool(imported.get("results_visible")),
            publish_manager_picks=bool(imported.get("publish_manager_picks")),
        )
        pick_config = (community_data or {}).get("pickem") or {}
        current.update(
            {
                "state": imported.get("state") or pick_config.get("status") or "upcoming",
                "form_url": imported.get("form_url") or pick_config.get("form_url"),
                "lock_at": deadline or imported.get("closes_at") or pick_config.get("lock_at"),
                "results_visibility": (
                    "public" if imported.get("results_visible") else "hidden_before_lock"
                ),
                "manager_picks_visibility": (
                    "public" if imported.get("publish_manager_picks") else "private"
                ),
            }
        )
    elif ballots:
        rejected = len(ballots)
    weekly_results = list((existing or {}).get("weekly_results") or [])
    weekly_results.sort(key=lambda item: (item["season"], item["week"]))
    archived_current = next(
        (
            item for item in weekly_results
            if current and (item.get("season"), item.get("week")) == (current.get("season"), current.get("week"))
        ),
        None,
    )
    if archived_current and not accepted:
        current = archived_current
    leaderboard = build_leaderboard(weekly_results, owners)
    return {
        "schema_version": 1,
        "season": season,
        "week": current.get("week") if current else None,
        "generated_at": generated_at_from_rows(imported, ballots),
        "source": {
            "type": "sanitized_google_forms_export_and_normalized_yahoo" if ballots else "normalized_yahoo",
            "coverage_status": "published" if accepted or archived_current else ("ready_for_ballots" if matchups else "unavailable"),
            "matchup_status": matchup_status,
            "accepted_ballots": accepted,
            "rejected_ballots": rejected,
            "superseded_ballots": len(ballots) - accepted - rejected,
            "duplicate_policy": "latest_valid_submission_before_deadline",
            "winner_source": "verified_completed_yahoo_matchups_only",
        },
        "scoring": {"correct": 1, "incorrect": 0, "confidence_points": False},
        "current_week": current,
        "weekly_results": weekly_results,
        "leaderboard": leaderboard,
    }


def pick_archive_path(season: int, week: int, root: Path = ARCHIVE_ROOT) -> Path:
    return root / str(season) / f"week-{week:02d}.json"


def finalized_week_payload(
    payload: dict[str, Any], *, generated_at: str | None, state: str
) -> dict[str, Any]:
    current = payload.get("current_week") or {}
    if state not in {"locked", "final"}:
        raise ValueError("Pick'em archive state must be locked or final")
    if not isinstance(current.get("week"), int) or not current.get("matchups"):
        raise ValueError("Pick'em finalization requires a canonical matchup week")
    if payload.get("source", {}).get("accepted_ballots", 0) < 1:
        raise ValueError("Pick'em finalization requires at least one valid ballot")
    manager_results = current.get("manager_results") or []
    if state != "final":
        manager_results = []
    aggregate = current.get("selection_totals") or []
    return {
        "schema_version": 1,
        "season": current["season"],
        "week": current["week"],
        "published_at": generated_at,
        "state": state,
        "lock_at": current.get("lock_at"),
        "results_visibility": current.get("results_visibility"),
        "manager_picks_visibility": current.get("manager_picks_visibility"),
        "ballots_counted": payload["source"]["accepted_ballots"],
        "aggregate_fingerprint": public_aggregate_fingerprint(aggregate),
        "matchups": current["matchups"],
        "manager_results": manager_results,
        "weekly_winners": [
            {
                "owner_id": row["owner_id"],
                "display_name": row["display_name"],
                "correct": row["correct"],
                "incorrect": row["incorrect"],
            }
            for row in manager_results
            if row.get("weekly_win")
        ],
        "source": {
            "type": "sanitized_google_forms_export_and_normalized_yahoo",
            "winner_source": "verified_completed_yahoo_matchups_only",
        },
    }


def persist_finalized_week(
    week: dict[str, Any], root: Path = ARCHIVE_ROOT, *, override: bool = False
) -> Path:
    path = pick_archive_path(week["season"], week["week"], root)
    serialized = json.dumps(week, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing == week:
            return path
        scoring_update = (
            existing.get("state") == "locked"
            and week.get("state") == "final"
            and existing.get("aggregate_fingerprint") == week.get("aggregate_fingerprint")
            and existing.get("ballots_counted") == week.get("ballots_counted")
        )
        if not scoring_update and not override:
            raise ValueError(f"refusing to overwrite finalized Pick'em selections: {path}")
        if existing.get("state") == "final" and not override:
            raise ValueError(f"refusing to overwrite finalized Pick'em results: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")
    return path


def load_finalized_weeks(
    season: int, root: Path = ARCHIVE_ROOT
) -> list[dict[str, Any]]:
    weeks = []
    for path in sorted((root / str(season)).glob("week-*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("season") == season and value.get("state") in {"locked", "final"}:
            weeks.append(value)
    return sorted(weeks, key=lambda item: item["week"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Sanitized CSV or JSON export")
    parser.add_argument("--existing", type=Path, help="Existing public picks archive")
    parser.add_argument("--deadline", help="ISO-8601 voting deadline override")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    imported = load_import(args.input) if args.input else None
    site_data = load_yaml("site.yml")
    season = int((imported or {}).get("season") or site_data["current_season"])
    existing = (
        json.loads(args.existing.read_text(encoding="utf-8"))
        if args.existing
        else {"weekly_results": load_finalized_weeks(season)}
    )
    matchups = json.loads((ROOT / "_data" / "generated" / "matchups.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "_data" / "generated" / "manifest.json").read_text(encoding="utf-8"))
    payload = build_output(
        imported,
        matchups,
        manifest,
        site_data,
        load_yaml("franchises.yml"),
        load_yaml("owners.yml"),
        existing=existing,
        deadline=args.deadline,
        community_data=load_yaml("community.yml"),
    )
    write_json(args.output, payload)
    print(f"Wrote {args.output}: {len(payload['leaderboard'])} managers in the Picks Leaderboard")


if __name__ == "__main__":
    main()
