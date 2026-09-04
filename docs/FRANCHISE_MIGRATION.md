# Franchise Migration Record

Milestone 4 migrates the public team directory from the original Road to Glory
Google Site into stable, data-driven Jekyll profiles. The source was reviewed in
the browser on 2026-08-31. This document records what was imported, normalized,
deferred, or intentionally omitted.

## Migration status

- Active franchises: **12 of 12 complete**
- Current public owners/coaches: **12 of 12 represented**
- Retired franchises: **2 of 2 complete**
- Local source assets: **31 imported** (14 identities, 14 venues, 3 honors)
- Individual routes: **14 collection-backed profiles**
- 2025 Yahoo mappings: **12 verified**
- 2026 Yahoo mappings: **1 commissioner-confirmed; 11 pending verification**

The canonical `franchise_id` is the durable join key. Slugs, display names,
aliases, owner names, and Yahoo team keys may change without changing that ID.

## Active franchise inventory

| Canonical ID | Public profile name | Coach/owner | Local route | 2025 Yahoo join |
|---|---|---|---|---|
| `albany-kneelers` | Albany Redskins | James “Beast” | `/teams/albany-kneelers/` | `461.l.103926.t.2` |
| `ayahuasca-rush` | Ayahuasca Rush | McCall | `/teams/ayahuasca-rush/` | `461.l.103926.t.3` |
| `baseball-furies` | The Baseball Furies | Forrest F. | `/teams/baseball-furies/` | `461.l.103926.t.9` |
| `buffalo-bravado` | Buffalo Bravado | Nate “Dogg” | `/teams/buffalo-bravado/` | `461.l.103926.t.4` |
| `crazy-wazs-team` | Crazy Waz's Team | Waz | `/teams/crazy-wazs-team/` | `461.l.103926.t.5` |
| `greendale-human-beings` | Greendale Human Beings | Ryan D. | `/teams/greendale-human-beings/` | `461.l.103926.t.6` |
| `maine-moose` | Maine Moose | Finn D. | `/teams/maine-moose/` | `461.l.103926.t.7` |
| `new-jersey-giants` | New Jersey Giants | Jack D. | `/teams/new-jersey-giants/` | `461.l.103926.t.12` |
| `north-town-ninnyhammers` | North Town Ninnyhammers | TJ | `/teams/north-town-ninnyhammers/` | `461.l.103926.t.8` |
| `turnbull-acs` | Turnbull AC's | Terry | `/teams/turnbull-acs/` | `461.l.103926.t.10` |
| `van-cortlant-rangers` | Van Cortlant Rangers | Joe | `/teams/van-cortlant-rangers/` | `461.l.103926.t.1` |
| `vegas-vandals` | Vegas Vandals | Coles | `/teams/vegas-vandals/` | `461.l.103926.t.11` |

Each Google Site team image linked to a team ID in the same 2025 Yahoo league
represented by the committed generated snapshot. Those ID links, team names,
and generated keys were used together to verify the 2025 joins. A display-name
difference was retained as an alias rather than treated as a new franchise.
Examples include `Albany Kneelers`, `Buffalo Bravados`, `Dilly Dilly`, `Broncos
Country Let’s Ride`, `North town Ninnyhammers`, `Turnbull AC’s`, and `Chris's
Crazy Team`. The commissioner confirmed on 2026-09-03 that Albany Kneelers is
now Albany Redskins, Dilly Dilly is Buffalo Bravado, Broncos Country Let’s Ride
is Vegas Vandals, and Quahog Stripes is the former New Jersey Giants identity.

Yahoo manager display names were not automatically converted into owner aliases.
Only obvious public-name variants supported by the profile (for example, `Jack
D.` / `Jack Donoghue`) were joined; ambiguous Yahoo handles remain unassigned.

## Retired franchise inventory

| Canonical ID | Public profile name | Coach/owner | Local route | Yahoo status |
|---|---|---|---|---|
| `savage-huns` | The Savage Huns | Teal F. | `/retired/the-savage-huns/` | Historical mapping unresolved |

`_data/retired_franchises.yml` contains the one retired canonical ID. Quahog
Stripes is preserved at `/retired/quahog-stripes/` as the 2021–2022 historical
identity of stable franchise ID `new-jersey-giants`; its original images and
story remain in the public archive without creating a second franchise total.

## Source pages and asset mapping

The active source path is
`https://sites.google.com/view/road-to-glory-ffl/teams/{source-slug}`. Historical
source paths use `/retired-teams/{source-slug}`. Exact source URLs and
the review date are stored on each franchise record.

Every source profile supplied an identity/helmet image and a venue image. Albany,
Ayahuasca, and Greendale also supplied championship artwork. Files were exported
from the rendered public page into:

```text
assets/img/franchises/{slug}/identity.{jpg|png}
assets/img/franchises/{slug}/venue.{jpg|png}
assets/img/franchises/{slug}/honors.{jpg|png}  # when present
```

No remote Google image URL is used at render time. Every imported asset is
referenced by canonical data, and there were no pre-existing franchise assets
to orphan. Alt text describes the team identity or venue rather than repeating
the filename.

## Content and editorial decisions

The migration preserves the playful team voices, coaches, locations, home
fields, capacities, rivals, slogans, fight-song titles, and source-listed titles.
Light editing corrects obvious spelling, punctuation, and readability problems
without inventing facts.

Three source fragments were not republished verbatim:

- The Quahog page's medical diagnosis/reference was omitted as unnecessary
  personal health information.
- The Savage Huns page's personal jab about why the team left was omitted; the
  football identity and competitive story remain intact.
- Albany's pronoun/protest punchlines were condensed into the broader public
  team-character description without retaining identity-directed phrasing.

The Las Vegas stadium street address was normalized to the public city/state
location because the street number adds no franchise value. Fight-song audio was
not imported: the source page did not expose approved local audio files in the
reviewed asset inventory, so only the public song titles are retained.

## Data and rendering architecture

- `_data/franchises.yml` owns stable identities, aliases, owner references,
  season-scoped Yahoo mappings, branding, profile copy, rival IDs, and provenance.
- `_data/owners.yml` owns approved public display names and aliases.
- `_data/retired_franchises.yml` is a canonical retired-ID index only.
- `_franchises/*.md` supplies one small route document per identity.
- `_layouts/franchise.html` renders every active and retired profile.
- `teams.md` and `retired.md` render filtered directories from the same data.

The profile collection defaults to `/teams/:slug/`; retired route documents
override the permalink to `/retired/:slug/`. Internal rival links use
`franchise_id`, never a mutable display name.

## Yahoo mapping policy

The live site points to public 2026 league alias `nfl.l.26455`. The verified
2026 discovery record and official current league page now resolve all twelve
team keys (`470.l.26455.t.1` through `.t.12`) to the existing stable franchise
IDs. Exact 2026 display names remain season-scoped; Albany's current `Albany
Redskins` name, for example, does not change stable ID `albany-kneelers` or its
canonical route. No 2025 key is presented as a 2026 key. Credentials, tokens,
manager account identifiers, and invitation links are not stored in franchise
data or documentation.

## Remaining migration gaps

The source pages do not reliably establish the following, so they remain blank
or deferred instead of being guessed:

- franchise founding seasons and retired seasons;
- full owner tenure and succession history;
- historical Yahoo keys for The Savage Huns;
- whether all public nicknames remain preferred in 2026;
- source-approved fight-song audio files;
- full championship verification against season recaps and bracket records;
- exact founding dates before the first verified 2021 participation season.

Verified 2021–2025 season records, weekly performance, opponent series, playoff
history, championship history, and season/week milestone events now render from
`_data/generated/records/franchise_career.json`. Historical name changes remain
season-scoped and do not create duplicate career identities.

These gaps should be filled from commissioner records, Yahoo historical exports,
and the later season-history migration—not inferred from current profile prose.

## Validation

`scripts/validate_franchise_data.py` enforces:

- 12 active and 1 retired canonical record, plus the archived Quahog identity;
- 12 distinct current owners;
- unique IDs, slugs, and cross-franchise aliases;
- valid owner and rival references;
- existing local images and required alt text;
- exactly one collection route per franchise;
- exact retired-ID indexing;
- season-aligned, unique Yahoo mappings that match the committed 2025 snapshot;
- 2026 mappings against verified discovery evidence and obvious private-content patterns.

`scripts/validate_built_site.py` also requires the canonical profile routes,
exactly 12 active cards, one retired-franchise card, one historical-identity
card, core profile sections, working internal links, local assets, and shell
landmarks.

## Recommended follow-up

Finalize the Week 1 Power Ranking and Pick’em ballots after commissioner review,
then let the verified weekly Yahoo snapshots accumulate without changing stable
franchise joins.
