# Joe's Next Steps — Week 1

1. **Review PR #24, then merge it yourself when its latest checks are green.**
   No merge was performed by this pass. Do not merge obsolete PRs #1 or #10.
2. **Create the three Forms.** Follow `docs/COMMUNITY_FORM_SETUP.md` manually or
   copy `tools/create_community_forms.gs` into a new project at script.google.com
   and run `createCommunityForms`. They start closed/unpublished. Do not submit
   test ballots into the real Forms.
3. **Review the questions and privacy settings.** Power Rankings needs your chosen
   deadline. General League Votes needs a real poll ID, options and opening/closing
   dates in `_data/votes.yml`; leave that Form closed until a real poll exists.
4. **Send the three public responder links here**, labeled Power Rankings, Pick’em,
   League Votes. Never send editor or private Sheet links for site configuration.
   Set their corresponding `_data/community.yml` URLs/statuses after verification.
5. **Confirm/announce Pick’em lock: Wednesday September 9 at 8:20 PM Eastern.**
   Canonical value is `2026-09-09T20:20:00-04:00`, `lock_week: 1`. It is already
   verified/configured in PR #24. Recheck only if the NFL changes the schedule.
6. **Refresh and check:** `python scripts/refresh_community.py`, then
   `python scripts/community_week.py --season 2026 --week 1`. Confirm six matchups,
   configured links, announced deadlines and no invented results. After merge,
   verify a successful Yahoo update and Pages deployment; stale data is not live data.
7. **Open the intended Forms and test their links signed out without submitting.**
   Share only after the site update is deployed. Close each Form at its deadline.
8. **When managers have responded**, use the helper's `exportPowerCsv`,
   `exportPicksCsv`, `exportVotesCsv`, or the guide's safe manual CSV conversion.
   Download only into ignored `private-vote-imports/`. Keep the linked Sheets private.
9. **Preview locally; do not finalize yet:**

   ```powershell
   python scripts/import_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1 --deadline <YOUR-ANNOUNCED-ISO-DEADLINE>
   python scripts/import_pickem.py private-vote-imports/picks-week-01.csv --season 2026 --week 1 --deadline 2026-09-09T20:20:00-04:00
   python scripts/import_vote_results.py --input private-vote-imports/votes-week-01.csv
   python scripts/community_week.py --season 2026 --week 1
   ```

10. **Review accepted/rejected/superseded submissions and missing managers.**
    Resolve identities privately. Changed files/rules/deadlines need another preview.
11. **Explicitly authorize finalization after lock.** Use the exact finalizer commands
    in `docs/WEEKLY_COMMISSIONER_CHECKLIST.md`, with the actual current publication
    time. General polls must be closed and re-previewed. Never supply a future time.
12. **After verified Yahoo finals**, grade Pick’em with the same locked private CSV.
    Preserve its private `.community-state` binding/backups. Validate public output,
    refresh the modules, review the diff and publish the reviewed commit. No secrets
    or raw responses go to GitHub. If Yahoo rolls into Week 2 first, ask for help
    recovering the verified Week 1 snapshot; do not change week numbers to bypass it.
