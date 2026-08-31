# Yahoo Data Pipeline

## Flow

```text
Yahoo Fantasy API
  -> GitHub Actions secret-backed request
  -> in-memory raw response
  -> explicit allowlist normalizers
  -> _data/generated/*.json
  -> public-data validation
  -> generated-data commit when changed
  -> GitHub Pages/Jekyll render
```

Raw Yahoo responses are not written to the repository. The Action keeps them in
memory only long enough to create sanitized public data.

## Required GitHub Actions secrets

Configure these under **Repository Settings → Secrets and variables → Actions**:

- `YAHOO_CLIENT_ID`
- `YAHOO_CLIENT_SECRET`
- `YAHOO_REFRESH_TOKEN`
- `LEAGUE_KEY`

Do not place values in repository files, logs, issues, or pull requests.

For 2026, `LEAGUE_KEY` should contain the alias `nfl.l.26455`. Yahoo may resolve
that alias to a season-specific game key. The code uses the API response as the
source of truth and does not hardcode a resolved game key.

## Manual Action run

1. Open the repository on GitHub.
2. Select **Actions**.
3. Select **Update Yahoo Data**.
4. Select **Run workflow** and choose the intended branch.
5. Review the normalizer tests, Yahoo fetch, news fetch, public-data validation,
   and commit steps.

The Action commits only `_data/generated/*.json` and `_data/news.json`, and only
when their normalized content changed.

## Moving to a new Yahoo season

1. Renew/create the Yahoo league and obtain its public league ID.
2. Change `_data/site.yml` `current_season`, `yahoo.league_alias`, and public
   league URL in a reviewed pull request.
3. Update the `LEAGUE_KEY` Actions secret to `nfl.l.<league-id>` without exposing
   the value in logs or source files.
4. Manually run the Action.
5. Confirm `league.json` reports the expected season and league ID.
6. Confirm team, standings, matchup, and roster outputs before merging any
   season-facing site changes.

Do not copy Yahoo's resolved season game key into site configuration.

## Local tests

Python 3.11 or newer is recommended.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python scripts/validate_public_data.py
```

The tests use synthetic, sanitized Yahoo-shaped fixtures and make no network
requests.

## Local Jekyll build

With Ruby and Bundler installed:

```powershell
bundle install
bundle exec jekyll build
```

The `Gemfile` pins the GitHub Pages dependency set. The project continues to use
the `/fantasy-football-site` base URL from `_config.yml`.
