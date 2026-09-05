# 2026 Power Rankings

Week 1 intentionally has no previous rank or movement. Exact aggregate ties use shared competition ranking. A history chart remains optional until more than one finalized weekly snapshot exists.

Commissioner publication requires `--published-at`; overrides require `--override-finalized` plus `--override-reason`. See `docs/COMMUNITY_FORM_SETUP.md` for the exact Form schema.

Power Rankings are manager opinion, never Yahoo standings. Each valid ballot
ranks all twelve active franchises exactly once. First place earns 12 points,
second earns 11, through twelfth earning 1. Results sort by ranking points,
first-place votes, and better average submitted rank. An exact mathematical
tie receives a shared competition rank and displays with `T-`; franchise ID is
used only for stable presentation order.

One manager counts once per week. The latest valid submission at or before the
deadline wins, while an invalid replacement cannot erase an earlier valid
ballot. Individual ballots never enter public output.

## Preview and finalize

```powershell
python scripts/import_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1 --deadline <ANNOUNCED-ISO-DEADLINE>
python scripts/finalize_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1 --deadline <ANNOUNCED-ISO-DEADLINE> --published-at <ACTUAL-ISO-TIME>
```

Preview writes only an ignored private context-bound receipt and reports row-level rejections, duplicates, and
missing managers. Finalize writes
`_data/power_rankings/2026/week-01.json`, refuses a different overwrite, and
regenerates the current aggregate plus history. A reviewed correction requires
`--override-finalized`; rejected rows require separate `--allow-rejected`
acknowledgement.

Later weeks use the latest earlier finalized week for previous rank and
movement. Each archive row includes season/week, franchise identity, rank,
tie state, prior rank, movement, average rank, ranking points, first-place
votes, votes received, and an optional Yahoo standings rank captured from that
week’s preserved live snapshot. Missing weeks remain explicit and chart lines
do not bridge them.

## Public experience

`/power-rankings/` keeps a complete accessible HTML table without JavaScript
and adds a lightweight vanilla SVG history chart when finalized weeks exist.
Rank 1 is at the top. Desktop can show all franchises; narrow screens begin
with a focused selection and retain keyboard-accessible filters. Labels,
movement symbols, points, and focus states ensure color is never the only cue.
Reduced-motion preferences disable chart transitions.

Season facts cover weeks at #1, average/peak/low rank, Top-3 weeks, biggest
rise/fall, and statistical stability/volatility. Franchise and weekly pages use
the same finalized archive. The Power-vs-standings comparison hook is present
only where a weekly Yahoo standings snapshot exists; the full comparison chart
is intentionally deferred until enough weekly snapshots accumulate.
