"""Validate the canonical public Yahoo configuration and template usage."""

from __future__ import annotations

import pathlib
import sys
from typing import Any
from urllib.parse import urlsplit

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE_CONFIG = ROOT / "_data" / "site.yml"
CANONICAL_2026 = {
    "league_url": "https://football.fantasysports.yahoo.com/f1/26455",
    "league_id": "26455",
    "league_key": "470.l.26455",
    "alias": "nfl.l.26455",
    "game_key": "470",
    "season": 2026,
}
UNSAFE_PUBLIC_URL_FRAGMENTS = (
    "fantasysports.yahooapis.com",
    "/invitation",
    "oauth",
    "/commish",
    "/commissioner",
    "/manage",
)
TEMPLATE_DIRECTORIES = ("_includes", "_layouts", "_franchises", "_seasons", "_drafts", "_live_weeks")


def validate_yahoo_config(config: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(config, dict):
        return ["site configuration must be an object"]
    yahoo = config.get("yahoo")
    if not isinstance(yahoo, dict):
        return ["site configuration must contain a yahoo object"]

    for field, expected in CANONICAL_2026.items():
        if yahoo.get(field) != expected:
            errors.append(f"yahoo.{field} must be {expected!r}")
    if config.get("current_season") != yahoo.get("season"):
        errors.append("current_season must match yahoo.season")

    league_url = str(yahoo.get("league_url") or "")
    parsed = urlsplit(league_url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "football.fantasysports.yahoo.com"
        or parsed.path != "/f1/26455"
        or parsed.query
        or parsed.fragment
    ):
        errors.append("yahoo.league_url must be the canonical public league root")
    lowered = league_url.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_URL_FRAGMENTS):
        errors.append("yahoo.league_url contains a private, management, OAuth, or API route")

    game_key = str(yahoo.get("game_key") or "")
    league_id = str(yahoo.get("league_id") or "")
    if yahoo.get("league_key") != f"{game_key}.l.{league_id}":
        errors.append("yahoo.league_key must match yahoo.game_key and yahoo.league_id")
    if yahoo.get("alias") != f"nfl.l.{league_id}":
        errors.append("yahoo.alias must match yahoo.league_id")
    return errors


def presentation_files(root: pathlib.Path = ROOT):
    yield from (path for path in root.glob("*.md") if path.name != "AGENTS.md")
    yield from root.glob("*.html")
    for directory in TEMPLATE_DIRECTORIES:
        location = root / directory
        if location.is_dir():
            yield from location.rglob("*.md")
            yield from location.rglob("*.html")


def validate_template_usage(root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = []
    canonical_reference = "site.data.site.yahoo.league_url"
    reference_count = 0
    for path in presentation_files(root):
        text = path.read_text(encoding="utf-8")
        if canonical_reference in text:
            reference_count += text.count(canonical_reference)
        if "football.fantasysports.yahoo.com" in text:
            errors.append(
                f"{path.relative_to(root)} hardcodes a public Yahoo URL; use {canonical_reference}"
            )
    if reference_count == 0:
        errors.append("no presentation template references the canonical Yahoo league URL")
    return errors


def main() -> None:
    try:
        config = yaml.safe_load(SITE_CONFIG.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise SystemExit(f"Yahoo configuration validation failed: {error}") from error
    errors = validate_yahoo_config(config) + validate_template_usage()
    if errors:
        print("Yahoo configuration validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print("Validated canonical 2026 Yahoo configuration and template references")


if __name__ == "__main__":
    main()
