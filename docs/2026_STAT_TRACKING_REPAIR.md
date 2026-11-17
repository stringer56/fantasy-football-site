# 2026 stat tracking repair — November 17, 2026

The primary visitor site is https://roadtogloryffl.com/. Its existing Sites
deployment and member database are distinct from the GitHub Pages rendering.
GitHub Actions remains the unattended collector of sanitized public Yahoo data.
The custom-domain Site reads that public data; publishing an older Jekyll layout
to GitHub Pages does not update the custom domain.

## Confirmed failures

- The custom-domain build still contained September 15 / Week 2 data.
- Its client refused a newer week rather than replacing the complete slate.
- Yahoo's longer week-selector markup moved the status beyond the fallback
  parser's 3,000-character limit, misclassifying both finals and upcoming games.
- Weekly snapshots stopped being refreshed when the next week opened, leaving
  some Monday scores incomplete.

## Repair and verification

Read the entire heading before matchup rows. Only Yahoo's explicit final status
permits final winners. `sync_completed_live_weeks.py` retrieves unresolved past
weeks and rechecks the last two completed weeks for scoring corrections; `--all`
rechecks every completed week. Raw pages remain in ignored cache. Archived
rosters and community snapshots remain tied to their original week; current
rosters are never substituted into a past game. A failed archive retrieval
does not block publication of otherwise valid current data, and retries on the
next scheduled full update.

All 60 matchups in Weeks 1–10 were reread from the official Yahoo public
scoreboard. All 12 teams' cumulative W/L/T, PF and PA exactly reconcile to
the current Yahoo standings. Week 11 has six upcoming matchups. The fallback
source is explicitly labeled; the authenticated API currently returns HTTP 403.
OAuth credentials and configuration were not changed.

The custom-domain repair reuses its existing Liquid presentation on the hosted
Worker, refreshing current standings, weekly routes, playoff projections,
statistics and franchise summaries from the public GitHub feed. Five-minute
server caching avoids a rebuild for each update. The full collector remains
scheduled every 15 minutes and the score-only collector every five minutes;
GitHub scheduling and Yahoo availability can delay those intervals. No local
computer needs to remain online. Source timestamps and fallback/stale labels
remain visible. Existing accounts, polls and NFL competitions are untouched.

## Checks

Regression tests cover long Yahoo navigation, explicit final/upcoming states,
incomplete slates, missing scores, unresolved mappings, and archive retention.
Two pre-existing Forms tests now use an in-memory lock matching their test
slate instead of requiring production Week 1 settings to match the live week.
No public community settings or responses were changed.
