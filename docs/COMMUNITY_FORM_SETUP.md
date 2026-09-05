# Community Google Forms Setup

September 2026: no real Forms or ballots exist. Blank responder URLs in
`_data/community.yml` are intentional. Google Forms is free external collection;
GitHub Pages never accepts submissions or accesses private Google data.

## Option A — Recommended: create all three with Apps Script

1. Open [Google Apps Script](https://script.google.com) in Joe's Google account.
   Click **New project**. No Cloud billing or repository credentials are needed.
2. Name it **Road to Glory Community Forms**. Replace **Code.gs** with the entire
   repository file `tools/create_community_forms.gs`. Save.
3. Click **Save project** (disk icon or Ctrl+S). In the function dropdown beside
   **Run**, select **createCommunityForms**, then click **Run**. Review permissions.
   This personal script uses Forms, its own script properties, and Drive for
   optional private CSV exports. Authorize only the reviewed copy in your account;
   Expected services are Google Forms and Drive (private CSV export), not Gmail,
   contacts, GitHub or external networking. Google may display an
   unverified-personal-script warning; proceed only for your own reviewed copy.
   Stop if permissions or the project/account are unexpected.
4. Open **Execution log** in the editor (or **Executions → latest run → Logs**).
   Wait for completion. Copy the three lines labeled **PUBLIC RESPONDER URL**,
   keeping each feature title beside its URL. These are the only links to give Codex.
   New Forms are unpublished/closed; the log also reports whether each accepts
   responses. A rerun reuses existing Forms without changing their open/closed state.
   Find editable Forms at [Google Forms home](https://forms.google.com).
5. League Votes intentionally has no poll choices. Populate `vote_id` and
   `option_id` from one real poll in `_data/votes.yml` before publishing.
   Do not publish the empty shell or invent placeholder choices.
6. Reruns in the same script project reuse saved Form IDs; they do not change
   existing questions/responses. If setup fails partway, inspect and complete
   that Form manually. Creating another script project would create duplicates.
7. Optionally select **Responses → Link to Sheets → Create a new spreadsheet**.
   Keep Sheet sharing **Restricted**. Never paste a Sheet URL into GitHub.
8. **Stop here with all three new Forms closed.** Send only the responder URLs to
   Codex, choose the Power Rankings deadline, and review the schema below. An
   unpublished responder link may not open yet; do not publish merely to obtain it.
   Never send the editor address ending `/edit` or linked `docs.google.com/spreadsheets/`
   URL for site configuration. A responder URL is not proof that access is enabled.
9. Only after review, publish the intended Forms with appropriate responder access.
   **Publishing can reset accepting-responses state**, so verify the Responses
   control immediately. Leave League Votes unpublished until a real poll exists.
   Test signed out without submitting a fake response before sharing with managers.

This helper is generated locally with `python scripts/build_community_forms.py`
from canonical owners/franchises and the verified current slate. Regenerate and
review before later weeks; there is no automatic rollover. It contains no secrets,
network forwarding, repository access, billing setup or deployed server. It has
not been run in Joe's Google account; an account-policy smoke test is still required.

If Apps Script fails: do not repeatedly create new script projects. Existing saved
Form IDs are retained to prevent duplicates, but a partial Form is not automatically
repaired. Inspect it in Google Forms home, keep it unpublished with Responses →
Accepting responses OFF, and complete its exact questions with Option B. If an
account blocks public access or authorization, stop and resolve the account policy;
do not bypass it or grant broader sharing permissions.

## Option B — Manual fallback and common settings

1. Open Google Forms and click **Blank form**. Use the exact feature title below.
2. In **Settings → Responses**, turn email collection OFF and **Limit to 1 response**
   OFF (that setting requires Google sign-in). Disable response editing and
   respondent result summaries. Do not ask for any other personal information.
3. Use **+** to add each question. Enter the exact lowercase title, choose the
   specified type, enter choices, and turn **Required** ON.
4. For the `owner_id` dropdown use these exact canonical choices:

| Choice | Manager |
|---|---|
| `james-beast` | James “Beast” |
| `mccall` | McCall |
| `forrest-f` | Forrest F. |
| `nate` | Nate “Dogg” |
| `waz` | Waz |
| `ryan-d` | Ryan D. |
| `finn-d` | Finn D. |
| `jack-d` | Jack D. |
| `tj` | TJ |
| `terry` | Terry |
| `joe` | Joe |
| `coles` | Coles |

Manager IDs are self-asserted, not authenticated. Latest valid response per ID
at or before the deadline counts once. A later invalid response does not replace
it. Joe must resolve disputed/impersonated identities privately.

5. Keep each Form unpublished during setup. After review, **Publish** with
   responder access **Anyone with the link**, if account policy permits.
6. Test the responder link signed out/in a private browser WITHOUT submitting a
   fake ballot. Copy the responder link, not the address bar's `/edit` link.
   Expanded `https://docs.google.com/forms/d/e/.../viewform` links are preferred.
7. Manually stop accepting responses at the announced deadline. A static website
   cannot close Google Forms.

## 1. Road to Glory FFL — Weekly Power Rankings

Every question is required:

| Exact title | Type | Choices |
|---|---|---|
| `owner_id` | Dropdown | Manager IDs above |
| `season` | Dropdown | `2026` only |
| `week` | Dropdown | `1` only for Week 1 |
| `rank_1` through `rank_12` | 12 separate Dropdowns | All franchise IDs below |

```text
albany-kneelers
ayahuasca-rush
baseball-furies
buffalo-bravado
crazy-wazs-team
greendale-human-beings
maine-moose
new-jersey-giants
north-town-ninnyhammers
turnbull-acs
van-cortlant-rangers
vegas-vandals
```

The importer enforces all franchises exactly once; Forms cannot enforce uniqueness
across dropdowns. Do not substitute a grid: its exported columns differ.
Scoring is 12 through 1; exact aggregate ties share competition rank.
Week 1 has no previous rank/movement. Joe must choose the ranking deadline.
After Joe chooses it, set **`power_rankings.closes_at` in `_data/community.yml`**
to the approved timezone-aware ISO timestamp and put the same deadline in the
Form description/league announcement. A consistent weekly deadline before the
first kickoff is a sensible operating pattern, not a configured requirement or
an approved time. It need not equal Pick’em's lock. No value is saved by this helper.

English linked-Sheet headers in question order:
`Timestamp,owner_id,season,week,rank_1,rank_2,rank_3,rank_4,rank_5,rank_6,rank_7,rank_8,rank_9,rank_10,rank_11,rank_12`.
Google may localize Timestamp. Safe importer headers replace it with
`submitted_at` **and convert its values to timezone-aware ISO-8601**.
Column order is immaterial.

## 2. Road to Glory FFL — Weekly Pick'em

Required dropdowns: `owner_id`, `season` (`2026`), `week` (`1`).
Then these required **Multiple choice** questions:

| Exact question title / CSV header | Exactly two choices |
|---|---|
| `2026-week-01-buffalo-bravado-vs-van-cortlant-rangers` | `buffalo-bravado`, `van-cortlant-rangers` |
| `2026-week-01-albany-kneelers-vs-turnbull-acs` | `albany-kneelers`, `turnbull-acs` |
| `2026-week-01-ayahuasca-rush-vs-vegas-vandals` | `ayahuasca-rush`, `vegas-vandals` |
| `2026-week-01-crazy-wazs-team-vs-north-town-ninnyhammers` | `crazy-wazs-team`, `north-town-ninnyhammers` |
| `2026-week-01-greendale-human-beings-vs-new-jersey-giants` | `greendale-human-beings`, `new-jersey-giants` |
| `2026-week-01-baseball-furies-vs-maine-moose` | `baseball-furies`, `maine-moose` |

Linked-Sheet headers: `Timestamp,owner_id,season,week`, then these six exact IDs.
Safe importer headers replace Timestamp with `submitted_at` and convert values.
Confirm the canonical Yahoo slate still reports Week 1 and six matchups.

### Next week: regenerate a reviewed weekly copy

The checked-in helper is a **Week 1 snapshot generated from canonical data**, not
a permanent generic matchup list. For Week 2 and later, first refresh/verify that
week's Yahoo slate and configure its commissioner-approved Pick’em lock with the
matching `lock_week`. Then have Codex run `python scripts/build_community_forms.py`
and `python scripts/build_community_forms.py --check`, review the exact new questions,
and provide the regenerated helper. Generation rejects a lock from another week.

Recommended: use a new named Apps Script project for the new week, run the same
`createCommunityForms` function, and keep the old project, Forms and private exports
intact. This creates a fresh weekly set of three closed Forms; the unused League
Votes shell can remain closed. Give Codex the new intended responder URLs.
Export each week from **its original script project**. Never replace old Pick’em
questions while responses or grading are pending, and never mix weeks in one CSV.

For manually created Forms, create a separate weekly copy and replace `week` and
all matchup-ID questions using that week's reviewed list. The old list above must
not be reused as a later week's slate. Google Sheet exports still need the documented
timestamp conversion. There is no automatic Form rollover or silent question update.

### Verified whole-slate lock

`2026-09-09T20:20:00-04:00`, America/New_York. Patriots at Seahawks begins
Wednesday September 9 at 8:20 PM EDT. Reverified September 5 against the
[official NFL schedule](https://www.nfl.com/schedules/2026/by-week/week-1) and
[Patriots broadcast guide](https://www.patriots.com/news/how-to-watch-listen-patriots-at-seahawks-week1).
Configuration: `pickem.lock_at`, `lock_week: 1`, `lock_timezone: America/New_York`.

All Wednesday/Thursday/Sunday/Monday selections close together at kickoff.
The established importer accepts timestamps at or before lock. Close the Form
at that instant. If earliest kickoff moves before lock, update configuration and
Form description, announce it, and preview again. Fantasy matchup IDs do not
change with NFL times. After lock, corrections/reopening require explicit review.
There is no automated postponement/rescheduling model.

No aggregates or private selections publish before lock. After lock only aggregates
publish by default. Keep individual selections private. Pending games stay ungraded;
verified tied/no-contest results never become losses. Keep the exact locked CSV
and private `.community-state` binding for later grading. If Yahoo is unavailable,
retain the private export and wait; never guess games/winners.

## 3. Road to Glory FFL — League Votes

All required: `owner_id` (**Dropdown**), `vote_id` (**Dropdown**, exact real poll
ID in `_data/votes.yml`), `option_id` (**Multiple choice**, real option IDs for
that poll). No comments question and no invented poll.

Configure one poll per reusable Form at a time. Concurrent polls with different
options need separate Forms and poll-specific URLs.
Linked-Sheet headers: `Timestamp,owner_id,vote_id,option_id`.
Safe headers: `submitted_at,owner_id,vote_id,option_id`.

General votes finalize only when YAML status is `closed`, the deadline has passed,
and a fresh preview is reviewed. Use `after_close` or `hidden` visibility.
Close both the Form and YAML poll; one does not change the other.

## Safe private CSV export

For helper-created Forms, run **exportPowerCsv**, **exportPicksCsv**, or
**exportVotesCsv** in the same script project. It reads actual responses,
uses Google's submission timestamp converted to ISO UTC (`Z`), and creates a
private Drive CSV. It never logs/shares responses or imports results into the site.
Download that file to ignored `private-vote-imports/`.

For manual Forms: **Responses → linked Sheet → File → Download → CSV**. Make a
private working copy, rename Timestamp to `submitted_at`, and convert values
from the Sheet's declared timezone to ISO-8601, e.g. `2026-09-08T18:30:00-04:00`.
Do not guess timezone or replace submission time with export time. Ask for help
with private conversion if uncertain. Other headers already match the importer.

Files: `power-week-01.csv`, `picks-week-01.csv`, `votes-week-01.csv`.
Never copy raw CSV, email, Sheet/editor URLs or comments into public `_data`.
No input is needed before real managers respond.

## Configuration, review and archive

Paste real responder URLs into `power_rankings.form_url`, `pickem.form_url`,
`league_votes.form_url` in `_data/community.yml`. Poll-specific `form_url`
overrides the reusable general-vote URL. Use lowercase configuration states:
`unconfigured`, `upcoming`, `open`, `closed`; Pick’em also uses `locked`/`final`.
Public labels are Opens soon/Open/Locked/Finalized/Archived.

```powershell
python scripts/refresh_community.py
python scripts/community_week.py --season 2026 --week 1
python scripts/validate_votes_data.py
python scripts/validate_privacy.py
```

See [Weekly Commissioner Checklist](WEEKLY_COMMISSIONER_CHECKLIST.md) for exact
preview/finalization commands. Previews report accepted/rejected/superseded rows,
missing managers and aggregate results, writing only an ignored private receipt.
Changing input, rules, identities, deadline or slate invalidates review. Finalizers
repeat validation and check publication time. Rejected rows need explicit
`--allow-rejected` for Power/Pick’em; general polls require zero rejected rows.

Archives: `_data/power_rankings/2026/week-NN.json`,
`_data/picks/2026/week-NN.json`, `_data/league_votes/2026/POLL-ID.json`.
Corrections require `--override-finalized --override-reason "public-safe reason"`
and actual `--published-at`. Audit metadata retains prior public fingerprints;
Git retains prior versions. CLI guards do not prevent an administrator manually
editing repository files. Keep private locked inputs backed up for grading.

Google APIs: [FormApp](https://developers.google.com/apps-script/reference/forms/form-app),
[Form](https://developers.google.com/apps-script/reference/forms/form),
[FormResponse](https://developers.google.com/apps-script/reference/forms/form-response).
