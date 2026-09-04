# 2021 Complete Season History

## Publication status

The `/history/2021/` route is complete at the season level. It publishes ten
verified final standings rows, ten resolved historical franchise identities, a
four-team championship bracket, two verified semifinal winners, the verified
championship score, twelve season-level fact cards, one conservative recap for
every team, and approved local history and draft images.

Weekly Yahoo matchup results were not recovered. The page therefore does not
publish a week-by-week archive or derive weekly scores, margins, head-to-head
results, matchup streaks, or player-level claims for 2021.

## Source hierarchy

1. `_data/yahoo_history/2021.yml`, a commissioner-supplied transcription of the
   authenticated Yahoo final standings page, supplies Yahoo team IDs, historical
   names, W-L-T, PF/PA, final rank, and the closing streak displayed by Yahoo.
2. `_data/seasons.yml` preserves the Google Site division records and the same
   verified final standings values.
3. `assets/img/history/2021/playoff-bracket.jpg` supplies the original playoff
   seeds, semifinal participants, and semifinal winners.
4. `_data/champions.yml` and
   `assets/img/history/2021/championship-matchup.jpg` agree that Albany Kneelers
   defeated Savage Huns 121.50–118.70.
5. The commissioner draft-order crosswalk and the committed franchise aliases
   establish the remaining historical identity joins.

The original Google Site did not provide reusable written season, playoff, team,
or championship prose. No human-written recap was overwritten.

## Final standings and franchise mappings

All ten standings rows retain their 2021 display names and resolve to stable
franchise IDs. The two continuity joins that do not follow from exact names are:

- The Swagger Daggers → `buffalo-bravado`
- Matthew's Optimal Team → `vegas-vandals`

Quahog Stripes resolves to `new-jersey-giants`, and The Savage Huns links to its
retired-franchise profile. There are no unresolved 2021 mappings.

Yahoo's final table and the approved bracket describe two different orderings.
The final table ranks The Swagger Daggers third and Greendale Human Beings
fourth after the postseason. The bracket labels Greendale as the No. 3 playoff
seed and The Swagger Daggers as No. 4. Canonical data preserves final rank and
playoff seed as separate fields rather than forcing one ordering onto the other.

## Playoffs and championship

The verified four-team field was Albany Kneelers (1), The Savage Huns (2),
Greendale Human Beings (3), and The Swagger Daggers (4). Albany advanced past
The Swagger Daggers, and The Savage Huns advanced past Greendale. The approved
bracket does not publish either semifinal score, so both score pairs remain
`null`, never zero. No third-place or consolation game is represented because
no independent source verifies one.

The final is the only scored 2021 playoff game: Albany Kneelers 121.50, Savage
Huns 118.70. Champion, runner-up, winner, and score agree across champions data,
playoff data, the bracket, and the championship matchup capture.

## Recap and records methodology

`scripts/build_recaps.py` produces a three-to-five-paragraph season narrative,
ten team mini-recaps, three playoff recaps, one championship recap, and twelve
By the Numbers cards. The public fact label is `Season Data — Verified 2021`.
All narrative inputs are season-level standings, displayed closing streaks,
verified playoff advancement, and the championship result.

2021 contributes to the `Verified 2021–2025` season-level records window. It
does not enter the `Verified 2022–2025` weekly-derived window. The displayed
Yahoo closing streak is a final-table field and is not treated as a calculated
weekly streak record.

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

Approved local draft assets remain under `assets/img/drafts/2021/`. No image is
hotlinked and no new league artwork was generated.

## Known limitations

- No 2021 weekly matchup scoreboard archive was recovered.
- Both semifinal scores are unavailable.
- No verified third-place or other placement game is available.
- Draft selections are preserved as source images, not structured pick rows.
- No authoritative player-level or transaction narrative is available.

These gaps remain explicit in canonical data, generated prose, validators, and
the rendered page.

## Validation coverage

`tests/test_2021_season_history.py` verifies the ten standings rows, source
agreement, all franchise mappings, final-rank/seed separation, empty weekly
coverage, the four-team field, the three playoff outcomes, the sole numeric
playoff score, champion consistency, recap boundaries, local assets, draft
status, and canonical routes. Repository validators additionally enforce null
unknowns, deterministic regeneration, internal links, and Jekyll rendering.

