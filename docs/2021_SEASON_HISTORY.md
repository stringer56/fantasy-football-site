# 2021 Complete Season History

## Publication status

The `/history/2021/` route is complete. It publishes ten verified standings
rows, ten resolved historical identities, 78 final matchups across Weeks 1–16,
the four-team championship bracket, the four-team consolation bracket, eight
scored postseason games, fifteen deterministic By the Numbers cards, and one
weekly-data-backed mini-recap for every franchise.

## Source hierarchy

1. `_data/yahoo_history/2021.yml` records the commissioner-authenticated Yahoo
   archive transcription: team IDs, historical names, W-L-T, PF/PA, final rank,
   closing streak, playoff seeds/finishes, and all Weeks 1–16 scores.
2. `_data/seasons.yml` preserves the Google Site division records and agrees
   with Yahoo's final standings values.
3. Yahoo's authenticated Playoffs view verifies the championship seeds, both
   semifinals, final, third-place game, and consolation structure.
4. `_data/champions.yml`, Yahoo Week 16, and
   `assets/img/history/2021/championship-matchup.jpg` agree that Albany Kneelers
   defeated Savage Huns 121.50–118.70.
5. `assets/img/history/2021/playoff-bracket.jpg` remains the approved archival
   bracket image. Its documented #2/#3 seed conflict is not silently copied
   into structured data.

The reviewed Google Site material contains historical images and result labels,
not reusable written recap prose. No human-authored narrative was overwritten.

## Final standings and franchise mappings

All ten historical display names resolve to stable franchise IDs. The notable
continuity joins are:

- The Swagger Daggers → `buffalo-bravado`
- Matthew's Optimal Team → `vegas-vandals`
- Quahog Stripes → `new-jersey-giants`

The Savage Huns links to its retired-franchise profile. There are no unresolved
2021 mappings.

## Weekly archive

The authenticated Yahoo Schedule view supplies 70 regular-season games across
Weeks 1–14. Yahoo's league-wide matchup views supply four Week 15 games and four
Week 16 games. The resulting 78-game archive is complete for the ten-team 2021
format; Yahoo did not schedule ninth- and tenth-place teams after Week 14.

Every normalized matchup includes numeric scores, winner/tie state, margin,
historical display names, stable franchise IDs, and regular/postseason status.
The committed source contains no roster or player-performance assertions.

## Playoffs and championship

Yahoo verifies the championship seeds as Albany Kneelers (1), Greendale Human
Beings (2), THE SAVAGE HUNS (3), and The Swagger Daggers (4). The approved
bracket image reverses seeds 2 and 3. The image is preserved unchanged, while
canonical structured data follows the authenticated Yahoo archive.

The scored championship bracket is:

- Albany Kneelers 128.48, The Swagger Daggers 73.26
- THE SAVAGE HUNS 93.58, Greendale Human Beings 80.04
- Albany Kneelers 121.50, THE SAVAGE HUNS 118.70

Yahoo also verifies The Swagger Daggers' 142.98–123.14 third-place win and two
rounds of consolation results determining places five through eight. Those five
games are explicitly classified as placement results and do not count as
championship-bracket wins.

## Recap and records methodology

`scripts/build_recaps.py` deterministically produces four season-narrative
paragraphs, ten team mini-recaps, eight playoff/placement recaps, one
championship recap, and fifteen By the Numbers cards. Weekly facts include the
highest and lowest scores, largest and closest margins, highest combined score,
and longest regular-season winning run.

The full 2021 archive expands weekly-derived records coverage to `Verified
2021–2025`. `scripts/build_historical_metrics.py` now incorporates all 446
verified matchups across those five seasons, while keeping placement games out
of championship-playoff totals.

## Draft and approved assets

The season page links to `/drafts/2021/`. The draft archive preserves the
verified ten-team opening order and three approved result images spanning 15
rounds. Individual selections remain image-only and are not represented as 150
structured picks.

Approved local history assets:

- `assets/img/history/2021/final-standings.jpg`
- `assets/img/history/2021/playoff-bracket.jpg`
- `assets/img/history/2021/championship-recap.jpg`
- `assets/img/history/2021/championship-matchup.jpg`

Approved draft assets remain under `assets/img/drafts/2021/`. No image is
hotlinked and no new league artwork was generated.

## Known limitations and conflicts

- The approved bracket image reverses Yahoo's verified #2/#3 seeds; structured
  data follows Yahoo and the image remains an unaltered historical artifact.
- Draft selections remain image-only rather than structured pick rows.
- No authoritative roster, player-week, or transaction narrative was recovered.
- The Yahoo archive requires commissioner authentication; sanitized canonical
  results are committed locally so the public site never requires login.

## Validation coverage

`tests/test_2021_season_history.py` verifies ten standings rows, all franchise
mappings, 16 weeks, 78 numeric matchup scores, margins and winners, the Yahoo
seed order, eight scored postseason games, champion consistency, ten weekly
mini-recaps, fifteen metrics, local assets, draft status, and routes. Repository,
history, recap, records, Yahoo-history, rendered-site, and Jekyll validators
enforce deterministic regeneration, null handling, local assets, and internal
links.
