"""Validate the rendered GitHub Pages output and its internal links."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "_site"
BASE_URL = "/fantasy-football-site"
EXPECTED_ROUTES = (
    "/",
    "/teams/",
    "/history/",
    "/seasons/",
    "/drafts/",
    "/cup/",
    "/records/",
    "/votes/",
    "/retired/",
    "/rules/",
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {"a", "link"} and attributes.get("href"):
            self.targets.append(("href", attributes["href"] or ""))
        if tag in {"img", "script", "source"} and attributes.get("src"):
            self.targets.append(("src", attributes["src"] or ""))


def route_target(route: str) -> Path:
    clean = route.strip("/")
    return SITE_DIR / clean / "index.html" if clean else SITE_DIR / "index.html"


def local_target(source_file: Path, raw_url: str) -> Path | None:
    parsed = urlsplit(raw_url)
    if parsed.scheme or parsed.netloc or raw_url.startswith(("mailto:", "tel:", "data:", "javascript:", "#")):
        return None

    path = unquote(parsed.path)
    if path.startswith(BASE_URL):
        path = path[len(BASE_URL) :]
    if path.startswith("/"):
        target = SITE_DIR / path.lstrip("/")
    else:
        target = source_file.parent / path

    if path.endswith("/") or not target.suffix:
        target = target / "index.html"
    return target.resolve()


def main() -> None:
    if not SITE_DIR.is_dir():
        raise SystemExit("_site is missing; run bundle exec jekyll build first")

    errors: list[str] = []
    pages = sorted(SITE_DIR.rglob("*.html"))
    for route in EXPECTED_ROUTES:
        if not route_target(route).is_file():
            errors.append(f"missing expected route: {route}")

    for page in pages:
        text = page.read_text(encoding="utf-8")
        if "{{" in text or "{%" in text:
            errors.append(f"unrendered Liquid in {page.relative_to(SITE_DIR)}")
        for landmark in ("<header", "<nav", "<main", "<footer"):
            if landmark not in text:
                errors.append(f"missing {landmark[1:]} landmark in {page.relative_to(SITE_DIR)}")

        parser = LinkParser()
        parser.feed(text)
        for attribute, raw_url in parser.targets:
            target = local_target(page, raw_url)
            if target is not None and not target.is_file():
                errors.append(
                    f"broken {attribute} in {page.relative_to(SITE_DIR)}: {raw_url}"
                )

    home = (SITE_DIR / "index.html").read_text(encoding="utf-8")
    site_data = yaml.safe_load((ROOT / "_data" / "site.yml").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "_data" / "generated" / "manifest.json").read_text(encoding="utf-8"))
    data_is_current = manifest.get("status") == "ready" and manifest.get("season") == site_data.get("current_season")
    if data_is_current:
        if "standings-table" not in home or "matchup-card" not in home:
            errors.append("current generated data did not render standings and matchup components")
    else:
        for expected in ("Draft Date TBA", "Standings arrive with the season", "The next slate is taking shape"):
            if expected not in home:
                errors.append(f"offseason homepage state is missing: {expected}")

    if errors:
        raise SystemExit("Built site validation failed:\n- " + "\n- ".join(errors))
    print(f"Validated {len(pages)} rendered pages, expected routes, links, landmarks, and homepage state")


if __name__ == "__main__":
    main()
