# Road to Glory FFL Design System

## Direction

The interface uses a deep navy sports-publication shell, restrained gold
accents, off-white editorial surfaces, condensed system display type, and
highly readable system body type. It should feel like an established league
headquarters rather than a generic dashboard or Jekyll theme.

All design tokens live at the top of `assets/css/style.css`. Components use the
same color, spacing, radius, shadow, typography, and content-width variables.
Minima remains in the Gemfile for GitHub Pages compatibility but does not
control the custom page presentation.

## Reusable components

- `_includes/page-hero.html`: interior-page title and purpose statement.
- `_includes/section-heading.html`: section eyebrow, title, description, and
  optional destination link.
- `_includes/empty-state.html`: intentional unavailable/migration state.
- `_includes/roster.html`: collapsed native `details` roster table connected to
  normalized Yahoo data.
- `.button`, `.panel`, `.standings-table`, `.matchup-card`, `.explore-card`, and
  `.migration-card`: CSS component patterns for present and future templates.

Includes remain intentionally coarse-grained. One-off editorial compositions,
such as the homepage hero and Brew Crew Cup feature, stay in the page template.

## Accessibility and interaction

- Layouts use semantic header, navigation, main, and footer landmarks.
- A skip link and high-contrast `:focus-visible` treatment support keyboard use.
- The mobile menu exposes `aria-expanded`, closes with Escape, and remains
  visible without JavaScript.
- Roster controls use native `details`/`summary` and start collapsed.
- Tables remain semantic and scroll inside labelled regions at narrow widths.
- Ticker animation pauses on hover/focus and becomes static when visitors
  prefer reduced motion.
- Decorative marks are hidden from assistive technology; future league and
  franchise images require meaningful, data-owned alt text.

## Responsive breakpoints

- Above 1100px: full publication grid and desktop navigation.
- 901–1100px: compressed desktop navigation and two-column archive cards.
- 769–900px: accessible menu control and stacked dashboard panels.
- 561–768px: single-column matchup and Cup layouts.
- 560px and below: compact brand, full-width hero actions, and one-column cards.

The supported verification widths are 1440, 1024, 768, 390, and 360 pixels.

## Asset policy

The text-based RTG crest is an explicit placeholder, not official league art.
Future imported helmets, logos, trophy images, and photography should be stored
locally, optimized, and referenced through Jekyll's `relative_url` filter.
