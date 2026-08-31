# Road to Glory FFL Website

## Project Goal

Rebuild the existing Road to Glory Fantasy Football League Google Site as a polished, responsive, free GitHub Pages website.

Existing Google Site:
https://sites.google.com/view/road-to-glory-ffl/home

GitHub Pages repository:
https://github.com/stringer56/fantasy-football-site

Live Yahoo league:
https://football.fantasysports.yahoo.com/f1/26455

## Hosting / Architecture

- Must remain free to host.
- Use GitHub Pages.
- Current site uses Jekyll/Liquid, HTML, CSS and JavaScript.
- Yahoo Fantasy data is fetched by GitHub Actions and stored in `_data/`.
- Never expose Yahoo Client ID, Client Secret, refresh tokens, or other credentials.
- Secrets must stay in GitHub Actions secrets.
- Do not require a permanent local server or user's PC to remain online.

## Design Goal

Build a professional fantasy-football league website, closer to a sports media/league portal than a generic GitHub Pages blog.

Style:

- Strong sports-site visual hierarchy.
- Dark navy / football-inspired base with gold accent.
- Responsive desktop/mobile.
- Strong cards, tables, standings, matchup cards and team branding.
- Avoid clutter and generic Bootstrap/Jekyll appearance.
- Preserve league personality and existing historical content.

## Core Sections

- Home
- Teams & Owners
- League History / Seasons
- Draft Archive
- Brew Crew Cup
- Records & Leaderboards
- League Votes
- Retired Franchises
- League Rules

## Existing Content to Preserve

Migrate relevant content from the current Google Site:

- Team/owner pages and write-ups
- Team helmets and logos
- Retired franchise pages
- League rules
- Past champions
- Season standings
- Playoff brackets
- Playoff summaries
- Championship recaps
- Draft orders
- Draft results
- Draft recaps
- Brew Crew Cup/trophy content

Do not delete historical material just because the current implementation is incomplete.

## Yahoo Data Features

The site should eventually support:

- Current standings
- Weekly matchups
- Expandable team rosters
- Historical league data
- Head-to-head history
- League records
- Season recap generation inputs
- Mini team recaps by season
- Playoff recaps
- Franchise milestones

## Planned Community Features

- Multi-source NFL/fantasy news ticker
- Draft-day countdown
- League voting hub
- Manager-voted weekly Power Rankings
- Weekly matchup winner voting
- Picks leaderboard

## Historical Statistics / Records

Plan data structures for:

- Career wins/losses
- Points for/against
- Win percentage
- Playoff appearances
- Championships
- Single-game records
- Single-season records
- Playoff scoring records
- Biggest/smallest margins of victory
- Win/loss streaks
- Top 10 bench player scoring misses:
  team / year / player / points missed / week

## Season Content

Each season page should eventually include:

- Overall season narrative recap
- Standings
- Playoff bracket
- Individual playoff game recaps
- Championship recap
- Mini recap for every team
- By-the-numbers section

## Engineering Rules

- Inspect existing code before changing it.
- Preserve working Yahoo API/GitHub Actions functionality.
- Prefer reusable data-driven templates over duplicated HTML.
- Use semantic HTML and accessible controls.
- Avoid unnecessary frameworks/dependencies.
- No secrets in commits.
- Keep changes reviewable.
- Run relevant validation before reporting completion.
- Do not modify unrelated files.
- When a task is complete, report:
  1. files changed
  2. behavior implemented
  3. tests/checks run
  4. known limitations
  5. recommended next task
