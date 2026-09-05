# Community Google Forms Setup

This guide prepares the three free public Google Forms used by Road to Glory. The forms collect responses; GitHub Pages remains the website. The linked Sheets and raw CSV files stay private.

No live form URLs have been supplied. The blank values in `_data/community.yml` are therefore intentional. Never invent a Form ID.

## Before you begin

1. Sign in to the commissioner Google account and open Google Forms.
2. Create a blank form. In **Settings**, turn off email collection and any option that exposes response summaries.
3. Do not require sign-in. Do not ask for email, Yahoo account, or any personal data.
4. Use the exact question titles below. Make every listed question required.
5. On **Responses**, choose **Link to Sheets** → **Create a new spreadsheet**. Keep that Sheet private.
6. Use public responder links only (`https://docs.google.com/forms/d/e/.../viewform`). Never commit edit, prefilled, Sheet, or response-edit links.

## 1. Weekly Power Rankings

Title the form `Road to Glory — Weekly Power Rankings`.

Add these questions in order:

| Exact question title | Type | Required | Validation |
|---|---|---:|---|
| `Manager ID` | Dropdown | Yes | The 12 canonical `owner_id` values from `_data/owners.yml` |
| `Season` | Dropdown | Yes | `2026` only |
| `Week` | Dropdown | Yes | Open week only |
| `Rank 1` through `Rank 12` | Dropdown | Yes | The 12 canonical `franchise_id` values from `_data/franchises.yml` |

Google Forms cannot enforce that every franchise is used once across 12 dropdowns. The importer rejects duplicates, omissions, unknown teams, wrong weeks, unknown managers, malformed timestamps, and responses after the deadline.

Download the response Sheet as CSV. Make a private working copy and rename the columns exactly:

```text
owner_id,submitted_at,season,week,rank_1,rank_2,rank_3,rank_4,rank_5,rank_6,rank_7,rank_8,rank_9,rank_10,rank_11,rank_12
```

Save it as `private-vote-imports/power-week-01.csv`. Preview:

```powershell
python scripts/import_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1 --deadline 2026-09-10T20:15:00-04:00
python scripts/community_week.py --season 2026 --week 1
```

After review, finalize with a real commissioner publication time:

```powershell
python scripts/finalize_power_rankings.py private-vote-imports/power-week-01.csv --season 2026 --week 1 --deadline 2026-09-10T20:15:00-04:00 --published-at 2026-09-10T20:20:00-04:00
```

Paste the public responder link into `power_rankings.form_url` in `_data/community.yml`, and set the status and close time when the window opens. Week 1 has no previous rank or movement. Those fields begin only after a second finalized snapshot.

## 2. Weekly Matchup Pick’em

Title the form `Road to Glory — Weekly Matchup Pick’em`.

Add:

| Exact question title | Type | Required | Validation |
|---|---|---:|---|
| `Manager ID` | Dropdown | Yes | Canonical active `owner_id` values |
| `Season` | Dropdown | Yes | `2026` only |
| `Week` | Dropdown | Yes | Open week only |
| One question per matchup | Multiple choice | Yes | The two participating canonical `franchise_id` values |

The exact Week 1 matchup question titles/CSV headers are:

```text
2026-week-01-buffalo-bravado-vs-van-cortlant-rangers
2026-week-01-albany-kneelers-vs-turnbull-acs
2026-week-01-ayahuasca-rush-vs-vegas-vandals
2026-week-01-crazy-wazs-team-vs-north-town-ninnyhammers
2026-week-01-greendale-human-beings-vs-new-jersey-giants
2026-week-01-baseball-furies-vs-maine-moose
```

Confirm the current canonical slate with a preview before opening the Form. The sanitized CSV begins:

```text
owner_id,submitted_at,season,week,<one stable matchup_id column for every matchup>
```

Save it as `private-vote-imports/picks-week-01.csv`. Preview and check status:

```powershell
python scripts/import_pickem.py private-vote-imports/picks-week-01.csv --season 2026 --week 1 --deadline 2026-09-10T20:15:00-04:00
python scripts/community_week.py --season 2026 --week 1
```

Finalize after the announced whole-slate lock:

```powershell
python scripts/finalize_pickem.py private-vote-imports/picks-week-01.csv --season 2026 --week 1 --lock-at 2026-09-10T20:15:00-04:00 --published-at 2026-09-10T20:20:00-04:00
```

The timestamp shown is an example of command shape, not the real Week 1 kickoff. Verify the NFL/Yahoo schedule before using it. Paste the public responder link into `pickem.form_url` in `_data/community.yml`.

### Lock policy

- `America/New_York` is authoritative. Every timestamp must include its UTC offset.
- One whole-slate deadline is set before the earliest NFL kickoff for that fantasy week. Thursday, Sunday, and Monday selections all close together.
- If kickoff moves before the lock, update the public time, Form description, and command deadline. Stable fantasy matchup IDs do not change merely because kickoff moves.
- If a game changes after lock, the archive stays locked. Reopening requires an explicit reviewed override.
- If Yahoo data is unavailable, close the Form manually at the announced time, retain the private export, and wait. Do not finalize or grade against guessed matchups or winners.
- Before lock, neither individual picks nor aggregate counts are public. After lock, aggregate counts may be published. Individual picks remain private unless the commissioner deliberately uses the existing `--publish-manager-picks` policy.
- A tied, canceled, or no-contest game is graded only from verified Yahoo status and never becomes an incorrect pick by assumption.

## 3. General League Votes

Title the reusable form `Road to Glory — League Vote`.

Add:

| Exact question title | Type | Required | Validation |
|---|---|---:|---|
| `Manager ID` | Dropdown | Yes | Canonical active `owner_id` values |
| `Poll ID` | Dropdown | Yes | The exact open `vote_id` from `_data/votes.yml` |
| `Selection` | Multiple choice | Yes | Exact option IDs configured for that poll |

The importer does not support publishing free-text comments. Do not add a comments question to the exported schema. The sanitized CSV headers are exactly:

```text
vote_id,owner_id,submitted_at,option_id
```

Save it as `private-vote-imports/votes-week-01.csv`. Preview first:

```powershell
python scripts/import_vote_results.py --input private-vote-imports/votes-week-01.csv
```

Only after review, publish the configured public aggregates:

```powershell
python scripts/import_vote_results.py --input private-vote-imports/votes-week-01.csv --publish
```

Paste the reusable public responder link into `league_votes.form_url` in `_data/community.yml`. Each poll may instead use its own public `form_url` in `_data/votes.yml`.

## Safe weekly export and archive

1. In the private linked Sheet, choose **File → Download → Comma-separated values (.csv)**.
2. Remove the Google-generated display headers and use the exact safe headers above. Do not add email, Sheet URL, response ID, edit URL, IP address, or comments.
3. Save only under ignored `private-vote-imports/`.
4. Run the importer. It does not publish; it writes a content-hash-only preview receipt under the ignored `.community-state` folder.
5. Resolve every rejected row. Missing managers are reported as a participation warning.
6. Run `community_week.py`. A receipt is current only when its SHA-256 matches the current private import.
7. Finalize explicitly. The public archive contains aggregates and audit metadata, not raw Google responses.
8. Commit only public generated output and finalized archives. Never force-add `private-vote-imports/`.

Finalized Power Rankings and Pick’em selections cannot be silently replaced. A correction requires `--override-finalized --override-reason "specific reviewed reason"` and a new `--published-at`; the archive records the reason and the fingerprint of the replaced version.

## Configuration check

Run:

```powershell
python scripts/community_week.py --season 2026 --week 1
python scripts/validate_votes_data.py
python scripts/validate_public_data.py
```

The status command prints only yes/no configuration and operational metadata. It never prints Form URLs, responses, or manager choices.
