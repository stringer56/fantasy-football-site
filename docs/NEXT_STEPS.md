# Joe's Next Steps — Create the Real Forms

PRs #24 and #25 are merged. Do not merge old PRs #1/#10. No real Forms or responses
have been created by Codex; the community configuration remains safely dormant.

1. **Confirm the post-#25 checks are green.** See the latest post-fix evidence in
   `docs/PRODUCTION_READINESS.md`. No additional Yahoo credential work is required.
2. **Open [Google Apps Script](https://script.google.com)** in your own Google
   account, click **New project**, and name it **RTG 2026 Week 1 Community Forms**.
3. **Copy the reviewed helper** from `tools/create_community_forms.gs` into
   **Code.gs**, replacing its initial contents. Save with Ctrl+S.
4. **Choose `createCommunityForms` and click Run.** Review the Google Forms/Drive
   permissions for your own script. No billing, GitHub secrets or backend is needed.
5. **Open Execution log and copy only the three PUBLIC RESPONDER URL lines**:
   Power Rankings, Pick’em, League Votes. Do not copy editor or linked Sheet URLs.
6. **Keep all three Forms closed/unpublished initially.** New Forms default closed.
   Reruns reuse existing Forms without changing their state. Do not submit test ballots.
7. **Paste the three labeled responder URLs into this Codex task.** They will be
   checked against the intended Forms before site configuration/activation.
8. **Choose the Power Rankings deadline and tell Codex.** Its configuration key is
   `power_rankings.closes_at` in `_data/community.yml`. It remains blank until you
   approve a time. Pick’em already uses Wednesday September 9, 8:20 PM Eastern
   (`2026-09-09T20:20:00-04:00`, America/New_York, Week 1).
9. **Leave League Votes closed until you need a real poll.** Provide a real poll
   question, option choices and opening/closing dates; no placeholder poll is needed.
10. **After configuration review, refresh and check**:
    `python scripts/refresh_community.py`, then
    `python scripts/community_week.py --season 2026 --week 1`.
    Review configured links, six matchups, deadlines and no invented results.
11. **Explicitly open only the intended Forms**, verify signed-out responder
    access without submitting, and share after the reviewed site update deploys.
    Publishing can change accepting-responses state; check it immediately.
    Close each Form manually at its announced deadline.
12. **Import/preview only after real managers respond.** Follow the commands below.
    Review warnings first; finalization is a separate explicit instruction after lock.

## When real responses arrive

Use `exportPowerCsv`, `exportPicksCsv` or `exportVotesCsv` in the same script
project that created that week's Forms. Download the private Drive CSV into
ignored `private-vote-imports/`. Keep linked Sheets restricted.

```powershell
python scripts/import_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1
python scripts/import_pickem.py private-vote-imports/picks-week-01.csv --season 2026 --week 1 --deadline 2026-09-09T20:20:00-04:00
python scripts/import_vote_results.py --input private-vote-imports/votes-week-01.csv
python scripts/community_week.py --season 2026 --week 1
```

The ranking command reads your approved `power_rankings.closes_at`; it stops if
that remains blank. Do not run an import command for a file you do not have.

Review accepted/rejected/superseded rows and missing managers. Changed files or
rules need another preview. Use `docs/WEEKLY_COMMISSIONER_CHECKLIST.md` only after
explicit approval to finalize. Keep the locked CSV and private `.community-state`
binding for later grading with verified Yahoo results. If Yahoo has rolled into
Week 2, ask for help recovering verified Week 1 data; do not relabel weeks.

Manual creation and weekly-copy instructions: [COMMUNITY_FORM_SETUP.md](COMMUNITY_FORM_SETUP.md).
