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
component usage are documented in [Design System](docs/DESIGN_SYSTEM.md).
