"""Validate voting schemas, public aggregates, identities, and empty states."""

from __future__ import annotations

import json
from numbers import Real
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from validate_public_data import validate_payload


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "_data" / "generated"
ALLOWED_TYPES = {"league_rule", "power_ranking", "matchup_pick", "award", "custom"}
REQUIRED_POLL_FIELDS = {
    "id", "season", "week", "title", "description", "type", "status", "opens_at",
    "closes_at", "options", "submission_url", "results_status", "results_source", "notes",
}


def numeric(value: object) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def load_json(name: str) -> dict:
    path = GENERATED / name
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{name}: root must be an object")
    return value


def valid_public_form_url(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return parsed.scheme == "https" and parsed.netloc == "docs.google.com" and "/forms/" in parsed.path and "/edit" not in parsed.path


def main() -> None:
    errors: list[str] = []
    config = yaml.safe_load((ROOT / "_data" / "votes.yml").read_text(encoding="utf-8"))
    owners = yaml.safe_load((ROOT / "_data" / "owners.yml").read_text(encoding="utf-8"))["owners"]
    franchises = yaml.safe_load((ROOT / "_data" / "franchises.yml").read_text(encoding="utf-8"))["franchises"]
    owner_ids = {item["owner_id"] for item in owners if item.get("active")}
    active_franchise_ids = {item["franchise_id"] for item in franchises if item.get("status") == "active"}

    if not isinstance(config, dict) or config.get("schema_version") != 1:
        errors.append("_data/votes.yml must be a schema_version 1 mapping")
        config = config if isinstance(config, dict) else {}
    if set(config.get("poll_types") or []) != ALLOWED_TYPES:
        errors.append("canonical poll types are incomplete")
    schema = config.get("poll_schema") or {}
    if set(schema.get("required_fields") or []) != REQUIRED_POLL_FIELDS:
        errors.append("poll_schema required fields are incomplete")
    if (config.get("submission_architecture") or {}).get("duplicate_policy") != "latest_valid_submission_before_deadline":
        errors.append("duplicate submission policy must be deterministic")

    poll_ids: set[str] = set()
    for poll in config.get("polls") or []:
        label = str(poll.get("id") or "unknown poll")
        if not REQUIRED_POLL_FIELDS <= set(poll):
            errors.append(f"{label}: missing required poll fields")
        if poll.get("id") in poll_ids:
            errors.append(f"{label}: duplicate poll id")
        poll_ids.add(poll.get("id"))
        if poll.get("type") not in ALLOWED_TYPES:
            errors.append(f"{label}: invalid poll type")
        if poll.get("status") not in set(schema.get("valid_statuses") or []):
            errors.append(f"{label}: invalid poll status")
        if poll.get("results_status") not in set(schema.get("valid_results_statuses") or []):
            errors.append(f"{label}: invalid results status")
        if not valid_public_form_url(poll.get("submission_url")):
            errors.append(f"{label}: submission_url must be a public Google Forms URL")
        option_ids = [item.get("id") for item in poll.get("options") or []]
        if len(option_ids) != len(set(option_ids)):
            errors.append(f"{label}: option IDs must be unique")

    datasets = {name: load_json(name) for name in ("votes.json", "power_rankings.json", "picks.json")}
    for name, payload in datasets.items():
        errors.extend(validate_payload(GENERATED / name, payload))
        if payload.get("schema_version") != 1 or not isinstance(payload.get("season"), int):
            errors.append(f"{name}: schema_version and season are required")
        source = payload.get("source")
        if not isinstance(source, dict) or "coverage_status" not in source or "type" not in source:
            errors.append(f"{name}: source and coverage status are required")
        for field in ("accepted_ballots", "rejected_ballots", "superseded_ballots"):
            if not isinstance((source or {}).get(field), int) or source[field] < 0:
                errors.append(f"{name}: source.{field} must be a non-negative integer")
        if payload.get("generated_at") is None and (source or {}).get("accepted_ballots") != 0:
            errors.append(f"{name}: accepted ballots require generated_at provenance")

    votes = datasets["votes.json"]
    for poll in [*(votes.get("active_polls") or []), *(votes.get("archived_polls") or [])]:
        if poll.get("id") not in poll_ids:
            errors.append(f"votes.json: unknown poll {poll.get('id')!r}")
        if not valid_public_form_url(poll.get("submission_url")):
            errors.append(f"votes.json: unsafe submission URL for {poll.get('id')}")
        results = poll.get("results") or []
        ballots = poll.get("ballots_counted") or 0
        if results:
            if sum(item.get("vote_count", 0) for item in results) != ballots:
                errors.append(f"votes.json: result counts do not match ballots for {poll.get('id')}")
            if ballots and abs(sum(item.get("percentage", 0) for item in results) - 1.0) > 0.002:
                errors.append(f"votes.json: result percentages are invalid for {poll.get('id')}")

    power = datasets["power_rankings.json"]
    rankings = power.get("rankings") or []
    if rankings:
        if len(rankings) != len(active_franchise_ids):
            errors.append("power_rankings.json: a published table must contain every active franchise")
        if [item.get("rank") for item in rankings] != list(range(1, len(rankings) + 1)):
            errors.append("power_rankings.json: ranks must be unique and ordered")
    for item in rankings:
        if item.get("franchise_id") not in active_franchise_ids:
            errors.append("power_rankings.json: unknown franchise ID")
        if item.get("ballots_counted") != power.get("ballots_counted"):
            errors.append("power_rankings.json: ballot counts disagree")
        for field in ("rank", "total_points", "first_place_votes", "ballots_counted"):
            if not isinstance(item.get(field), int) or item[field] < 0:
                errors.append(f"power_rankings.json: {field} must be a non-negative integer")
        if not numeric(item.get("average_rank")):
            errors.append("power_rankings.json: average_rank must be numeric")
    if not rankings and power.get("source", {}).get("coverage_status") != "unavailable":
        errors.append("power_rankings.json: empty rankings require an unavailable state")

    picks = datasets["picks.json"]
    for week in picks.get("weekly_results") or []:
        matchup_ids: set[str] = set()
        winner_status: dict[str, str] = {}
        for matchup in week.get("matchups") or []:
            matchup_id = matchup.get("matchup_id")
            if matchup_id in matchup_ids:
                errors.append("picks.json: duplicate matchup ID within a week")
            matchup_ids.add(matchup_id)
            participants = {item.get("franchise_id") for item in matchup.get("participants") or []}
            if len(participants) != 2 or not participants <= active_franchise_ids:
                errors.append(f"picks.json: invalid participants for {matchup_id}")
            status = matchup.get("winner_status")
            winner_status[matchup_id] = status
            winner = matchup.get("winner_franchise_id")
            if status == "verified" and winner not in participants:
                errors.append(f"picks.json: verified winner is not a participant for {matchup_id}")
            if status != "verified" and winner is not None:
                errors.append(f"picks.json: unverified winner must be null for {matchup_id}")
        for manager in week.get("manager_results") or []:
            if manager.get("owner_id") not in owner_ids:
                errors.append("picks.json: unknown manager")
            if manager.get("total_picks") != manager.get("correct", 0) + manager.get("incorrect", 0):
                errors.append("picks.json: total_picks must equal decided picks")
            expected_accuracy = round(manager["correct"] / manager["total_picks"], 3) if manager.get("total_picks") else None
            if manager.get("accuracy") != expected_accuracy:
                errors.append("picks.json: manager accuracy is invalid")
            for pick in manager.get("picks") or []:
                if pick.get("matchup_id") not in matchup_ids:
                    errors.append("picks.json: manager pick references an unknown matchup")
                if pick.get("result") in {"correct", "incorrect"} and winner_status.get(pick.get("matchup_id")) != "verified":
                    errors.append("picks.json: a pick was scored without a verified Yahoo winner")
    leaderboard = picks.get("leaderboard") or []
    if [item.get("rank") for item in leaderboard] != list(range(1, len(leaderboard) + 1)):
        errors.append("picks.json: leaderboard ranks must be unique and ordered")
    for item in leaderboard:
        if item.get("owner_id") not in owner_ids:
            errors.append("picks.json: leaderboard contains an unknown manager")
        if item.get("total_picks") != item.get("correct", 0) + item.get("incorrect", 0):
            errors.append("picks.json: leaderboard totals are inconsistent")
        expected_accuracy = round(item["correct"] / item["total_picks"], 3) if item.get("total_picks") else None
        if item.get("accuracy") != expected_accuracy:
            errors.append("picks.json: leaderboard accuracy is invalid")
    if picks.get("current_week") is None and picks.get("source", {}).get("coverage_status") not in {"unavailable", "published"}:
        errors.append("picks.json: missing current week needs an unavailable or archived state")

    if errors:
        raise SystemExit("Voting validation failed:\n- " + "\n- ".join(errors))
    print(
        f"Validated {len(config.get('polls') or [])} polls, {len(rankings)} Power Ranking rows, "
        f"{len(picks.get('weekly_results') or [])} pick weeks, privacy rules, identities, and empty states"
    )


if __name__ == "__main__":
    main()
