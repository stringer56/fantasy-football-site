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

## Coverage scopes

Downstream builders must use the two machine-readable scopes in
`_data/generated/history/completeness.json` and must not combine them into an
all-time label:

- **Season-level metrics — Verified 2021–2025.** Final standings, W-L-T, PF/PA,
  final rank, playoff seed, verified championships, and season-level franchise
  summaries may use this window. Unresolved historical identities remain valid
  season rows but are excluded from franchise-level aggregation.
- **Weekly-derived metrics — Verified 2022–2025.** Head-to-head, largest and
  closest wins, weekly scoring highs/lows, matchup margins, weekly result streaks,
  and detailed playoff matchup metrics must use this narrower window. The 2021
  season is explicitly excluded because no Yahoo weekly scoreboards were recovered.

## Verified coverage

| Season | League key | Standings | Weekly archive | Scored matchups | Draft | Transactions | Franchise mapping |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2021 | `406.l.12928` | 10/10 commissioner-supplied Yahoo | Yahoo weekly routes require sign-in | 0 | Image-only / unverified picks | 0 | 8 resolved, 2 unresolved |
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

## Focused 2021 recovery pass

The 2021 recovery result is **Level C — Partial**. A small, sequential route
test was performed before any crawl. The working 2022 explicit archive route
returned HTTP 200, while each 2021 content route returned HTTP 302 to Yahoo's
sign-in host:

- the commissioner-linked custom history route;
- the explicit `https://football.fantasysports.yahoo.com/2021/f1/12928` route;
- the explicit 2021 standings subroute; and
- the legacy `/archive/nfl/2021/12928` form, which redirects back to the
  explicit 2021 route before the sign-in gate.

Earlier followed requests sometimes ended with HTTP 429 on the Yahoo login
destination. The archive entry route itself is now classified as authentication
required, not as an unknown league key or a recoverable rate-limit-only failure.
No full crawl followed the failed small probe.

The commissioner then supplied the authenticated Yahoo standings table. That
evidence is stored separately from automated archive output and remains
explicitly source-labelled:

- All 10 Yahoo team IDs and final standings rows are recovered. Every W-L-T and
  PF/PA value agrees with the existing Google Site/canonical table. Eight teams
  map to canonical franchises; The Swagger Daggers and Matthew's Optimal Team
  remain unresolved.
- Yahoo explicitly confirms Albany Kneelers first, The Savage Huns second, and
  The Swagger Daggers third. Other final placement values remain null.
- Fourteen regular-season games per team plus the verified semifinal and final
  rounds establish an expected 16-week season, but zero Yahoo weekly scoreboards
  were recovered.
- The playoff bracket verifies both semifinal winners and the championship;
  only the 121.50–118.70 championship has verified scores.
- Three local draft-result images cover 15 rounds and preserve the 10-team draft
  order, but pick-by-pick data remains image-only and unverified.
- No 2021 Yahoo transaction history was recovered.

Accordingly, 2021 may participate in season-level standings, PF/PA, champion,
and conservative recap features with its existing provenance under the label
**Verified 2021–2025**. It must not enter weekly head-to-head, margin, scoring,
or streak calculations. Those features retain the label **Verified 2022–2025**.

## Unresolved identities

No continuity was guessed. These names remain explicitly unresolved:

- 2022: Broncos Country Let’s Ride
- 2022: Dilly Dilly
- 2023: Broncos Country Let’s Ride

Their weekly results and draft picks are preserved under the exact historical
name with a null `franchise_id`. The commissioner-supplied 2021 Yahoo team keys
also preserve The Swagger Daggers and Matthew's Optimal Team as unresolved
rather than guessing their franchise continuity.

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

- 2021 detailed archive content redirects automated requests to Yahoo sign-in;
  its recovery level remains C.
- Three 2022–2023 historical identities remain unresolved.
- Postseason matchup lane/consolation classification is not inferred.
- Historical rosters and player points are not verified.
- 2026 is current and intentionally excluded from completed-season backfill.
