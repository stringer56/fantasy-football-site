# Yahoo Historical League Discovery

## Status

Milestone 4.5 now has two deliberately separate discovery paths: the existing
credential-safe Yahoo API probe and the commissioner-linked public Yahoo League
History archive. Neither path changes OAuth, publishes raw Yahoo responses, or
performs a full historical import.

The latest ordered live retest on 2026-09-03 confirms that Yahoo's refresh-token
exchange succeeds. The first Fantasy API request—Yahoo's documented
logged-in-user NFL teams resource—still returns HTTP 403. Per the stop rule, the
job does not attempt later authenticated resources after that failure.

The commissioner created the public custom league URL `rtgffl264552026` and
linked the Road to Glory seasons in Yahoo's League History tool. Those official
Yahoo pages independently resolve the exact 2021–2026 league IDs and expose
representative standings, team, matchup, roster, draft, and transaction pages.
The focused 2021 recovery pass established that its detailed public routes
redirect to Yahoo sign-in; followed requests may then receive HTTP 429. The
season identity remains verified while its Yahoo page-level data is unavailable.
No credential value, authorization header, token response, private commissioner
information, or raw Yahoo page was printed or saved.

## Verified seasons and safe league keys

| Season | Game key | Yahoo league key | League ID | Verification evidence |
|---:|---:|---|---:|---|
| 2021 | `406` | `406.l.12928` | `12928` | Commissioner-provided Yahoo archive URL and linked custom history route. |
| 2022 | `414` | `414.l.527645` | `527645` | Official Yahoo custom history page resolved the underlying league ID. |
| 2023 | `423` | `423.l.161807` | `161807` | Official Yahoo custom history page resolved the underlying league ID. |
| 2024 | `449` | `449.l.761310` | `761310` | The preserved authenticated 2025 metadata names `449_761310` as the prior league in its `renew` field. |
| 2025 | `461` | `461.l.103926` | `103926` | The committed sanitized league/team/standings snapshot is from Road To Glory FFL. |
| 2026 | `470` | `470.l.26455` | `26455` | Official current league page exposes game ID 470 and league ID 26455. |

The earliest linked and verified Yahoo season is **2021** and the latest is
**2026**. The commissioner confirmed that Road to Glory began in 2021, so the
absence of a 2020 league is expected and is not a migration gap.

## Renewal chain

Yahoo renewal metadata previously verified this portion:

```text
449.l.761310 (2024) -> 461.l.103926 (2025)
```

The commissioner-linked Yahoo League History chain is broader:

```text
406.l.12928 (2021)
  -> 414.l.527645 (2022)
  -> 423.l.161807 (2023)
  -> 449.l.761310 (2024)
  -> 461.l.103926 (2025)
  -> 470.l.26455 (2026)
```

The manifest keeps `renew_chain` limited to relationships proven by Yahoo
renewal metadata and records the complete UI-linked sequence separately as
`linked_history_chain`.

The script starts from the configured current alias, resolves it while
authenticated, and follows only explicit Yahoo `renew` and `renewed`
relationships. A league with the same name but no connection to that chain is
retained as an unresolved candidate. League IDs are never assumed to carry
across seasons.

## Capability matrix

`available_snapshot` means a safe existing snapshot proves that resource was
once returned. `single_week_snapshot_only` is not a historical archive.
`Not tested — authorization stop` means the endpoint was deliberately skipped
after the user-level HTTP 403. It does not establish whether the resource would
exist for a correctly authorized Fantasy Sports application/account.

| Season | Metadata | Teams | Standings | Weekly matchups | Final playoff matchups | Rosters | Draft results | Transactions |
|---:|---|---|---|---|---|---|---|---|
| 2021 | Public history URL verified | Authentication required | Authentication required | Authentication required | Authentication required | Authentication required | Authentication required | Authentication required |
| 2022 | Public page available | 12 team links | Available | Week 1 available | Week 16 available | Sample roster/points available | Available | Available |
| 2023 | Public page available | 12 team links | Available | Week 1 available | Week 16 available | Sample roster/points available | Available | Available |
| 2024 | Public page available | 12 team links | Available | Week 1 available | Week 16 available | Sample roster/points available | Available | Available |
| 2025 | Public page plus prior snapshot | 12 team links | Complete snapshot retained | Week 1 available | Complete seven-game bracket retained | Sample roster/points available | Available | Available |
| 2026 | Public page available | 12 team links | Available | Week 1 page available | Not yet available | Sample roster available | Available | Available |

On a successful authenticated run, the discovery job probes league metadata,
teams, standings, the first weekly scoreboard, the final-week scoreboard, one
representative roster, draft results, and transactions. A successful probe
means the endpoint returned the requested resource; it does not prove every
week or every row is complete.

Because the user-level Fantasy resource fails before any league-specific
request, this is not evidence of a bad current or historical league key. The
result is most consistent with Yahoo not recognizing Fantasy Sports access for
the credential set used by Actions, or with the authorizing Yahoo account not
being entitled to the requested private Fantasy resource. Yahoo's official
registration guidance requires the developer application to request private
user data and select Fantasy Sports Read or Read/Write access. A refresh token
used by Actions must come from an authorization-code grant completed after
those permissions are enabled, using the same developer application and the
Yahoo account that belongs to Road to Glory FFL. A separately issued Postman
access token does not change what GitHub Actions receives when it exchanges the
repository's existing refresh token.

Live workflow evidence:

- OAuth/2026 update test: <https://github.com/stringer56/fantasy-football-site/actions/runs/33465603477>
- Sanitized historical diagnostic: <https://github.com/stringer56/fantasy-football-site/actions/runs/33465879232>
- Ordered authorization retest: <https://github.com/stringer56/fantasy-football-site/actions/runs/33467871852>
- Documented NFL user-resource retest: <https://github.com/stringer56/fantasy-football-site/actions/runs/33709094263>
- Site validation: <https://github.com/stringer56/fantasy-football-site/actions/runs/33465873918>

The endpoint composition follows Yahoo's official Fantasy Sports API resources:

- <https://sports.yahoo.com/developer/docs/>
- <https://developer.yahoo.com/fantasysports/guide/>
- <https://developer.yahoo.com/oauth2/guide/>

## Historical franchise mapping

The discovery output compares Yahoo teams with the 14 canonical franchise
records. It resolves a mapping only when either:

1. the exact season-specific Yahoo team key is already verified; or
2. the Yahoo name has exactly one approved canonical name/alias match.

The existing 2025 key-based joins remain verified:

| Yahoo team key | Yahoo team name | Canonical franchise ID | Status |
|---|---|---|---|
| `461.l.103926.t.1` | Van Cortlant Rangers | `van-cortlant-rangers` | Verified |
| `461.l.103926.t.2` | Albany Kneelers | `albany-kneelers` | Verified |
| `461.l.103926.t.3` | Ayahuasca Rush | `ayahuasca-rush` | Verified |
| `461.l.103926.t.4` | Buffalo Bravados | `buffalo-bravado` | Verified |
| `461.l.103926.t.5` | Chris's Crazy Team | `crazy-wazs-team` | Verified |
| `461.l.103926.t.6` | Greendale Human Beings | `greendale-human-beings` | Verified |
| `461.l.103926.t.7` | Maine Moose | `maine-moose` | Verified |
| `461.l.103926.t.8` | North town Ninnyhammers | `north-town-ninnyhammers` | Verified |
| `461.l.103926.t.9` | The Baseball Furies | `baseball-furies` | Verified |
| `461.l.103926.t.10` | Turnbull AC’s | `turnbull-acs` | Verified |
| `461.l.103926.t.11` | Vegas Vandals | `vegas-vandals` | Verified |
| `461.l.103926.t.12` | New Jersey Giants | `new-jersey-giants` | Verified |

The public history pages expose complete 12-team link sets for 2022–2026. Name
and key matching resolves 10 of 12 teams in 2022, 11 of 12 in 2023, all 12 in
2024, all 12 in 2025, and 11 of 12 in 2026. The unresolved public identities are:

- 2022: Broncos Country Let’s Ride and Dilly Dilly;
- 2023: Broncos Country Let’s Ride; and
- 2026: Albany Redskins.

The 2026 name is not silently assigned to Albany Kneelers without explicit
continuity evidence. The 2021 league identity is verified, but team-key
extraction remains unavailable because Yahoo redirects detailed archive routes
to sign-in. Unmatched names
retain a null candidate franchise ID.

## Commissioner-confirmed 2025 playoff archive

The commissioner supplied the public Yahoo results for the complete 2025
championship playoff bracket. They are normalized in
`_data/generated/history/2025/playoffs.json` rather than folded into the
current-week matchup snapshot.

- Week 14: New Jersey Giants defeated Van Cortlant Rangers 125.96–113.44;
  Ayahuasca Rush defeated Maine Moose 75.26–51.92. Greendale and Albany had
  verified byes.
- Week 15: Greendale defeated New Jersey 159.06–134.52; Albany defeated
  Ayahuasca 159.92–86.84. Van Cortlant won the fifth-place game 136.26–110.20.
- Week 16: Greendale defeated Albany 107.12–106.72 for the championship;
  Ayahuasca defeated New Jersey 144.58–103.26 for third place.

The archive records seven scored games, two byes, and final places one through
six. All six participants resolve through their verified 2025 Yahoo team keys.
Placement games are explicitly classified so future playoff-win leaderboards
can decide whether to include them rather than silently mixing them with the
championship bracket.

## Discovery and publication flow

```text
manual workflow_dispatch
  -> existing refresh-token flow and repository secrets
  -> logged-in user's NFL games
  -> leagues for those game keys
  -> configured current alias as trusted anchor
  -> explicit renew/renewed traversal
  -> small capability probes
  -> canonical franchise comparison
  -> strict public allowlist and privacy validation
  -> _data/generated/history_manifest.json only
```

`.github/workflows/discover-yahoo-history.yml` is manual-only. It runs offline
tests first, performs discovery with the existing four secret/environment names,
validates the resulting public data, and stages only the sanitized manifest.
The workflow never writes raw Yahoo payloads. If authentication or validation
fails, the last good manifest remains unchanged.

GitHub registers a new manual workflow after the workflow file reaches the
default branch. Until this PR is merged, its authenticated job cannot be
dispatched from GitHub's Actions interface.

## Safe output boundary

The manifest may contain only public fantasy metadata needed for migration:

- season/game/league keys;
- league name, team count, dates, and finished state;
- renewal relationships;
- capability states; and
- fantasy team keys, names, canonical candidate IDs, and mapping status.

It rejects OAuth tokens, client values, authorization text, invitation data,
emails, account/GUID/manager identifiers, chat IDs, IP data, and edit/admin URLs.
Raw Yahoo responses are kept only in memory and are never written as artifacts.

## Recommended automated import strategy

The archive can now be backfilled without guessing league IDs:

1. merge this milestone and retain the exact six-season key map;
2. build a manual, cached backfill job against the verified official Yahoo
   archive pages while authenticated API access remains blocked;
3. throttle requests, retry HTTP 429/5xx responses with backoff, and resume from
   cached normalized checkpoints;
4. import league standings and every weekly matchup before attempting derived
   records;
5. validate team identity and week completeness before importing rosters,
   player scoring, draft results, or transactions;
6. keep raw Yahoo HTML and private account data out of the repository;
7. continue pursuing Fantasy Sports Read approval because the documented API is
   the preferred durable source;
8. after approval, rerun **Update Yahoo Data** and compare API-normalized output
   against the public-history backfill; and
9. keep historical retrieval manual rather than adding it to the six-hour
   current-season workflow.

The follow-on public archive importer is now implemented and documented in
[Yahoo Historical Backfill](YAHOO_HISTORY_BACKFILL.md). It recovered complete
weekly scoreboards and public draft boards for 2022–2025. The 2021 detailed
archive currently redirects automated requests to Yahoo sign-in, so the existing
verified manual 2021 sources remain authoritative until access changes.

Milestone 5 should use **both** sources. Yahoo should supply structured standings,
weekly results, and draft data only where authenticated discovery and coverage
checks succeed. The Google Site should continue to supply the verified 2021–2024
brackets, recaps, images, and any facts Yahoo cannot expose. Conflicts should be
documented and left unresolved rather than silently choosing one source.
