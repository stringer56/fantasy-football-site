# League History Migration Record

Milestone 5 migrates the public Road to Glory league-history archive into local,
structured Jekyll data and collection-backed season pages. The Google Site was
reviewed in the browser on 2026-08-31. This record distinguishes facts visible
in the source from mappings or narratives that remain unresolved.

## Migration status

- Completed seasons represented: **4** (2021–2024)
- Verified champions and runners-up: **4 of 4**
- Final standings rows transcribed: **46**
- Playoff games represented: **16**
- Locally preserved history assets: **16**
- Season routes: **4** (`/history/2021/` through `/history/2024/`)
- Stable franchise joins resolved: **41 of 46 standings rows**
- Unique historical display names still unresolved: **4**

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
| 2024 | Turnbull AC's | Chris's Crazy Team | 148.18–140.98 | 12 rows | 6 teams / 5 games | Champion artwork and Yahoo matchup capture; no written recap |
| 2023 | Greendale Human Beings | Albany Kneelers | 132.82–132.74 | 12 rows | 6 teams / 5 games | Champion artwork and Yahoo matchup capture; no written recap |
| 2022 | Ayahuasca Rush | Turnbull AC's | 115.20–69.16 | 12 rows | 4 teams / 3 games | Champion artwork and Yahoo matchup capture; no written recap |
| 2021 | Albany Kneelers | Savage Huns | 121.50–118.70 | 10 rows | 4 teams / 3 games | Champion artwork and Yahoo matchup capture; no written recap |

The year-specific championship sources are stored in `_data/seasons.yml` and
`_data/champions.yml`. The Google pages label themselves as recaps, but the
reviewed content contains a champion label plus images rather than narrative
copy. The new pages therefore publish a factual final and preserve the images;
they do not manufacture play-by-play or season stories.

## Local asset mapping

Each season folder contains four source assets:

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
| Quahog Stripes | `quahog-stripes` | Exact retired-franchise name |
| THE SAVAGE HUNS / Savage Huns | `savage-huns` | Canonical name / verified alias |
| Turnbull AC's | `turnbull-acs` | Exact canonical name |
| Van Cortlant Rangers | `van-cortlant-rangers` | Exact canonical name |
| Vegas Vandals | `vegas-vandals` | Exact canonical name |

No new aliases were necessary: every resolved historical variant was already in
the canonical franchise record. Retired teams remain linked to retired-profile
routes rather than being treated as active teams.

## Unresolved historical identities

| Display name | Season(s) | What is known | Missing proof |
|---|---:|---|---|
| Broncos Country Let's Ride | 2022, 2023 | Final rank and season statistics | Verified continuity to a canonical franchise/owner |
| Dilly Dilly | 2022 | Final rank and season statistics | Verified continuity to a canonical franchise/owner |
| The Swagger Daggers | 2021 | Final rank, playoff seed, semifinal loss | Verified continuity to a canonical franchise/owner |
| Matthew's Optimal Team | 2021 | Final rank and season statistics | Verified continuity to a canonical franchise/owner |

These rows retain the source display name and a null `franchise_id`. A zero,
guessed modern ID, or inferred alias would incorrectly create historical joins.

## Source conflicts and limitations

1. The 2024 champions page labels Turnbull's `1610.10` as PA and `1425.58` as PF.
   The final-standings table labels those same values PF and PA respectively.
   Structured standings use the table headers: PF `1610.10`, PA `1425.58`. The
   source screenshot is preserved for commissioner review.
2. The 2023 bracket graphic places the two quarterfinal winners in opposite
   semifinal lanes relative to the drawn connector lines. It still identifies
   Greendale and Turnbull as the advancing teams and Albany and Greendale as the
   finalists. The structured games preserve those advancing identities and add
   a source-conflict note; commissioner confirmation of lane ordering remains
   welcome.
3. The bracket graphics do not publish quarterfinal or semifinal scores. Those
   values are `null`, never zero. Only championship scores visible in the public
   matchup captures are structured.
4. No third-place or consolation game result is shown. Final standings include
   third-place finishers, but no unshown game is created.
5. The source does not provide written overall-season, playoff-game,
   championship, or team mini-recaps. Milestone 9 now derives conservative
   narrative from the verified structured results; it does not present those
   generated passages as migrated source prose.
6. The committed generated Yahoo fallback is from 2025 and is not used as proof
   for any 2021–2024 historical result.
7. Milestone 10 verifies the Yahoo league key for 2024 through the 2025 renewal
   metadata, but no weekly 2024 Yahoo archive has been recovered. The curated
   standings, bracket, and championship sources therefore remain authoritative.

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
- `_layouts/season.html` renders every season from those canonical records.
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

- Map the four unresolved historical display names to stable franchises, or
  confirm that they should remain season-only identities.
- Confirm the 2023 quarterfinal-winner lane ordering shown inconsistently by the
  source graphic.
- Resolve the 2024 champion PF/PA label conflict if another authoritative export
  differs from the final-standings capture.
- Supply approved regular-playoff scores, third-place results, season narratives,
  championship prose, and team mini-recaps if those records exist elsewhere.

## Recommended next milestone

Milestone 6 should migrate the draft archive: audit every public draft recap and
result, create canonical season-scoped draft data keyed by stable franchise IDs,
import local draft-board assets, build `/drafts/` and year routes, document
unresolved historical names, and validate picks, rounds, routes, and assets.
