# Weekly Commissioner Checklist

All raw exports stay in ignored `private-vote-imports/`. Replace Week 1 and timestamps below with the current verified week.

## Monday / Tuesday

- Confirm Yahoo freshness and feature states: `python scripts/community_week.py --season 2026 --week 1`
- Verify the slate and matching `lock_week`, then create that week's reviewed Form
  copy using the setup guide. Preserve prior Forms/script projects for exports and grading.
- Open only the intended Forms; set lowercase `open` status and public responder URLs in `_data/community.yml`.
- Announce the whole-slate Pick’em lock in `America/New_York` with an explicit offset.

## Before games

- Export and sanitize responses to `private-vote-imports/`.
- Preview Power Rankings: `python scripts/import_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1 --deadline <ISO-TIME>`
- Preview Pick’em: `python scripts/import_pickem.py private-vote-imports/picks-week-01.csv --season 2026 --week 1 --deadline <ISO-TIME>`
- Preview votes: `python scripts/import_vote_results.py --input private-vote-imports/votes-week-01.csv`
- Re-run status. Resolve rejected rows, stale receipts, unknown mappings, and participation warnings. Review the aggregate preview.

## At lock

- Close the Google Form manually.
- Finalize Pick’em: `python scripts/finalize_pickem.py private-vote-imports/picks-week-01.csv --season 2026 --week 1 --lock-at <ISO-TIME> --published-at <ISO-TIME>`
- Confirm aggregates are public and individual selections remain private.

## Power Rankings / league polls

- Finalize Power Rankings: `python scripts/finalize_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1 --deadline <ISO-TIME> --published-at <ISO-TIME>`
- Close the real poll in `_data/votes.yml`, preview again, then publish: `python scripts/import_vote_results.py --input private-vote-imports/votes-week-01.csv --publish --published-at <ISO-TIME>`

## After Yahoo results finalize

- Refresh Yahoo data, confirm all winners are verified, then run the same Pick’em finalization command to grade the locked archive.
- Confirm weekly winners and season leaderboard; generated `final` results display as Finalized. Do not manually rewrite archives.
- Refresh public modules: `python scripts/refresh_community.py`, then run `python scripts/validate_privacy.py`.
- Run the full validators and Jekyll build before pushing.
- If a finalized archive truly needs correction, use `--override-finalized --override-reason "specific reviewed reason"` and a new publication time. Never edit it silently.

Week 1 lock is **Wednesday September 9, 2026, 8:20 PM Eastern**:
`2026-09-09T20:20:00-04:00`. Use it for Pick’em preview and `--lock-at`.
Replace `<ISO-TIME>` publication values with the actual current timezone-aware
time, not a future timestamp. Power Rankings needs Joe's separately chosen deadline.
Keep the exact locked private CSV and `.community-state` binding backed up for grading.
