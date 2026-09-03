# Road to Glory FFL

GitHub Pages/Jekyll website for the Road to Glory Fantasy Football League.

## Architecture

- Human-maintained league history lives in `_data/*.yml`.
- Sanitized current Yahoo data lives in `_data/generated/*.json`.
- GitHub Actions fetches Yahoo/news data without requiring a local computer.
- OAuth credentials remain in GitHub Actions secrets.
- Jekyll renders the committed data as a free GitHub Pages site.
- Pull requests run offline parser, data, and Jekyll build validation.
- The presentation layer is a custom responsive sports-media design system with
  no client framework or npm build step.

## Development

Run the offline parser/news tests:

```powershell
python -m unittest discover -s tests -v
python scripts/validate_public_data.py
python scripts/validate_repository.py
python scripts/validate_franchise_data.py
python scripts/validate_history_data.py
python scripts/validate_draft_data.py
python scripts/build_records.py --check
python scripts/validate_records_data.py
python scripts/validate_votes_data.py
python scripts/build_recaps.py --check
python scripts/validate_recaps.py
python scripts/discover_yahoo_history.py --dry-run --check
python scripts/validate_yahoo_history_backfill.py
```

Run a GitHub Pages-compatible build when Ruby and Bundler are installed:

```powershell
bundle install
bundle exec jekyll build
python scripts/validate_built_site.py
```

The pull-request validation workflow also uploads the rendered `_site` output
as a short-retention artifact for browser testing before merge.

See [Yahoo Data Pipeline](docs/YAHOO_DATA_PIPELINE.md),
[Data Schemas](docs/DATA_SCHEMAS.md), and
[Site Overhaul Plan](docs/SITE_OVERHAUL_PLAN.md). Presentation conventions and
component usage are documented in [Design System](docs/DESIGN_SYSTEM.md). The
Google Site team inventory, editorial decisions, asset provenance, and Yahoo
identity joins are recorded in [Franchise Migration](docs/FRANCHISE_MIGRATION.md).
Verified season provenance is recorded in
[History Migration](docs/HISTORY_MIGRATION.md), and the image-backed draft
archive and unresolved draft identities are recorded in
[Draft Migration](docs/DRAFT_MIGRATION.md).
Record coverage, exclusions, and publication rules are documented in
[Records Data Coverage](docs/RECORDS_DATA_COVERAGE.md).
The free Google Forms collection boundary, sanitization workflow, deadline
limitations, and duplicate-ballot policy are documented in
[Voting Architecture](docs/VOTING_ARCHITECTURE.md).
Deterministic season, team, playoff, and championship storytelling plus the
commissioner override workflow are documented in
[Historical Narrative System](docs/NARRATIVE_SYSTEM.md).
The manual, sanitized Yahoo renewal-chain and resource-capability workflow is
documented in
[Yahoo Historical League Discovery](docs/YAHOO_HISTORY_DISCOVERY.md).
The cache-first, rate-limited public archive importer and its verified coverage
are documented in
[Yahoo Historical Backfill](docs/YAHOO_HISTORY_BACKFILL.md).
