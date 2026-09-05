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

Results will be recorded after the branch build and rendered review.
