# 2026 Community Operations

For first-time Google Forms creation and exact response headers, use `docs/COMMUNITY_FORM_SETUP.md`. For the short recurring routine, use `docs/WEEKLY_COMMISSIONER_CHECKLIST.md`.

The status command reports the current Yahoo week and freshness, all three Form configuration states, pending private imports, content-matched preview receipts, finalization permission, archive states, and open league polls. It never prints Form URLs or response contents.

Preview commands write only a SHA-256 and counts to ignored `private-vote-imports/.community-state/`. Changing a source file makes its receipt stale. Finalization requires `--published-at`; a correction requires `--override-finalized --override-reason "reviewed explanation"` and records the previous archive fingerprint.

## Privacy go-live review

- Public configuration contains responder links only; Google Sheet, editor, prefilled, response-edit, and account links are rejected.
- Forms do not require email addresses or Google sign-in.
- Raw CSV exports and preview receipts stay in ignored `private-vote-imports/`, never public `_data`.
- Pick choices and aggregates remain private before lock. Individual picks remain private after lock unless the existing explicit publication option is deliberately selected.
- Free-text comments are outside the supported import schema and cannot be published accidentally.
- Community output contains no credentials, OAuth values, Yahoo account identifiers, or private response contents.

This is the commissioner runbook for Power Rankings, weekly Pick’em, and
general league polls. All commands run from the repository root. Raw Form and
Sheet data stays private and ignored by Git.

## Before every community week

1. Run `python scripts/community_week.py --season 2026 --week WEEK`.
2. Confirm the normalized Yahoo snapshot reports the intended week and six
   current matchups before creating the Pick’em Form.
3. Put public responder URLs, statuses, and lock times in
   `_data/community.yml`. Use ISO-8601 timestamps with an explicit offset.
4. Never paste a Form editor URL, Sheet URL, response-edit URL, prefilled URL,
   account identifier, credential, or Yahoo private-management URL.

## Power Rankings Form

Title: `RTG 2026 Week WEEK Power Rankings`

- Required manager dropdown using the approved names in `_data/owners.yml`.
- Required ranking grid containing every active franchise and ranks 1–12.
- Require exactly one response per rank and do not collect email.

Sanitized CSV columns:

```text
owner_id,submitted_at,season,week,rank_1,rank_2,...,rank_12
```

Each rank value is a canonical `franchise_id`. Preview, then finalize:

```powershell
python scripts/import_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1 --deadline 2026-09-10T19:00:00-04:00
python scripts/finalize_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1 --deadline 2026-09-10T19:00:00-04:00
```

Do not finalize until the preview’s rejected rows and missing-manager list are
understood. `--allow-rejected` confirms that reviewed rejected rows may be
excluded. `--override-finalized` is only for a documented correction.

## Pick’em Form

Title: `RTG 2026 Week WEEK Pick’em`

- Required manager dropdown.
- One required multiple-choice question for every matchup printed by the
  Pick’em preview command.
- Two franchise choices per question, using the exact canonical IDs in the
  sanitized export.
- One lock time for the entire weekly Form; manually stop responses then.

Sanitized CSV columns begin with:

```text
owner_id,submitted_at,season,week
```

Append the exact stable `matchup_id` printed by the preview command as one
column per game. Every row must choose one participating `franchise_id` in
every matchup column. First run preview:

```powershell
python scripts/import_pickem.py private-vote-imports/picks-week-01.csv --season 2026 --week 1 --deadline 2026-09-10T19:00:00-04:00
```

At lock, publish immutable aggregate selections:

```powershell
python scripts/finalize_pickem.py private-vote-imports/picks-week-01.csv --season 2026 --week 1 --lock-at 2026-09-10T19:00:00-04:00
```

Run the same finalizer after all Yahoo results are verified. It advances the
same aggregate from `locked` to `final` and builds weekly/season manager scores.
Selections and percentages are public after lock by default; individual
manager choices are private. Use `--publish-manager-picks` only after a league
decision to make them public. `--hide-aggregates` hides even aggregate choices.

If a locked selection aggregate or finalized score needs correction, use
`--override-finalized` only after documenting why. A normal rerun cannot mutate
a finalized week. A correct-pick “streak” is not published because six fantasy
matchups have no authoritative within-week order; season accuracy and weekly
wins remain deterministic.

## General league poll

Create the poll in `_data/votes.yml` with all fields required by its schema.
Use `vote_id` consistently. Sanitized response columns are:

```text
vote_id,owner_id,submitted_at,option_id
```

Preview, then explicitly publish:

```powershell
python scripts/import_vote_results.py --input private-vote-imports/general.csv
python scripts/import_vote_results.py --input private-vote-imports/general.csv --publish
```

Set `status: closed` after the window. `results_visibility: after_close` keeps
counts hidden until then. `hidden` never exposes them; `public` exposes current
aggregates. The optional `embed_url` must be a public Google Forms URL, and
`form_url` remains the accessible fallback link.

## Review and publish checklist

```powershell
python scripts/community_week.py --season 2026 --week 1
python scripts/validate_votes_data.py
python scripts/validate_public_data.py
python scripts/validate_repository.py
python -m unittest discover -s tests -v
bundle exec jekyll build
git diff --check
```

Review the generated diff for accepted/rejected/superseded counts, week and
season, manager omissions, stable IDs, lock/reveal state, and absence of private
fields. Then run `python scripts/build_live_season.py` and
`python scripts/sync_live_week_pages.py` so finalized community facts reach the
matching weekly hub. Commit only reviewed configuration, immutable aggregates,
and generated public data. Yahoo OAuth, Forms credentials, and private Sheets
remain unchanged and outside the repository.
