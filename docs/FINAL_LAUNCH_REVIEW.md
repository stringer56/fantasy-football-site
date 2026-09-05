# Final UI polish and launch readiness

## Branch and merge prerequisite

PR #28 was merged before this work. Main base:
`f17ba7f72127ad99c9528ea179edada2f6ec2799`.

Branch: `codex/final-launch-polish`.
Draft PR: [#29](https://github.com/stringer56/fantasy-football-site/pull/29).
Do not merge automatically. This polish is not deployed by the draft PR.
The Full UI Overhaul design remains canonical.

## Changes

- Visual: rules-page headings now use the shared sentence-case scale rather than
  leftover oversized all-caps styling. Footer metadata uses readable light text
  on navy; measured contrast is 12.14:1. Existing grids, colors, and layouts remain.
- Home: franchise strip precedes the Cup feature, with shorter Cup/source copy.
  The compact current-season pulse retains its standings preview beside the
  featured matchup; the full weekly slate remains immediately after the pulse.
  No verified source-status message or section is removed.
- Copy: concise rules-pending state, reader-facing compatibility pages and
  statistical archive introductions; redundant Pick'em conditional removed.
  Original franchise stories and generated factual historical narratives remain.
- Navigation: verified champions' profiles gain a Cup-history link. Existing
  season/franchise, draft/season, and record/franchise links resolve. Compatibility
  pages remain useful doorways and now identify their primary canonical URLs.
- Albany: current name and approved historical Kneelers helmet are preserved.
  An explicit archival note is associated with the image via `aria-describedby`.
  No missing era, helmet, insignia, or artwork is invented.
- Images/performance: local originals unchanged; below-fold matchup helmets are
  lazy-loaded, Cup feature has true source dimensions, countdown script loads
  only on its homepage, and seven conclusively unused draft-analysis CSS rules
  are removed. No framework, font, tracker, or external asset dependency added.
- Accessibility: named, keyboard-focusable draft-round and roster scroll regions,
  named tables, readable footer, existing skip/menu focus behavior, reduced motion,
  and no-JavaScript content. No data or voting semantics change.
- Metadata: one reusable canonical/Open Graph include, escaped title/description,
  absolute public URLs, approved local share image/alt, and existing local favicon.
  Four compatibility routes canonicalize to their primary pages. New rendered
  contracts check metadata, image existence, and safe new-tab links.

## Files changed

Created:

- `_includes/social-meta.html`
- `docs/ASSET_REPLACEMENT_WISHLIST.md`
- `docs/FINAL_LAUNCH_REVIEW.md`
- `tests/test_launch_polish.py`

Modified:

- `.gitignore`, `README.md`
- `_includes/live-matchup-card.html`, `_includes/pickem-preview.html`
- `_layouts/default.html`, `_layouts/draft.html`, `_layouts/franchise.html`
- `assets/css/style.css`, `assets/css/publication.css`, `assets/css/franchises.css`
- `index.md`, `rules.md`, `all-time-standings.md`, `head-to-head.md`
- `pickem.md`, `picks-legacy.md`, `power-rankings-legacy.md`, `seasons.md`
- `docs/DESIGN_SYSTEM.md`
- `scripts/audit_browser.py`, `scripts/validate_built_site.py`

No original image, `_data`, Yahoo OAuth/fetcher, or GitHub workflow changed.
Unused draft-analysis styling is the only deleted code family. Historical
infrastructure and the legacy roster include remain; broad CSS deletion would
risk dynamic states that are correctly empty today.

## Asset and performance findings

[Asset Replacement Wishlist](ASSET_REPLACEMENT_WISHLIST.md) inventories all 63
local assets: 13,708,685 bytes, no SHA-256-identical duplicates. It documents
intrinsic sizes, measured enlargements, decorative crops, large archival PNGs,
and exactly what Albany source material is still needed.

The historical Kneelers helmet is already available. The missing approved asset
is current-name Redskins art (plus higher-resolution originals if desired).
Do not overwrite older seasonal identity art with a current-name replacement.

Full-visit uncompressed estimates are ~1.47 MiB for home, 3.50 MiB for Teams,
4.08 MiB for Draft Archive, and 3.85 MiB for the 2025 draft. These include each
referenced local asset once, even lazy images, and are not initial-transfer or
Core Web Vitals measurements. Two archival PNGs dominate the heavy pages.
Approved originals retain readability and full-size access. No lossy optimization
or artificial upscaling is performed.

## External links and news

All 25 unique external anchor destinations in the rendered site returned HTTP 200
on the read-only launch probe, including the canonical public Yahoo league URL
and Google Site source pages. New-tab anchors carry `noopener`; external calls
retain their existing visual indicators. No private Google URLs or OAuth/API
destinations were introduced.

There are no committed news articles to probe individually. The three configured
feed endpoints were checked without writing data: ESPN returned a parseable feed
(23 items at the time of the probe); NFL.com and FantasyPros returned HTTP 200
but content the existing parser could not parse as a feed. Safe empty behavior
remains unchanged. This is an existing news-source limitation, not fake headlines
or a change to feed adapters. Endpoint status can change after the audit.

## Validation

Final UI commit: `b71d4853d80ef8d05e9c48c776073e9e9a1c12c6`.
[CI run 33997156463](https://github.com/stringer56/fantasy-football-site/actions/runs/33997156463)
passed. Documentation-only follow-ups do not alter the reviewed public output.

- Python compilation: passed.
- Full unit suite: **223 tests passed**; 12 launch-polish regression tests added.
- All thirteen canonical validators plus the Yahoo compatibility entry point:
  passed. Includes public data, repository, configuration, franchises, history,
  drafts, records, votes, recaps, Yahoo history, historical metrics, live season,
  and privacy.
- Records/recaps/historical-metrics generation and Yahoo discovery baseline:
  current and reproducible.
- `python -m pip check`: no broken requirements.
- `git diff --check`: passed.
- `bundle exec jekyll build`: passed in the existing pinned-Ruby CI environment;
  local Ruby/Bundler is unavailable. The exact CI artifact was downloaded.
- Rendered-site and privacy validators: all 44 HTML routes passed, with internal
  links/assets, metadata/canonicals, public content and privacy boundaries checked.
- JavaScript syntax: passed in CI.
- Keyboard/no-JavaScript/reduced-motion checks: passed, including menu Tab/Escape,
  focus return, franchise scrolling, bracket scrolling, roster expansion, named
  draft/roster regions, and the underlying accessible Power Rankings table.

## Browser review and reproduction

Every public route is checked at 1440, 1024, 430, 390, and 360 pixels. Representative
screenshots cover home, teams, Albany/Greendale, retired archive, 2024 history,
Cup, records, draft, community and rules. The representative selection is 17
page/viewport pairs (34 full-page/cover captures), plus a few focused accessibility
views; it does not capture hundreds of screenshots per run.

The exact final artifact is checked again without repeating screenshots after
the last footer-color-only correction: **220 checks passed, zero problems**.
No body overflow, broken images, failed internal requests, JavaScript errors,
missing alt attributes, flagged private/synthetic content, or escaped identity
images were detected. Local evidence lives under ignored
`.cache/final-launch-polish/`: `final-review/` for representative images,
`release-checks/` for final route results, plus focused rules/Albany views,
external-link results, and page-weight estimates. Original source snapshots and
synthetic fixtures never enter the generated site.

```text
python scripts/audit_browser.py --site ARTIFACT --all-routes --widths 1440,1024,430,390,360 --screenshots representative --browser CHROMIUM --output REVIEW
```

Use `--screenshots none` for repeated mechanical checks. This is real Chromium
rendered inspection, not a substitute hand-built HTML mockup or a full WCAG,
assistive-technology, Safari, or Firefox certification.

## Commissioner decisions and technical limits

1. Approve the final visual/copy pass before any merge or production verification.
2. Supply commissioner-approved rules with version/effective date.
3. Optionally approve current-name Albany artwork and higher-resolution originals
   from the wishlist, as a separate source-asset change.
4. Real Forms/deadlines/polls remain a separate operational activation step and
   are not required for this design to look complete.

Known technical limits: large archival originals; some low-resolution source
lettering/photos; two currently non-parseable news feeds; existing Yahoo fallback
status remains explicit and OAuth recovery was not attempted. No blocking internal
route/asset defect was found. User-facing empty states remain intentional.

No redesign, fabricated data, secrets, tracking/analytics, paid service, new
community system, or OAuth changes were introduced. GitHub Pages remains the host.
