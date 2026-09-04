# All-Time Statistical Experience

## Published scope

Road to Glory's known league archive begins in 2021. Public statistical pages
therefore use **All-Time League History — 2021–2025** or **Verified League
History — 2021–2025**, never an unbounded all-time claim.

The deterministic archive contains 446 verified final matchups, 78 resolved
franchise pairs, 21 independently classified championship-bracket games, 58
franchise-season standings rows, 13 canonical franchise career rows, and five
verified championship results. Historical display names stay attached to their
source seasons while every aggregate uses a stable franchise ID.

## Generated architecture

`scripts/build_historical_metrics.py` reads the five normalized weekly archives,
five normalized standings files, canonical franchise mappings, playoff
classification, and championship facts. It writes the following schema-versioned
files to `_data/generated/records/`:

- `manifest.json`
- `franchise_career.json`
- `head_to_head.json`
- `biggest_wins.json`
- `closest_games.json`
- `weekly_scores.json`
- `streaks.json`
- `playoffs.json`
- `championships.json`
- `season_leaders.json`
- `record_thresholds.json`

`franchise_summaries.json` remains a generated compatibility alias during the
template migration. New pages consume `franchise_career.json`.

Every output includes a schema version, deterministic `generated_at` value, and
the appropriate bounded coverage object. The manifest records input and output
counts, unresolved-identity policy, postseason classification policy, and the
disabled bench-record flag. Regenerate with:

```powershell
python scripts/build_historical_metrics.py
python scripts/build_historical_metrics.py --check
python scripts/validate_historical_metrics.py
```

## Statistical definitions

- Career W-L-T and PF/PA come from verified final standings and represent the
  regular season. Weekly averages and opponent series come from all verified
  final Yahoo scoreboards, including postseason matchups.
- Default career rank is regular-season win percentage, then wins, then PF, with
  franchise ID as the deterministic final tie-breaker.
- A head-to-head series includes every verified matchup between two resolved
  canonical franchises. Ties count as meetings and break series win streaks.
- Biggest-win rankings exclude ties. Closest-game rankings include only decided
  games; ties are published separately.
- General weekly score rankings include regular-season and postseason scores and
  preserve `game_type` and `playoff_round` on every record.
- Single-season streaks reset at season boundaries. Cross-season streaks may
  continue only into the immediately adjacent represented season. Ties break win
  and loss streaks and extend unbeaten streaks.
- Playoff totals include only games whose season, week, participants, and winner
  independently match the championship bracket. Placement and ambiguous
  postseason games stay in general matchup history but never count as playoff
  wins or losses.
- Championship totals use the five canonical champion/runner-up results and
  consolidate historical names under stable franchise identities.

## Public experience

- `/all-time-standings/` provides the canonical career table with keyboard-
  accessible client-side sorting.
- `/head-to-head/` provides shareable `?a=&b=` comparisons, complete series
  totals, landmark games, streaks, and postseason meetings.
- `/records/` publishes career, weekly, margin, streak, playoff, championship,
  cross-season, and Record Watch views without becoming a wall of tables.
- `/championships/` publishes the five finals and canonical franchise leaderboards.
- Every franchise route includes career, weekly, records, season, opponent,
  championship, and verified timeline modules.

Rivalry data exposes nullable `rivalry_title` and `editorial_history` fields plus
participants, series totals, memorable meetings, playoff meetings, largest wins,
closest game, and current streak. No rivalry names or editorial history are
invented.

## Record Watch

`record_thresholds.json` stores archive benchmarks for the #1, #10, and #25
weekly scores; largest and #10 victory margins; high and low combined scores;
highest losing score; lowest winning score; and per-franchise score, margin, and
combined-score records. It has no live Yahoo dependency.

## Explicit exclusions

- Bench-player records remain disabled because authoritative historical
  starter/bench scoring is unavailable.
- Playoff droughts remain unpublished because verified franchise tenure dates
  are incomplete.
- No `_data/generated/history/events.json` is produced. The normalized archive
  verifies season and week but does not provide reliable calendar dates for all
  matchups; week numbers are not converted into invented dates.
- Named rivalry pages, Hall of Fame, awards, playoff odds, and live weekly recap
  generation are outside this milestone.

## Validation contract

`scripts/validate_historical_metrics.py` rebuilds every output in memory and
requires byte-equivalent data, valid coverage metadata, exactly-once H2H matchup
usage, correct winner/margin/tie logic, career-to-regular-season reconciliation,
playoff and title reconciliation, canonical franchise references, correctly
sorted rankings, threshold agreement, and the absence of bench records.

Rendered-site validation covers the four new statistical routes and franchise
modules. Tables contain their own horizontal scrolling regions; page-level
overflow is not intentional.

## Known evidence boundaries

The 2024 final standings table remains authoritative for Turnbull AC's PF/PA
despite the preserved champions-view label reversal. The 2022 and 2021 approved
bracket artwork reverses seeds #2 and #3 relative to authenticated Yahoo data;
structured seeds follow Yahoo while the approved artwork remains unchanged.
Those documented conflicts do not affect matchup scores, champions, or canonical
franchise continuity.
