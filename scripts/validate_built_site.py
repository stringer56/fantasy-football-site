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
    franchise_data = yaml.safe_load((ROOT / "_data" / "franchises.yml").read_text(encoding="utf-8"))
    franchise_routes = tuple(
        f"/{'retired' if franchise['status'] == 'retired' else 'teams'}/{franchise['slug']}/"
        for franchise in franchise_data["franchises"]
    )
    season_data = yaml.safe_load((ROOT / "_data" / "seasons.yml").read_text(encoding="utf-8"))
    season_routes = tuple(f"/history/{season['year']}/" for season in season_data["seasons"])
    draft_data = yaml.safe_load((ROOT / "_data" / "drafts.yml").read_text(encoding="utf-8"))
    draft_routes = tuple(f"/drafts/{draft['year']}/" for draft in draft_data["drafts"])
    for route in EXPECTED_ROUTES + franchise_routes + season_routes + draft_routes:
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
    teams_page = route_target("/teams/").read_text(encoding="utf-8")
    retired_page = route_target("/retired/").read_text(encoding="utf-8")
    history_page = route_target("/history/").read_text(encoding="utf-8")
    drafts_page = route_target("/drafts/").read_text(encoding="utf-8")
    cup_page = route_target("/cup/").read_text(encoding="utf-8")
    if teams_page.count('class="franchise-card"') != 12:
        errors.append("teams directory must render exactly 12 active franchise cards")
    if retired_page.count('class="retired-card"') != 2:
        errors.append("retired directory must render exactly 2 retired franchise cards")
    if history_page.count('class="season-archive-card"') != 4:
        errors.append("history archive must render exactly 4 season cards")
    if drafts_page.count('class="draft-season-card"') != 4:
        errors.append("draft archive must render exactly 4 draft cards")
    if cup_page.count("<article>") != 4:
        errors.append("Brew Crew Cup page must render exactly 4 champion entries")
    for season in season_data["seasons"]:
        route = f"/history/{season['year']}/"
        rendered = route_target(route).read_text(encoding="utf-8")
        for expected in ("Final standings", "Playoff Bracket", "Playoff Results", "Championship recap", "Season Recap Index"):
            if expected not in rendered:
                errors.append(f"season page {route} is missing: {expected}")
        if rendered.count('class="playoff-result') < 3:
            errors.append(f"season page {route} did not render playoff result cards")
        if f"/drafts/{season['year']}/" not in rendered:
            errors.append(f"season page {route} does not link to its draft")
    for draft in draft_data["drafts"]:
        route = f"/drafts/{draft['year']}/"
        rendered = route_target(route).read_text(encoding="utf-8")
        for expected in ("Draft Order", "Draft Board &amp; Results", "Draft recap", "Verified Notes", "Future Draft Analysis"):
            if expected not in rendered:
                errors.append(f"draft page {route} is missing: {expected}")
        if rendered.count('class="draft-order-entry"') != draft["team_count"]:
            errors.append(f"draft page {route} did not render every order entry")
        if rendered.count("Open full size") != len(draft["results_assets"]):
            errors.append(f"draft page {route} did not render every result asset")
    for franchise in franchise_data["franchises"]:
        route = f"/{'retired' if franchise['status'] == 'retired' else 'teams'}/{franchise['slug']}/"
        profile = route_target(route).read_text(encoding="utf-8")
        for expected in (franchise["name"], "Team information", "Home turf", "Migration record"):
            if expected not in profile:
                errors.append(f"franchise profile {route} is missing: {expected}")
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
    print(f"Validated {len(pages)} rendered pages, franchise routes, links, landmarks, and homepage state")


if __name__ == "__main__":
    main()
