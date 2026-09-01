# Yahoo Historical League Discovery

## Status

Milestone 4.5 adds a manual, credential-safe discovery path for every Road to
Glory FFL league available to the Yahoo account authorized by the repository.
It does not change OAuth, publish raw Yahoo responses, or perform a full
historical import.

The latest authenticated attempt on 2026-08-31 did not reach the Fantasy API:
Yahoo's OAuth token endpoint returned HTTP 400 while refreshing the stored
credential. The failure occurred before the script could enumerate the user's
games or probe historical resources. No credential value, authorization header,
token response, or raw API body was printed or saved.

The committed manifest therefore reports a **partial** baseline using only
previously sanitized, source-controlled Yahoo evidence. A successful manual
workflow run will replace it with a live sanitized discovery report.

## Verified seasons and safe league keys

| Season | Game key | Yahoo league key | League ID | Verification evidence |
|---:|---:|---|---:|---|
| 2024 | `449` | `449.l.761310` | `761310` | The preserved authenticated 2025 metadata names `449_761310` as the prior league in its `renew` field. |
| 2025 | `461` | `461.l.103926` | `103926` | The committed sanitized league/team/standings snapshot is from Road To Glory FFL. |
| 2026 | Unresolved | Unresolved | `26455` in configured alias only | `nfl.l.26455` has not resolved while authentication is blocked, so it is not recorded as a global season key. |

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
`not_probed` means the current credential failure prevented a live check; it
does not mean Yahoo lacks the resource.

| Season | Metadata | Teams | Standings | Weekly matchups | Final playoff matchups | Rosters | Draft results | Transactions |
|---:|---|---|---|---|---|---|---|---|
| 2024 | Not probed | Not probed | Not probed | Not probed | Not probed | Not probed | Not probed | Not probed |
| 2025 | Available snapshot | Available snapshot | Available snapshot | Complete playoff Weeks 14–16 supplied; regular-season weeks not recovered | Complete seven-game bracket plus two byes | Single-week snapshot only | Not probed | Not probed |
| 2026 | Authentication required | Authentication required | Authentication required | Authentication required | Authentication required | Authentication required | Authentication required | Authentication required |

On a successful authenticated run, the discovery job probes league metadata,
teams, standings, the first weekly scoreboard, the final-week scoreboard, one
representative roster, draft results, and transactions. A successful probe
means the endpoint returned the requested resource; it does not prove every
week or every row is complete.

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

After an authorized administrator restores the Yahoo refresh credential:

1. run **Update Yahoo Data** to verify the current 2026 alias and team mappings;
2. merge this milestone, then manually run **Discover Yahoo History**;
3. review the sanitized season/key chain and unresolved same-name candidates;
4. backfill standings and weekly scoreboards one verified season at a time;
5. validate team identity and week completeness before importing rosters,
   draft results, or transactions; and
6. keep historical backfill manual rather than adding it to the six-hour
   current-season workflow.

Milestone 5 should use **both** sources. Yahoo should supply structured standings,
weekly results, and draft data only where authenticated discovery and coverage
checks succeed. The Google Site should continue to supply the verified 2021–2024
brackets, recaps, images, and any facts Yahoo cannot expose. Conflicts should be
documented and left unresolved rather than silently choosing one source.
