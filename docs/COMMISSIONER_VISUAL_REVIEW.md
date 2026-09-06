# Commissioner review — brand, wire, Cup and draft archive

## Scope and git strategy

PR #30 was already merged as `cc18d0a` when these notes arrived. It was not
reopened or rewritten. Branch `codex/commissioner-brand-content` starts at that
merge. Draft PR #31 is its follow-up against main; there is no unmerged dependency
and neither automatic merge nor production publication is part of this task.

This follow-up combines the expressly requested presentation with the content it
must present: a shared league identity, venue terminology, Cup/photo history,
draft artwork and completed 2026 draft, plus the existing wire's feed adapter.
No Yahoo/community calculations or new infrastructure are bundled with it.

## Visual changes

- Reusable SVG RTG shield/typographic monogram with an uppercase gold-accented
  league wordmark. The homepage uses a large ruled championship banner treatment.
  This is UI branding, not a replacement for historical league/franchise art.
- Stadium-blue/navy editorial bands alternate with light reading/data surfaces.
  Team cards, profile record strips, galleries and draft cards no longer default
  to white. Verified team colors drive helmet backplates, accents and hero wash.
- Original helmet pixels remain untouched, contained and shadowed. The white or
  framed backgrounds baked into some source artwork are not removed or recolored.
- All venue labels now say **Home Field**. Internal `home_field` keys stay intact.
- Cup hero links to the canonical defending champion. A dedicated Oliver's story,
  full-original gallery and clearly contextualized historical poster follow it.
- The homepage and draft index now link to the completed 2026 draft, without a
  false countdown or invented draft-order graphic.

## Cup source audit and migration

Source, inspected September 6, 2026:
[Original League Trophy Page](https://sites.google.com/view/road-to-glory-ffl/league-trophy-page).
The complete original Oliver's text is retained as explicitly attributed archive
writing, split into readable paragraphs; one missing conjunction was supplied.
Its historic stock/award/service claims are preserved as the league's archived
account, not newly asserted current business information. The final staff/league
connection remains prominent. The original Brew Crew video is a normal external
link, not an embedded third-party player or tracking request.

The page has six content images (including the shared league logo) plus a
13-frame carousel. Media positions below exclude the sitewide first header image
and count the remaining ordinary images before carousel frames.

| Source positions | Local asset under `assets/img/cup/` | Treatment |
| --- | --- | --- |
| 1 | Existing league logo, not duplicated | Original identity preserved |
| 2 | `cup-tradition-2024.jpg` | Original poster, displayed with historical caveats |
| 3 | `brew-crew-wordmark.jpg` | Original blue/yellow wordmark |
| 4 | `brew-crew-cup.jpg` | Existing higher-resolution commissioner source reused |
| 5 | `brew-crew-history.jpg` | Existing original artwork reused |
| 6 | `olivers-street.jpg` | Exterior panorama |
| 7 | `brew-crew-entrance.jpg` | Blue awning/entrance |
| 8 | `olivers-storefront.jpg` | Parking area/storefront |
| 9, 15 | `bottle-aisle.jpg` | Duplicate carousel image represented once |
| 10, 18 | `blue-floor-aisle.jpg` | Duplicate carousel image represented once |
| 11 | `cooler-aisle.jpg` | Bottle/cooler aisle |
| 12 | `bottle-return.jpg` | Return entrance |
| 13 | `craft-beer-display.jpg` | Brewery display |
| 14 | `keg-wall.jpg` | Mountain mural and kegs |
| 16 | `yellow-step-aisle.jpg` | Yellow stool aisle |
| 17 | `stockroom-aisle.jpg` | Shelving/baskets |
| 19 | `brew-crew-forklift.jpg` | Store forklift |

**14 new Cup images: 12 distinct photographs and two historical graphics.**
JPEG bytes/dimensions are preserved. Most gallery photos are 382–680px wide;
the panorama is 1280px. No upscaling, destructive crops or Google image hotlinks.
Every gallery photograph links to its local original. Metadata/alt/source order
is maintained in `_data/cup_gallery.yml`; duplicate frames were not lost.

Historical discrepancy explicitly disclosed on the page: the old poster lists
winners only through 2024 and says nobody repeated. It predates Greendale's second
title in 2025. Its twelve-team generalization also does not describe the ten-team
inaugural year. The canonical championship data is unchanged and authoritative.

## Draft artwork audit

Source: [Original Draft Index](https://sites.google.com/view/road-to-glory-ffl/league-draft-recaps),
plus every linked 2021–2024 individual recap page. The index carries all five
order graphics. Each individual recap carries three result captures already
stored locally; no additional written recap was found. No 2026 order image or
additional draft year was linked in this source audit.

| Year | Original index content position | Local order artwork | Result coverage |
| --- | --- | --- | --- |
| 2021 | 6 | `assets/img/drafts/2021/draft-order.webp` | Three existing result images; no invented structured picks |
| 2022 | 5 | `assets/img/drafts/2022/draft-order.webp` | Existing 180-pick Yahoo board and three images |
| 2023 | 4 | `assets/img/drafts/2023/draft-order.jpg` | Existing 180-pick Yahoo board and three images |
| 2024 | 3 | `assets/img/drafts/2024/draft-order.jpg` | Existing 180-pick Yahoo board and three images |
| 2025 | 2 | `assets/img/drafts/2025/draft-order.png` | Existing commissioner artwork and 180-pick Yahoo board |
| 2026 | Not present | None; intentionally not fabricated | No verified pick board in repository |

Four new order assets; all five historical pages use the shared draft preview
component with full-size links. 2021/2022 source PNGs were losslessly encoded as
WebP: 2,563,039 → 1,972,020 bytes and 3,193,809 → 2,467,658 bytes, respectively.
Decoded pixels and original dimensions were compared and are identical. 2023/2024
JPEG bytes are unchanged. Historic names in the structured order are preserved;
retrospective artwork sometimes uses later aliases (for example Vegas Vandals).
Artwork is not used to overwrite authoritative Yahoo selections or display names.

## 2026 draft provenance

Commissioner input is authoritative: **Wednesday, September 2, 2026, 9 PM ET**
(`2026-09-02T21:00:00-04:00`, America/New_York), and the draft has occurred.
`_drafts/2026.md`, `_data/drafts.yml` and `_data/league.yml` represent those facts.
The current generated league/team/roster files contain no draft picks; historical
draft boards end at 2025. No opening order or draft type/round count is inferred
from rosters. Unknown counts remain null, not zero; order/results arrays are
explicitly empty with an unavailable status. The new page links to the 2026 hub.
Next data input: an authoritative 2026 Yahoo draft-board export or commissioner
draft-results file, not a current-roster export.

## NFL/fantasy wire

The existing six-hour GitHub Actions workflow already invokes `pull_news.py` and
publishes `_data/news.json`. Its schedule, Yahoo steps and credentials are untouched.
The improved adapter retains schema version 1 and existing `title`/`link` fields,
adds `category`, normalizes timestamps to UTC and deduplicates/sorts headlines.
Only source, title, link, published_at and category may reach public data.

Selected and HTTP/XML-verified sources:

- [CBS Sports NFL RSS](https://www.cbssports.com/rss/headlines/nfl/) — NFL news.
- [RotoWire public feeds](https://www.rotowire.com/rss/) — the publisher explicitly
  offers NFL player news for blogs/personal websites; NFL endpoint is
  `https://www.rotowire.com/rss/news.php?sport=NFL`, categorized fantasy.

Rejected during the audit: NFL.com's former RSS endpoint now returns HTML;
ESPN's endpoint returned 403; FantasyPros NFL news/articles returned empty 200
responses; NBC's tested page returned HTML. Yahoo's NFL feed returned XML but
included college-football material, so it was not selected. No restricted page
scraping, paid API, article-body ingestion or new server was introduced.

Failure behavior: retain a failed source's last good headlines while successful
sources refresh; complete failure preserves a safe previous snapshot. Without
valid history the wire has an intentional empty state. Article descriptions,
content fields and arbitrary CSV/private data are never copied. Legacy snapshots
with unsupported fields are sanitized rather than retained blindly.

The wire shows category/source, escaped headline, UTC timestamp and an external
publisher link. Animation pauses on hover and with an explicit toggle. Keyboard
focus exposes the complete original link list; repeated animation copies are
hidden from assistive technology and removed from tab order. Reduced motion uses
static content. No browser requests are made to publishers until a link is used.
Categories support a future news index; a new news backend/page was not added.

## Validation and visual evidence

The source build at `520cf81` passed [Validate Site, run 34056883534](https://github.com/stringer56/fantasy-football-site/actions/runs/34056883534).
No local Ruby is installed; the actual pinned GitHub Actions Jekyll artifact was
downloaded and served temporarily for browser review, not approximated with a
different local renderer. This is PR preview validation, not production deployment.

- `python -m compileall -q scripts tests`: pass.
- Full unit suite: **245 tests passed**, including 11 new commissioner regressions
  for branding/labels, safe wire output, failed feeds, malformed URLs, newest-first
  limits, complete local Cup/draft art, and the verified-only 2026 draft contract.
- All 13 canonical data/repository validators: pass; the compatibility Yahoo
  history validator also passes. Generated records, recaps, historical metrics
  and history discovery baseline checks are current.
- `python -m pip check`: no broken requirements. JavaScript syntax checks: pass.
- `bundle exec jekyll build`: pass in CI. Rendered-site validation: **45 pages**,
  valid assets/internal links/landmarks. Public-data and rendered privacy: pass.
- Full-route Chromium review: **225 checks, no problems reported**, using
  **1440, 1024, 768, 390 and 360px**, checking
  body overflow, missing/broken/distorted images, headings, disclosure controls,
  JavaScript errors and visible debug/private content.
- Additional focused review covers homepage, directory, Albany/Greendale,
  Cup story/gallery, draft index, and 2021/2024/2026 draft pages at all five widths.
  Representative desktop/mobile screenshots were visually inspected. Corrections
  include Cup section spacing, compact 2026 year display, readable mobile branding,
  long team-name wrapping and champion-score reflow.
- **200% text at 390px:** homepage, directory, Greendale, Cup, draft index and
  2026 draft all pass without body overflow. Ticker pause/resume, keyboard focus,
  reduced motion and no-JS headlines pass. Existing no-JS navigation, keyboard
  menu/Escape, franchise scrolling, roster expansion and contained bracket tests pass.
- Rendered search finds no obsolete standalone `Field:` venue labels. Venue
  labels say **Home Field**. `git diff --check`: pass.

Ignored local evidence is under `.cache/commissioner-verified-review/` (all-route
audit/screenshots) and `.cache/commissioner-review/` (focused views/interactions).
These are QA evidence, never production content. No source assets were stretched,
recolored or replaced. The two PNG-to-WebP conversions preserve decoded pixels.

## Handoff and remaining input

[Draft PR #31](https://github.com/stringer56/fantasy-football-site/pull/31) contains
this complete follow-up. PR #30 was already merged; no changes were retroactively
added to it and no unmerged prerequisite remains. **Do not merge automatically.**

The changed files comprise reusable layouts/includes, one lightweight CSS layer
and wire script, the news adapter/snapshot, Cup/draft metadata and pages, 18 new
local assets, 11 regressions, validators and documentation. Canonical generated
Yahoo/history/records data, franchise artwork, community configuration, workflow
files and Yahoo OAuth logic have no diff against the merged base.

Next: commissioner review/approval of PR #31, then provide an authoritative 2026
draft-results export if results should be populated. The missing historical
Albany helmet and higher-resolution originals remain optional future artwork
inputs; the approved fallback stays intact. Existing photography's baked frames
and modest source resolutions are preserved rather than artificially enhanced.
Feed availability remains publisher-dependent; refresh is scheduled every six
hours, not a live push service. No article bodies, fake picks, community ballots,
credentials or raw private inputs were introduced. GitHub Pages remains the host.
