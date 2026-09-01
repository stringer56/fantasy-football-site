# Yahoo Historical Data Coverage

## Status

Milestone 10 establishes a manual, sanitized Yahoo historical discovery and
backfill system. It does not claim that league identity alone proves weekly data
coverage. As of the 2026-08-31 audit:

- earliest verified Yahoo league season: **2024**;
- latest verified Yahoo league season: **2025**;
- season-specific league keys verified: **2**;
- complete weekly matchups recovered: **0**;
- weekly team scores recovered: **0**;
- historical roster snapshots recovered: **0**;
- player weekly point rows recovered: **0**; and
- new weekly/game/bench record categories published: **0**.

The existing four-season Google Site archive remains the source of truth for
2021–2024 standings, brackets, and championships. Yahoo league-key verification
does not replace those curated sources.

## Verified renewal chain

| Season | Yahoo game key | Yahoo league key | Verification | Previous | Next |
|---:|---:|---|---|---|---|
| 2024 | `449` | `449.l.761310` | Yahoo's preserved 2025 league metadata identifies `449_761310` in the `renew` field | Unknown | `461.l.103926` |
| 2025 | `461` | `461.l.103926` | Sanitized Yahoo league snapshot committed from a successful authenticated fetch | `449.l.761310` | Unknown |

The configured 2026 alias `nfl.l.26455` is not treated as a resolved global
league key. The manual 2026 workflow run on 2026-09-01 failed at Yahoo's token
refresh endpoint with HTTP 400 before any Fantasy API request was made. It did
not verify 2026 metadata, team names, team keys, or franchise mappings.

No 2021–2023 league key is inferred from the Google archive, league IDs from
other leagues, or a numeric sequence.

## Coverage matrix

| Season | League key verified? | Teams | Weekly matchups | Weekly scores | Playoff weeks/scores | Rosters | Selected positions | Player points | Bench reconstruction | Head-to-head | Streaks | Margins |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|
| 2021 | No | Not queried | Unavailable | Unavailable | Curated bracket only; non-final Yahoo scores unavailable | Unavailable | Unavailable | Unavailable | No | No | No | No |
| 2022 | No | Not queried | Unavailable | Unavailable | Curated bracket only; non-final Yahoo scores unavailable | Unavailable | Unavailable | Unavailable | No | No | No | No |
| 2023 | No | Not queried | Unavailable | Unavailable | Curated bracket only; non-final Yahoo scores unavailable | Unavailable | Unavailable | Unavailable | No | No | No | No |
| 2024 | Yes | Not recovered | Not recovered | Not recovered | Curated championship score only; Yahoo weekly archive not recovered | Not recovered | Not recovered | Not recovered | No | No | No | No |
| 2025 | Yes | Sanitized final team/standings snapshot exists | Not recovered | Not recovered | Not recovered | Current-week snapshot only; not a historical archive | Current snapshot only | Not recovered | No | No | No | No |
| 2026 | No; configured alias only | Not verified | Not started | Not started | Not started | Not started | Not started | Not started | No | No | No | No |

No season currently has complete regular-season weekly coverage. Playoff scores
are not complete for any Yahoo-backed season. Head-to-head, win/loss streak,
weekly score, margin, and bench leaderboards therefore remain unavailable.

## Official API capabilities investigated

Yahoo's current official Fantasy Sports API documentation supports the
resources required by this design:

- logged-in user games and game-scoped leagues;
- season/game-code filters for NFL games;
- league metadata, teams, scoreboard by week, players, draft results, and
  transactions;
- team roster by NFL week;
- team weekly stats; and
- player stats by NFL week in league context.

Primary documentation:

- <https://sports.yahoo.com/developer/docs/>
- <https://developer.yahoo.com/fantasysports/guide/>
- <https://developer.yahoo.com/oauth2/guide/>

The implementation uses documented collection/resource composition. Player
points requested through a roster/player weekly-stats chain remain an empirical
availability check: bench reconstruction is not enabled until the response
contains both a selected bench position and a numeric Yahoo fantasy-point total
for every required player-week.

## Backfill architecture

```text
manual workflow_dispatch
  -> existing secret-backed OAuth refresh
  -> sanitized renewal discovery report
  -> verified league keys only
  -> one scoreboard request per week
  -> optional roster/player-week requests
  -> allowlisted per-season JSON
  -> completeness and privacy validation
  -> seven-day review artifact
  -> commissioner review before any repository commit
```

`.github/workflows/backfill-yahoo-history.yml` is manual-only and has read-only
repository permission. It never runs on the normal six-hour update. The workflow
does not push data; it uploads a sanitized artifact for review.

GitHub registers a new `workflow_dispatch` workflow only after its workflow file
exists on the default branch. PR validation exercises all offline discovery,
normalization, privacy, and archive tests, but the first authenticated historical
dispatch must occur after this milestone is reviewed and merged.

The request client uses an in-memory cache, a configurable inter-request delay,
bounded retries, exponential backoff for network failures and 429/5xx responses,
and `Retry-After` when supplied. The backfill writes sanitized checkpoints after
each week. `--resume` reuses already-normalized week files and avoids refetching
them. Raw Yahoo responses are never written to disk.

## Generated archive schemas

Successful reviewed backfills use:

```text
_data/generated/yahoo_history_manifest.json
_data/generated/history/{season}/matchups.json
_data/generated/history/{season}/team_weeks.json
_data/generated/history/{season}/rosters.json
_data/generated/history/{season}/player_weeks.json
_data/generated/history/{season}/facts.json
_data/generated/head_to_head.json
```

Matchup and roster rows preserve exact historical team names and use stable
franchise IDs only when a season team key or unique verified canonical alias
supports the join. Ambiguous names remain unresolved. The four unresolved names
from the curated archive remain:

- Broncos Country Let's Ride
- Dilly Dilly
- Matthew's Optimal Team
- The Swagger Daggers

No alias or owner continuity was added in this milestone.

## Publication gates

- Head-to-head pairs require complete regular-season weeks, numeric scores, and
  resolved franchise mappings for the published source period.
- Margins and weekly scoring records require every regular-season score in the
  labelled period.
- Win/loss streaks use regular-season games only, break on ties, and reset at
  every season boundary.
- Playoff and regular-season scoring remain separate.
- Bench scores require a Yahoo-selected bench position plus numeric weekly
  fantasy points. Missing points are never converted to zero.
- The bench metric is an individual bench player's actual fantasy score, not an
  optimal-lineup counterfactual.

No generated category may say “all-time” unless a later coverage review proves
the league's full historical range complete.

## Privacy and retention review

Only league keys, team keys, fantasy team names, public player metadata,
selected fantasy positions, and scores are allowlisted. OAuth tokens, Yahoo
GUIDs, manager IDs, invitation data, email addresses, private URLs, and raw
responses are prohibited.

Yahoo's Developer Network Guidelines include restrictions on retaining user
data, with exceptions only where Yahoo explicitly permits longer storage. Before
committing a successful historical artifact for indefinite public retention,
the commissioner should confirm that the repository's Yahoo API access terms
permit the intended league-history storage and display:
<https://legal.yahoo.com/us/en/yahoo/guidelines/ydn/index.html>.

## Current blocker and recovery path

The immediate blocker is the stored Yahoo refresh credential, not an API-route
or parser failure. An authorized repository administrator must refresh or
reauthorize the Yahoo credential outside source control. After that:

1. rerun **Update Yahoo Data** and verify 2026 league/team metadata;
2. run **Backfill Yahoo History** for 2024–2025 without rosters;
3. review the sanitized artifact and completeness report;
4. only then test historical rosters and player stats on one season;
5. commit validated archives on a review branch if Yahoo retention terms permit;
6. rerun record coverage before enabling any new leaderboard.
