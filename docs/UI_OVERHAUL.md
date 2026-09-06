# UI Overhaul — League publication and franchise profiles

## Broader second-pass refinement — September 6, 2026

Continued the requested visual review on `codex/ui-overhaul-team-pages`, draft
PR #30. This is the substantive follow-up to the field-caption pass below, not
another redesign. No merge, new branch, data changes or new features.

Additional implementation files: `_includes/franchise-card.html`,
`assets/css/franchises.css`, `assets/css/publication.css`, and
`tests/test_professional_ui.py`. Updated this report and `docs/DESIGN_SYSTEM.md`.
No new production assets/files or obsolete infrastructure removed.

| Area | Observed finding and refinement |
| --- | --- |
| Mobile covers | Tightened hero, owner, honors and CTA spacing. At 390px, the home hero decreases from 773 to 729px, Greendale from 739 to 659px, Albany from 709 to 621px. Helmets remain prominent and contained. |
| Team directory | Stack each editorial panel at 1100px; consistent 22rem portrait rows align tablet captions. Keep two directory columns until 600px. Excerpts now end on word boundaries instead of clipping words. |
| Typography | Soften secondary navigation, card headings and jump links; slightly enlarge small identity labels. Preserve full original profile writing and league personality. |
| Record tables | Fixed a genuine inherited hover defect: sort labels became navy on a navy header. Hover and keyboard focus now remain white; keyboard sorting and `aria-sort` verified. |
| Text enlargement | At 200% root text size, found and fixed overflow in the homepage news label, archive images/footer, long matchup names and franchise championship subheads. Home, directory, Greendale and North Town now reflow at 390px. |
| Interaction | Whole-card hover/focus also underlines the franchise name. Existing outlines, reduced-motion behavior, navigation and accessible scroll containers remain. |
| Other routes | History, season, Cup, records, drafts, community, rules and both archive pages retain the canonical publication design. No gratuitous redesign or copy rewrite. |

Actual Jekyll artifact reviewed: commit
`a9105763b0ca8ffbd10c2fdda3309d53d830e46a`, successful build
https://github.com/stringer56/fantasy-football-site/actions/runs/34052737559.
Four new regression tests bring the suite to **234 passing tests**. All 13
canonical validators, compileall, pip check, three generator check modes,
Yahoo discovery dry-run check and git diff check passed. CI also passed the
pinned Jekyll build, rendered-site/privacy validation and JavaScript syntax checks.
The downloaded artifact independently passed 44-route link/landmark validation
and the public privacy scan. Local Ruby is unavailable; build evidence is the
actual GitHub Actions output, not a substituted local renderer.

All 44 public routes were reviewed at 1440/1024/768/390/360, with representative
screenshots: **220 checks passed, zero problems**. The focused profile/archive
review passed **101 checks**, covering
all 12 active franchises and both archive destinations at those widths. The
additional no-JS, keyboard/Escape, reduced-motion, roster and bracket interaction
checks passed. Four enlarged-text scenarios passed without body overflow.
Screenshot comparisons include mobile home/Greendale/Albany, aligned tablet
directory portraits, the focused record header and the preserved archive covers.

Evidence is ignored and not published: `.cache/professional-ui/refined-review/`,
`refined-details/`, and `polish-comparison/`. No identity image distortion,
source image edits, broken assets or private data were introduced. Field captions
still use **Field: [canonical home field]**. Historical narratives/calculations,
Yahoo OAuth/fallback, community configuration and all canonical data are unchanged.
No secrets, frameworks, external dependencies or extra asset requests were added.
Google Forms remain optional; dormant community pages remain intentional.

**Ready for commissioner visual sign-off; PR remains a draft and is not merged.**
Remaining limits are approved-source image resolution, missing approved
current-name Albany artwork, and Chromium-only browser coverage. Next step:
commissioner review of the home page, Teams directory and representative franchise
covers on desktop and phone, followed by explicit approval or specific visual notes.

## Second-pass sign-off and field captions — September 6, 2026

Continued on draft PR #30; no new branch and no merge. Requested portrait titles
now read **Field: [canonical home field]** on all twelve directory cards and the
full-size venue galleries. Quahog's historical venue reads **Field: Quahog Dome**.
Team names, coach names, historical writing and field-name data are unchanged.

Additional files modified: `_includes/franchise-card.html`,
`_includes/franchise-gallery.html`, `retired/quahog-stripes.md`,
`tests/test_professional_ui.py`, `scripts/validate_built_site.py`,
`scripts/audit_browser.py`, and this report. No files or artwork removed.

| Review area | Finding / action |
| --- | --- |
| Team pages | Venue captions needed explicit context; prefixed them with `Field:` using escaped canonical names. Retained the complete helmet, readable coach/story treatment and dated career ledger. |
| Team index | All twelve portraits reviewed together. Explicit field labels clarify the venue text; added a geometric caption/helmet overlap check for long names. |
| Homepage | Cup/champion composition, wire, matchups, standings and subdued community sections remain coherent; no additional change needed. |
| History / Records / Drafts / Cup | Existing chronology, numerical hierarchy, accessible tables and full-size artwork remain consistent; no additional change needed. |
| Community | Dormant states remain intentional. No forms, responses, results or workflows changed. |
| Mobile / typography | Long field names wrap without overlapping helmets or causing page overflow; retained current heading, body and metadata sizes. |
| Image composition | All source artwork remains unchanged and contained. Venue crops are decorative; uncropped originals remain available through gallery links. |
| Accessibility | No-JS content, keyboard menu/Escape, reduced motion, roster controls, bracket scrolling and 200% directory text sizing passed. |
| Performance | No new asset requests, dependencies, scripts or image re-encoding. Existing lazy loading and fixed image frames retained. |

Validated actual CI artifact for `62adb082f4ed7be89c67fde71bcfd54292099cfc`:
https://github.com/stringer56/fantasy-football-site/actions/runs/34051837479.
All 230 unit tests, 13 canonical validators, generator check modes, Python compile,
dependency consistency, JavaScript syntax, Git diff, Jekyll build, rendered links
and privacy checks passed. Added one unit test, canonical rendered-caption checks
and a browser geometry regression check. All 44 public pages build.

Browser review: 44 routes × 1440/1024/768/390/360 = **220 passing checks, zero
problems**. A separate focused pass covered every active franchise and both archive
pages plus history/drafts/Cup/community at the same widths: **101 checks passed**,
including 200% text sizing. Manual screenshot inspection covered all twelve active
identities; six-plus representative profiles received desktop/mobile comparison.
Both Savage Huns and Quahog retained full archive presentation. Home, directory,
2024 season, records and shared navigation also received the all-route review.

Evidence stays outside production in ignored `.cache/professional-ui/caption-review/`
and `caption-details/`. No body overflow, distorted identity images, broken local
assets, failed internal requests, script errors or overlapping field labels were
detected. No logic/data, Yahoo OAuth, community configuration, historical facts or
calculations changed. No secrets/private data introduced. GitHub Pages/Jekyll passes.

**Ready for commissioner visual sign-off, not automatically approved or merged.**
Remaining limitations: existing low-resolution source artwork, missing approved
current-name Albany artwork, and Chromium-only browser coverage. No further
redesign is recommended before commissioner feedback.

## Professional identity pass — September 6, 2026

New baseline: `303fd2c`, latest main after #29 and scheduled Yahoo updates.
The previously merged `codex/ui-overhaul-team-pages` branch was fast-forwarded
without rewriting history. All material below this section documents the earlier
#27 implementation, not new validation evidence.

Before review uses the actual #29 deployed Pages artifact across 44 routes at
1440, 1024, 768, 390 and 360 pixels. Original Google Site captures from the
previous migration were reviewed: home, Greendale and Turnbull. A fresh web
fetch was unavailable, so no new source content or assets were inferred.

Observed opportunities: separated venue/helmet bands make directory entries tall;
profile covers underemphasize the helmet; mobile statistical cards repeat a long
single-column rhythm; the homepage's championship identity lacks the champion's
helmet. The existing design is healthy; this is a presentation refinement.

Changes: two-column editorial identity panels pair artwork with coach/story;
helmet-first desktop profile covers retain readable navy text surfaces; a labelled
2021–2025 ledger reuses existing verified career metrics; mobile records use two
columns. Home pairs the real Cup with its canonical defending champion. Archive
year panels, championship chronology, record leaders and draft/community borders
share restrained navy/gold treatment. Original summaries, canonical data, art,
routes, Yahoo, community and statistical logic are unchanged.

No assets migrated or recompressed. Existing colors and source-resolution limits
remain as documented below and in ASSET_REPLACEMENT_WISHLIST.md. The original
31 franchise assets remain intact. Newly shown champion artwork is lazy-loaded
and already used elsewhere on the homepage, allowing browser cache reuse.

### Delivery and file inventory

- Branch: `codex/ui-overhaul-team-pages` (fast-forwarded from its merged #27 tip).
- Draft PR: https://github.com/stringer56/fantasy-football-site/pull/30 — not merged.
- Final UI revision: `8336676ba5e86392179c6118f6e4cac407a5fc6f`.
- Created: `tests/test_professional_ui.py`.
- Modified: `.gitignore`, `_includes/franchise-card.html`,
  `_layouts/franchise.html`, `assets/css/franchises.css`,
  `assets/css/publication.css`, `docs/DESIGN_SYSTEM.md`, `docs/UI_OVERHAUL.md`,
  `index.md`, `retired/quahog-stripes.md`.
- Removed: none. No images, canonical data, JavaScript, dependency manifests,
  workflows, generators or Yahoo files changed relative to the baseline.

### Review findings and final refinements

The final cover puts the complete helmet ahead of the profile copy on desktop;
mobile retains the title-first reading order and contained art. The directory
uses fewer, larger identity panels per row and venue-backed art rather than
separate venue and helmet bands. This makes the coach and original voice visible
beside the image. Existing global header/menu behavior was retained after review,
not rebuilt just to produce changes. The Sites building skill's existing-site
and imagery guidance was applied without changing the required GitHub Pages host.

Manual screenshot review led to three small iterations: remove the mobile
trophy's oversized fixed-height frame, enlarge career-stat labels, and give the
Power Rankings "Managers" field a full-width mobile row rather than splitting
the word. Quahog's two gallery images now link to their full-size local originals.
History year panels, record/draft category edges, Cup chronology and community
empty states share the navy/gold rules; detailed season templates and all verified
storytelling remain intact. No new stats or feature behavior were needed.

Reviewed all 12 active profile routes and both archive destinations through the
all-route browser matrix. Focused rendered review covered Albany, Greendale,
Turnbull and Baseball Furies, plus Savage Huns and Quahog, at all five requested
widths. Quahog remains an earlier identity of New Jersey, not a second retired
canonical franchise. Home, directory, history, 2024 season, records, drafts, Cup,
Power Rankings, Pick'em, votes, rules and mobile navigation were also reviewed.

### Validation evidence for this pass

- 229 unit tests passed (six new presentation contracts); Python compilation and
  `python -m pip check` passed; `git diff --check` passed.
- All 13 canonical validators passed: public data, repository, site config,
  franchises, history, drafts, records, votes/community, recaps, Yahoo historical
  backfill, historical metrics, live season and privacy.
- Record, recap and historical-metric generator `--check` modes passed; Yahoo
  discovery `--dry-run --check` passed without changing data or authenticating.
- CI https://github.com/stringer56/fantasy-football-site/actions/runs/34051108661
  passed for final UI revision `8336676`: pinned Ruby/Bundler Jekyll build,
  JavaScript syntax, all tests/validators and rendered checks. Ruby is not
  installed locally; the actual CI artifact, not a hand-built substitute, was
  downloaded and inspected.
- Rendered-site validation: all 44 pages, local routes, assets, landmarks and
  internal links passed. Public-data and rendered privacy checks passed.
- Final browser matrix: 44 routes × 5 widths (1440, 1024, 768, 390, 360).
  All 220 checks passed with zero reported problems: no body overflow, broken
  images, failed internal requests or script errors. Results are recorded in
  `.cache/professional-ui/final-review/results.json`.
- Focused checks: 60 page/width checks plus directory 200% text-resize test passed.
- Keyboard/no-JS review passed: menu/Escape/focus return, four no-JS pages,
  reduced motion, franchise-strip scrolling, bracket arrow-key scrolling and
  roster disclosure expansion. No UI dependencies or scripts were added.

Representative cover/full-page screenshots are in the ignored
`.cache/professional-ui/final-review/` and `final-details/` folders. They are QA
evidence only and never production content. The baseline and first-iteration
artifacts/results are retained separately for comparison. No source art was
stretched, substituted or edited. Decorative venue crops have full uncropped
counterparts in the profile galleries. All helmet/logo references resolve locally;
no Google image hotlinks were introduced or retained in place of local copies.

### Limitations and next refinement

No assets were newly migrated. Existing palette values listed below were reused
unchanged; uncertain/retired accents retain league gold. Image bytes are unchanged:
31 franchise files (4,063,255 bytes) and existing Cup/archive media. Fixed frames,
lazy loading and cached reuse avoid new heavyweight requests; large historical
PNGs and low-resolution venues remain documented source-quality limitations, not
silently recompressed artwork. No independent owner biographies/photos exist.

Albany's current-name approved artwork is still needed; its historical Kneelers
helmet and explicit note remain. No historical or community facts were fabricated.
All Yahoo OAuth/fallback, community privacy/data flow, ranking/pick/voting logic,
and history/record/draft calculations are unchanged. No secrets, raw responses,
private picks, test fixtures, paid services, analytics or frameworks were added.
Google Forms remain optional and dormant states intentional. The review covers
Chromium, not a formal full assistive-technology or Safari/Firefox certification.

Exact next refinement: commissioner visual sign-off on draft #30, followed by a
separate approved-artwork-only pass for Albany and higher-resolution venue/source
originals from ASSET_REPLACEMENT_WISHLIST.md. Do not fabricate replacements or merge
this draft without commissioner authorization.

## Audit before implementation

Started from main after PR #26, on `codex/ui-overhaul-team-pages`.
Production was inspected at 1440 and 390 pixels: home, directory, Turnbull,
Greendale and Quahog. The Google Site home and team references were also opened.
Approved local Cup, helmet and venue images were visually inspected.

- Oversized repeated page introductions put the first directory row below the fold.
- Tiny navigation/metadata competes with heavy Impact headings; long franchise names
  wrap awkwardly, and the menu omits direct Power Rankings/Pick’em destinations.
- Uniform gold identity frames ignore existing franchise colors. Tall card bodies
  and repeated profile summaries consume space without adding information.
- Home's RTG/BC placeholder graphics underuse the approved actual Cup photography.
- Venue photography is buried after long statistical sections; owner information
  is not a distinct editorial section. Hero image width/height attributes assume
  a common aspect ratio despite differing source sizes.
- A single stylesheet mixes historical/data components and accumulated overrides.
- Greendale's profile-era honors list contains 2023 only; canonical champions also
  verify 2025. Presentation will read the canonical championship data, not rewrite facts.
- There are 12 active franchises, one retired franchise (Savage Huns), and a second
  archive page for Quahog, an earlier identity of New Jersey. Do not invent a second
  retired franchise or duplicate its statistics.

## Visual thesis

An editorial league annual: midnight masthead, warm paper, gold rules, bold but
readable sports typography, trophy-led home, and color-coded franchise identity
panels. Keep data dense and legible; use real local imagery instead of new artwork.
Franchise hero → compact identity/coach → preserved story/venue → live and career
statistics. Archive pages retain full personality, not disabled styling.

## Scope and integrity

Jekyll/Liquid, canonical data, IDs, URLs, original editorial text and all Yahoo,
historical and community behavior remain. Team colors come only from existing
`branding.primary_color`; unverified colors use navy/gold. Color is decorative,
never the only identifier or text-contrast foundation. No owner images are invented.
All imagery is already approved/local. Dense source artwork retains full-size links.

## Implementation

- Shared masthead: six destinations per row on desktop, explicit active route,
  direct Power Rankings/Pick’em links, two-column mobile menu, Escape/focus return,
  and visible navigation without JavaScript. Existing menu behavior is unchanged.
- Homepage: approved real Cup photography, canonical latest champion link, stronger
  score emphasis, restrained league modules, and approved Cup-history artwork.
- Directory: 12 color-coded franchise panels with large contained helmets, coach,
  preserved story excerpt, canonical verified title count/years and profile links.
- Profiles: helmet-led cover, slogan, coach, canonical championship badges, jump
  navigation, complete original story once, coach/facts dossier, aliases/rivals,
  local venue/honors strip before statistics, and retained live/career/season/H2H
  sections. Draft archive is linked without inventing franchise draft summaries.
- Quahog uses the same cover/gallery language while preserving its relationship
  to New Jersey. Savage Huns retains full identity and career treatment.
- History, season, draft, records, Cup and community pages inherit coherent
  headings, compact covers, scoreboard rows, editorial rules and empty states.
  Bracket/standings overflow stays in the existing labelled containers.

## Components and CSS ownership

`style.css` retains data-specific mechanics and baseline tokens. `publication.css`
owns the shared editorial layer; `franchises.css` owns directory/profile/archive
identity components and their responsive rules. The former franchise block and
unused RTG crest/BC placeholder selectors were removed from `style.css`.
No JavaScript dependency or external font was added. The existing navigation and
chart/disclosure scripts were not changed.

Meaningful new includes: `franchise-card.html` and `franchise-gallery.html`.
Titles are derived directly from `_data/champions.yml`; no duplicate honors data.
The existing season table remains canonical and linked, with no new statistics.

## Asset and color inventory

All 31 franchise files remain local and unchanged (4,063,255 bytes combined).
Each of the 13 canonical franchises has identity and venue art; Albany, Ayahuasca
and Greendale also have championship art. Quahog has identity and venue art.
The largest file is Greendale's 945×531 venue PNG, 614,701 bytes; all remaining
files are smaller. Existing source sizes are reasonable for this pass; avoid a
lossy re-encoding of already-small helmet JPEGs or altering their baked-in frames.
Images below the cover remain lazy-loaded. Contained fixed-size cover/card frames
reserve space; source proportions and full-size gallery access are preserved.

| Asset group | Local source | Presentation |
| --- | --- | --- |
| 14 identity images | `assets/img/franchises/*/identity.jpg` | Hero/directory/archive, contain |
| 14 venue images | Same folders, `venue.jpg` (Greendale `venue.png`) | Editorial gallery, contain |
| 3 honors images | Albany/Ayahuasca/Greendale `honors.jpg` | Full-size linked archival artwork |
| Cup photograph | `assets/img/cup/brew-crew-cup.jpg` | Homepage and existing Cup page |
| Cup history artwork | `assets/img/cup/brew-crew-history.jpg` | Homepage Cup feature |

No new image migration was necessary. No AI art, new owner photo, external image
hotlink or inferred founding date was introduced. Public Google reference pages
for Turnbull and Greendale were compared with migrated local artwork and writing.

All 12 active accents use existing `branding.primary_color` unchanged:
Albany #111827; Ayahuasca #2e7d32; Baseball Furies #155e75; Buffalo #2563eb;
Crazy Waz #15803d; Greendale #1e3a8a; Maine #b45309; New Jersey #1d4ed8;
North Town #dc2626; Turnbull #7e22ce; Van Cortlant #0f4c81; Vegas #991b1b.
Savage Huns and Quahog use the league's neutral gold, not an invented team color.

## Content reconciliation and limitations

- Greendale's profile-era 2023 honors list is incomplete compared with the verified
  champions archive (2023, 2025). Badges/counts now use the latter. The original
  2023 image is correctly captioned as archived 2023 artwork, not relabelled 2025.
- Albany's current name is Redskins while its approved helmet retains the
  historical Kneelers identity. Keep approved art and its accurate alt text;
  do not silently replace it with unapproved current-name artwork.
- Quahog is an earlier identity, not an additional canonical retired franchise.
- Owner display names and coaching voice exist, but dedicated owner photographs
  and independent biographies do not. The preserved team story carries that voice;
  no new biography or image was invented. Founding dates remain unresolved/omitted.
- Small lettering baked into historical art cannot be made sharper by CSS.
  Full-size links preserve access to the approved source resolution.

## Accessibility and responsive review

Readable system fonts, fixed high-contrast text colors, labelled navigation,
visible blue/gold keyboard focus, reduced-motion rules and native disclosures
remain. Team colors are decorative rules, not the sole source of identity/status.
Light-surface eyebrows use dark brown, while dark covers use pale gold.
Directory grids are 3 / 2 / 1 columns. Profiles stack at 600px; story/facts stack
at 900px. Mobile menus stay within viewport height and scroll internally.

The browser auditor now covers all 14 profile/archive destinations, checks menu
open/Escape, one H1, descriptions, local requests, alt attributes, body overflow,
page anchors, image containment and synthetic/debug leakage. It exits nonzero
on failures. Browser screenshots caught grid intrinsic sizing that allowed an
image to overlap copy; fixed with constrained flex frames and added a bounds
regression check. Screenshot review also corrected low-contrast light eyebrows.

## Validation evidence

204 unit tests, Python compile, 13 public/repository/data/privacy validators,
records/recaps/historical-metrics regeneration checks, Yahoo discovery dry-run,
dependency consistency and JavaScript syntax checks passed locally.
Jekyll is built with the project's pinned Ruby/Bundler setup in GitHub Actions,
not an unavailable local Ruby installation. The rendered artifact passed the
44-page link/landmark/data validator and rendered privacy validator.

## Review inventory and reproducibility

Branch: `codex/ui-overhaul-team-pages`.
Draft PR: https://github.com/stringer56/fantasy-football-site/pull/27 (do not merge).
Base after PR #26: `c14d42547f0e1d716323ad9ce24eda898405e0c5`.

Created (6): `_includes/franchise-card.html`, `_includes/franchise-gallery.html`,
`assets/css/publication.css`, `assets/css/franchises.css`, `docs/UI_OVERHAUL.md`,
`tests/test_ui_contract.py`.

Modified (9): `_layouts/default.html`, `_layouts/franchise.html`,
`assets/css/style.css`, `docs/DESIGN_SYSTEM.md`, `index.md`,
`retired/quahog-stripes.md`, `scripts/audit_browser.py`,
`scripts/validate_built_site.py`, `teams.md`. No files removed; no images changed.

Six new unit contracts cover explicit community navigation, single preserved
profile story/gallery, canonical championship badges, approved local assets/colors,
CSS module loading/unused crest removal, and Quahog franchise continuity.
Rendered checks additionally enforce original story preservation, all approved
profile media, gallery anchors and every canonical championship badge.

Reproduce the browser pass with Playwright and an installed Chromium executable:

```text
python scripts/audit_browser.py --site _site --browser <chromium-executable> --output .cache/reconciliation-ui/review --all-franchises
```

Screenshots and JSON are local QA evidence only, under the ignored
`.cache/reconciliation-ui/` tree; not copied to public assets or committed.
`before/` contains production/Google reference captures. `release-review/` contains
the final five-width matrix and desktop/390/360 full-page and cover screenshots.
`interactions/` contains detailed galleries, live cards, career sections, brackets,
homepage modules and mobile menu captures, including 1024/768 tablet views.

The next UI/content task is a commissioner review of approved current-name identity
art, starting with Albany's historical Kneelers helmet. Obtain approved replacement
art only if desired, then make a separate small asset-only update. Dedicated owner
portraits/biographies also require commissioner-supplied, approved material.

## Final results — September 5, 2026

- UI build: `0a2f852c583388f67fa83044af3b892665da2d3b`.
- Green CI/Jekyll artifact: https://github.com/stringer56/fantasy-football-site/actions/runs/33990929046
- Final responsive matrix: **145 checks, zero failures** (29 routes each at
  1440, 1024, 768, 390 and 360 pixels). Includes all 12 active franchises and both
  archive profiles (Savage Huns retired franchise; Quahog historical identity).
- No body overflow, failed internal requests, missing images/alt attributes,
  stretched/escaped identity images, missing in-page anchors, duplicate H1s,
  unreadable live-card messages, synthetic content or debug-state leaks detected.
- **19 additional section/no-JavaScript checks passed**: keyboard Enter/Escape and
  focus return, all navigation destinations visible without JS on four routes,
  native weekly disclosure open/close, and detailed section views at all five widths.
- Every franchise cover was visually reviewed. Desktop/mobile directory, home,
  community, history, season, records, draft, Cup, gallery and archive screenshots
  were inspected; tablet story/live-card views were inspected at 1024 and 768.
- **204 tests passed**, including six new presentation contracts. Complete CI
  validation, all 13 source validators, generator checks, Python compilation,
  JavaScript syntax, `pip check`, rendered 44-page link/landmark validation,
  rendered privacy checks and `git diff --check` passed.
- All approved helmet/logo images resolve and remain contained without stretching.
  No Google image hotlinks, historical facts, community/Yahoo logic, OAuth changes,
  new secrets or private data were introduced. GitHub Pages/Jekyll remains the host
  and renderer. No new frameworks or runtime service dependencies.
- Source data, generated data, workflow and JavaScript paths are unchanged.
  Final documentation-only updates do not alter the reviewed public artifact.

No known blocking rendering defects remain. This is Chromium responsive and
keyboard QA, not a full assistive-technology or cross-engine certification.
The redesign remains in a draft PR; production still uses main until approved.
