# Records Data Coverage

Milestone 7 audits every available structured input before publishing the first
Road to Glory record book. Coverage is limited to the verified 2021–2024 archive;
the word “all-time” is not used for any generated category.

## Coverage definitions

- **COMPLETE** — every required value is verified for the stated 2021–2024 period.
- **PARTIAL** — useful values can be calculated, but unresolved identity or source
  coverage prevents a complete franchise-history claim.
- **UNAVAILABLE** — the required inputs do not exist; no values may be generated.

## Coverage matrix

| Category | Seasons | Sources | Coverage | Unresolved impact | Public calculation |
|---|---|---|---|---|---|
| Franchise wins, losses, ties, win percentage | 2021–2024 | `_data/seasons.yml`, `_data/franchises.yml` | PARTIAL | Five standings rows / four names cannot join to franchises | Yes, resolved rows only and explicitly labelled partial |
| Franchise PF and PA | 2021–2024 | `_data/seasons.yml`, `_data/franchises.yml` | PARTIAL | Same unresolved rows; 2024 Turnbull PF/PA labels conflict between two source views | Yes, using the final-standings table with the conflict disclosed |
| Single-season wins, losses, ties, win percentage | 2021–2024 | `_data/seasons.yml` | COMPLETE | Historical names can remain unlinked without changing season values | Yes |
| Single-season PF and PA | 2021–2024 | `_data/seasons.yml`, `docs/HISTORY_MIGRATION.md` | PARTIAL | Identity mapping does not affect values; 2024 Turnbull label conflict affects source confidence | Yes, labelled partial and sourced to final standings |
| Championships | 2021–2024 | `_data/champions.yml` | COMPLETE | None; all champions resolve | Yes |
| Championship appearances | 2021–2024 | `_data/champions.yml` | COMPLETE | None; all finalists resolve | Yes |
| Playoff appearances, wins, losses | 2021–2024 | `_data/playoffs.yml`, `_data/franchises.yml` | PARTIAL | The Swagger Daggers’ 2021 appearance/loss cannot join to a franchise | Yes, resolved teams only and explicitly labelled partial |
| Playoff appearance streaks | 2021–2024 | `_data/playoffs.yml`, `_data/franchises.yml` | PARTIAL | One unresolved 2021 participant is excluded; the window is only four seasons | Yes, as “Verified 2021–2024,” never all-time |
| Playoff scoring records | 2021–2024 | `_data/playoffs.yml` | UNAVAILABLE | Twelve non-final games have null scores | No |
| Highest/lowest weekly score | None | Historical matchup data absent | UNAVAILABLE | Not applicable | No |
| Largest/smallest victory margin | None | Historical matchup data absent | UNAVAILABLE | Not applicable | No |
| Regular-season win/loss streaks | None | Historical matchup sequence absent | UNAVAILABLE | Not applicable | No |
| Playoff droughts | 2021–2024 | `_data/playoffs.yml`, `_data/franchises.yml` | UNAVAILABLE | Founding seasons and identity continuity are incomplete | No |
| Top 10 bench scoring misses | None | Weekly roster/bench scoring absent | UNAVAILABLE | Not applicable | No; schema only |
| Draft value, ADP, steals, busts | 2021–2024 images only | `_data/drafts.yml` | UNAVAILABLE | Pick data is image-only and unverified | No |

## Input audit

### Canonical history

- Four verified season standings contain 46 rows and complete W–L–T, PF, and PA
  values for their historical team-season entries.
- Forty-one standings rows resolve to stable franchise IDs. Five rows retain
  four unresolved historical names and are never silently assigned.
- All four champions and all eight finalist slots resolve to canonical franchises.
- Sixteen playoff games have verified participants and winners. Only the four
  championships have scores; twelve non-final scores remain null.
- Draft results contain no authoritative structured picks, so draft-performance
  records are outside this milestone.

### Generated Yahoo data

The committed Yahoo snapshot is a sanitized, completed 2025 standings snapshot.
It does not provide the complete weekly matchup, transaction, or bench history
needed for game, margin, streak, or bench records, and it sits outside the
verified 2021–2024 historical archive. It is therefore not blended into this
record build. The records generator is isolated from OAuth and can accept future
verified season inputs without changing authentication.

## Conflict and exclusion policy

1. The 2024 final-standings table lists Turnbull AC’s PF as `1610.10` and PA as
   `1425.58`; the champions page reverses those labels. Generated PF/PA categories
   use the canonical standings-table values and remain `partial` until confirmed.
2. The 2023 bracket lane ambiguity does not change its verified advancing teams,
   so win/loss counts use the structured winners while retaining partial coverage.
3. The Swagger Daggers’ verified 2021 playoff loss and appearance remain in the
   source history but are excluded from franchise leaderboards because the stable
   identity is unresolved.
4. Missing values are never converted to zero. A missing metric is excluded and
   downgrades coverage rather than creating a false record.
5. Unavailable categories carry an empty entry array and a reader-facing status
   message. They never render an empty “Top 10.”

## Future completeness path

To expand the record book, import commissioner-approved weekly matchup exports,
weekly active/bench roster scoring, franchise tenure dates, and mappings for the
four unresolved historical identities. Each new source should be normalized to
stable franchise IDs, retain year/week provenance, and pass the records validator
before any coverage label is upgraded.
