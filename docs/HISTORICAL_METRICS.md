# Historical Derived Metrics

## Coverage contract

The analytics layer consumes the coverage gates in
`_data/generated/history/completeness.json` and publishes two separate windows:

- **Season-level metrics — Verified 2021–2025.** Final standings, W-L-T, PF/PA,
  final rank, playoff seed, verified championships, and mapped franchise season
  summaries use this scope.
- **Weekly-derived metrics — Verified 2021–2025.** Head-to-head, weekly scoring,
  margins, regular-season result streaks, and classified playoff-game metrics use
  this scope.

Neither window is described as all-time.

## Deterministic build

Run:

```powershell
python scripts/build_historical_metrics.py
python scripts/build_historical_metrics.py --check
python scripts/validate_historical_metrics.py
```

The builder reads normalized final Yahoo matchups, verified standings, canonical
franchises and championship facts, and playoff classification sources. It writes
nine schema-versioned files under `_data/generated/records/`. Repeated builds
with unchanged inputs produce identical bytes.

General weekly rankings use final Yahoo matchups where both canonical identities
resolve. All 446 recovered 2021–2025 matchups now have both identities, producing
78 franchise-pair series without an unresolved-matchup exclusion.

## Playoff classification

Yahoo's league-wide postseason scoreboard does not identify consolation lanes.
The builder therefore calls a game a `championship_playoff` only when its season,
week, participants, and winner independently match `_data/playoffs.yml` or the
verified 2025 playoff archive. Placement and ambiguous postseason games remain
available to general matchup history but do not count as championship-playoff
wins.

The approved 2024 bracket and Yahoo Week 14 archive independently identify
Albany Kneelers against Maine Moose. Correcting the earlier Buffalo transcription
allows that quarterfinal to enter the classified playoff metrics. The 2024 and
2025 placement games remain explicitly excluded from playoff-win calculations.

The complete 2023 season audit adds numeric scores to all five canonical
championship-bracket games and resolves the bracket image's crossed semifinal
connectors through Yahoo Week 15. Its verified third- and fifth-place games are
also explicit, but remain excluded from playoff-win calculations.

The complete 2022 audit adds Yahoo's authoritative scores to both semifinals,
confirms the four-team field, and records Yahoo's separately labelled third-place
game. The three championship-bracket games were already independently matched,
so classified playoff coverage remains 18 games; the third-place game stays
excluded from playoff-win calculations. Yahoo's official bracket also resolves
the source artwork's reversed #2/#3 seed labels in favor of Greendale #2 and
Turnbull #3.

The authenticated 2021 audit adds all 78 weekly results and independently
classifies its three championship-bracket games. Five consolation/placement
games remain available to general matchup history but stay outside
championship-playoff win totals. Structured seeds follow Yahoo where the
preserved bracket image reverses seeds #2 and #3.

## Historical identity coverage

All 2021 identities now resolve. The commissioner draft-order
crosswalk maps The Swagger Daggers to Buffalo Bravado and Matthew's Optimal Team
to Vegas Vandals while preserving their historical display names.

## Definitions

- Biggest and closest wins use absolute final-score margin; ties are excluded.
- Weekly score lists include regular and postseason Yahoo scores and retain a
  game-type label.
- Single-season streaks use regular-season games only. Ties break win and loss
  streaks and extend unbeaten streaks.
- Cross-season streaks are separate and continue only across adjacent represented
  seasons for the same canonical franchise.
- Championship totals include verified 2021–2025 season outcomes. Detailed
  playoff scoring/win-loss metrics use only independently classified 2021–2025 games.
- Bench records remain disabled because historical roster position and player
  scoring coverage is insufficient.

## Record Watch readiness

`record_thresholds.json` stores the current first- and tenth-place thresholds for
weekly score and victory margin, plus high/low combined matchup scores. It is an
input for a future live Record Watch feature; this milestone does not implement
live monitoring.
