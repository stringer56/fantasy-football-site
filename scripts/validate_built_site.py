"""Validate the rendered GitHub Pages output and its internal links."""

from __future__ import annotations

import json
from html import unescape
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
    "/all-time-standings/",
    "/championships/",
    "/2026/",
    "/2026/week/1/",
    "/votes/",
    "/power-rankings/",
    "/picks/",
    "/pickem/",
    "/votes/power-rankings/",
    "/votes/picks/",
    "/retired/",
    "/rules/",
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[tuple[str, str]] = []
        self.anchors: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a":
            self.anchors.append(attributes)
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
    site_data = yaml.safe_load((ROOT / "_data" / "site.yml").read_text(encoding="utf-8"))
    yahoo_url = site_data["yahoo"]["league_url"]
    franchise_data = yaml.safe_load((ROOT / "_data" / "franchises.yml").read_text(encoding="utf-8"))
    franchise_routes = tuple(
        f"/{'retired' if franchise['status'] == 'retired' else 'teams'}/{franchise['slug']}/"
        for franchise in franchise_data["franchises"]
    )
    season_data = yaml.safe_load((ROOT / "_data" / "seasons.yml").read_text(encoding="utf-8"))
    season_routes = tuple(f"/history/{season['year']}/" for season in season_data["seasons"])
    playoff_data = yaml.safe_load((ROOT / "_data" / "playoffs.yml").read_text(encoding="utf-8"))
    playoff_by_year = {item["season"]: item for item in playoff_data["playoffs"]}
    draft_data = yaml.safe_load((ROOT / "_data" / "drafts.yml").read_text(encoding="utf-8"))
    draft_routes = tuple(f"/drafts/{draft['year']}/" for draft in draft_data["drafts"])
    for route in EXPECTED_ROUTES + franchise_routes + season_routes + draft_routes:
        if not route_target(route).is_file():
            errors.append(f"missing expected route: {route}")

    for page in pages:
        text = page.read_text(encoding="utf-8")
        if "{{" in text or "{%" in text:
            errors.append(f"unrendered Liquid in {page.relative_to(SITE_DIR)}")
        for unsafe in (
            "fantasysports.yahooapis.com",
            "/invitation?key=",
            "oauth2.request.auth.yahoo.com",
        ):
            if unsafe in text.casefold():
                errors.append(
                    f"unsafe Yahoo URL in {page.relative_to(SITE_DIR)}: {unsafe}"
                )
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
    all_time_page = route_target("/all-time-standings/").read_text(encoding="utf-8")
    championships_page = route_target("/championships/").read_text(encoding="utf-8")
    votes_page = route_target("/votes/").read_text(encoding="utf-8")
    live_page = route_target("/2026/").read_text(encoding="utf-8")
    live_week_page = route_target("/2026/week/1/").read_text(encoding="utf-8")
    power_page = route_target("/power-rankings/").read_text(encoding="utf-8")
    power_legacy_page = route_target("/votes/power-rankings/").read_text(encoding="utf-8")
    picks_page = route_target("/picks/").read_text(encoding="utf-8")
    picks_legacy_page = route_target("/votes/picks/").read_text(encoding="utf-8")
    for label, rendered in (("homepage", home), ("2026 hub", live_page)):
        parser = LinkParser()
        parser.feed(rendered)
        canonical_links = [
            anchor for anchor in parser.anchors if anchor.get("href") == yahoo_url
        ]
        if not canonical_links:
            errors.append(f"{label} must link to the canonical Yahoo league URL")
        for anchor in canonical_links:
            rel_tokens = str(anchor.get("rel") or "").split()
            if anchor.get("target") != "_blank" or "noopener" not in rel_tokens:
                errors.append(f"{label} Yahoo links must open safely in a new tab")
    if 'aria-label="Open navigation"' not in votes_page:
        errors.append("mobile navigation toggle must have an accessible name")
    if teams_page.count('class="franchise-card"') != 12:
        errors.append("teams directory must render exactly 12 active franchise cards")
    if retired_page.count('data-archive-kind="retired-franchise"') != 1:
        errors.append("franchise archive must render exactly 1 retired franchise card")
    if retired_page.count('data-archive-kind="historical-identity"') != 1:
        errors.append("franchise archive must render exactly 1 historical identity card")
    if history_page.count('class="season-archive-card"') != 5:
        errors.append("history archive must render exactly 5 season cards")
    if drafts_page.count('class="draft-season-card"') != 5:
        errors.append("draft archive must render exactly 5 draft cards")
    if cup_page.count("<article>") != 5:
        errors.append("Brew Crew Cup page must render exactly 5 champion entries")
    for expected in (
        "Road to Glory",
        "Record Book",
        "Franchise Career Leaders",
        "Weekly Scoring Records",
        "Biggest Wins &amp; Closest Games",
        "Winning &amp; Losing Streaks",
        "Playoff &amp; Championship Records",
        "Cross-Season Comparisons",
        "Record Watch",
        "Not Yet Published",
        "Bench Blunders",
    ):
        if expected not in records_page:
            errors.append(f"records page is missing: {expected}")
    record_book = json.loads((ROOT / "_data" / "generated" / "record_book.json").read_text(encoding="utf-8"))
    historical_summaries = json.loads((ROOT / "_data" / "generated" / "records" / "franchise_career.json").read_text(encoding="utf-8"))
    career_count = len(historical_summaries["franchises"])
    if records_page.count('class="record-team"') != min(10, career_count):
        errors.append("records page did not render the expected career leader rows")
    if records_page.count('class="record-card"') != 10:
        errors.append("records page must render four weekly and six season-comparison record cards")
    if records_page.count('class="unavailable-card') != 2:
        errors.append("records page must render only playoff drought and bench unavailable states")
    for expected in ('id="franchise-a"', 'id="franchise-b"', 'id="h2h-data"', "Verified 2021–2025"):
        if expected not in head_to_head_page:
            errors.append(f"head-to-head page is missing: {expected}")
    for expected in ("All-Time Franchise Standings", "2021–2025 Leaderboard", "data-all-time-table", "data-sort=\"pct\""):
        if expected not in all_time_page:
            errors.append(f"all-time standings page is missing: {expected}")
    if all_time_page.count("data-name=") != career_count:
        errors.append("all-time standings page did not render every canonical franchise")
    for expected in ("Championship History", "Championship Results", "Championship Leaders", "Brew Crew Cup"):
        if expected not in championships_page:
            errors.append(f"championship history page is missing: {expected}")
    championship_data = json.loads((ROOT / "_data" / "generated" / "records" / "championships.json").read_text(encoding="utf-8"))
    if championships_page.count('class="record-rank"') != len(championship_data["championships"]):
        errors.append("championship history page did not render every verified final")
    for expected in ("League", "Votes", "Active Votes", "Weekly Matchup Picks", "Power Rankings", "Vote Archive"):
        if expected not in votes_page:
            errors.append(f"votes hub is missing: {expected}")
    for expected in ("2026 Power Rankings", "Manager ballots only"):
        if expected not in power_page:
            errors.append(f"Power Rankings page is missing: {expected}")
    for expected in ("2026 League HQ", "2026 Standings", "Record Watch", "Road to Glory Wire", "Power Rankings"):
        if expected not in live_page:
            errors.append(f"2026 hub is missing: {expected}")
    for expected in ("Week 1", "All Matchups", "Weekly Facts", "Record Watch"):
        if expected not in live_week_page:
            errors.append(f"2026 Week 1 hub is missing: {expected}")
    for expected in ("Average manager rank", "Ranking points", "First-place votes", "Previous rank", "Movement", "power-rankings.js"):
        if expected not in power_page:
            errors.append(f"Power Rankings experience is missing: {expected}")
    if "/power-rankings/" not in power_legacy_page:
        errors.append("legacy Power Rankings route must link to the canonical route")
    if "/picks/" not in picks_legacy_page:
        errors.append("legacy Picks route must link to the canonical route")
    for expected in ("Matchup Picks", "Weekly Matchups", "Season Picks Leaderboard", "Pick Results Archive"):
        if expected not in picks_page:
            errors.append(f"Picks page is missing: {expected}")
    voting_data = json.loads((ROOT / "_data" / "generated" / "votes.json").read_text(encoding="utf-8"))
    power_data = json.loads((ROOT / "_data" / "generated" / "power_rankings.json").read_text(encoding="utf-8"))
    picks_data = json.loads((ROOT / "_data" / "generated" / "picks.json").read_text(encoding="utf-8"))
    recaps_data = json.loads((ROOT / "_data" / "generated" / "recaps.json").read_text(encoding="utf-8"))
    if not voting_data["active_polls"] and "No league ballots are open" not in votes_page:
        errors.append("votes hub did not render its intentional no-active-votes state")
    if not power_data["rankings"] and "Week 1 ballots have not been finalized" not in power_page:
        errors.append("Power Rankings page did not render its offseason state")
    if power_data["rankings"] and power_page.count('data-power-ranking-row') != len(power_data["rankings"]):
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
        if "/cup/" not in rendered:
            errors.append(f"season page {route} does not link to the Brew Crew Cup")
        if season.get("data_mode") == "detailed":
            expected_content = ["Complete", "Week-by-Week Archive", "Playoff Field"]
            if season["year"] == 2025:
                expected_content.extend(["Verified Yahoo results", "Albany Kneelers selected Ja’Marr Chase"])
            elif season["year"] == 2021:
                expected_content.extend(["Select to view full size", "Placement games", "individual selections remain image-only"])
            else:
                expected_content.extend(["Select to view full size", "Placement games", "180 verified selections across 15 rounds"])
            for expected in expected_content:
                if expected not in rendered:
                    errors.append(f"season page {route} is missing {season['year']} content: {expected}")
            if rendered.count('class="week-card"') != 16:
                errors.append(f"{season['year']} season page must render all 16 weekly accordions")
            expected_matchups = 78 if season["year"] == 2021 else 92
            if rendered.count('class="week-matchup"') != expected_matchups:
                errors.append(f"{season['year']} season page must render all {expected_matchups} verified matchups")
            expected_field_size = len(playoff_by_year[season["year"]].get("playoff_field") or [])
            if rendered.count('class="playoff-field__grid"') != 1 or rendered.count("Seed #") < expected_field_size:
                errors.append(
                    f"{season['year']} season page must render its {expected_field_size}-team playoff field"
                )
            if rendered.count('class="team-recap-card"') != season["team_count"]:
                errors.append(f"{season['year']} season page must render all verified team mini-recaps")
        elif season.get("data_mode") == "season_level":
            for expected in (
                "Complete", "Season Data — Verified 2021", "Final streak", "Playoff Field",
                "individual selections remain image-only", "Winner verified · score unavailable",
            ):
                if expected not in rendered:
                    errors.append(f"season page {route} is missing {season['year']} content: {expected}")
            if "Week-by-Week Archive" in rendered or 'class="week-card"' in rendered:
                errors.append(f"{season['year']} season page must not render an unavailable weekly archive")
            if rendered.count('class="team-recap-card"') != season["team_count"]:
                errors.append(f"{season['year']} season page must render all verified team mini-recaps")
            if rendered.count('<article class="playoff-result') != 3:
                errors.append(f"{season['year']} season page must render exactly three verified playoff outcomes")
    for draft in draft_data["drafts"]:
        route = f"/drafts/{draft['year']}/"
        rendered = route_target(route).read_text(encoding="utf-8")
        for expected in ("Draft Order", "Draft Board &amp; Results", "Draft recap", "Verified Notes", 'aria-label="Draft years"'):
            if expected not in rendered:
                errors.append(f"draft page {route} is missing: {expected}")
        if rendered.count('class="draft-order-entry"') != draft["team_count"]:
            errors.append(f"draft page {route} did not render every order entry")
        if rendered.count("Open full size") != len(draft["results_assets"]):
            errors.append(f"draft page {route} did not render every result asset")
        if draft.get("order_asset") and Path(draft["order_asset"]["path"]).name not in rendered:
            errors.append(f"draft page {route} did not render its commissioner order asset")
        if draft.get("pick_data_status") == "verified_structured":
            if rendered.count('class="draft-round"') != draft["rounds"]:
                errors.append(f"draft page {route} did not render every structured round")
            if rendered.count("<tbody>") != draft["rounds"] or rendered.count("<tr>") < draft["pick_count"]:
                errors.append(f"draft page {route} did not render the complete structured board")
    for franchise in franchise_data["franchises"]:
        route = f"/{'retired' if franchise['status'] == 'retired' else 'teams'}/{franchise['slug']}/"
        profile = route_target(route).read_text(encoding="utf-8")
        for expected in (
            franchise["name"], "Coach &amp; identity", "Home turf", "View source page",
            "Franchise Record", "Season History", "Head-to-Head",
            "Championship History", "Franchise Timeline",
        ):
            if expected not in profile:
                errors.append(f"franchise profile {route} is missing: {expected}")
        if unescape(profile).count(franchise['profile']['summary']) != 1:
            errors.append(f"franchise profile {route} must preserve its full story exactly once")
        for key in ('identity_image', 'venue_image', 'honors_image'):
            asset = franchise['branding'].get(key)
            if asset and asset not in profile:
                errors.append(f"franchise profile {route} is missing approved {key}")
        if 'class="franchise-identity"' not in profile or 'id="home-turf"' not in profile:
            errors.append(f"franchise profile {route} is missing its identity/gallery structure")
    champions = yaml.safe_load((ROOT / '_data/champions.yml').read_text(encoding='utf-8'))['champions']
    for row in champions:
        franchise = next(f for f in franchise_data['franchises'] if f['franchise_id'] == row['champion_franchise_id'])
        route = f"/{'retired' if franchise['status'] == 'retired' else 'teams'}/{franchise['slug']}/"
        if f"{row['year']} Champion" not in route_target(route).read_text(encoding='utf-8'):
            errors.append(f"{route} is missing its canonical {row['year']} championship badge")
    manifest = json.loads((ROOT / "_data" / "generated" / "manifest.json").read_text(encoding="utf-8"))
    data_is_current = manifest.get("status") == "ready" and manifest.get("season") == site_data.get("current_season")
    if data_is_current:
        if "home-standings-top" not in home or "home-featured-matchup" not in home:
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
