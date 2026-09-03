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
resolve. A resolved franchise's own weekly summary may retain a result against an
unresolved historical opponent, but opponent-dependent records and head-to-head
pairs require both identities.

## Playoff classification

Yahoo's league-wide postseason scoreboard does not identify consolation lanes.
The builder therefore calls a game a `championship_playoff` only when its season,
week, participants, and winner independently match `_data/playoffs.yml` or the
verified 2025 playoff archive. Placement and ambiguous postseason games remain
available to general matchup history but do not count as championship-playoff
wins.

One 2024 quarterfinal conflict remains intentionally unclassified: the canonical
bracket lists Buffalo Bravado against Maine Moose, while Yahoo Week 14 records
Albany Kneelers against Maine Moose. No side is selected by assumption.

## Unresolved identities

The Swagger Daggers, Matthew's Optimal Team, Broncos Country Let’s Ride, and
Dilly Dilly remain unresolved wherever they appear. The builder excludes 42
2022–2025 matchups from pair/opponent-dependent canonical metrics because at
least one side is unresolved. It does not create aliases or modify franchise
history.

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
