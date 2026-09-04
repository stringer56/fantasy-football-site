# 2023 Complete Season History

## Migration status

The `/history/2023/` route is a complete, data-driven season page using the same
shared architecture as 2024 and 2025. It combines the approved 2023 archive
artwork with verified Yahoo standings, Weeks 1–16, classified playoff and
placement games, deterministic narratives, team mini-recaps, and record-book
integration.

| Item | Verified result |
|---|---|
| Franchises | 12 of 12 mapped |
| Weekly coverage | 16 of 16 weeks |
| Matchups | 92 verified final scores |
| Championship bracket | Six teams, two byes, two quarterfinals, two semifinals, one championship |
| Placement games | Fifth-place and third-place games, kept separate from the championship bracket |
| Champion | Greendale Human Beings |
| Runner-up | Albany Kneelers |
| Championship score | 132.82–132.74 |
| Team mini-recaps | 12 |
| By the Numbers cards | 15 |

## Source hierarchy

1. `_data/generated/history/2023/standings.json` and
   `_data/generated/history/2023/weeks.json`, recovered from the official Yahoo
   public archive at `https://football.fantasysports.yahoo.com/2023/f1/161807`.
2. Canonical champion and season facts in `_data/champions.yml` and
   `_data/seasons.yml`.
3. The approved local Google Site and commissioner exports under
   `assets/img/history/2023/`.
4. The approved bracket plus Yahoo Weeks 14–16 for the championship lane.
5. The final-standings capture plus Yahoo Weeks 15–16 for the fifth- and
   third-place results.
6. The complete structured 2023 draft archive in `_data/drafts.yml` and
   `_data/generated/history/2023/draft.json`.

The audited Google Site championship page contains champion imagery and the
final Yahoo matchup capture rather than source-written recap prose. No
human-written season, playoff, championship, or team recap was available to
incorporate.

## Final standings and playoff seeds

All 12 final rows preserve the source-season display name, W–L–T record,
calculated win percentage, PF, PA, playoff seed where applicable, final playoff
placement, and stable franchise link.

Yahoo's final standings rank reflects completed postseason placement rather
than original bracket seeding. The approved bracket establishes the actual
2023 seeds:

1. Albany Kneelers
2. Ayahuasca Rush
3. THE SAVAGE HUNS
4. Greendale Human Beings
5. Maine Moose
6. Turnbull AC's

## Franchise mapping

Every 2023 Yahoo team row has `mapping_status: verified` and resolves to one
stable franchise ID. Historical punctuation, capitalization, and names remain
season-accurate on the page.

| 2023 display name | Franchise ID | Status |
|---|---|---|
| Greendale Human Beings | `greendale-human-beings` | verified |
| Albany Kneelers | `albany-kneelers` | verified |
| Turnbull AC's | `turnbull-acs` | verified |
| Ayahuasca Rush | `ayahuasca-rush` | verified |
| THE SAVAGE HUNS | `savage-huns` | verified |
| Maine Moose | `maine-moose` | verified |
| Buffalo Bravados | `buffalo-bravado` | verified |
| North town Ninnyhammers | `north-town-ninnyhammers` | verified |
| The Baseball Furies | `baseball-furies` | verified |
| Broncos Country Let's Ride | `vegas-vandals` | verified |
| Van Cortlant Rangers | `van-cortlant-rangers` | verified |
| Chris's Crazy Team | `crazy-wazs-team` | verified |

No 2023 mapping is `needs-review` or `unresolved`. Broncos Country Let's Ride
retains its historical name while linking to the stable Vegas Vandals
franchise, following commissioner-confirmed ownership continuity.

## Weekly archive and deterministic facts

The official Yahoo archive supplies 92 final matchups across Weeks 1–16. Every
score is numeric, each winner agrees with the score, and every margin is
recomputed from the two final values. Week accordions are accessible and closed
by default.

The deterministic recap generator calculates these season signals:

- Highest weekly score: Maine Moose, 237.18 in Week 5
- Lowest weekly score: The Baseball Furies, 56.02 in Week 4
- Biggest victory: Maine Moose over North town Ninnyhammers by 113.66 in Week 5
- Closest game: Greendale Human Beings over Albany Kneelers by 0.08 in Week 16
- Highest combined score: Maine Moose and North town Ninnyhammers, 360.70 in Week 5
- Longest regular-season winning streak: Albany Kneelers, nine games

These are deterministic score calculations, not editorial judgments.

## Playoff format, bracket correction, and champion verification

The approved bracket and verified Yahoo Weeks 14–16 agree on the six-team
field, two first-round byes, advancing teams, finalists, champion, and final
score. The championship bracket contains five games:

- Week 14: Greendale Human Beings 132.76, Maine Moose 101.62
- Week 14: Turnbull AC's 120.22, THE SAVAGE HUNS 107.84
- Week 15: Albany Kneelers 114.38, Turnbull AC's 61.38
- Week 15: Greendale Human Beings 118.32, Ayahuasca Rush 73.44
- Week 16: Greendale Human Beings 132.82, Albany Kneelers 132.74

The bracket image draws the two quarterfinal winner connectors toward the
opposite semifinal participants. Yahoo Week 15 resolves that graphic error:
Albany faced Turnbull, while Greendale faced Ayahuasca. The structured bracket
uses those verified pairings; the approved image remains available as the
unaltered archival artifact.

The placement lane is rendered separately:

- Week 15 fifth-place game: THE SAVAGE HUNS 128.40, Maine Moose 72.84
- Week 16 third-place game: Turnbull AC's 108.30, Ayahuasca Rush 86.78

Those pairings and scores come from Yahoo, and their placement labels are
independently supported by the source final standings. Placement games do not
count as championship-bracket playoff wins.

The champion, runner-up, and 132.82–132.74 result agree across
`_data/champions.yml`, the approved bracket, the championship matchup image,
the final standings, canonical playoff data, and Yahoo Week 16.

## Approved local assets

- `/assets/img/history/2023/final-standings.jpg`
- `/assets/img/history/2023/playoff-bracket.jpg`
- `/assets/img/history/2023/championship-recap.jpg`
- `/assets/img/history/2023/championship-matchup.jpg`

No image is hotlinked. The bracket has descriptive alt text, a contained mobile
scroll region, and a link to the full-resolution local file. Personal imagery
excluded by the commissioner archive audit is not used.

## Narrative, draft, and cross-links

`scripts/build_recaps.py` deterministically regenerates a five-paragraph season
narrative, all 12 team mini-recaps, seven game recaps, the championship recap,
and 15 By the Numbers cards. Manual editorial overrides remain separate in
`_data/editorial/recaps.yml`; none is used for 2023.

No player-level, injury, transaction, strategy, luck, or causal claim is
generated. The championship screenshot is retained as an approved historical
image, but its player rows are not transcribed into a player-history dataset.

The season page links to `/drafts/2023/`, which preserves 180 verified picks
across 15 rounds, as well as `/cup/`, `/history/`, `/records/`, the champion and
runner-up profiles, and every mapped franchise page.

## Record-book effects

The historical records generator already matched all five 2023 championship-
bracket games to the complete Yahoo archive. Adding source scores and explicit
placement rows to the canonical season page does not broaden the coverage
windows. The later authenticated 2021 migration brings the current total to 21
classified championship-bracket games. The two 2023
placement games remain excluded from playoff-only records.

## Conflicts, corrections, and limitations

1. The bracket's crossed semifinal connectors are corrected only in structured
   data, using the verified Yahoo Week 15 pairings. The archival image is not
   altered.
2. Yahoo final rank is not used as the playoff seed; seed values come from the
   approved bracket.
3. The Google Site provides no source-written 2023 narrative prose.
4. Historical roster and player-point coverage remains unavailable, so no
   player-level championship claim or bench-blunder record is produced.

No remaining 2023 matchup, playoff result, championship field, or franchise
mapping is unresolved.

## Validation contract

`tests/test_2023_season_history.py` verifies standings, mappings, complete
weekly coverage, numeric scores, winners, margins, corrected semifinal lanes,
playoff/placement classification, champion/final agreement, local assets,
mini-recap coverage, route and draft integration, metrics, and safe prose.
Shared history, recap, records, Yahoo, repository, and rendered-site validators
provide the cross-season regression layer.
