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
    "/head-to-head/",
    "/votes/",
    "/votes/power-rankings/",
    "/votes/picks/",
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
    records_page = route_target("/records/").read_text(encoding="utf-8")
    head_to_head_page = route_target("/head-to-head/").read_text(encoding="utf-8")
    votes_page = route_target("/votes/").read_text(encoding="utf-8")
    power_page = route_target("/votes/power-rankings/").read_text(encoding="utf-8")
    picks_page = route_target("/votes/picks/").read_text(encoding="utf-8")
    if 'aria-label="Open navigation"' not in votes_page:
        errors.append("mobile navigation toggle must have an accessible name")
    if teams_page.count('class="franchise-card"') != 12:
        errors.append("teams directory must render exactly 12 active franchise cards")
    if retired_page.count('data-archive-kind="retired-franchise"') != 1:
        errors.append("franchise archive must render exactly 1 retired franchise card")
    if retired_page.count('data-archive-kind="historical-identity"') != 1:
        errors.append("franchise archive must render exactly 1 historical identity card")
    if history_page.count('class="season-archive-card"') != 4:
        errors.append("history archive must render exactly 4 season cards")
    if drafts_page.count('class="draft-season-card"') != 4:
        errors.append("draft archive must render exactly 4 draft cards")
    if cup_page.count("<article>") != 4:
        errors.append("Brew Crew Cup page must render exactly 4 champion entries")
    for expected in (
        "Road to Glory",
        "Record Book",
        "Franchise Leaders",
        "Season Records",
        "Weekly Records",
        "Biggest Wins",
        "Closest Games",
        "Winning &amp; Losing Streaks",
        "Playoff Records",
        "Still Being Built",
        "Bench Blunders",
    ):
        if expected not in records_page:
            errors.append(f"records page is missing: {expected}")
    record_book = json.loads((ROOT / "_data" / "generated" / "record_book.json").read_text(encoding="utf-8"))
    historical_summaries = json.loads((ROOT / "_data" / "generated" / "records" / "franchise_summaries.json").read_text(encoding="utf-8"))
    historical_playoffs = json.loads((ROOT / "_data" / "generated" / "records" / "playoffs.json").read_text(encoding="utf-8"))
    career_count = len(historical_summaries["franchises"])
    playoff_count = len(historical_playoffs["franchises"])
    if records_page.count('class="record-team"') < career_count + playoff_count:
        errors.append("records page did not render every career and playoff franchise reference")
    if records_page.count('class="record-card"') != 7:
        errors.append("records page must render exactly 7 verified single-season record cards")
    if records_page.count('class="unavailable-card') != 2:
        errors.append("records page must render only playoff drought and bench unavailable states")
    for expected in ('id="franchise-a"', 'id="franchise-b"', 'id="h2h-data"', "Verified 2022–2025"):
        if expected not in head_to_head_page:
            errors.append(f"head-to-head page is missing: {expected}")
    for expected in ("League", "Votes", "Active Votes", "Weekly Matchup Picks", "Power Rankings", "Vote Archive"):
        if expected not in votes_page:
            errors.append(f"votes hub is missing: {expected}")
    for expected in ("Manager Power Rankings", "Purely Manager Voted"):
        if expected not in power_page:
            errors.append(f"Power Rankings page is missing: {expected}")
    for expected in ("Matchup Picks", "Weekly Matchups", "Season Picks Leaderboard", "Pick Results Archive"):
        if expected not in picks_page:
            errors.append(f"Picks page is missing: {expected}")
    voting_data = json.loads((ROOT / "_data" / "generated" / "votes.json").read_text(encoding="utf-8"))
    power_data = json.loads((ROOT / "_data" / "generated" / "power_rankings.json").read_text(encoding="utf-8"))
    picks_data = json.loads((ROOT / "_data" / "generated" / "picks.json").read_text(encoding="utf-8"))
    recaps_data = json.loads((ROOT / "_data" / "generated" / "recaps.json").read_text(encoding="utf-8"))
    if not voting_data["active_polls"] and "No league ballots are open" not in votes_page:
        errors.append("votes hub did not render its intentional no-active-votes state")
    if not power_data["rankings"] and "Voting opens during the season" not in power_page:
        errors.append("Power Rankings page did not render its offseason state")
    if power_data["rankings"] and power_page.count('class="vote-team"') != len(power_data["rankings"]):
        errors.append("Power Rankings page did not render every ranked franchise")
    if picks_data["current_week"] is None and "current slate is not available yet" not in picks_page:
        errors.append("Picks page did not render its unavailable current-week state")
    if not picks_data["leaderboard"] and "Results begin after verified games" not in picks_page:
        errors.append("Picks page did not render its empty leaderboard state")
    for season in season_data["seasons"]:
        route = f"/history/{season['year']}/"
        rendered = route_target(route).read_text(encoding="utf-8")
        for expected in ("Season story", "By the Numbers", "Final standings", "Playoff Bracket", "Playoff Results", "Playoff Round Recaps", "Championship recap", "Season Recaps"):
            if expected not in rendered:
                errors.append(f"season page {route} is missing: {expected}")
        if rendered.count('class="playoff-result') < 3:
            errors.append(f"season page {route} did not render playoff result cards")
        expected_numbers = sum(item["season"] == season["year"] for item in recaps_data["by_the_numbers"])
        expected_playoff_recaps = sum(item["season"] == season["year"] for item in recaps_data["playoff_recaps"])
        expected_team_recaps = sum(item["season"] == season["year"] for item in recaps_data["team_recaps"])
        if rendered.count('class="season-number-card') != expected_numbers:
            errors.append(f"season page {route} did not render every supported By the Numbers card")
        if rendered.count('class="playoff-recap-card"') != expected_playoff_recaps:
            errors.append(f"season page {route} did not render every playoff recap")
        if rendered.count('class="team-recap-card"') != expected_team_recaps:
            errors.append(f"season page {route} did not render every team recap")
        if "Generated from verified league results." not in rendered:
            errors.append(f"season page {route} is missing the narrative provenance label")
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
