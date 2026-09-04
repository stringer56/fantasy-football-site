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

### Draft archive patterns

- `.draft-season-card` pairs a cropped source-result preview with compact year,
  team-count, and round-count metadata on the newest-first archive.
- `.draft-order-entry` uses a large opening slot, canonical identity art, the
  exact historical team name, and a quieter canonical-name line. Unresolved
  identities replace the image with a neutral marker and never create a link.
- `.draft-results-gallery` preserves dense source images at full width and links
  every capture to its original-size local file.
- `.draft-analysis-hooks` reserves future analysis regions without presenting
  unavailable calculations as content.

At mobile widths, archive cards and draft-order entries collapse to one column;
long historical names may wrap, and dense result images remain available through
their full-size links rather than being downscaled into illegibility.

### Records patterns

- `.coverage-scorecard` makes the verified date window prominent without
  describing a partial archive as all-time history.
- `.record-table` presents compact, linked franchise totals inside a labelled,
  keyboard-focusable horizontal scroll region. The public view leads with ten
  rows and preserves the remaining totals in a native disclosure.
- `.record-card` pairs one verified single-season value with every tied holder;
  unresolved historical names render as text and never create broken links.
- `.honor-board` and `.streak-grid` separate complete championship results from
  partial bracket-derived totals.
- `.unavailable-card` explains missing source coverage as an intentional state;
  it never renders an empty or fabricated Top 10.

At 1100px the record cards and streaks reduce their column count, at 900px the
hero and honor boards stack, and at 560px every record card becomes one column.
Dense semantic tables keep an accessible horizontal scroll treatment rather
than shrinking numeric content past legibility.

### Voting patterns

- `.vote-principles` explains the free static architecture without exposing
  commissioner controls or raw form data.
- `.poll-card` supports a real ballot question, public deadline, result bars,
  and a finger-friendly external Google Form action.
- `.vote-matchup-card` and `.pick-card` keep two-team choices legible without
  pretending the static page accepts or locks a vote.
- `.community-feature` previews Power Rankings and the Picks Leaderboard while
  preserving explicit empty-season states.
- `.vote-table` handles manager-voted rankings and season pick totals in a
  labelled keyboard-focusable horizontal scroll region.
- `.vote-empty` is the canonical no-ballot, stale-matchup, or no-results state;
  it never fills the UI with example votes.

Voting grids collapse from two columns to one by 768px. Tables keep deliberate
horizontal scrolling, buttons retain touch-size targets, and matchup identities
remain side by side inside their card even when the cards themselves stack.

### Historical narrative patterns

- `.narrative-copy` keeps season and championship prose at an editorial reading
  width with generous line height; `.narrative-provenance` identifies the
  verified-data source without exposing technical warnings.
- `.season-number-card` turns only supported canonical facts into a compact
  scorecard. Partial source confidence receives a restrained gold treatment.
- `.playoff-recap-card` sits below the structured result grid, preserving the
  result cards as the primary score source while adding conservative prose.
- `.team-recap-card` combines identity art, historical name, W–L–T, concise
  narrative, and a canonical link. Unresolved identities use a neutral marker
  and never create a profile link.

Number cards use three columns on desktop, two below 900px, and one below
560px. Team recaps use two columns before stacking at 560px. The sticky season
subnavigation remains horizontally scrollable rather than shrinking labels.

### Live season and Power Ranking patterns

- `.live-season-hero`, `.live-matchup-card`, and `.live-status-card` establish
  the 2026 scoreboard hierarchy while preserving explicit current/stale labels.
- Matchup scores and projections are separately labelled; roster tables remain
  collapsed in native disclosures.
- `.record-watch-alert` is reserved for deterministic verified-history
  comparisons, while `.league-wire-list` is separate from external NFL news.
- `.power-chart` progressively enhances immutable weekly HTML tables with a
  keyboard-filterable SVG. Rank 1 is always visually above rank 12, and line
  identity is never communicated by color alone.

Live cards move from two columns to one at 768px. Homepage grids reduce from
three to two columns at 1024px and to one at 560px. The Power Ranking legend can
scroll inside its own region at narrow widths; chart controls wrap without
creating body-level overflow.

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
