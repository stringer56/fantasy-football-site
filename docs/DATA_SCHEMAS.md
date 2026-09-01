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

Each `owners` entry uses:

- `owner_id`: stable lowercase ID.
- `display_name`: approved public name.
- `aliases`: historical public display names.
- `active`, `joined_season`, and optional `departed_season`.

### `franchises.yml`

Each `franchises` entry uses:

- `franchise_id` and `slug`: stable lowercase identifiers.
- `name`, `short_name`, `status`, and `aliases`.
- `owner_ids`: references to `owners.yml`.
- `founded_season` and optional `retired_season`.
- `yahoo.team_keys`, `yahoo.team_ids`, and `yahoo.team_names`: maps keyed by season.
- `branding`: local identity/venue/honors paths and accessible alt text.
- `profile`: approved public summary, venue facts, honors, rivals, slogan, and fight-song title.
- `rival_franchise_ids`: canonical internal relationship references.
- `source`: public source URL and verification date.

Team names and Yahoo team keys are mutable and must never replace
`franchise_id` as the historical join key.

`retired_franchises.yml` contains only canonical `franchise_id` references. It
does not duplicate franchise facts.

The `_franchises` collection contains route documents that reference one
`franchise_id`; the reusable layout resolves all public content from canonical
data. See [Franchise Migration](FRANCHISE_MIGRATION.md) for mapping provenance,
editorial decisions, and unresolved fields.

### Historical data

- `champions.yml`: one verified title result per season with champion and
  runner-up franchise IDs/display names, final score, bracket path, season route,
  public source URL, and verification date.
- `seasons.yml`: completed-season metadata, source URLs, local source assets,
  champion references, and ordered final standings. Each standings row keeps the
  source-season display name plus a stable `franchise_id` when verified; unresolved
  identities use `null`, never `0` or a guessed join.
- `playoffs.yml`: one record per season with a local bracket and structured games.
  Games include a stable game ID, actual source round, order, seeds, display names,
  optional franchise IDs, nullable scores, winner, and a source note. Unpublished
  scores remain `null`; a third-place or consolation game is absent unless sourced.
- `drafts.yml`: one source-backed draft per year with nullable date/location,
  observed draft type, round/team counts, ordered opening slots, local result
  assets, optional board/recap assets, notes, and pick-data status. Each order
  entry preserves `display_name_that_year`; verified joins use a stable
  `franchise_id` and `mapping_status: resolved`, while uncertain identities use
  `franchise_id: null` and `mapping_status: unresolved`. Image-only selections
  remain `picks: null` with `pick_data_status: image_only_unverified` until an
  authoritative export can be checked. See [Draft Migration](DRAFT_MIGRATION.md).
- `records.yml`: typed record definitions and ranked entries with provenance.
- `votes.yml`: poll metadata, options, static result snapshots, and timestamps.

Unmigrated domains retain empty arrays. Season, champion, and playoff values are
published only after transcription and source verification; see
[History Migration](HISTORY_MIGRATION.md) for provenance and unresolved joins.

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
