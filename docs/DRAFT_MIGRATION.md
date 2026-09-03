# Draft Archive Migration Record

Milestone 6 migrates the public Road to Glory draft recap archive into local,
structured Jekyll data and collection-backed draft pages. The Google Site and
its linked public Yahoo result page were reviewed in the browser on 2026-08-31.
Only evidence attributable to this league is published.

## Migration summary

- Draft years migrated: **4** (2021–2024)
- Draft-order slots migrated: **46**
- Stable franchise joins resolved: **44 of 46 slots**
- Unresolved order entries: **2 slots / 2 unique historical names**
- Original result captures stored locally: **12**
- Verified rounds represented: **15 per year**
- Structured pick-by-pick selections: **0**
- Draft dates and locations verified: **0**
- Draft routes: **4** (`/drafts/2021/` through `/drafts/2024/`)

The source pages show a reversing order across rounds, so `draft_type: snake` is
an observation from the published sequence rather than a separate source label.

## Source audit and year status

The public [Draft Recaps hub](https://sites.google.com/view/road-to-glory-ffl/league-draft-recaps)
links four league-hosted recap pages and one external 2025 Yahoo result link.

| Year | Source Google page | Order | Board | Results | Recap | Date | Location | Franchise mapping |
|---:|---|---|---|---|---|---|---|---|
| 2024 | [2024 Draft Recap](https://sites.google.com/view/road-to-glory-ffl/league-draft-recaps/2024-draft-recap) | 12 slots | No separate board | 3 images / 15 rounds | Images only | Not published | Not published | 12 resolved |
| 2023 | [2023 Draft Recap](https://sites.google.com/view/road-to-glory-ffl/league-draft-recaps/2023-draft-recap) | 12 slots | No separate board | 3 images / 15 rounds | Images only | Not published | Not published | 12 resolved |
| 2022 | [2022 Draft Recap](https://sites.google.com/view/road-to-glory-ffl/league-draft-recaps/2022-draft-recap) | 12 slots | No separate board | 3 images / 15 rounds | Images only | Not published | Not published | 12 resolved |
| 2021 | [2021 Draft Recap](https://sites.google.com/view/road-to-glory-ffl/league-draft-recaps/2021-draft-recap) | 10 slots | No separate board | 3 images / 15 rounds | Images only | Not published | Not published | 8 resolved, 2 unresolved |

Each Google recap consists of three Yahoo screenshots covering rounds 1–6,
7–12, and 13–15. It contains no written narrative, separate draft-order image,
standalone board, date, or location. The opening order is visible in round one
and repeats consistently through the snake sequence.

## Local asset mapping

Each migrated year has these original-resolution JPEG files:

```text
assets/img/drafts/{year}/draft-results-rounds-01-06.jpg
assets/img/drafts/{year}/draft-results-rounds-07-12.jpg
assets/img/drafts/{year}/draft-results-rounds-13-15.jpg
```

All 12 assets are local; no Google image is hotlinked. The files remain between
1180 and 1280 pixels wide so the source text is readable. Every display is linked
to its full-size file and has descriptive alternative text. There is no separate
`board_asset` or `recap_asset`, so those fields remain null rather than pointing
to duplicate files.

## Stable franchise mapping

Resolved order entries reuse the Milestone 4 franchise IDs and verified aliases.
Historical labels such as `Buffalo Bravados`, `North town Ninnyhammers`,
`Dilly Dilly`, `Broncos Country Let's Ride`, `Chris's Crazy Team`, and `THE
SAVAGE HUNS` remain visible while linking to the canonical franchise. Dilly
Dilly resolves to Buffalo Bravado, Broncos Country Let's Ride resolves to Vegas
Vandals, and Quahog Stripes resolves to New Jersey Giants through
commissioner-confirmed continuity. The historical Quahog label remains visible;
`THE SAVAGE HUNS` entries continue to link to the retired-franchise profile.

The two remaining unresolved slots reuse the exact unresolved state established
in the league-history migration:

| Historical display name | Draft year(s) | Canonical ID | Status |
|---|---:|---|---|
| Matthew's Optimal Team | 2021 | `null` | Unresolved |
| The Swagger Daggers | 2021 | `null` | Unresolved |

No current franchise, owner, or mutable Yahoo team name was guessed for these
identities. Unresolved names render as text without broken profile links.

## Pick-by-pick data decision

The result images visibly contain player selections, but some historical team
labels are truncated and there is no machine-readable export in the Google
archive. A 540-selection transcription would rely on image reading and would
not independently verify every spelling, position, or NFL team. Therefore every
draft explicitly uses:

```yaml
pick_data_status: image_only_unverified
picks: null
```

The images remain authoritative source captures; no OCR output is committed as
fact. Future structured picks should come from a commissioner-supplied Yahoo
export or another authoritative table and be checked against the captures.

## The excluded 2025 link

The Draft Recaps hub labels an external Yahoo URL as `2025 Draft Results`. On
inspection, that URL rendered an unrelated eight-team league with names such as
`GRIM!!!`, `HUFFDOGZ`, and `Not Grim!!!!!`, not Road to Glory's 12-team identity
set. It also showed a 16-round result. The link is not treated as Road to Glory
evidence, no 2025 route or asset was created, and no data from that page was
copied. The commissioner should replace or confirm the intended 2025 source.

## Data and rendering architecture

- `_data/drafts.yml` is the canonical source for year metadata, opening order,
  mappings, result assets, source status, and future pick-data status.
- `_drafts/{year}.md` provides stable collection routes without duplicating data.
- `_layouts/draft.html` renders the reusable hero, order, full-size results,
  source recap statement, verified notes, and inactive analysis hooks.
- `drafts.md` renders the newest-first archive from the canonical data.
- `_layouts/season.html` links each supported season back to its draft.
- Franchise links resolve from canonical franchise data, including retired routes.

The reserved analysis modules are presentation hooks only. No grades, value,
ADP, steals, busts, or draft-slot performance are calculated in this milestone.

## Privacy and editorial review

The migrated screenshots contain public fantasy selections and public team
display names. They do not expose credentials, invitation URLs, emails, phone
numbers, home addresses, chat identifiers, or private Yahoo account IDs. No
asset required redaction. The unrelated 2025 Yahoo results were omitted both
for accuracy and editorial scope.

## Validation

`scripts/validate_draft_data.py` enforces unique years, complete unique slots,
team counts, canonical franchise references, explicit unresolved mappings,
null-not-empty unknown facts, local assets, alt text, collection routes,
corresponding season records, and explicit unverified pick status. The rendered
site validator requires all archive cards, year routes, sections, order entries,
result assets, season cross-links, and internal file targets.

## Items requiring commissioner verification

1. Supply the correct Road to Glory 2025 draft-results source; the Google Site's
   current external link points to a different league.
2. Map the two unresolved historical names to stable franchises, or confirm
   they should remain year-only identities.
3. Supply draft dates and locations for 2021–2024 if they are approved public facts.
4. Supply any separate boards or written recap copy that exists outside the
   reviewed public pages.
5. Supply an authoritative pick export before player selections are structured.

## Recommended next milestone

Milestone 7 should build the records and leaderboards foundation: define typed,
provenance-aware record schemas; add deterministic aggregation scripts for
verified season data; publish career, season, game, playoff, margin, streak, and
bench-miss records only where source inputs are complete; and document every
legacy-data gap without manufacturing results.
