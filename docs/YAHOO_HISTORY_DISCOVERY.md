# Yahoo Historical League Discovery

## Status

Milestone 4.5 adds a manual, credential-safe discovery path for every Road to
Glory FFL league available to the Yahoo account authorized by the repository.
It does not change OAuth, publish raw Yahoo responses, or perform a full
historical import.

The ordered live retest on 2026-09-02 confirms that Yahoo's refresh-token
exchange succeeds. The first Fantasy API request—Yahoo's documented
logged-in-user NFL teams resource—still returns HTTP 403, with no safe Yahoo
error code in the response. Per the required stop rule, the job did not request the NFL game
resource, the configured 2026 alias, either known historical key, or user
league enumeration after that failure.

The committed manifest therefore reports **authorization blocked**. Its 2024
and 2025 identities remain supported by earlier sanitized repository evidence;
the retest did not recover new Yahoo data. No credential value, authorization
header, request URL, token response, error body, or raw API response was printed
or saved.

## Verified seasons and safe league keys

| Season | Game key | Yahoo league key | League ID | Verification evidence |
|---:|---:|---|---:|---|
| 2024 | `449` | `449.l.761310` | `761310` | The preserved authenticated 2025 metadata names `449_761310` as the prior league in its `renew` field. |
| 2025 | `461` | `461.l.103926` | `103926` | The committed sanitized league/team/standings snapshot is from Road To Glory FFL. |
| 2026 | Unresolved | Unresolved | `26455` in configured alias only | Not tested in the ordered retest because the authenticated user Fantasy resource failed first; the alias is not recorded as a global season key. |

The earliest verified Yahoo season is currently **2024** and the latest is
**2025**. This is the earliest verified season available from repository
evidence, not a claim that the authenticated account exposes nothing earlier.
A live user/game enumeration is required to answer that conclusively.

## Renewal chain

The verified portion is:

```text
449.l.761310 (2024) -> 461.l.103926 (2025)
```

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
| 2024 | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop |
| 2025 | Not tested; prior snapshot retained | Not tested; prior snapshot retained | Not tested; final snapshot retained | Not tested; commissioner-supplied playoff Weeks 14–16 retained | Not tested; seven-game bracket plus two byes retained | Not tested; prior Week 16 snapshot retained | Not tested — authorization stop | Not tested — authorization stop |
| 2026 | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop | Not tested — authorization stop |

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

No 2024 or 2026 team list was recovered in this milestone. Those season joins,
the two retired-franchise Yahoo histories, and any older Yahoo identities remain
unresolved. The script leaves unmatched or ambiguous historical names with a
null candidate franchise ID instead of using owner/name similarity as a guess.

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

Before another live retest:

1. confirm the Yahoo developer application has private Fantasy Sports Read or
   Read/Write permission;
2. complete a fresh authorization-code consent from that same application while
   signed into the Yahoo account that belongs to Road to Glory FFL;
3. update `YAHOO_REFRESH_TOKEN` in GitHub Secrets with the refresh token from
   that post-permission authorization-code exchange; do not paste it into Codex,
   logs, commits, or artifacts;
4. confirm `YAHOO_CLIENT_ID` and `YAHOO_CLIENT_SECRET` are from the same app and
   keep `LEAGUE_KEY` as the existing public alias;
5. run **Update Yahoo Data** to repeat the ordered user/game/league probes;
6. after the user-level probe succeeds, verify the current 2026 alias and team
   mappings;
7. merge this milestone, then manually run **Discover Yahoo History**;
8. review the sanitized season/key chain and unresolved same-name candidates;
9. backfill standings and weekly scoreboards one verified season at a time;
10. validate team identity and week completeness before importing rosters,
   draft results, or transactions; and
11. keep historical backfill manual rather than adding it to the six-hour
   current-season workflow.

Milestone 5 should use **both** sources. Yahoo should supply structured standings,
weekly results, and draft data only where authenticated discovery and coverage
checks succeed. The Google Site should continue to supply the verified 2021–2024
brackets, recaps, images, and any facts Yahoo cannot expose. Conflicts should be
documented and left unresolved rather than silently choosing one source.
