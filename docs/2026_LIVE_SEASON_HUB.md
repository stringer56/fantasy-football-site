# 2026 Live Season Hub

## Scope and routes

The 2026 experience is the current-season layer above the normalized Yahoo
files. `/2026/` is the league headquarters; a weekly route is created only when
`_data/generated/live/2026/week-{week}.json` exists. The first verified route is
`/2026/week/1/`. The generator does not pre-create empty Week 2–18 pages.

The homepage contains compact modules for the featured matchup, standings,
Record Watch, the Road to Glory Wire, Power Rankings, and Pick’em. Active
franchise profiles receive a 2026 summary from the same generated source.
Only finalized Power Rankings and locked/final Pick’em aggregates can produce
community modules or League Wire headlines; importer previews never do.

## Data sources and fallback

Source priority is:

1. the secret-backed Yahoo Fantasy API GitHub Action;
2. the official public Yahoo league and team pages parsed by
   `scripts/yahoo_live.py` when the authenticated request fails;
3. the last valid normalized 2026 snapshot, clearly labelled stale;
4. an explicit unavailable state.

The fallback emits the existing allowlisted `manifest`, `league`, `teams`,
`standings`, `matchups`, and `rosters` schemas. Raw API responses and raw HTML
are never committed. Local fallback cache files remain disposable and outside
the public data model. Yahoo OAuth, secret names, and token handling are
unchanged.

The reviewed Yahoo identity lives once in `_data/site.yml`: season `2026`, game
key `470`, league ID `26455`, league key `470.l.26455`, public alias
`nfl.l.26455`, and the canonical public league URL. Header, homepage, 2026 hub,
and empty-state calls to action all read that URL from configuration and open it
with safe external-link attributes. The public fallback also starts from this
configured URL rather than synthesizing a visitor-facing address from API
identifiers.

The verified September 4, 2026 snapshot reports Week 1, twelve teams, six
matchups, preseason 0–0 standings, current projections, and twelve roster
pages. Blank preseason standings ranks remain null; they are not converted into
an invented order.

## Generated model

`scripts/build_live_season.py` joins normalized Yahoo team keys to stable
franchise IDs and writes:

- `_data/generated/live_season.json`: current hub, canonical standings,
  matchups, rosters, historical matchup context, weekly facts, Record Watch,
  community hooks, franchise summaries, and freshness state;
- `_data/generated/league_wire.json`: deterministic league-only headlines;
- `_data/generated/live/2026/week-{week}.json`: the normalized weekly view;
- `_live_weeks/2026-week-{week}.md`: a small generated route document.

New weekly snapshots also preserve that week’s standings array. Finalized
Power Rankings may attach the matching Yahoo rank as a comparison hook. A full
rankings-versus-standings history chart remains deferred until enough weekly
standings snapshots exist for an honest comparison.

The external NFL/fantasy news ticker remains separate and is labelled
`NFL + Fantasy Wire`. League Wire headlines are sourced only from current
normalized league facts and verified historical thresholds.

## Record Watch rules

Historical thresholds come from
`_data/generated/records/record_thresholds.json`, whose supported coverage is
verified 2021–2025 data. The initial tracked categories are weekly team score,
Top-10 and Top-25 score cutoffs, league/franchise highs, victory margin,
combined matchup score, and highest losing score.

- A live score may produce a proximity watch.
- A projection never promotes, replaces, or qualifies for a record.
- Only a matchup marked final can produce a verified record-book event.
- Event IDs are deterministic and de-duplicated.
- No 2026 result is inserted into the historical record generator until the
  source is final and a later reviewed integration explicitly does so.

## Incomplete features

The playoff race renders an honest foundation state. Clinched, in-position,
bubble, and eliminated labels require deterministic league-settings and
tiebreaker rules that are not yet modeled. Power Rankings and Pick’em render
their existing unavailable states until commissioner-reviewed ballots exist.
No fake rankings, picks, playoff odds, or editorial headlines are substituted.

## Validation

`scripts/validate_live_season.py` enforces 12 unique franchise joins, six
two-team current matchups, numeric-or-null scoring, final-score winner
consistency, one current matchup per franchise, unique Record Watch events,
League Wire provenance, and corresponding snapshot/route presence. Unit tests
cover the public-page fallback, blank preseason ranks, Record Watch thresholds,
final-only promotion, de-duplication, deterministic weekly facts, and explicit
stale handling.
