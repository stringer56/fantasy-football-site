# Yahoo Historical Backfill

## Outcome

The official Yahoo public league archive now provides a normalized, locally
cached source for Road to Glory results. The first completed backfill recovered
all public weekly scoreboards and draft boards for 2022–2025 without changing
the existing OAuth flow.

The generated files are evidence, not an automatic claim that every category is
an all-time league record. Downstream record and narrative builders must consult
`_data/generated/history/completeness.json` before using them.

Each season entry records direct gate fields for expected/fetched weeks and
matchups, fetched roster weeks, unresolved franchise mappings, and a conservative
confidence label. `matchups_expected` remains null when Yahoo did not expose a
schedule rather than silently treating missing games as zero.

## Verified coverage

| Season | League key | Standings | Weekly archive | Scored matchups | Draft | Transactions | Franchise mapping |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2021 | `406.l.12928` | Existing manual archive only | Public request redirects to sign-in | 0 imported | Not imported | Not imported | Existing manual mappings only |
| 2022 | `414.l.527645` | 12/12 | 16/16 weeks | 92 | 180 picks | 337 | 10 resolved, 2 unresolved |
| 2023 | `423.l.161807` | 12/12 | 16/16 weeks | 92 | 180 picks | 283 | 11 resolved, 1 unresolved |
| 2024 | `449.l.761310` | 12/12 | 16/16 weeks | 92 | 180 picks | 259 | 12 resolved |
| 2025 | `461.l.103926` | 12/12 | 16/16 weeks | 92 | 180 picks | 261 | 12 resolved |

The regular-season schedule is complete in the recovered archive for 2022–2025:
weeks 1–14 in 2022 and weeks 1–13 in 2023–2025. Yahoo also returns scored
postseason/placement matchups for the remaining weeks. Every imported matchup
has both final scores. The importer intentionally leaves `is_consolation` null
because the league-wide scoreboard does not identify bracket lanes reliably.

The two independently captured 2025 playoff sources agree on the championship
bracket scores: commissioner-supplied results remain in `2025/playoffs.json`,
while the full Yahoo weekly schedule is in `2025/weeks.json`.

## Unresolved identities

No continuity was guessed. These names remain explicitly unresolved:

- 2022: Broncos Country Let’s Ride
- 2022: Dilly Dilly
- 2023: Broncos Country Let’s Ride

Their weekly results and draft picks are preserved under the exact historical
name with a null `franchise_id`. The previously documented unresolved 2021 names
also remain unchanged because the 2021 public archive is not accessible to the
backfill client.

## Storage model

Raw HTML is cache-only and ignored by Git:

```text
.cache/yahoo-history/{season}/
```

Only allowlisted normalized JSON is committed:

```text
_data/generated/history/
  completeness.json
  {season}/
    league.json
    teams.json
    standings.json
    weeks.json
    draft.json
    transactions.json
```

Rosters and transaction files are created only when their source is normalized
and verified. No raw Yahoo response is committed.

## Running and resuming

The default command uses the verified 2021–2025 manifest and a 2.5-second
minimum delay:

```bash
python scripts/backfill_yahoo_history.py --seasons 2021-2025
```

Useful options:

- `--seasons 2024-2025` limits the run.
- `--sections league,standings,matchups,draft` selects sources.
- `--refresh` ignores cached HTML.
- `--delay 3` increases the minimum request interval.
- `--max-retries 4` controls bounded retry attempts for 429/5xx failures.
- `--include-rosters` enables the much larger roster crawl; do not use it until
  the historical identity check below is resolved.

Successful pages are cached immediately, so interrupted runs resume without
re-requesting them. Failures contain only season, section, exception type, and a
short sanitized message in `completeness.json`.

## Rate-limit behavior

`ArchiveClient` provides:

- a configurable minimum request delay;
- cache-first reads;
- bounded exponential backoff with jitter for 429 and 5xx responses;
- `Retry-After` support;
- per-request timeout;
- resumable season/week cache paths;
- sanitized errors that omit response bodies, headers, credentials, and private
  query values.

Historical backfill is manual-only. It is not part of the six-hour current-
season update workflow.

## Rosters and player points

Rosters are not published by this run. A representative 2025 historical team
page exposed a weekly points table but also contained current 2026 player/team
presentation signals. Until Yahoo's archive behavior can be verified across
multiple teams and weeks, those pages are not authoritative historical roster
snapshots.

Therefore:

- historical roster coverage is unavailable;
- historical selected-position coverage is unavailable;
- historical player weekly points are unavailable;
- bench-player scoring cannot yet be verified;
- bench-blunder records must remain unavailable.

The parser and fixtures support future ingestion, but `--include-rosters` is an
explicit opt-in and completeness must be reviewed before publication.

## Drafts and transactions

Yahoo's public draft boards are complete for 2022–2025: 15 rounds and 180 picks
per year. Exact player and historical team names are retained; unresolved teams
remain null-mapped.

Transaction pagination is complete for 2022–2025. The archive contains 1,140
normalized events across 48 pages. Add/drop pairs preserve their relationship,
public player metadata, historical team identity, and Yahoo's display timestamp.
No unsupported manager identity or account metadata is retained.

## Privacy and security

- Yahoo OAuth code and GitHub Actions secrets are unchanged.
- The backfill uses public league archive pages and requires no token.
- Raw HTML, login redirects, cookies, headers, and account data are never
  committed.
- Public output contains no email, GUID, manager/account ID, invitation key,
  access token, refresh token, client secret, or authorization header.
- `validate_public_data.py` and `validate_yahoo_history_backfill.py` scan every
  generated history file.

## Derived-stat readiness

The recovered 2022–2025 weekly results are suitable inputs for coverage-labeled
head-to-head totals, weekly scoring records, margins, and season-bounded win/loss
streaks. Those derived records are deliberately not published in this milestone.
The next milestone should add a deterministic derived-history builder, compare
its season totals to the canonical standings, and only then expand the public
record book.

## Known gaps

- 2021 public archive content redirects automated requests to Yahoo sign-in.
- Three 2022–2023 historical identities remain unresolved.
- Postseason matchup lane/consolation classification is not inferred.
- Historical rosters and player points are not verified.
- 2026 is current and intentionally excluded from completed-season backfill.
