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

- `founded_season`: commissioner-confirmed inaugural league season.
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
- `records.yml`: typed coverage definitions for career, season, playoff, game,
  streak, and bench domains. Every category declares its output type,
  `coverage_status`, whether calculation is allowed, source type/years/files,
  and notes. The empty `bench_blunder_schema` fixes the future entry shape
  without publishing invented rows. `scripts/build_records.py` reads these
  definitions and the canonical historical files to create the sanitized
  `_data/generated/records.json`; see
  [Records Data Coverage](RECORDS_DATA_COVERAGE.md).
- `votes.yml`: poll metadata, options, static result snapshots, and timestamps.
  It also fixes the allowed poll types, required fields, Google Forms import
  architecture, manager-only Power Ranking scoring, picks scoring, privacy
  boundary, and latest-valid-before-deadline duplicate policy. Production polls
  remain absent until the commissioner supplies them.
- `editorial/recaps.yml`: approved commissioner narrative overrides. Separate
  arrays identify season, team, playoff-game, and championship copy without
  changing generator code. Unresolved team overrides use a null franchise ID
  plus the exact historical display name.

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

### `records.json`

Contains deterministic record-book output: `generated_at`, archive coverage,
typed leaderboards, single-season records, unavailable-category states, and an
empty bench-blunder structure. Every published group carries `source_type`,
`source_years`, `source_files`, `coverage_status`, `last_generated`, and notes.
Partial groups use the label `Verified 2021–2024`; unavailable groups contain no
record values.

### Voting outputs

- `votes.json`: active and archived public poll metadata plus anonymous option
  counts/percentages. It never contains individual general-vote ballots.
- `power_rankings.json`: manager-voted aggregate rank, movement when a prior
  week exists, total points, average rank, first-place votes, and ballots counted.
  Individual ballots and Yahoo standings are not inputs to the public output.
- `picks.json`: current canonical Yahoo matchup choices, optional public vote
  percentages, weekly approved manager results, verified winner state, and the
  cumulative season Picks Leaderboard. Correctness is recorded only after Yahoo
  reports a completed matchup winner.

All three include `season`, nullable `week`, nullable `generated_at`, and a
source/coverage object with accepted, rejected, and superseded ballot counts.
Empty preseason data uses explicit unavailable states.
See [Voting Architecture](VOTING_ARCHITECTURE.md) for private export handling.

### `recaps.json`

Contains deterministic historical storytelling output in `seasons`,
`team_recaps`, `playoff_recaps`, `championship_recaps`, and `by_the_numbers`.
Every narrative carries `season`, `source_files`, `generated_at`,
`coverage_status`, `facts_used`, `warnings`, generated fallback text, selected
public text, and a public provenance label. Approved overrides remain separate
from generated prose and survive regeneration. Unresolved identities keep null
franchise routes. See [Historical Narrative System](NARRATIVE_SYSTEM.md).

### `history_manifest.json`

Contains the sanitized output of the manual Yahoo historical discovery job:
`generated_at`, `discovery_status`, verified season/game/league keys, safe
league metadata, explicit renewal relationships, endpoint capability states,
public Yahoo history URLs, the separately labeled commissioner-linked history
chain, the confirmed inaugural season, and season-scoped Yahoo-team-to-franchise mapping results. Capability
values distinguish authenticated API probes from representative official public
history pages; neither implies complete row-level ingestion. Unresolved candidate
leagues and teams remain explicitly unresolved. OAuth data, account identifiers,
invitation data, raw Yahoo responses, and authorization headers are prohibited.
See [Yahoo Historical League Discovery](YAHOO_HISTORY_DISCOVERY.md).

Sanitized recovered season data is stored in small per-season files below
`_data/generated/history/{season}/`. The 2025 playoff archive preserves scored
games, byes, bracket/placement classification, final placements, canonical
franchise mappings, coverage, and public-source provenance without copying raw
Yahoo responses.

### Yahoo public archive backfill

`_data/generated/history/completeness.json` is the coverage gate for historical
Yahoo imports. It records each season and category as `complete`, `partial`,
`unavailable`, or `not_requested`, with recovered row/week counts and sanitized
failures. A downstream builder must not publish an unsupported category merely
because a file exists.

Its `coverage_scopes` object separates source windows by metric type:

- `season_level_metrics` is labelled `Verified 2021–2025` and allows final
  standings, W-L-T, PF/PA, final rank, playoff seed, verified championships, and
  resolved franchise season summaries. Unresolved identities remain unlinked.
- `weekly_derived_metrics` is labelled `Verified 2022–2025` and allows only
  results derived from complete weekly matchups, including head-to-head, weekly
  scoring and margins, season-bounded result streaks, and detailed playoff games.
  It explicitly excludes 2021.

These scopes must never be collapsed into a single all-time label.

The 2021 entry additionally records `recovery_level`, `yahoo_route_status`,
sanitized public `routes_checked`, and source-labelled fallbacks. Commissioner-
supplied Yahoo standings provide all ten team keys and final rows; the Google
Site playoff bracket and draft images remain partial. Zero Yahoo weekly
matchups were fetched, so these sources cannot unlock weekly-derived metrics.

Per-season backfill files use these shapes:

- `league.json`: safe season/game/league metadata and renewal links.
- `teams.json`: Yahoo team key/ID, exact historical name, nullable canonical
  `franchise_id`, and explicit `mapping_status`.
- `standings.json`: final rank, W-L-T, PF/PA, streak, and the same identity fields.
- `weeks.json`: available/recovered-week coverage plus matchups containing two
  teams, final scores, winner/tie state, playoff-week flag, source, and verified
  state. Missing values remain null; projected scores are not imported.
- `draft.json`: round, round pick, sequential overall pick, exact player and
  historical team names, public Yahoo player ID, provenance, and mapping state.
- `transactions.json`: paginated add/drop/trade event type, Yahoo display
  timestamp, historical team identity, normalized player action metadata, and
  explicit pagination coverage.
- `rosters.json` (optional): season/week/team, player ID/name, selected position,
  starter-or-bench state, and verified fantasy points. It is absent until the
  public historical roster identity is trustworthy.

`_data/yahoo_history/2021.yml` is the commissioner-supplied source transcription
for the authenticated 2021 Yahoo standings page. It contains only public fantasy
team IDs/names, final standings values, playoff seeds/known finishes, provenance,
and canonical franchise joins. It contains no account or authentication data.

Raw HTML lives only under ignored `.cache/yahoo-history/`. See
[Yahoo Historical Backfill](YAHOO_HISTORY_BACKFILL.md).
