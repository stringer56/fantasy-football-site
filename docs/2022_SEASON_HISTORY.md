# 2022 Complete Season History

## Migration status

The `/history/2022/` route is a complete, data-driven season page using the
shared 2023–2025 architecture. It combines the approved 2022 commissioner art
with verified Yahoo standings, all 16 weeks, a four-team championship bracket,
one independently labelled placement game, deterministic narratives, one mini-
recap per franchise, and record-book integration.

| Item | Verified result |
|---|---|
| Franchises | 12 of 12 mapped |
| Weekly coverage | 16 of 16 weeks |
| Matchups | 92 verified final scores |
| Regular-season boundary | Weeks 1–14 |
| Championship bracket | Four teams, no byes, two semifinals, one championship |
| Placement games | One Yahoo-labelled third-place game, kept separate from the championship bracket |
| Champion | Ayahuasca Rush |
| Runner-up | Turnbull AC’s |
| Championship score | 115.20–69.16 |
| Team mini-recaps | 12 |
| By the Numbers cards | 15 |

## Source hierarchy

1. `_data/generated/history/2022/standings.json` and
   `_data/generated/history/2022/weeks.json`, recovered from the official Yahoo
   public archive at `https://football.fantasysports.yahoo.com/2022/f1/527645`.
2. Yahoo’s official 2022 Playoffs view, which publishes the four seeds, both
   semifinal scores, the championship, and the third-place game.
3. Canonical champion and season facts in `_data/champions.yml` and
   `_data/seasons.yml`.
4. The approved local Google Site and commissioner exports under
   `assets/img/history/2022/`.
5. The complete structured 2022 draft archive in `_data/drafts.yml` and
   `_data/generated/history/2022/draft.json`.

Yahoo league key `414.l.527645` is the verified 2022 Road to Glory league. The
official archive identifies Weeks 1–14 as the regular season and Weeks 15–16 as
postseason coverage.

The public Google Site was reviewed again on 2026-09-04. Its 2022 standings and
playoff sections are image-based. The championship page contains the heading
“2022 League Championship Game,” the champion label, and source images rather
than human-written recap prose. No original narrative was available to merge.

## Final standings and historical franchise mapping

All 12 final rows preserve the 2022 Yahoo display name, W–L–T record, win
percentage, PF, PA, verified championship-bracket seed where applicable, final
postseason placement, and stable franchise route.

| 2022 display name | Franchise ID | Status |
|---|---|---|
| Ayahuasca Rush | `ayahuasca-rush` | verified |
| Turnbull AC’s | `turnbull-acs` | verified |
| Greendale Human Beings | `greendale-human-beings` | verified |
| Quahog Stripes | `new-jersey-giants` | verified |
| The Baseball Furies | `baseball-furies` | verified |
| Albany Kneelers | `albany-kneelers` | verified |
| Maine Moose | `maine-moose` | verified |
| Chris's Crazy Team | `crazy-wazs-team` | verified |
| Broncos Country Let’s Ride | `vegas-vandals` | verified |
| Van Cortlant Rangers | `van-cortlant-rangers` | verified |
| THE SAVAGE HUNS | `savage-huns` | verified |
| Dilly Dilly | `buffalo-bravado` | verified |

Quahog Stripes remains visible as the historical name while its results link to
the stable New Jersey Giants franchise. Broncos Country Let’s Ride and Dilly
Dilly likewise retain their source-season names while linking to Vegas Vandals
and Buffalo Bravado. These continuity mappings were already commissioner-
confirmed and agree with the 2022 Yahoo team-key crosswalk. No 2022 identity is
`needs-review` or `unresolved`.

## Weekly archive and deterministic facts

The official Yahoo archive supplies 92 final matchups across Weeks 1–16. Every
score is numeric, every winner agrees with the two scores, and every margin is
recomputed from those values. The page renders all weeks in accessible,
closed-by-default accordions.

The recap generator calculates these 2022 signals:

- Highest weekly score: The Baseball Furies, 177.88 in Week 2
- Lowest weekly score: Broncos Country Let’s Ride, 63.84 in Week 8
- Biggest victory: Van Cortlant Rangers over Ayahuasca Rush by 95.94 in Week 5
- Closest matchup: THE SAVAGE HUNS and Dilly Dilly tied in Week 11, a 0.00 margin
- Highest combined score: Chris's Crazy Team and Ayahuasca Rush, 342.56 in Week 8
- Longest regular-season winning streak: Greendale Human Beings, eight games

The streak calculation uses the verified 2022 boundary of Week 14. This differs
from 2023–2025, whose regular seasons end in Week 13. A regression test protects
that distinction; Turnbull’s five-game and Van Cortlant’s five-game streaks both
depend on including Week 14.

## Playoff format, results, and source conflict

Yahoo’s official Playoffs view establishes a four-team championship field, no
byes, semifinals in Week 15, and the final plus third-place game in Week 16:

1. Ayahuasca Rush — champion
2. Greendale Human Beings — third place
3. Turnbull AC’s — runner-up
4. Quahog Stripes — fourth place

The championship bracket contains three games:

- Week 15: Ayahuasca Rush 149.70, Quahog Stripes 75.76
- Week 15: Turnbull AC’s 132.20, Greendale Human Beings 117.94
- Week 16: Ayahuasca Rush 115.20, Turnbull AC’s 69.16

The separately rendered placement lane contains:

- Week 16 third-place game: Greendale Human Beings 148.96, Quahog Stripes 83.12

Other Week 15–16 Yahoo matchups are retained in the complete weekly archive but
remain unclassified because Yahoo’s official Playoffs view does not label them
as part of this championship bracket. They do not count as playoff wins.

The approved bracket image labels Turnbull as seed #2 and Greendale as seed #3.
Yahoo’s official Playoffs view labels Greendale #2 and Turnbull #3, including
Turnbull as the #3 seed in the final. Structured data follows the stronger Yahoo
playoff source. The archival bracket remains unaltered and available for full-
size viewing so the historical discrepancy is visible rather than silently
erased.

## Champion verification and recap

Ayahuasca Rush, Turnbull AC’s, and the 115.20–69.16 final agree across Yahoo’s
official Playoffs view, the verified Week 16 archive, `_data/champions.yml`, the
approved bracket’s advancing teams, the champion image, and the championship
matchup capture.

The championship recap uses the verified final, final standings, and scored
postseason path. It makes no player-level claim. Player rows visible in the
archival matchup image are not transcribed into a player-history dataset.

## Approved local assets

- `/assets/img/history/2022/final-standings.jpg`
- `/assets/img/history/2022/playoff-bracket.jpg`
- `/assets/img/history/2022/championship-recap.png`
- `/assets/img/history/2022/championship-matchup.jpg`

All four assets are local and commissioner-approved. The bracket has descriptive
alt text, remains inside a contained responsive frame, and links to its original
resolution. No personal or team-folder photography is added.

## Narrative, draft, and cross-links

`scripts/build_recaps.py` deterministically regenerates a five-paragraph season
narrative, all 12 team mini-recaps, four playoff/placement recaps, the
championship recap, and 15 By the Numbers cards. Manual editorial overrides
remain separate in `_data/editorial/recaps.yml`; none is used for 2022.

The page links to `/drafts/2022/`, which preserves 180 verified selections across
15 rounds, plus `/cup/`, `/history/`, `/records/`, the champion and runner-up
profiles, and every resolved franchise route.

## Record-book effects

The historical metrics generator continues to classify the three 2022
championship-bracket games and excludes the third-place result from playoff-win
totals. The classified 2022–2025 championship-playoff count remains 18 because
those three participants and winners were already independently matched. The
canonical season page now publishes the authoritative Yahoo semifinal scores
and the labelled third-place game without changing the coverage scopes:

- Season-level: Verified 2021–2025
- Weekly-derived: Verified 2021–2025

## Corrections, unresolved values, and limitations

1. The canonical 2022 semifinal scores were previously null because the approved
   image does not print scores. Yahoo’s official Playoffs view and the verified
   weekly archive now supply both scores.
2. The official Yahoo seed order corrects the Turnbull/Greendale seed reversal
   in the archival bracket image. The image is preserved unchanged.
3. Yahoo independently labels and scores the third-place game, so it is now
   represented as a placement game and excluded from championship-playoff wins.
4. The Google Site contains no source-written 2022 season, playoff,
   championship, or team recap.
5. Historical roster/player-point coverage remains unavailable; no player,
   injury, transaction, draft-effect, strategy, luck, or causal claim is made.

No 2022 matchup score, championship participant, franchise mapping, or
championship-bracket result remains unresolved. Postseason matchups outside the
official four-team Yahoo Playoffs view remain intentionally unclassified.

## Validation contract

`tests/test_2022_season_history.py` verifies the 12 standings rows, historical
identities, all 16 weeks and 92 numeric final scores, winners and margins, Week
14 regular-season boundary, four-team playoff field, Yahoo score agreement,
third-place classification, champion/final agreement, approved local assets,
12 mini-recaps, 15 metrics cards, safe prose, route, draft, and Cup integration.
Shared history, recap, records, Yahoo, repository, and rendered-site validators
provide the cross-season regression layer.
