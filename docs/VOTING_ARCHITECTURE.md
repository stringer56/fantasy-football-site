# Voting Architecture

## Decision

Road to Glory uses **Google Forms with a commissioner-owned private Google
Sheet** for ballot collection. GitHub Pages remains the public presentation
layer, and validated aggregate JSON remains the only voting data committed to
the repository. This costs nothing, requires no always-on server, adds no member
accounts, and does not change Yahoo authentication.

The site never writes votes. A public button opens a configured Google Form;
the commissioner closes and exports that form, sanitizes the export locally,
runs the deterministic importer, reviews the diff, and commits only the public
result snapshot.

```text
manager -> public Google Form -> private commissioner Sheet
        -> private CSV/JSON export -> local validation/aggregation
        -> _data/generated/{votes,power_rankings,picks}.json
        -> reviewed commit -> GitHub Pages
```

## Privacy boundary

- Disable **Collect email addresses** in every Form.
- Use a required dropdown containing approved manager display names. During
  sanitization, replace the choice with its canonical `_data/owners.yml`
  `owner_id`.
- Keep raw exports under the ignored `private-vote-imports/` directory or
  outside the repository entirely.
- Remove spreadsheet response IDs and every email, IP address, Google account
  identifier, edit link, or authentication field before import.
- Power Ranking output publishes team aggregates only. Individual ranking
  ballots are never written to `_data/generated/`.
- Weekly picks may publish an approved manager display name and the manager's
  football picks/results. They never include private submission metadata.
- General league votes default to anonymous aggregate totals.

The public-data validator rejects `email`, `email_address`, `ip`, `ip_address`,
`google_user_id`, `account_id`, `auth_token`, `edit_url`, and the existing Yahoo
private-field denylist anywhere in generated output.

## Form templates

### Weekly Power Rankings

1. Create a Form titled `RTG 2026 Week {week} Power Rankings`.
2. Add a required manager dropdown using approved display names.
3. Add one required ranking grid containing all 12 active franchises and ranks
   1–12; enable the setting that requires one response per column.
4. Do not collect email addresses and do not require Google sign-in.
5. Link responses to a private Sheet.
6. Put only the public responder URL in the corresponding poll's
   `submission_url`; never commit the editor URL.

Sanitized CSV columns are `owner_id`, `submitted_at`, then `rank_1` through
`rank_12`, where each rank cell contains a canonical franchise ID.

### Weekly Matchup Picks

1. Create a Form titled `RTG 2026 Week {week} Matchup Picks`.
2. Add the required manager dropdown.
3. Add one required multiple-choice question per current Yahoo matchup. Each
   choice is one of the two participating franchises.
4. Export columns as `owner_id`, `submitted_at`, followed by one column named
   for each canonical `matchup_id`; its value is the selected `franchise_id`.
5. Publish aggregate percentages only when the commissioner intends results to
   be visible.

### General League Vote

1. Create a Form using the canonical poll title and choices.
2. Add the manager dropdown, without collecting email.
3. Export the sanitized columns `poll_id`, `owner_id`, `submitted_at`, and
   `option_id`.
4. Do not create production proposals in `_data/votes.yml` until the
   commissioner supplies the actual question, choices, window, and form URL.

## Deadlines and locking

GitHub Pages cannot enforce a transactional deadline. The poll's `closes_at`
is a public notice, not a security control. The commissioner must manually stop
Form responses before the applicable games begin (or use a separately reviewed
free Google Workspace automation later). Importers reject submissions after the
configured deadline, but they cannot prevent the Form from accepting them.

Never describe a browser clock, disabled button, or JavaScript-only state as a
secure lock.

## Validation and duplicate policy

The deterministic duplicate rule is:

> The latest valid submission from each manager at or before the deadline wins.

Invalid submissions do not replace an earlier valid submission. Importers
reject unknown owners, timestamps without a timezone, late ballots, unknown
franchises/matchups/options, duplicate ranking teams, missing ranking teams,
duplicate ranks, and picks for teams outside their matchup. Rejection counts are
published only as moderation totals, without identities or private row data.
Valid earlier duplicates are counted separately as `superseded_ballots`, so the
latest-submission rule is visible rather than silently merging rows.

Power Rankings use manager votes only. In a 12-team league, rank 1 earns 12
points through rank 12 earning 1. Sorting uses total points, first-place votes,
better average rank, then franchise ID as the deterministic final fallback.
Yahoo standings are never used as a ranking input.

Picks score one point for a correct selection and zero for an incorrect one.
Pending games do not affect totals. Actual winners are accepted only from the
current-season normalized Yahoo matchup output after Yahoo marks the matchup
complete. Picks never write to or modify Yahoo.

## Import and moderation procedure

1. Close the Form manually at the announced deadline.
2. Duplicate the private response Sheet as a moderation copy.
3. Remove disallowed/private columns and map display choices to canonical IDs.
4. Save the sanitized export under `private-vote-imports/`.
5. Run the matching command:

   ```powershell
   python scripts/import_vote_results.py --input private-vote-imports/general.csv
   python scripts/build_power_rankings.py --input private-vote-imports/power-rankings.csv --finalize
   python scripts/build_picks_leaderboard.py --input private-vote-imports/matchup-picks.csv
   ```

6. Review accepted/rejected counts and inspect the generated JSON diff.
7. Run voting, privacy, repository, and Jekyll validation.
8. Commit only generated JSON and any reviewed poll-status change.

Generated timestamps come from the sanitized export, not the local clock, so
re-running the same import produces identical output.

`--finalize` preserves the reviewed weekly aggregate under
`_data/power_rankings/{season}/week-{week}.json`, refuses a different overwrite,
and regenerates the ordered chart/facts model. See
[2026 Power Rankings](POWER_RANKINGS.md).

## Archive process

After results are final, set the poll to `closed` and then `archived`, set
`results_status: final`, record the public generated file as `results_source`,
and remove the public submission URL if the form should no longer accept visits.
Retain the private Sheet according to the commissioner's league policy. The
public archive keeps only sanitized aggregates and approved display names.
