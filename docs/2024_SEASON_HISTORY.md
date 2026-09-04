# 2024 Complete Season History

## Migration status

The `/history/2024/` route is a complete, data-driven season page using the 2025
season architecture. It preserves the approved 2024 commissioner artwork while
adding structured standings, Weeks 1–16, scored playoff and placement games,
deterministic narratives, team mini-recaps, and record-book integration.

| Item | Verified result |
|---|---|
| Franchises | 12 of 12 mapped |
| Weekly coverage | 16 of 16 weeks |
| Matchups | 92 verified final scores |
| Championship bracket | Six teams, two byes, two quarterfinals, two semifinals, one championship |
| Placement games | Fifth-place and third-place games, kept separate from the championship bracket |
| Champion | Turnbull AC's |
| Runner-up | Chris's Crazy Team |
| Championship score | 148.18–140.98 |
| Team mini-recaps | 12 |
| By the Numbers cards | 15 |

## Source hierarchy

1. `_data/generated/history/2024/standings.json` and
   `_data/generated/history/2024/weeks.json`, recovered from the official Yahoo
   public archive at `https://football.fantasysports.yahoo.com/2024/f1/761310`.
2. Canonical champion and standings facts already preserved in
   `_data/champions.yml` and `_data/seasons.yml`.
3. The approved local Google Site exports under `assets/img/history/2024/`.
4. The commissioner playoff-summary capture supplied with the migration source
   set, used to confirm the two placement games.
5. The existing structured 2024 draft archive in `_data/drafts.yml` and
   `_data/generated/history/2024/draft.json`.

The public Google Site was rechecked during this milestone. Its indexed pages
were not available to the web retriever, so the already audited local exports
and migration notes remain the reproducible Google Site record. The 2024 recap
page contains champion imagery and the final matchup capture, not source-written
narrative prose. No human-written recap was available to incorporate.

## Final standings

All 12 final rows preserve the 2024 display names, W-L-T record, calculated win
percentage, PF, PA, verified bracket seed where applicable, final playoff
placement, and stable franchise link. Final rank is postseason placement and is
not treated as the playoff seed.

The Yahoo standings parser marks playoff qualification from the asterisk in the
final-rank column. For 2024 that value reflects final placement rather than the
original bracket seed, so the canonical seeds come from the approved bracket:

1. Turnbull AC's
2. Ayahuasca Rush
3. Chris's Crazy Team
4. Albany Kneelers
5. Maine Moose
6. Greendale Human Beings

## Franchise mapping

Every 2024 Yahoo team row has `mapping_status: verified` and resolves to one
stable franchise ID. Historical capitalization and punctuation are preserved in
the season display name even when the current franchise name differs.

| 2024 display name | Franchise ID | Status |
|---|---|---|
| Turnbull AC's | `turnbull-acs` | verified |
| Chris's Crazy Team | `crazy-wazs-team` | verified |
| Maine Moose | `maine-moose` | verified |
| Ayahuasca Rush | `ayahuasca-rush` | verified |
| Albany Kneelers | `albany-kneelers` | verified |
| Greendale Human Beings | `greendale-human-beings` | verified |
| Buffalo Bravados | `buffalo-bravado` | verified |
| Van Cortlant Rangers | `van-cortlant-rangers` | verified |
| North town Ninnyhammers | `north-town-ninnyhammers` | verified |
| THE SAVAGE HUNS | `savage-huns` | verified |
| Vegas Vandals | `vegas-vandals` | verified |
| The Baseball Furies | `baseball-furies` | verified |

No 2024 mapping is `needs-review` or `unresolved`; no alias documentation needed
to change.

## Weekly archive and deterministic facts

The official Yahoo archive supplies 92 final matchups across Weeks 1–16. Scores
must be numeric, winners must agree with scores, and margins are recomputed from
the two score values. The page renders these games in closed-by-default,
accessible week accordions.

The recap generator calculates these 2024 season signals:

- Highest weekly score: Albany Kneelers, 202.90 in Week 11
- Lowest weekly score: Buffalo Bravados, 68.70 in Week 4
- Biggest victory: Maine Moose over Vegas Vandals by 76.10 in Week 5
- Closest game: Turnbull AC's over Albany Kneelers by 0.10 in Week 4
- Highest combined score: Van Cortlant Rangers and Albany Kneelers, 376.72 in Week 11
- Longest regular-season winning streak: Ayahuasca Rush, six games

These are deterministic score calculations, not editorial judgments.

## Playoffs and champion verification

The approved bracket and verified Yahoo Weeks 14–16 agree on the six-team field,
two first-round byes, advancing teams, finalists, champion, and championship
score. The canonical championship bracket contains five games:

- Week 14: Maine Moose 156.14, Albany Kneelers 103.52
- Week 14: Chris's Crazy Team 142.96, Greendale Human Beings 113.12
- Week 15: Turnbull AC's 160.30, Maine Moose 106.54
- Week 15: Chris's Crazy Team 117.34, Ayahuasca Rush 105.96
- Week 16: Turnbull AC's 148.18, Chris's Crazy Team 140.98

The verified placement lane is rendered separately:

- Week 15 fifth-place game: Albany Kneelers 143.68, Greendale Human Beings 103.14
- Week 16 third-place game: Maine Moose 149.90, Ayahuasca Rush 127.18

The champion and runner-up agree across `_data/champions.yml`, the approved
bracket, the championship matchup image, canonical playoff data, and the Yahoo
Week 16 archive.

## Approved local assets

- `/assets/img/history/2024/final-standings.jpg`
- `/assets/img/history/2024/playoff-bracket.jpg`
- `/assets/img/history/2024/championship-recap.jpg`
- `/assets/img/history/2024/championship-matchup.jpg`

The page does not hotlink these images. The bracket remains linked to its
full-resolution local file, has descriptive alt text, and is contained within
the responsive page layout.

## Recap architecture and editorial decisions

`scripts/build_recaps.py` deterministically regenerates the four-paragraph
season narrative, all 12 team mini-recaps, seven game recaps, the championship
recap, and 15 By the Numbers cards. Manual editorial overrides remain separate
in `_data/editorial/recaps.yml`; none is used for 2024 because the Google Site
did not publish written recap copy.

No player-level claim is generated. The title-game screenshot is preserved as
an approved historical image, but its player rows are not converted into a new
player-history dataset.

## Draft and cross-links

The season page links to the complete `/drafts/2024/` archive, which contains
180 verified selections across 15 rounds. It also links to `/history/`,
`/cup/`, `/records/`, the champion and runner-up profiles, every franchise in
the standings and recaps, and the local source captures.

## Record-book effects

Regenerating the historical metrics classifies the corrected Albany–Maine
quarterfinal as a championship-bracket playoff game. Classified playoff coverage
increases from 17 to 18 games. Albany's 2024 appearance and loss and Maine's
2024 quarterfinal win now enter playoff-only metrics; Buffalo is no longer
incorrectly credited with a 2024 playoff appearance. Placement games remain
excluded from playoff-win records.

## Conflicts, unresolved values, and limitations

1. The Google Site champions view reverses Turnbull's PF and PA labels relative
   to the final-standings table. Canonical data follows the final-standings table:
   PF 1610.10 and PA 1425.58. PF/PA-derived public cards retain a partial-coverage
   warning.
2. The earlier structured quarterfinal row named Buffalo Bravados as the #4 seed.
   The approved bracket and Yahoo Week 14 archive independently agree that the
   #4 seed was Albany Kneelers, so the canonical row is corrected to Albany.
3. Yahoo's final standings capture does not preserve original playoff seeds;
   seeds are taken from the approved bracket rather than inferred from rank.
4. No source-written 2024 season, playoff, championship, or team recap exists in
   the audited Google Site material.
5. No player-level championship claims are made.

No remaining 2024 matchup, franchise mapping, playoff result, or championship
field is unresolved.

## Validation contract

`tests/test_2024_season_history.py` verifies standings, mappings, weekly coverage,
all numeric scores, winner and margin calculations, playoff classification,
champion/final agreement, local bracket existence, mini-recap coverage, the
season route, the draft route, and the 15-card metrics set. Shared history,
recap, records, Yahoo, repository, and rendered-site validators provide the
cross-season regression layer.
