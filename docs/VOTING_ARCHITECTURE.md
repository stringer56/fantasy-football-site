# Voting Architecture

Operational configuration lives in `_data/community.yml`: `power_rankings.form_url`, `pickem.form_url`, and `league_votes.form_url`. Blank values are valid, explicit unconfigured states. Only public Google Forms responder URLs are allowed.

Raw responses and private preview receipts remain under ignored `private-vote-imports/`. Publication follows import → validate → preview → human review → finalize → archive. Public output never contains raw response rows, emails, Sheet URLs, OAuth values, or private comments.

## Decision and trust boundary

Road to Glory uses public Google Forms backed by commissioner-owned private
Sheets. GitHub Pages is presentation only: it does not accept ballots, enforce
locks, authenticate managers, or write to Yahoo. A commissioner exports and
sanitizes responses locally, previews validation, explicitly finalizes, and
commits only approved public aggregates.

```text
manager -> public Google Form -> private commissioner Sheet
        -> ignored sanitized CSV/JSON -> local preview -> explicit finalize
        -> immutable weekly aggregate -> generated public views -> GitHub Pages
```

`owner_id` in `_data/owners.yml` is the canonical stable manager ID. It is used
as `manager_id` by importers so a second manager identity registry is neither
needed nor permitted. Approved manager display names may appear in Pick’em
scoreboards; submission timestamps and account identifiers never do.

## Privacy rules

- Disable email collection and Google sign-in requirements in every Form.
- Use a required manager dropdown and map it to `owner_id` during sanitization.
- Keep exports in ignored `private-vote-imports/` or outside the repository.
- Remove emails, response IDs, IPs, account IDs, edit links, prefilled links,
  authentication values, and all Sheet metadata before previewing.
- Commit only public Form responder URLs. Never commit Form editor, Sheet,
  individual response-edit, invitation, or private commissioner URLs.
- Power Rankings publish franchise aggregates only; individual ballots remain
  private.
- Pick’em publishes aggregate percentages after lock by default. Individual
  manager selections remain private unless the commissioner deliberately uses
  `--publish-manager-picks`.
- General votes publish configured poll metadata and aggregate option totals.

The public-data and voting validators reject known private keys recursively.

## Deterministic ballot policy

The latest valid submission from each manager at or before the announced
deadline counts. A later invalid or late row does not erase an earlier valid
row. Preview output identifies rejected row numbers/reasons, superseded rows,
and managers with no valid submission without writing public files.

Power ballots must rank every active franchise exactly once. With 12 teams,
first earns 12 points through twelfth earning 1. Sort order is points,
first-place votes, then lower average rank. Exact mathematical ties share a
competition rank; franchise ID only makes the display order deterministic.
Yahoo standings never affect the vote calculation.

Pick’em ballots must select every current Yahoo matchup exactly once using its
stable canonical matchup ID. One commissioner-defined weekly time locks the
entire slate. A correct verified Yahoo winner earns one point; an incorrect
pick earns zero. Pending or no-contest games do not become losses. The public
percentage layer is hidden before lock.

## General league polls

`_data/votes.yml` is the human-managed registry. Each poll contains:
`vote_id`, title, description, season, type, options, open/close dates, status,
results visibility, named/anonymous mode, public Form/embed URLs, result
summary/source, and notes. Status is `upcoming`, `open`, or `closed`; visibility
is `hidden`, `after_close`, or `public`.

An optional public Google Forms iframe is progressively enhanced only. Every
embedded poll also needs a normal external Form link, and the page remains
usable when the iframe or JavaScript fails.

## Deadlines and finalization

A timestamp printed on a static page is not a security lock. The commissioner
must stop Form responses at the announced time. Importers additionally reject
late rows. Finalized Power weeks are immutable. Pick’em selections become
immutable at `locked`; the same aggregate may later advance to `final` after
Yahoo verifies every winner. Any material correction requires the explicit
`--override-finalized` flag and a documented review.

Exact commissioner commands and Form field definitions are in
[Community Operations](COMMUNITY_OPERATIONS.md). Power-specific persistence and
chart behavior are in [2026 Power Rankings](POWER_RANKINGS.md).

## Public separation

`/power-rankings/`, `/picks/`, and `/votes/` are separate systems even though
they share identity and privacy helpers. Homepage and weekly-hub modules remain
compact and link to their canonical pages. Community headlines are generated
only from finalized weekly archives; previews and open ballots never become
news.
