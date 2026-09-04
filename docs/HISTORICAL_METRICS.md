# Historical Derived Metrics

## Coverage contract

The analytics layer consumes the coverage gates in
`_data/generated/history/completeness.json` and publishes two separate windows:

- **Season-level metrics — Verified 2021–2025.** Final standings, W-L-T, PF/PA,
  final rank, playoff seed, verified championships, and mapped franchise season
  summaries use this scope.
- **Weekly-derived metrics — Verified 2022–2025.** Head-to-head, weekly scoring,
  margins, regular-season result streaks, and classified playoff-game metrics use
  this scope. No 2021 weekly result enters these files.

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
resolve. All 368 recovered 2022–2025 matchups now have both identities, producing
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

## Historical identity coverage

All 2021 season-level identities now resolve. The commissioner draft-order
crosswalk maps The Swagger Daggers to Buffalo Bravado and Matthew's Optimal Team
to Vegas Vandals while preserving their historical display names. The lack of
2021 weekly scoreboards—not identity ambiguity—is why 2021 remains excluded
from weekly-derived metrics.

## Definitions

- Biggest and closest wins use absolute final-score margin; ties are excluded.
- Weekly score lists include regular and postseason Yahoo scores and retain a
  game-type label.
- Single-season streaks use regular-season games only. Ties break win and loss
  streaks and extend unbeaten streaks.
- Cross-season streaks are separate and continue only across adjacent represented
  seasons for the same canonical franchise.
- Championship totals include verified 2021–2025 season outcomes. Detailed
  playoff scoring/win-loss metrics use only classified 2022–2025 games.
- Bench records remain disabled because historical roster position and player
  scoring coverage is insufficient.

## Record Watch readiness

`record_thresholds.json` stores the current first- and tenth-place thresholds for
weekly score and victory margin, plus high/low combined matchup scores. It is an
input for a future live Record Watch feature; this milestone does not implement
live monitoring.
