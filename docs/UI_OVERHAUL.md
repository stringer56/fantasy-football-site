# UI Overhaul — League publication and franchise profiles

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

Final CI and responsive evidence is recorded below after the last review pass.
