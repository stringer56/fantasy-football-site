# Records Data Coverage

Road to Glory records use two explicit evidence windows. Public headings may say
**All-Time League History — 2021–2025**; coverage labels never imply data outside
the known 2021–2025 league archive.

- **Season-level metrics — Verified 2021–2025.** Final standings, W-L-T, PF/PA,
  rank, championships, and franchise season summaries may use this window. All
  58 represented team-seasons resolve to stable franchise IDs.
- **Weekly-derived metrics — Verified 2021–2025.** Head-to-head, weekly scoring,
  margins, streaks, and classified playoff-game metrics use this window.

The canonical five season pages now cover 2021–2025, each with a complete
verified weekly archive. The broader deterministic outputs live in
`_data/generated/records/` and retain their own source lists and coverage labels.

## Coverage matrix

| Category | Evidence window | Coverage | Public result |
|---|---|---|---|
| Franchise W-L-T, win percentage, PF/PA | 2021–2025 final standings | COMPLETE for stated window | Published |
| Championships and finals appearances | 2021–2025 verified outcomes | COMPLETE for stated window | Published |
| Head-to-head series | 2021–2025 weekly scoreboards | COMPLETE for stated window | Published, 78 pairs |
| Highest and lowest weekly scores | 2021–2025 weekly scoreboards | COMPLETE for stated window | Published |
| Biggest and closest victories | 2021–2025 weekly scoreboards | COMPLETE for stated window | Published |
| Win, loss, and unbeaten streaks | 2021–2025 weekly scoreboards | COMPLETE for stated window | Published |
| Classified playoff records | 2021–2025 brackets plus weekly results | COMPLETE for the independently classified championship bracket | Published; placement/ambiguous games excluded |
| Playoff droughts | Franchise tenure dates unavailable | UNAVAILABLE | Not published |
| Top 10 bench misses | Complete weekly roster/bench scoring unavailable | UNAVAILABLE | Schema only |
| Draft value, ADP, steals, and busts | 720 verified picks for 2022–2025 | PARTIAL INPUTS | Not calculated without an approved ADP/value method |

## Input audit

- Five final standings sources contain 58 resolved franchise-season rows.
- Five complete weekly archives contain 446 verified matchups, including 78
  authenticated Yahoo results from 2021.
- The 2021 commissioner draft-order crosswalk resolves The Swagger Daggers to
  Buffalo Bravado and Matthew's Optimal Team to Vegas Vandals.
- The 2021 page contributes all ten resolved final standings rows and 78 weekly
  matchups to aggregation. Streak records are recalculated from Weeks 1–14 rather
  than copying Yahoo's displayed closing-streak column.
- Twenty-one classified 2021–2025 championship-bracket games have independently
  matched participants, winners, weeks, and numeric Yahoo scores. The 2022–2025
  public archive supplies 18, and the authenticated 2021 archive supplies three.
- The complete Yahoo draft boards contain 180 picks per year for 2022–2025.
- Transaction archives are complete for 2022–2025, but no public record category
  currently turns raw transaction volume into a quality claim.

## Conflict and exclusion policy

1. The 2024 final-standings table lists Turnbull AC’s PF as `1610.10` and PA as
   `1425.58`; the champions view reverses those labels. Season-level PF/PA uses
   the canonical final-standings table and keeps the conflict documented.
2. An earlier 2024 quarterfinal transcription named Buffalo Bravados, but the
   approved bracket and Yahoo Week 14 archive agree on Albany Kneelers. The
   corrected game now enters playoff-only calculations; placement games do not.
3. The approved 2022 bracket reverses Greendale and Turnbull's seed labels
   relative to Yahoo's official Playoffs view. Canonical seeds follow Yahoo;
   the artwork remains preserved unchanged. Yahoo's scored third-place game is
   explicitly classified as placement and does not enter playoff-win totals.
4. The approved 2021 bracket reverses Yahoo's verified seeds #2 and #3. Canonical
   data follows the authenticated Yahoo playoff view—Greendale #2 and THE SAVAGE
   HUNS #3—while preserving the artwork unchanged.
5. Missing values are never converted to zero. A missing input excludes the
   affected metric or downgrades its coverage.
6. Unavailable categories carry an empty entry array and reader-facing status;
   they never render a misleading empty ranking.

## Completeness path

The next record categories require commissioner-approved weekly roster/bench
exports, franchise tenure dates, and an explicit draft-value methodology. Each
new source must retain season/week provenance and pass the records validator
before any coverage label changes.

Reliable calendar dates are not available across the normalized matchup archive,
so no On This Day event file is published. Season/week references remain factual;
they are not transformed into approximate dates.
