# League History Migration Record

Milestone 5 migrates the public Road to Glory league-history archive into local,
structured Jekyll data and collection-backed season pages. The Google Site was
reviewed in the browser on 2026-08-31 and supplemented by the commissioner
source archive on 2026-09-03. This record distinguishes source facts from
editorial narrative that remains unavailable.

## Migration status

- Completed seasons represented: **5** (2021–2025)
- Verified champions and runners-up: **5 of 5**
- Final standings rows transcribed: **58**
- Playoff games represented: **27**
- Locally preserved history assets: **16**
- Season routes: **5** (`/history/2021/` through `/history/2025/`)
- Stable franchise joins resolved: **58 of 58 standings rows**
- Unique historical display names still unresolved: **0**

The final rank in the Yahoo captures reflects the completed season, including
playoff placement. It is not assumed to be the playoff seed. Seeds come from the
separate bracket graphics.

## Source inventory and per-season migration

All four seasons use these public source hubs:

- [Past Season Standings](https://sites.google.com/view/road-to-glory-ffl/league-history/past-season-standings)
- [Past Playoff Summary](https://sites.google.com/view/road-to-glory-ffl/league-history/past-playoff-summary)
- [List of Past Champions](https://sites.google.com/view/road-to-glory-ffl/league-history/list-of-past-champions)

| Season | Champion | Runner-up | Final | Standings | Playoff field | Source recap content |
|---|---|---|---:|---:|---:|---|
| 2025 | Greendale Human Beings | Albany Kneelers | 107.12–106.72 | 12 rows | 6 teams / 7 scored games | Complete Yahoo standings, Weeks 1–16, classified playoff results, and local franchise identity art; no player-level recap |
| 2024 | Turnbull AC's | Chris's Crazy Team | 148.18–140.98 | 12 rows | 6 teams / 7 scored games | Complete Yahoo standings, Weeks 1–16, classified playoff and placement results, and approved local Google Site assets; no written recap |
| 2023 | Greendale Human Beings | Albany Kneelers | 132.82–132.74 | 12 rows | 6 teams / 7 scored games | Complete Yahoo standings, Weeks 1–16, classified playoff and placement results, and approved local Google Site assets; no written recap |
| 2022 | Ayahuasca Rush | Turnbull AC's | 115.20–69.16 | 12 rows | 4 teams / 3 games | Champion artwork and Yahoo matchup capture; no written recap |
| 2021 | Albany Kneelers | Savage Huns | 121.50–118.70 | 10 rows | 4 teams / 3 games | Champion artwork and Yahoo matchup capture; no written recap |

The year-specific championship sources are stored in `_data/seasons.yml` and
`_data/champions.yml`. The Google pages label themselves as recaps, but the
reviewed content contains a champion label plus images rather than narrative
copy. The new pages therefore publish a factual final and preserve the images;
they do not manufacture play-by-play or season stories.

## Local asset mapping

Each 2021–2024 season folder contains four source assets:

```text
assets/img/history/{year}/final-standings.jpg
assets/img/history/{year}/playoff-bracket.jpg
assets/img/history/{year}/championship-recap.{jpg|png}
assets/img/history/{year}/championship-matchup.jpg
```

The bracket and standings images are linked to their full-size local files. No
Google-hosted image URL is required at render time. The championship files keep
the source format; the 2022 champion artwork is PNG and the remaining source
exports are JPEG.

The 2025 page is deliberately data-driven because no commissioner-approved
2025 standings, bracket, or championship image has been imported. Its bracket,
scoreboard, and championship card render from verified structured results and
reuse only the already approved local franchise identity art.

## Stable franchise mapping

Mappings were accepted only when the historical display name matched a current
canonical name or an already verified alias from the franchise migration.

| Historical display | Canonical ID | Basis |
|---|---|---|
| Albany Kneelers | `albany-kneelers` | Exact canonical name |
| Ayahuasca Rush | `ayahuasca-rush` | Exact canonical name |
| The Baseball Furies / Baseball Furies | `baseball-furies` | Canonical name / verified alias |
| Buffalo Bravados | `buffalo-bravado` | Verified alias |
| Chris's Crazy Team | `crazy-wazs-team` | Verified Yahoo/profile alias |
| Greendale Human Beings | `greendale-human-beings` | Exact canonical name |
| Maine Moose | `maine-moose` | Exact canonical name |
| North town Ninnyhammers | `north-town-ninnyhammers` | Verified capitalization alias |
| Quahog Stripes | `new-jersey-giants` | Commissioner-confirmed former identity |
| THE SAVAGE HUNS / Savage Huns | `savage-huns` | Canonical name / verified alias |
| Turnbull AC's | `turnbull-acs` | Exact canonical name |
| Van Cortlant Rangers | `van-cortlant-rangers` | Exact canonical name |
| Vegas Vandals | `vegas-vandals` | Exact canonical name |
| Broncos Country Let's Ride | `vegas-vandals` | Commissioner-confirmed historical continuity |
| Dilly Dilly | `buffalo-bravado` | Commissioner-confirmed historical continuity |
| The Swagger Daggers | `buffalo-bravado` | Commissioner-provided 2021 draft-order crosswalk |
| Matthew's Optimal Team | `vegas-vandals` | Commissioner-provided 2021 draft-order crosswalk |

Commissioner-confirmed historical names are retained as canonical aliases.
Quahog results link to the current New Jersey Giants stable identity while the
historical display name remains unchanged. The Savage Huns remains linked to its
retired-franchise profile.

## Commissioner-confirmed 2021 crosswalk

The 2021 draft-order text identifies Vegas Vandals in the same opening slot
occupied by Matthew's Optimal Team in Yahoo, and Buffalo Bravado in the slot
occupied by The Swagger Daggers. Those paired source records establish the two
remaining continuity joins without changing their historical display names.

Quahog Stripes is part of New Jersey Giants franchise history for 2021–2022 and
is not counted as a separate franchise.

## Source conflicts and limitations

1. The 2024 champions page labels Turnbull's `1610.10` as PA and `1425.58` as PF.
   The final-standings table labels those same values PF and PA respectively.
   Structured standings use the table headers: PF `1610.10`, PA `1425.58`. The
   source screenshot is preserved for commissioner review.
2. The 2023 bracket graphic places the two quarterfinal winners in opposite
   semifinal lanes relative to the drawn connector lines. Yahoo Week 15 resolves
   the graphic error: Albany faced Turnbull and Greendale faced Ayahuasca. The
   structured games use those verified pairings while preserving the original
   image unchanged.
3. The 2021–2022 bracket graphics do not publish semifinal scores. Those
   canonical values remain `null`, never zero. The 2023–2025 season pages use
   independently matched Yahoo scores for every championship-bracket game.
4. No 2021–2022 third-place or consolation result is independently shown. The
   verified 2023–2025 third- and fifth-place games are included and explicitly
   classified as placement games.
5. The source does not provide written overall-season, playoff-game,
   championship, or team mini-recaps. Milestone 9 now derives conservative
   narrative from the verified structured results; it does not present those
   generated passages as migrated source prose.
6. Complete committed Yahoo weekly archives cover 2022–2025. Each canonical
   playoff classification still requires agreement with an independent bracket
   or commissioner playoff source.

## Editorial and privacy decisions

Only public football records, team display names, and league-created graphics
were migrated. No Yahoo credentials, tokens, private manager identifiers,
invitation links, private messages, personal contact details, or medical content
were copied. Player-level championship screenshots are retained because they
are part of the public source recap, but their data is not extracted into a new
player-history model in this milestone.

## Data and rendering architecture

- `_data/seasons.yml` owns year metadata, source URLs, assets, and final standings.
- `_data/champions.yml` owns one canonical championship result per year.
- `_data/playoffs.yml` owns rounds, games, seeds, scores, winners, and source notes.
- `_seasons/{year}.md` provides stable collection routes.
- `_layouts/season.html` renders every season from those canonical records and
  adds the complete weekly archive only when a season supplies a verified
  `weeks_data_path`.
- `history.md` is the newest-first season archive.
- `cup.md` reads the same championship source of truth.

This structure leaves future narrative fields optional. Commissioner-approved
story copy, game recaps, and team mini-recaps can be added without duplicating
the standings or champion records.

Milestone 9 implements that separation in `_data/generated/recaps.json` and
`_data/editorial/recaps.yml`; see [Historical Narrative System](NARRATIVE_SYSTEM.md).

## Validation

`scripts/validate_history_data.py` enforces unique years, canonical franchise
references, local source assets, collection routes, standing shapes, ordered
ranks, numeric records and scores, null-not-zero unknowns, unique playoff games,
and agreement between the champion and playoff final. The rendered-site validator
also requires every season route, archive card, Cup entry, page section, and
internal asset/link target.

## Items requiring commissioner verification

- Confirm the 2023 quarterfinal-winner lane ordering shown inconsistently by the
  source graphic.
- Resolve the 2024 champion PF/PA label conflict if another authoritative export
  differs from the final-standings capture.
- Supply approved source-written season or championship prose if it exists
  outside the audited archive.

## Recommended next milestone

Build the 2022 Complete Season History with the same normalized structure:
verified Weeks 1–16, independently classified playoffs, deterministic season and
team recaps, approved local assets, and record-book regeneration.
