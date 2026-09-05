# 2026 Community Operations

Start with [Joe's Next Steps](NEXT_STEPS.md), then the exact
[Form Setup](COMMUNITY_FORM_SETUP.md) and [Weekly Checklist](WEEKLY_COMMISSIONER_CHECKLIST.md).
These supersede old Thursday sample timestamps and ranking-grid instructions.

## Trust boundary

Google Forms collects in Joe's account. Private Sheets/CSV stay there or in ignored
`private-vote-imports/`. Local importers validate/preview; explicit reviewed
finalizers write public aggregate archives. Jekyll/GitHub Pages never accepts
submissions, authenticates managers or reads private Google data. IDs are
self-asserted; Joe resolves disputes. No fake Forms, polls, ballots or results exist.

## Review guarantees

- Private preview receipts bind input hash, configuration, identities, deadline and
  Pick’em slate. Raw rows never appear in receipts or public data.
- Finalization repeats validation. Raw imports cannot publish through builders.
- Power/Pick’em check wall-clock and publication time before releasing results.
- Pick’em grading needs the unchanged private locked CSV and its private hash binding.
- General polls finalize only after closing; archives persist across subsequent polls.
- Overrides require explicit flags/reasons and preserve audit history. Reasons are public.
- Privacy checks cover all public data and built output. Jekyll excludes private
  imports, scripts, tools, docs and fixtures. No OAuth architecture changes.

## Yahoo unavailable / rollover

Power Rankings and general polls do not need Yahoo. Pick’em needs the verified
canonical slate and completed Yahoo winners for grading. A retained verified slate
can still support collection if Joe confirms its week; stale never means fabricated.
If the source is unavailable, retain private responses and wait. If Yahoo's current
week advances before grading, recover a verified saved week with engineering help;
the current CLI intentionally refuses to grade a different current week.

## Status

`python scripts/community_week.py --season 2026 --week 1` reports configuration,
lock/deadline, private input/receipt presence, finalization gates, archives, active
polls and Yahoo age. Older than 12 hours is stale, not an NFL schedule guarantee.
No response contents or credentials print. Status is advisory; finalizers repeat
the authoritative checks, including private binding and overrides.

Before publication run the complete suite and CI documented in
`docs/PRODUCTION_READINESS.md`. Never finalize without Joe's explicit instruction.
