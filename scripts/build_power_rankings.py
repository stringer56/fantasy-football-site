"""Validate manager ballots and build deterministic weekly Power Rankings."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

try:
    from .voting_common import (
        BallotError,
        ROOT,
        active_franchises,
        generated_at_from_rows,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid,
        write_json,
    )
except ImportError:
    from voting_common import (
        BallotError,
        ROOT,
        active_franchises,
        generated_at_from_rows,
        load_import,
        load_yaml,
        owner_index,
        parse_deadline,
        select_latest_valid,
        write_json,
    )


OUTPUT_PATH = ROOT / "_data" / "generated" / "power_rankings.json"
HISTORY_OUTPUT_PATH = ROOT / "_data" / "generated" / "power_rankings_history.json"
ARCHIVE_ROOT = ROOT / "_data" / "power_rankings"


def rows_to_ballots(imported: dict[str, Any], team_count: int) -> list[dict[str, Any]]:
    if isinstance(imported.get("ballots"), list):
        return imported["ballots"]
    ballots = []
    for row in imported.get("rows") or []:
        ballots.append(
            {
                "owner_id": row.get("owner_id"),
                "submitted_at": row.get("submitted_at"),
                "season": row.get("season"),
                "week": row.get("week"),
                "rankings": [row.get(f"rank_{rank}") for rank in range(1, team_count + 1)],
            }
        )
    return ballots


def validate_ballot(ballot: dict[str, Any], active_ids: set[str]) -> None:
    rankings = ballot.get("rankings")
    if not isinstance(rankings, list) or len(rankings) != len(active_ids):
        raise BallotError("ranking ballot must contain every active franchise")
    if any(not isinstance(item, str) for item in rankings):
        raise BallotError("ranking entries must be franchise IDs")
    if len(set(rankings)) != len(rankings):
        raise BallotError("ranking ballot contains a duplicate franchise")
    if set(rankings) != active_ids:
        raise BallotError("ranking ballot contains missing or unknown franchises")


def aggregate_rankings(
    ballots: list[dict[str, Any]],
    franchises: list[dict[str, Any]],
    owners: dict[str, dict[str, Any]],
    *,
    deadline: object = None,
    previous_rankings: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], int, int]:
    active_ids = {item["franchise_id"] for item in franchises}
    selected, rejected = select_latest_valid(
        ballots,
        set(owners),
        lambda ballot: validate_ballot(ballot, active_ids),
        parse_deadline(deadline),
    )
    previous = {item["franchise_id"]: item["rank"] for item in previous_rankings or []}
    totals = {
        item["franchise_id"]: {
            "franchise_id": item["franchise_id"],
            "display_name": item["name"],
            "path": f"/teams/{item['slug']}/",
            "identity_image": (item.get("branding") or {}).get("identity_image"),
            "total_points": 0,
            "rank_sum": 0,
            "first_place_votes": 0,
        }
        for item in franchises
    }
    team_count = len(franchises)
    for ballot in selected:
        for rank, franchise_id in enumerate(ballot["rankings"], start=1):
            totals[franchise_id]["total_points"] += team_count - rank + 1
            totals[franchise_id]["rank_sum"] += rank
            totals[franchise_id]["first_place_votes"] += int(rank == 1)
    entries = []
    for item in totals.values():
        item["average_rank"] = round(item.pop("rank_sum") / len(selected), 3) if selected else None
        item["ballots_counted"] = len(selected)
        entries.append(item)
    if selected:
        entries.sort(
            key=lambda item: (
                -item["total_points"],
                -item["first_place_votes"],
                item["average_rank"],
                item["franchise_id"],
            )
        )
        prior_key = None
        prior_rank = None
        for position, item in enumerate(entries, start=1):
            tie_key = (
                item["total_points"],
                item["first_place_votes"],
                item["average_rank"],
            )
            rank = prior_rank if tie_key == prior_key else position
            item["rank"] = rank
            item["previous_rank"] = previous.get(item["franchise_id"])
            item["movement"] = previous[item["franchise_id"]] - rank if item["franchise_id"] in previous else None
            item["ranking_points"] = item["total_points"]
            item["votes_received"] = item["ballots_counted"]
            prior_key = tie_key
            prior_rank = rank
        rank_counts = {rank: sum(row["rank"] == rank for row in entries) for rank in {row["rank"] for row in entries}}
        for item in entries:
            item["is_tied"] = rank_counts[item["rank"]] > 1
    else:
        entries = []
    return entries, len(selected), rejected


def build_output(
    imported: dict[str, Any] | None,
    franchises_data: dict[str, Any],
    owners_data: dict[str, Any],
    *,
    deadline: object = None,
    previous: dict[str, Any] | None = None,
    community_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    imported = imported or {}
    franchises = active_franchises(franchises_data)
    owners = owner_index(owners_data)
    ballots = rows_to_ballots(imported, len(franchises))
    rankings, accepted, rejected = aggregate_rankings(
        ballots,
        franchises,
        owners,
        deadline=deadline,
        previous_rankings=(previous or {}).get("rankings") or [],
    )
    voting = (community_data or {}).get("power_rankings") or {}
    return {
        "schema_version": 1,
        "season": int(imported.get("season") or 2026),
        "week": int(imported["week"]) if imported.get("week") not in (None, "") else None,
        "generated_at": generated_at_from_rows(imported, ballots),
        "source": {
            "type": "sanitized_google_forms_export" if ballots else "none",
            "coverage_status": "complete" if accepted == len(owners) and accepted else ("partial" if accepted else "unavailable"),
            "accepted_ballots": accepted,
            "rejected_ballots": rejected,
            "superseded_ballots": len(ballots) - accepted - rejected,
            "duplicate_policy": "latest_valid_submission_before_deadline",
            "ranking_input": "manager_ballots_only",
        },
        "scoring": {
            "team_count": len(franchises),
            "first_place_points": len(franchises),
            "last_place_points": 1,
            "tie_breakers": ["total_points", "first_place_votes", "average_rank"],
            "unresolved_tie_policy": "shared_competition_rank",
        },
        "ballots_counted": accepted,
        "rankings": rankings,
        "voting": {
            "status": voting.get("status") or "upcoming",
            "form_url": voting.get("form_url"),
            "closes_at": deadline or voting.get("closes_at"),
        },
    }


def finalized_week_payload(
    payload: dict[str, Any], standings_by_id: dict[str, int | None] | None = None
) -> dict[str, Any]:
    if not isinstance(payload.get("week"), int) or not payload.get("rankings"):
        raise ValueError("a finalized Power Ranking requires a week and published rankings")
    return {
        "schema_version": 1,
        "season": payload["season"],
        "week": payload["week"],
        "generated_at": payload.get("generated_at"),
        "results_status": "final",
        "source": payload["source"],
        "scoring": payload["scoring"],
        "ballots_counted": payload["ballots_counted"],
        "rankings": [
            {
                "season": payload["season"],
                "week": payload["week"],
                "franchise_id": row["franchise_id"],
                "display_name": row["display_name"],
                "path": row["path"],
                "identity_image": row["identity_image"],
                "rank": row["rank"],
                "previous_rank": row.get("previous_rank"),
                "movement": row.get("movement"),
                "average_rank": row["average_rank"],
                "ranking_points": row["ranking_points"],
                "first_place_votes": row["first_place_votes"],
                "votes_received": row["votes_received"],
                "is_tied": bool(row.get("is_tied")),
                "yahoo_standings_rank": (standings_by_id or {}).get(row["franchise_id"]),
            }
            for row in payload["rankings"]
        ],
    }


def archive_path(season: int, week: int, root: Path = ARCHIVE_ROOT) -> Path:
    return root / str(season) / f"week-{week:02d}.json"


def persist_finalized_week(
    payload: dict[str, Any], root: Path = ARCHIVE_ROOT, *, override: bool = False,
    standings_by_id: dict[str, int | None] | None = None,
) -> Path:
    final = finalized_week_payload(payload, standings_by_id)
    path = archive_path(final["season"], final["week"], root)
    serialized = json.dumps(final, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != serialized and not override:
            raise ValueError(f"refusing to overwrite finalized Power Rankings: {path}")
        if existing != serialized:
            path.write_text(serialized, encoding="utf-8")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")
    return path


def load_finalized_weeks(season: int, root: Path = ARCHIVE_ROOT) -> list[dict[str, Any]]:
    weeks = []
    for path in sorted((root / str(season)).glob("week-*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("season") == season and value.get("results_status") == "final":
            weeks.append(value)
    return sorted(weeks, key=lambda item: item["week"])


def previous_finalized(season: int, week: int | None, root: Path = ARCHIVE_ROOT) -> dict[str, Any] | None:
    candidates = [item for item in load_finalized_weeks(season, root) if week is None or item["week"] < week]
    return candidates[-1] if candidates else None


def _fact(label: str, value: Any, rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    return {
        "metric": metric,
        "label": label,
        "value": value,
        "leaders": [
            {"franchise_id": row["franchise_id"], "display_name": row["display_name"], "path": row["path"]}
            for row in rows
        ],
    }


def build_history(season: int, franchises: list[dict[str, Any]], weeks: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(weeks, key=lambda item: item["week"])
    by_id = {item["franchise_id"]: item for item in franchises}
    series: dict[str, list[dict[str, Any]]] = {franchise_id: [] for franchise_id in by_id}
    for week in ordered:
        for row in week.get("rankings", []):
            if row.get("franchise_id") in series:
                series[row["franchise_id"]].append(
                    {
                        "week": week["week"],
                        "rank": row["rank"],
                        "previous_rank": row.get("previous_rank"),
                        "movement": row.get("movement"),
                        "average_rank": row["average_rank"],
                        "ranking_points": row["ranking_points"],
                        "first_place_votes": row["first_place_votes"],
                        "yahoo_standings_rank": row.get("yahoo_standings_rank"),
                    }
                )

    summaries = []
    for franchise_id, rows in sorted(series.items()):
        franchise = by_id[franchise_id]
        ranks = [row["rank"] for row in rows]
        averages = [row["average_rank"] for row in rows]
        summary = {
            "franchise_id": franchise_id,
            "display_name": franchise["name"],
            "short_name": franchise.get("short_name") or franchise["name"],
            "path": f"/teams/{franchise['slug']}/",
            "identity_image": (franchise.get("branding") or {}).get("identity_image"),
            "primary_color": (franchise.get("branding") or {}).get("primary_color"),
            "current_rank": ranks[-1] if ranks else None,
            "peak_rank": min(ranks) if ranks else None,
            "lowest_rank": max(ranks) if ranks else None,
            "average_rank": round(sum(averages) / len(averages), 3) if averages else None,
            "weeks_at_number_one": sum(rank == 1 for rank in ranks),
            "weeks_in_top_three": sum(rank <= 3 for rank in ranks),
            "stability": round(statistics.pstdev(ranks), 3) if len(ranks) > 1 else (0.0 if ranks else None),
            "biggest_rise": max((row.get("movement") for row in rows if isinstance(row.get("movement"), int)), default=None),
            "biggest_fall": min((row.get("movement") for row in rows if isinstance(row.get("movement"), int)), default=None),
            "weeks": rows,
        }
        summaries.append(summary)

    populated = [row for row in summaries if row["weeks"]]
    facts = []
    if populated:
        def winners(key: str, target: Any) -> list[dict[str, Any]]:
            return [row for row in populated if row[key] == target]

        most_one = max(row["weeks_at_number_one"] for row in populated)
        high_avg = min(row["average_rank"] for row in populated)
        low_avg = max(row["average_rank"] for row in populated)
        most_stable = min(row["stability"] for row in populated)
        most_volatile = max(row["stability"] for row in populated)
        top_three = max(row["weeks_in_top_three"] for row in populated)
        peak = min(row["peak_rank"] for row in populated)
        low_rank = max(row["lowest_rank"] for row in populated)
        facts.extend([
            _fact("Most weeks ranked #1", most_one, winners("weeks_at_number_one", most_one), "most_weeks_number_one"),
            _fact("Highest average ranking", high_avg, winners("average_rank", high_avg), "highest_average_rank"),
            _fact("Lowest average ranking", low_avg, winners("average_rank", low_avg), "lowest_average_rank"),
            _fact("Most stable ranking", most_stable, winners("stability", most_stable), "most_stable"),
            _fact("Most volatile ranking", most_volatile, winners("stability", most_volatile), "most_volatile"),
            _fact("Highest peak rank", peak, winners("peak_rank", peak), "highest_peak"),
            _fact("Lowest rank", low_rank, winners("lowest_rank", low_rank), "lowest_rank"),
            _fact("Most weeks in Top 3", top_three, winners("weeks_in_top_three", top_three), "weeks_in_top_three"),
        ])
        rises = [row for row in populated if row["biggest_rise"] is not None]
        falls = [row for row in populated if row["biggest_fall"] is not None]
        if rises:
            biggest_rise = max(row["biggest_rise"] for row in rises)
            facts.append(_fact("Biggest single-week rise", biggest_rise, [row for row in rises if row["biggest_rise"] == biggest_rise], "biggest_rise"))
        if falls:
            biggest_fall = min(row["biggest_fall"] for row in falls)
            facts.append(_fact("Biggest single-week fall", abs(biggest_fall), [row for row in falls if row["biggest_fall"] == biggest_fall], "biggest_fall"))

    week_numbers = [row["week"] for row in ordered]
    missing = [week for week in range(min(week_numbers), max(week_numbers) + 1) if week not in week_numbers] if week_numbers else []
    return {
        "schema_version": 1,
        "season": season,
        "generated_at": ordered[-1].get("generated_at") if ordered else None,
        "coverage_status": "complete_to_latest_finalized_week" if ordered else "unavailable",
        "finalized_weeks": week_numbers,
        "missing_weeks": missing,
        "weeks": ordered,
        "franchises": summaries,
        "season_facts": facts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Sanitized CSV or JSON export")
    parser.add_argument("--previous", type=Path, help="Previous generated ranking JSON")
    parser.add_argument("--deadline", help="ISO-8601 voting deadline override")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    imported = load_import(args.input) if args.input else None
    season = int((imported or {}).get("season") or 2026)
    week = int(imported["week"]) if imported and imported.get("week") not in (None, "") else None
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else previous_finalized(season, week)
    payload = build_output(
        imported,
        load_yaml("franchises.yml"),
        load_yaml("owners.yml"),
        deadline=args.deadline,
        previous=previous,
        community_data=load_yaml("community.yml"),
    )
    write_json(args.output, payload)
    print(f"Wrote {args.output}: {payload['ballots_counted']} accepted manager ballots")


if __name__ == "__main__":
    main()
