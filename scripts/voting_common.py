"""Shared, privacy-safe voting import helpers."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_VOTE_KEYS = {"account_id", "auth_token", "edit_url", "email", "email_address", "google_user_id", "ip", "ip_address"}


class BallotError(ValueError):
    """Raised when a ballot cannot be accepted."""


def load_yaml(name: str) -> dict[str, Any]:
    value = yaml.safe_load((ROOT / "_data" / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"_data/{name}: expected a schema_version 1 mapping")
    return value


def load_import(path: Path) -> dict[str, Any]:
    if path.suffix.casefold() == ".json":
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("JSON import root must be an object")
        reject_private_fields(value)
        return value
    if path.suffix.casefold() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        value = {"rows": rows}
        reject_private_fields(value)
        return value
    raise ValueError("Voting imports must be .csv or .json")


def reject_private_fields(value: Any, location: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).strip().casefold() in FORBIDDEN_VOTE_KEYS:
                raise BallotError(f"private field is not allowed at {location}.{key}")
            reject_private_fields(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_fields(child, f"{location}[{index}]")


def parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise BallotError("submitted_at is required")
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise BallotError("submitted_at must be ISO-8601") from error
    if parsed.tzinfo is None:
        raise BallotError("submitted_at must include a timezone")
    return parsed


def parse_deadline(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    return parse_timestamp(value)


def owner_index(owners_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["owner_id"]: item for item in owners_data["owners"] if item.get("active")}


def active_franchises(franchises_data: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in franchises_data["franchises"] if item.get("status") == "active"]


def select_latest_valid(
    ballots: Iterable[dict[str, Any]],
    owner_ids: set[str],
    validator: Callable[[dict[str, Any]], None],
    deadline: datetime | None = None,
) -> tuple[list[dict[str, Any]], int]:
    selected: dict[str, tuple[datetime, dict[str, Any]]] = {}
    rejected = 0
    for ballot in ballots:
        try:
            owner_id = ballot.get("owner_id")
            if owner_id not in owner_ids:
                raise BallotError(f"unknown owner_id {owner_id!r}")
            submitted = parse_timestamp(ballot.get("submitted_at"))
            if deadline is not None and submitted > deadline:
                raise BallotError("submission is after the deadline")
            validator(ballot)
        except (BallotError, TypeError):
            rejected += 1
            continue
        current = selected.get(owner_id)
        if current is None or submitted > current[0]:
            selected[owner_id] = (submitted, ballot)
    return [selected[key][1] for key in sorted(selected)], rejected


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generated_at_from_import(payload: dict[str, Any], has_rows: bool) -> str | None:
    value = payload.get("generated_at") or payload.get("exported_at")
    if not has_rows:
        return None if value in (None, "") else str(value)
    parse_timestamp(value)
    return str(value)


def generated_at_from_rows(payload: dict[str, Any], rows: list[dict[str, Any]]) -> str | None:
    explicit = payload.get("generated_at") or payload.get("exported_at")
    if explicit not in (None, ""):
        parse_timestamp(explicit)
        return str(explicit)
    timestamps = []
    for row in rows:
        try:
            timestamps.append(parse_timestamp(row.get("submitted_at")))
        except (BallotError, TypeError):
            continue
    return max(timestamps).isoformat() if timestamps else None
