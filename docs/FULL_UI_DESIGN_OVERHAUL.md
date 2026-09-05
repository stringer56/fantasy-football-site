# Full UI / UX design overhaul

Branch: `codex/full-ui-design-overhaul`

## Scope and source

UI-only milestone based on main `d12f74e87f06883edec897b731f8bbabfa45f37d`.
The original Google Site homepage was checked read-only. Existing approved
franchise imagery, venue photographs, trophy photographs, historical brackets,
draft captures, and migration documentation remain the source of visual identity.
No artwork is generated, replaced, or retouched.

## Page system

- Global: compact nine-destination masthead, season utility link, active states,
  accessible mobile disclosure, and shared Community navigation.
- Home: trophy cover, compact NFL/fantasy wire, league headlines, six-matchup
  slate with rosters, standings preview, Cup, all twelve franchises, recent
  champions, verified record spotlights, draft status, and quiet community modules.
- Franchises: venue-backed covers, uncropped identities, coach dossier, original
  story, title badges, real milestone timeline, seasons, and opponent records.
- Archives: champion covers with final scores; Cup identity chronology; season
  scorecards, editorial recaps, contained bracket scrolling, and weekly disclosures.
- Drafts: uncropped preview artwork, year navigation, existing selections and
  source captures. Unimplemented future-analysis tiles removed from public view.
- Records: reusable numerical leader spotlights and compact existing tables.
- Community: upcoming states without developer/setup instructions. Existing
  voting semantics, privacy rules, blank forms, and real data are unchanged.
- Rules: reviewed-source boundary retained with a safe canonical Yahoo link.

## Validation procedure

Run the complete existing Python unit suite and all thirteen data/repository
validators, generated-history checks, dependency checks, and diff checks.
Jekyll runs through the existing pinned-Ruby GitHub validation workflow.
Download that exact branch artifact and run:

```text
python scripts/validate_privacy.py --site ARTIFACT
python scripts/audit_browser.py --site ARTIFACT --all-routes --browser CHROMIUM --output LOCAL_REVIEW
```

The browser review enumerates every artifact HTML route at 1440, 1024, 768,
430, 390, and 360 pixels. It records screenshots and checks requests, image
loading, alt attributes, body overflow, menu behavior, anchors, landmarks,
identity sizing, and private/synthetic content. Screenshots remain ignored local
QA artifacts, not public site assets. Rendered-site validation separately checks
all internal links and expected content/data contracts.

## Boundaries

Google Forms are not needed for the public site to look complete.
Rules still await commissioner-approved text; no rulebook was invented.
Current Albany identity art still carries its historical name: no replacement
has been approved. Some original raster images contain frames or low-resolution
text; these source characteristics are preserved and full-size links remain.
Original editorial stories and all canonical historical/Yahoo data stay intact.
No OAuth, secrets, hosting architecture, import, or finalization changes.

## Review results

Draft PR: [#28](https://github.com/stringer56/fantasy-football-site/pull/28).
Production is unchanged; this branch has not been merged.

### Files created

- `_includes/champion-card.html`: reusable verified champion/score presentation.
- `_includes/community-nav.html`: shared feature navigation and current state.
- `_includes/record-spotlights.html`: three existing canonical record leaders.
- `docs/FULL_UI_DESIGN_OVERHAUL.md`: scope, review evidence, and handoff.

### Files modified

- `.gitignore`: keep local screenshots/artifacts outside commits and the site.
- `index.md`, `2026.md`: league homepage and current-season presentation.
- `_layouts/default.html`, `_layouts/franchise.html`, `_layouts/season.html`,
  `_layouts/draft.html`: common navigation and reusable page systems.
- `_includes/franchise-card.html`, `_includes/page-hero.html`,
  `_includes/live-power-preview.html`, `_includes/pickem-preview.html`:
  identity presentation and visitor-facing states.
- `assets/css/publication.css`, `assets/css/franchises.css`,
  `assets/js/site.js`: typography, layout, responsive behavior, menu accessibility.
- `history.md`, `cup.md`, `records.md`, `drafts.md`,
  `retired/quahog-stripes.md`, `rules.md`: consistent archive/editorial treatments.
- `votes.md`, `power-rankings.md`, `picks.md`: coordinated community presentation.
- `docs/DESIGN_SYSTEM.md`: updated design and component guidance.
- `scripts/audit_browser.py`, `scripts/validate_built_site.py`,
  `tests/test_ui_contract.py`: rendered coverage and UI regression contracts.

### Review coverage and iteration

The artifact contains 44 HTML routes. All are reviewed at six viewport widths;
representative screenshots are visually inspected across the homepage, team
directory, franchise profile, retired archive, season, history, Cup, records,
drafts, and community pages. This includes compatibility and secondary records
routes, not just primary navigation destinations.

Rendered inspection led to corrections for the featured-matchup grid, season
champion caption/score overlap, mobile Power Rankings metadata, centered draft
artwork, shared page gutters, and the 360px Picks Leaderboard heading.
The browser harness now tests an expanded native disclosure and preserves its
element identity when closing it, so screenshots show the normal collapsed state.

Supplemental Chromium checks passed for no-JavaScript navigation/content on four
routes, an accessible underlying ranking table, keyboard menu/Tab/Escape behavior,
reduced motion, keyboard franchise-strip scrolling, contained keyboard bracket
scrolling, and keyboard roster expansion. The bracket check waits for its lazy
image to load before measuring the intentionally scrollable full-resolution art.

### Automated validation

The final UI commit is `992e0370cc97d4ac276877b176df5d20f04c5d51`.
[Validate Site run 33995000214](https://github.com/stringer56/fantasy-football-site/actions/runs/33995000214)
passed, including `bundle exec jekyll build` and rendered-site/privacy validation.
Ruby/Bundler are not installed locally; the downloaded artifact is from that
successful pinned-Ruby CI build, not a substitute HTML renderer.

- Python compilation: passed.
- Full unit suite: 211 tests passed, including seven additional UI contracts.
- All thirteen canonical repository/data validators: passed; the Yahoo history
  compatibility entry point also passed.
- Generated records, recaps, historical metrics, and Yahoo discovery baseline:
  current and reproducible.
- `python -m pip check`: no broken requirements.
- Downloaded artifact: all 44 rendered pages and internal links validated;
  public-data and rendered-artifact privacy checks passed.
- Final all-route Chromium review: **264 checks passed, zero problems** across
  44 routes at 1440, 1024, 768, 430, 390, and 360 pixels. No body overflow,
  missing images, failed internal requests, missing alt attributes, or flagged
  synthetic/private content. Full-page and cover screenshots were captured for
  every check (528 screenshots). Representative aesthetics were inspected, not
  merely inferred from DOM assertions.
- Local evidence: `.cache/full-ui-design/release-review/results.json` and the
  adjacent screenshots. Supplemental mobile-card and bracket screenshots are in
  `.cache/full-ui-design/`. These files are intentionally excluded from git.
- `git diff --check`: passed.

### Performance, privacy, and integrity

No new runtime dependencies, frameworks, fonts, or external image hosts were added.
Existing images are reused with contain sizing and below-the-fold lazy loading.
Original files and raster characteristics remain intact; no lossy conversion was
performed. Screenshot output is local and ignored.

No canonical `_data`, approved `assets/img`, GitHub workflows, or Yahoo API/OAuth
implementation changed. No forms, ballots, results, player claims, private picks,
or statistical values were invented. Public fallback provenance remains explicit
and is not presented as a successful Yahoo API refresh.

### Remaining visual/content gaps and next polish

All public routes share the design system. Remaining source limitations are the
historical Albany helmet name, framed/low-resolution original raster artwork,
commissioner-approved rules still pending, and an intentionally quiet League Wire
when the safe feed has no headlines. These are not filled with invented content.

Recommended final polish: commissioner review of the draft PR's screenshots and
original franchise copy, with explicit approval of any future replacement Albany
identity or higher-resolution source artwork. After approval, merge through the
normal review process and separately verify the production Pages deployment.
Real Google Form setup is independent and is not a prerequisite for this design.
