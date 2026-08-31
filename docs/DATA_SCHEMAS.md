# Road to Glory FFL Data Schemas

All committed data is public. Never add credentials, Yahoo account identifiers,
private invitation data, email addresses, or private league communications.

Every data file uses `schema_version: 1` or `"schema_version": 1`.

## Human-maintained YAML

### `site.yml`

- `current_season`: active fantasy season.
- `yahoo.league_alias`: public alias expected in the `LEAGUE_KEY` Actions secret.
- `yahoo.league_url`: public league link.
- `generated_data_namespace`: Jekyll namespace below `site.data`.

The 2026 alias is `nfl.l.26455`. Yahoo may resolve it to a season-specific game
key; do not copy that resolved key into configuration.

### `league.yml`

- `draft_datetime`: commissioner-confirmed ISO-8601 draft date and time.

The timestamp must include an explicit UTC offset, for example
`2026-08-30T19:30:00-04:00`, so the static JavaScript countdown represents the
same instant in every visitor's timezone. Leave it empty to render the
intentional `2026 Draft Date TBA` state.

### `owners.yml`

Each future `owners` entry uses:

- `owner_id`: stable lowercase ID.
- `display_name`: approved public name.
- `aliases`: historical public display names.
- `active`, `joined_season`, and optional `departed_season`.

### `franchises.yml`

Each future `franchises` entry uses:

- `franchise_id` and `slug`: stable lowercase identifiers.
- `name`, `short_name`, `status`, and `aliases`.
- `owner_ids`: references to `owners.yml`.
- `founded_season` and optional `retired_season`.
- `yahoo`: season-to-team ID/key mappings.
- `branding`, `profile`, and `rival_franchise_ids`.

Team names and Yahoo team keys are mutable and must never replace
`franchise_id` as the historical join key.

`retired_franchises.yml` contains only canonical `franchise_id` references. It
does not duplicate franchise facts.

### Historical data

- `champions.yml`: season, champion/runner-up franchise IDs, verified record,
  championship score, and recap path.
- `seasons.yml`: season metadata and source verification state.
- `playoffs.yml`: season, rounds, matchups, scores, winners, and source state.
- `drafts.yml`: season, order, picks, recap metadata, and source state.
- `records.yml`: typed record definitions and ranked entries with provenance.
- `votes.yml`: poll metadata, options, static result snapshots, and timestamps.

Empty arrays are intentional. Historical values will be added only after they
are transcribed and verified during later migration milestones.

## Generated public JSON

The Yahoo Action writes only to `_data/generated/`.

### `manifest.json`

- `schema_version`
- `season`
- `source_update_timestamp`
- `status`: `ready` or `unavailable`

### `league.json`

The `league` object contains only league key/ID, name, season, team count,
current/matchup week, start/end dates, finished state, public logo URL, and
source update timestamp.

### `teams.json`

Each `teams` entry contains team key/ID, name, approved manager display names,
public logo URL, waiver priority, moves, and trades. Yahoo manager IDs and GUIDs
are intentionally omitted.

### `standings.json`

Each `standings` entry contains rank, team key/ID/name, record, winning
percentage, points for/against, streak, and playoff seed.

### `matchups.json`

Contains the scoring week and matchups. Each matchup includes status, playoff
flags, tie/winner information, and two team records containing IDs, names,
scores, and projected scores when supplied by Yahoo.

### `rosters.json`

Contains the scoring week and one entry per team. Each player contains player
key/name, NFL team, primary position, selected fantasy position, and public
injury/status designation when supplied by Yahoo.

### `news.json`

Contains `schema_version`, `updated`, and valid article `items`. Feed failures
are logged in Actions and are never stored as public headlines.
