# Yahoo Historical Backfill

## Outcome

The Yahoo league archive now provides normalized local Road to Glory results.
Public archive routes supplied 2022–2025, and the commissioner-authenticated
2021 archive supplied the remaining standings and Weeks 1–16 results. The
existing OAuth flow remains unchanged.

The generated files are evidence, not an automatic claim that every category is
an all-time league record. Downstream record and narrative builders must consult
`_data/generated/history/completeness.json` before using them.

Each season entry records direct gate fields for expected/fetched weeks and
matchups, fetched roster weeks, unresolved franchise mappings, and a conservative
confidence label. `matchups_expected` remains null when Yahoo did not expose a
schedule rather than silently treating missing games as zero.

## Coverage scopes

Downstream builders must use the two machine-readable scopes in
`_data/generated/history/completeness.json` and must not combine them into an
all-time label:

- **Season-level metrics — Verified 2021–2025.** Final standings, W-L-T, PF/PA,
  final rank, playoff seed, verified championships, and season-level franchise
  summaries may use this window. Unresolved historical identities remain valid
  season rows but are excluded from franchise-level aggregation.
- **Weekly-derived metrics — Verified 2021–2025.** Head-to-head, largest and
  closest wins, weekly scoring highs/lows, matchup margins, weekly result streaks,
  and detailed playoff matchup metrics use this window.

## Verified coverage

| Season | League key | Standings | Weekly archive | Scored matchups | Draft | Transactions | Franchise mapping |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2021 | `406.l.12928` | 10/10 authenticated Yahoo | 16/16 weeks | 78 | Image-only / unverified picks | 0 | 10 resolved |
| 2022 | `414.l.527645` | 12/12 | 16/16 weeks | 92 | 180 picks | 337 | 12 resolved |
| 2023 | `423.l.161807` | 12/12 | 16/16 weeks | 92 | 180 picks | 283 | 12 resolved |
| 2024 | `449.l.761310` | 12/12 | 16/16 weeks | 92 | 180 picks | 259 | 12 resolved |
| 2025 | `461.l.103926` | 12/12 | 16/16 weeks | 92 | 180 picks | 261 | 12 resolved |

The regular-season schedule is complete in the recovered archive for 2021–2025:
weeks 1–14 in 2021–2022 and weeks 1–13 in 2023–2025. Yahoo also returns scored
postseason/placement matchups for the remaining weeks. Every imported matchup
has both final scores. The importer intentionally leaves `is_consolation` null
because the league-wide scoreboard does not identify bracket lanes reliably.

The two independently captured 2025 playoff sources agree on the championship
bracket scores: commissioner-supplied results remain in `2025/playoffs.json`,
while the full Yahoo weekly schedule is in `2025/weeks.json`.

## Focused 2021 recovery pass

The 2021 recovery result is **Level A — Complete authenticated results**. An
initial small route test confirmed that public 2021 content routes redirect to
Yahoo's sign-in host:

- the commissioner-linked custom history route;
- the explicit `https://football.fantasysports.yahoo.com/2021/f1/12928` route;
- the explicit 2021 standings subroute; and
- the legacy `/archive/nfl/2021/12928` form, which redirects back to the
  explicit 2021 route before the sign-in gate.

The commissioner then authenticated in the Codex browser. Sanitized results are
stored separately from automated public-archive output and remain explicitly
source-labelled:

- All 10 Yahoo team IDs and final standings rows are recovered. Every W-L-T and
  PF/PA value agrees with the existing Google Site/canonical table. All ten
  teams map to canonical franchises through verified names or the commissioner
  draft-order crosswalk.
- The authenticated Schedule and matchup views supply 70 regular-season games
  and eight postseason/placement games, for 78 final matchups across Weeks 1–16.
- Yahoo explicitly verifies Albany #1, Greendale #2, THE SAVAGE HUNS #3, and The
  Swagger Daggers #4 in the championship field, plus all championship and
  consolation scores. The approved bracket image's reversed #2/#3 labels remain
  documented while structured data follows Yahoo.
- Three local draft-result images cover 15 rounds and preserve the 10-team draft
  order, but pick-by-pick data remains image-only and unverified.
- No 2021 Yahoo transaction history was recovered.

Accordingly, 2021 participates in both season-level and weekly-derived metrics
under the label **Verified 2021–2025**.

## Historical identity crosswalk

Commissioner confirmation resolves Dilly Dilly to Buffalo Bravado, Broncos
Country Let’s Ride to Vegas Vandals, and Quahog Stripes to New Jersey Giants.
Their results and draft orders preserve the exact historical names while using
stable franchise IDs. The 2021 draft-order crosswalk additionally resolves The
Swagger Daggers to Buffalo Bravado and Matthew's Optimal Team to Vegas Vandals.

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

The recovered 2021–2025 weekly results drive the coverage-labelled head-to-head,
weekly scoring, margin, streak, and classified playoff records generated by
`scripts/build_historical_metrics.py`.

## Known gaps

- 2021 detailed archive content redirects automated requests to Yahoo sign-in;
  commissioner-authenticated results are complete and recorded as recovery Level A.
- All recovered historical identities and all 2021–2025 weekly scoreboards resolve.
- Postseason matchup lane/consolation classification is not inferred.
- Historical rosters and player points are not verified.
- 2026 is current and intentionally excluded from completed-season backfill.
