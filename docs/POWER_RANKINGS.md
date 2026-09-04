# 2026 Power Rankings

## Canonical calculation

Power Rankings are manager opinion, not Yahoo standings. Each valid ballot
ranks all twelve active franchises exactly once. First place earns 12 points,
second earns 11, through twelfth earning 1. The public table includes rank,
average submitted rank, ranking points, first-place votes, prior rank, and
movement. Ties resolve by ranking points, first-place votes, average rank, then
stable franchise ID.

The duplicate policy remains `latest_valid_submission_before_deadline`: one
manager cannot count twice in a week, and an invalid or late replacement does
not erase an earlier valid ballot. Only team aggregates are public.

## Finalization and persistence

Use a sanitized private export and explicitly finalize the reviewed result:

```powershell
python scripts/build_power_rankings.py `
  --input private-vote-imports/power-rankings-week-01.csv `
  --finalize
```

Finalization writes an immutable weekly aggregate to
`_data/power_rankings/2026/week-01.json` and regenerates
`_data/generated/power_rankings_history.json`. A second attempt with different
content refuses to overwrite the finalized week. Later weeks automatically use
the latest earlier finalized week for prior rank and movement.

Every archived ranking row contains `season`, `week`, `franchise_id`, `rank`,
`previous_rank`, `movement`, `average_rank`, `ranking_points`,
`first_place_votes`, and `votes_received`. Missing weeks remain explicit in the
history output and line segments do not bridge those gaps.

## Public experience

`/power-rankings/` is the canonical route. The old
`/votes/power-rankings/` route remains as a compatibility link. The page keeps
the current accessible HTML table even if JavaScript fails, then adds a vanilla
SVG history chart when finalized weeks exist.

Rank 1 is at the top of the chart. Desktop starts with all franchises; narrow
screens start with the current Top 3 and provide show-all, clear, single-team,
and multi-team controls. Legend buttons and chart points are keyboard
accessible. Focus or hover identifies the week, rank, previous rank, movement,
average manager rank, and first-place votes. Color is paired with team labels,
points, and focus treatment, and reduced-motion preferences disable chart
transitions.

Season facts are deterministic: weeks at #1, average rank, peak/low rank,
Top-3 weeks, biggest rise/fall, and population-standard-deviation
stability/volatility. Franchise pages receive current, peak, low, average,
weeks-at-#1, and Top-3 summaries. Weekly hubs and the homepage show compact
Top-3 and movement modules only after a finalized aggregate exists.

No 2026 ballots are committed at this milestone, so the current page correctly
renders an unavailable state. It does not manufacture sample rankings merely
to populate the visualization.

