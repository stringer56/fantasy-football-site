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

Implementation, asset inventory, validation and responsive evidence follow below.
