"""Validate allowlisted generated JSON before it is committed or rendered."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Iterable


GENERATED_DIRECTORY = pathlib.Path("_data/generated")
NEWS_PATH = pathlib.Path("_data/news.json")
REQUIRED_FILES = {
    "manifest.json",
    "league.json",
    "teams.json",
    "standings.json",
    "matchups.json",
    "rosters.json",
    "records.json",
    "votes.json",
    "power_rankings.json",
    "picks.json",
    "recaps.json",
    "history_manifest.json",
}
FORBIDDEN_KEYS = {
    "access_token",
    "client_secret",
    "email",
    "guid",
    "iris_group_chat_id",
    "manager_id",
    "password",
    "refresh_token",
    "short_invitation_url",
    "email_address",
    "ip",
    "ip_address",
    "google_user_id",
    "account_id",
    "auth_token",
    "edit_url",
}
FORBIDDEN_TEXT = ("/invitation?key=", "&ikey=")


def walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def validate_payload(path: pathlib.Path, payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{path}: root must be an object"]
    if payload.get("schema_version") != 1:
        errors.append(f"{path}: schema_version must be 1")

    def inspect(value: Any, location: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.lower() in FORBIDDEN_KEYS:
                    errors.append(f"{path}: forbidden public key at {location}.{key}")
                inspect(child, f"{location}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, f"{location}[{index}]")
        elif isinstance(value, str):
            lowered = value.lower()
            if any(fragment in lowered for fragment in FORBIDDEN_TEXT):
                errors.append(f"{path}: private invitation data at {location}")

    inspect(payload, "root")
    return errors


def validate_news(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{NEWS_PATH}: root must be an object"]
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append(f"{NEWS_PATH}: schema_version must be 1")
    items = payload.get("items")
    if not isinstance(items, list):
        return errors + [f"{NEWS_PATH}: items must be an array"]
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{NEWS_PATH}: item {index} must be an object")
            continue
        title = str(item.get("title") or "").strip()
        link = str(item.get("link") or "").strip()
        if not title or not link.startswith(("https://", "http://")):
            errors.append(f"{NEWS_PATH}: item {index} is not a valid public article")
        if "feed error" in title.lower():
            errors.append(f"{NEWS_PATH}: item {index} exposes a feed error")
    return errors


def main() -> None:
    present = {path.name for path in GENERATED_DIRECTORY.glob("*.json")}
    errors = [
        f"missing generated file: {name}" for name in sorted(REQUIRED_FILES - present)
    ]

    generated_paths = sorted(GENERATED_DIRECTORY.rglob("*.json"))
    for path in generated_paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            errors.append(f"{path}: {error}")
            continue
        errors.extend(validate_payload(path, payload))

    try:
        news = json.loads(NEWS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        errors.append(f"{NEWS_PATH}: {error}")
    else:
        errors.extend(validate_news(news))

    if errors:
        print("Public data validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Validated {len(generated_paths)} sanitized generated files and news data")


if __name__ == "__main__":
    main()
