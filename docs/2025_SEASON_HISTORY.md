# 2025 Complete Season History

## Public outcome

`/history/2025/` is the reference implementation for a complete Road to Glory
season page. It uses the shared season collection and layout rather than a
one-off route.

The page publishes:

- all 12 verified final standings rows;
- all 16 verified Yahoo weeks and 92 final matchups;
- the six-team playoff field, two byes, five championship-bracket games, and two
  explicitly labelled placement games;
- the 107.12–106.72 Greendale Human Beings championship result over Albany
  Kneelers;
- a deterministic four-paragraph season narrative;
- one verified mini recap for each of the 12 franchises;
- weekly scoring, margin, combined-score, and regular-season streak cards; and
- links to the 2025 Draft and Brew Crew Cup.

## Provenance

Yahoo provides the standings, weekly final scores, draft board, and public league
identity through `_data/generated/history/2025/`. The commissioner-supplied Yahoo
playoff archive in `playoffs.json` independently classifies the championship and
placement lanes. Canonical joins and public routes come from
`_data/franchises.yml`.

The page uses the already imported Greendale and Albany franchise identity art,
the commissioner-approved 2025 draft-order graphic, and the approved Brew Crew
Cup assets on their linked pages. No new personal photo or excluded archive image
is used. Because no approved 2025 bracket or championship screenshot was
imported, those sections are rendered from structured data.

## Factual boundary

The recap generator may derive only deterministic facts from the complete weekly
archive: scores, margins, combined scores, and ordered regular-season result
streaks. It does not make claims about players, injuries, luck, draft quality,
manager skill, strategy, or causation. Yahoo's league-wide postseason scoreboard
does not identify every consolation lane, so only games independently matched to
the commissioner playoff archive receive a postseason classification.

## Reuse

Future season pages can opt into the same detailed presentation by declaring a
verified `weeks_data_path`, detailed standings fields, and either a local bracket
asset or a data-driven bracket path in `_data/seasons.yml`. The shared recap
builder, layout, and validators then provide weekly accordions, season/team
metrics, bracket cards, championship presentation, and coverage checks.
