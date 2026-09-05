# Authoritative Roadmap — September 2026

Reconciled against main `db6af82626a28f0eee4a9e71e72f3f5419cdedcb` and PR #24.
This supersedes the sequence in the original Milestone 1 overhaul plan; that plan
is retained as historical design context. Do not restart completed migrations.

## Implemented baseline

- Free GitHub Pages/Jekyll portal, navy/gold reusable layouts, responsive navigation.
- 12 active franchises, one retired franchise plus preserved Quahog identity.
- Complete 2021–2025 seasons: 58 team-seasons, 80 weeks, 446 verified matchups,
  58 team mini-recaps, five champions, 33 playoff/placement game recaps.
- All-time engine: 78 head-to-head pairs, career tables, scoring/margin/streak
  records, 21 classified title-bracket games, franchise histories and thresholds.
- Drafts: 58 resolved opening slots, 720 structured 2022–2025 picks; 2021 image archive.
- 2026 hub, verified Week 1 route, standings/matchups/rosters, deterministic League
  Wire and Record Watch foundation. No fabricated clinching/odds.
- Manager Power Rankings, SVG ranking history, Pick’em, general polls, private
  previews and public archives. PR #24 holds operations/launch safety additions.

## Launch blockers

1. Review and merge corrected PR #24 explicitly; verify Pages and the next Yahoo
   update after merge. Current main's staging step fails on an absent archive folder.
2. Joe creates/reviews/publishes real Forms and supplies only public responder links.
3. Choose Power Rankings deadline and any real general poll/options/window. A Form
   URL alone does not establish poll metadata or a complete operation.
4. Run signed-out responder checks and verify current Week 1 slate before sharing.
5. Google account execution of optional helper remains untested; manual setup works.

## Week 1 operations

- Whole-slate Pick’em lock: Wednesday September 9, 8:20 PM America/New_York.
- Keep Forms, response Sheets, private CSVs and locked export backups in Joe's account.
- Review participation/duplicate identity disputes; IDs are not authenticated.
- Import → validate → preview → Joe reviews → explicit finalization → archive.
- Grade before current Yahoo week rolls over, or recover an authoritative saved
  week with engineering assistance. Never infer missing results.
- Confirm latest scheduled public fallback commits and deployment actually succeed.
- Keep public state safe while Forms remain unconfigured; do not publish test ballots.

## Current-season enhancements

- Reliable operational freshness alerts and verified previous-week grading recovery.
- Current 2026 draft import if authoritative results are available; no invented date.
- Weekly League Hub expansion/verified weekly recaps, not a new hub architecture.
- Record Watch integration into completed-season records only after final verification.
- Playoff race/clinching scenarios require exact settings, tiebreakers and schedule model.
- Trophy tracker and league calendar require approved event dates.

## Historical data gaps

- Machine-readable 2021 player draft board; preserve existing approved images.
- Authoritative weekly historical rosters/starter/bench points: bench misses remain disabled.
- 2021 transactions; current 2026 draft/transaction ingestion not yet normalized.
- Founding/retirement dates, owner succession/tenure and approved fight-song media.
- Historical calendar dates for On This Day, not approximate dates inferred from weeks.
- Source-written recaps and approved editorial rivalry material if supplied.
- Preserve documented 2021/2022 seed-art conflicts, 2023 bracket lane error and
  2024 champion PF/PA label reversal. Canonical verified results already resolve calculations.

## Community enhancements

- Private operator receipt/archive recovery UX and optional authenticated identity
  mechanism only if needed, free and separately reviewed.
- Power Rankings vs standings visualization after multiple real snapshots exist.
- Manager Pick’em already exists; improve operations before adding new scoring modes.
- League awards and Hall of Fame require approved polls/criteria; no automatic inductees.
- No correct-pick streaks without authoritative within-week ordering.

## News/media backlog

- Multi-source NFL/fantasy ticker code exists (NFL.com, ESPN, FantasyPros); committed
  feed is empty. Audit source reliability and freshness after updater staging repair.
- League Wire already exists as deterministic league facts, separate from outside news.
- Full News hub, roster-relevant player news, YouTube/media embeds and editorial wire
  are deferred. Require public source attribution, safe embeds and graceful feed failure.

## Long-term ideas

Named rivalry pages, richer franchise timelines, On This Day, transaction/trade
center, expanded draft room with source-backed ADP/value methods, trophy tracking,
league calendar, awards and Hall of Fame. No backend, paid infrastructure or visual
redesign is justified merely by their presence in this backlog.

## PR reconciliation

`main (through #23) → #24 (operations + this reconciliation) → real Form activation`.
#1 is an obsolete conflicting visual foundation. #10 is a conflicting old historical
foundation; later merged work supersedes its core coverage. Do not merge either.
Joe may close them as superseded after preserving any useful design notes; they
remain untouched by this pass. New future work starts from reviewed latest main.

## Recommended next engineering milestone

**Week 1 live activation and first verified results rehearsal**: wire Joe's real
responder URLs, validate signed-out Forms, confirm Yahoo refresh/deployment and run
private real-response previews. Finalize only with explicit commissioner approval.
