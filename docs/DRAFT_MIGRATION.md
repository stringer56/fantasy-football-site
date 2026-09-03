# Draft Archive Migration Record

The draft archive combines commissioner-provided source files, the original
Google Site recap captures, and verified official Yahoo public draft boards.
Only data attributable to Road to Glory is published.

## Current coverage

- Draft years: **5** (2021–2025)
- Draft-order slots: **58 of 58 resolved to stable franchises**
- Original result captures: **12** (three per season for 2021–2024)
- Commissioner order graphics: **1** (2025)
- Verified structured selections: **720** (180 per season for 2022–2025)
- Image-only selections: **2021**
- Commissioner-confirmed draft dates: **1** (August 28, 2025 at 8:00 p.m. EDT)
- Draft routes: **5** (`/drafts/2021/` through `/drafts/2025/`)

All five drafts use a snake format. For 2022–2025, the alternating order is
verified by the complete Yahoo boards. The 2021 format remains an observation
from the published result captures.

## Sources by season

| Year | Opening order | Results | Structured picks | Mapping |
|---:|---|---|---:|---:|
| 2025 | Commissioner text and graphic | Official Yahoo public board | 180 | 12/12 |
| 2024 | Google Site recap | 3 captures plus official Yahoo board | 180 | 12/12 |
| 2023 | Google Site recap | 3 captures plus official Yahoo board | 180 | 12/12 |
| 2022 | Google Site recap | 3 captures plus official Yahoo board | 180 | 12/12 |
| 2021 | Commissioner text plus Google Site recap | 3 captures | Image-only | 10/10 |

The Google Site's old external “2025 Draft Results” link previously led to an
unrelated league and remains excluded. The 2025 page instead uses the
commissioner-provided Road to Glory order and the verified Yahoo league
`461.l.103926` draft archive.

## Identity crosswalk

Historical display names stay visible on draft pages while linking to their
stable franchise records. The commissioner-provided opening orders close the
last two 2021 gaps:

| Historical name | Stable franchise |
|---|---|
| Matthew's Optimal Team | `vegas-vandals` |
| The Swagger Daggers | `buffalo-bravado` |
| Quahog Stripes | `new-jersey-giants` |

The first two joins are supported by the 2021 order's franchise names in the
same slots occupied by those Yahoo display names. Quahog continuity was
separately commissioner-confirmed. No unresolved draft-order identity remains.

## Assets and rendering

The 2021–2024 captures remain at:

```text
assets/img/drafts/{year}/draft-results-rounds-01-06.jpg
assets/img/drafts/{year}/draft-results-rounds-07-12.jpg
assets/img/drafts/{year}/draft-results-rounds-13-15.jpg
```

The commissioner graphic for 2025 is
`assets/img/drafts/2025/draft-order.png`. The reusable draft layout displays
the ordered franchise list, local source images, and expandable round tables
for every season with structured Yahoo picks.

`_data/drafts.yml` is the canonical metadata source. Structured rows remain in
`_data/generated/history/{year}/draft.json`; they are not duplicated in YAML.
Collection files in `_drafts/` provide stable routes.

## Editorial limits

No draft grades, steals, busts, or ADP claims are generated yet. The complete
2022–2025 boards make those analyses possible, but any future metric must define
its comparison method and provenance first. The 2021 player board remains
image-only until an authoritative machine-readable source is supplied.

## Validation

`scripts/validate_draft_data.py` checks all five years, unique slots, stable
franchise links, source URLs, local assets, complete Yahoo board status, exact
pick counts, and collection routes. The rendered-site validator checks all five
archive cards, each draft route, all 15 structured rounds where available, and
every local source link.

## Remaining commissioner inputs

1. Draft dates and locations for 2021–2024, if they are approved public facts.
2. A machine-readable 2021 Yahoo draft export, if one exists.
3. Any written season-specific draft recap copy intended for publication.
