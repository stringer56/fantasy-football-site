# Production Readiness Reconciliation — September 5, 2026

## Current post-fix status — supersedes the original audit below

PR #24 is merged. PR #25 was merged at
`8f989952719f124b8d62cb28948d0fc90efc9e1b` on September 5, 2026.
Manual [Yahoo update 33988217973](https://github.com/stringer56/fantasy-football-site/actions/runs/33988217973)
then succeeded and published main `e0e82acb6bf27c75035ac8da6b9a7a8de520ca72`.
The canonical history manifest is byte-for-byte unchanged by that update; the
timestamped diagnostic remained a separate temporary artifact. Post-update
[main validation 33988310265](https://github.com/stringer56/fantasy-football-site/actions/runs/33988310265)
passed all 194 tests, deterministic checks, validators, Jekyll and rendered/privacy
checks. This verifies the regression fix after real publishing, not only in a PR.

[Production Pages deployment 33988248843](https://github.com/stringer56/fantasy-football-site/actions/runs/33988248843)
successfully serves that same main commit. Yahoo API still returned HTTP 403;
the official public fallback supplies 12 teams, 12 standings rows, six Week 1
matchups and 122 available roster players, timestamp `2026-09-05T19:49:01Z`.
This is fallback-fed data, not authenticated API recovery. OAuth is unchanged.
The actual deployed Pages artifact passed the 44-page and privacy validators;
the live site passed 80 responsive checks across 16 routes at
1440/1024/768/390/360, with no broken assets, body overflow or synthetic content.

Community remains dormant: three blank Form URLs, no imports/previews/results,
no active poll, Pick’em lock `2026-09-09T20:20:00-04:00` in America/New_York,
Power Rankings deadline unset. No real Forms have been created by Codex.

The separate Forms-creation polish reviews the helper against importer fields,
tests three-Form creation using local Google-service doubles (no live Google calls),
guards against a mismatched weekly lock, and clarifies responder-only output,
closed defaults, safe reuse, manual fallback and weekly copies. Google-account
permissions/publication still require Joe's first-run review. See `NEXT_STEPS.md`.
The polish branch passes 198 tests (four helper-specific regressions added),
all current validators and helper/JavaScript syntax checks. No production
configuration or importer was changed.

## Original pre-merge audit record

The sections below preserve the earlier evidence as recorded; their pending-merge
and old-snapshot descriptions are historical, not current operating instructions.

## Repository evidence

Main: `db6af82626a28f0eee4a9e71e72f3f5419cdedcb` (merged PR #23).
Work continues on `codex/milestone-2026-community-operations`, existing draft
[PR #24](https://github.com/stringer56/fantasy-football-site/pull/24), not an overlapping PR.
At inspection #24 was mergeable and its original CI run 33936006144 passed.
PRs #1 and #10 are draft/conflicting; later merged foundations/history supersede
their principal functionality. No PR has been merged/closed automatically.

Dependency map: main → corrected #24 → actual Form activation. Old #1/#10 are not dependencies.

## Production audit

Pages deployment 33934938393 succeeded on current main. The live browser pass
checked 16 routes at 1440/1024/768/390/360 (80 combinations). All canonical routes
were HTTP 200, with no body overflow, failed assets, missing alt attributes or
synthetic ballots. Mobile menu click/Escape worked. `/pickem/` alone returned
GitHub's 404; canonical `/picks/` already worked. This PR adds a compatibility
landing page. Lazy venue images loaded correctly when requested; no replacement
artwork was needed. No new design system or league artwork was created.

Public community modules intentionally lack results. Forms remain null, polls
empty, rankings empty and Pick’em unfinalized. The old current-data badge did not
age out after failed publishing; this pass marks snapshots older than 12 hours stale.
Picks' raw `unconfigured` label is replaced with a reader-facing Opens soon label.

## Yahoo: partially available, not a blanket OAuth failure

Latest inspected updater: [33972404433](https://github.com/stringer56/fantasy-football-site/actions/runs/33972404433).
API request returned HTTP 403; official public-page fallback succeeded. Normalized
data and validators succeeded. Publishing then failed with a missing
`_data/power_rankings` pathspec. There are no finalized ballots yet, so that directory
correctly does not exist. This PR stages only existing generated targets; it does
not change secrets, consent, OAuth, invitation data or API architecture.

| Domain | Status | Evidence / limitation |
|---|---|---|
| 2026 metadata | PARTIALLY AVAILABLE | Public fallback succeeds; API blocked; publishing fix awaits merge |
| 2026 teams | PARTIALLY AVAILABLE | 12 verified canonical joins in retained September 4 snapshot |
| 2026 standings | PARTIALLY AVAILABLE | 12 real preseason 0–0 rows; no invented rank |
| 2026 matchups | PARTIALLY AVAILABLE | Six Week 1 matchups; refreshed fallback passed before publish failure |
| 2026 rosters | PARTIALLY AVAILABLE | 12 normalized team rosters; no historical points claim |
| Historical seasons | HEALTHY for committed results | Five completed seasons/446 verified games; 2021 automated access blocked but commissioner recovery complete |
| Historical player rosters | BLOCKED for publication | Source season identity/scoring not authoritative |
| Drafts | PARTIALLY AVAILABLE | 2022–2025 structured; 2021 image-only; 2026 not normalized |
| Transactions | PARTIALLY AVAILABLE | 2022–2025: 1,140 verified events; 2021/2026 not ingested |

Power Rankings/general polls work without Yahoo. Pick’em needs verified slate
and completed results; retained verified Week 1 data can support collection after
Joe's confirmation, but a fresh public result is needed for grading. No fake
fallback matchup/winner is allowed. The next scheduled/manual updater on merged
main must demonstrate actual successful commit/deployment before freshness is called healthy.

## Actual data architecture

Human-managed YAML (`site`, `community`, `owners`, `franchises`, `votes`, historical
facts/editorial) supplies identities/rules/provenance. Yahoo API or public pages
normalize in memory to allowlisted `_data/generated` JSON. Historical transcription
and recovered archives feed deterministic records/recaps. Jekyll reads these
public inputs and GitHub Pages serves the rendered static site.

Commissioner Google Forms → private Sheets/CSV → local validation/preview →
explicit reviewed finalizers → aggregate archives → generated community/live views → Jekyll.

| Boundary | Location |
|---|---|
| Human-maintained public configuration | `_data/*.yml`, editorial/source YAML |
| Sanitized generated public data | `_data/generated/`, `_data/news.json` |
| Immutable aggregate archives | `_data/power_rankings/`, `_data/picks/`, `_data/league_votes/` |
| Private/ignored responses and receipts | `private-vote-imports/` (including `.community-state`) |
| Disposable raw Yahoo cache | `.cache/yahoo-history/`, `.cache/yahoo-live/` |
| Synthetic fixtures | `tests/fixtures/`; CLI test repositories use OS temporary directories |
| Optional commissioner helper | `tools/`, excluded from Jekyll output |

## Community code-path audit and corrections

- Shared latest-valid-per-owner policy remains unchanged; malformed CSV now rejects
  duplicate columns and inconsistent row widths instead of losing fields silently.
- Preview receipts bind raw private file hash AND reviewed rules/identities/deadline/slate.
- Power finalization gates time, uses immutable audited weekly archive, and public
  refresh keeps the latest finalized result. Validator accepts the canonical archive fields.
- Pick’em finalization gates actual lock/current time and canonical lock week; grading
  needs the unchanged private locked CSV binding. Equal aggregate totals cannot hide
  swapped manager choices. Private hash never enters public archive.
- General polls require closed status/deadline plus reviewed preview, persist immutable
  per-poll archives with explicit override/reason, and retain prior polls across imports.
- Low-level public builders reject raw imports; no preview-bypass CLI publication.
- `refresh_community.py` rebuilds configuration/finalized-only views, including fallback
  general Form URL. Yahoo fresh updates use it so later-week slates do not stay at Week 1.
- Status now reports timestamp age, canonical lock/week and blocking reasons. It is
  advisory, not an authorization system; finalizers perform complete checks again.
- Exact Forms guide fixes grid/dropdown inconsistencies, column titles, timestamps,
  missing publication arguments and stale sample kickoff dates. Optional generated
  Apps Script creates closed Forms and private schema-correct CSV exports; not run in Google.

## Privacy and security

No real responses were provided/imported/finalized. Public picks remain private
before lock; default individual selections remain private afterward. No synthetic
results publish. All raw input and receipt bindings remain outside public data.
Jekyll explicitly excludes private imports, tools, scripts, docs and fixtures.
New privacy validator scans public data/build for emails, private Google links,
credential values, invitation keys, raw response CSV and synthetic markers. Existing
recursive allowlist/privacy validators remain in force. No secrets were read or changed.

These are local repository workflow safeguards, not cryptographic protection from
an administrator editing archives. Forms manager identity is self-asserted; Joe
must handle impersonation privately. Do not claim Google sign-in or secure identity.

## Validation and review record

Local suite: 192 tests passed at reconciliation validation, including ten
new tests and isolated CLI dry runs for all three flows. Compilation, pip check,
all 14 non-rendered validator entrypoints, deterministic records/recap/metrics and
Yahoo discovery checks, JavaScript syntax checks and diff whitespace checks passed.
Local Bundler is unavailable; the exact GitHub Actions Jekyll/rendered/privacy
build passed on this PR. CI and artifact review evidence is recorded below.

Synthetic tests cover complete/partial ballots, duplicates, invalid IDs/options,
deadline rejection, Yahoo-unavailable behavior, ranking ties, missing previews,
changed input/configuration, private pre-lock picks, grading, immutable archives
and reviewed overrides. No authoritative within-week order or rescheduling model
is invented. Tests use simulated final Yahoo-shaped inputs only inside temp repos.

## Quick quality pass and limitations

Largest images are approved archival originals: 2025 draft-order PNG ~3.34 MB and
2022 championship PNG ~1.72 MB. Preserve originals; future thumbnail/WebP variants
are a low-priority optimization, not a launch blocker. No oversized new art added.
No legacy root debug/diagnostic/duplicate script files remain. `_includes/roster.html`
has no static consumer in the current templates; retained pending deliberate cleanup
because live rosters use their newer presentation. Canonical/OG SEO metadata is a
future low-risk improvement; titles, descriptions and language metadata already exist.
Compatibility
`franchise_summaries.json` is intentionally retained; later cleanup needs consumers checked.
External ticker has three source adapters but no committed articles; ESPN feed
returned 403 in the latest job. Feed errors are not public headlines.
No autoplay media/heavy framework added. Visual review is not a full WCAG audit.
Missing historical rosters, 2021 structured draft and unverified tenure/calendar
facts remain explicit. Full historical migrations are not restarted.

See `ROADMAP.md` for deferred enhancements and `NEXT_STEPS.md` for Joe's exact actions.

## Final build evidence

[CI run 33982767324](https://github.com/stringer56/fantasy-football-site/actions/runs/33982767324)
passed for implementation commit `723cd8082333d347739714a90114e9e8aec4cc69`, including
192 tests, Jekyll and the rendered/privacy checks. Its downloaded artifact passed
the existing validator for **44 rendered pages** and the new privacy scan locally.
Browser review of that exact artifact passed **80/80 combinations** (16 routes at
1440, 1024, 768, 390, 360): no body overflow, broken images, missing alt attributes,
failed internal requests, debug states or synthetic data; mobile menu/Escape worked.
Desktop and mobile screenshots of home, weekly hub and community pages were reviewed.
Local screenshots/results remain ignored under `.cache/reconciliation-*`.

No merge/deployment is performed by this pass. The code is suitable for commissioner
review/merge when the latest PR check stays green; production still runs main #23.
The site is not operationally activated until real Forms, ranking deadline and a
real poll are configured and Joe verifies the repaired updater on merged main.
