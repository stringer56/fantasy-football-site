# Historical Narrative System

## Purpose and boundary

Road to Glory's recap engine turns verified structured results into conservative
sports-yearbook prose. It is a deterministic Python template system, not an AI
writer. It makes no network request, uses no OpenAI or other LLM API, and runs
without a server or paid service.

The source of truth is limited to:

- `_data/seasons.yml` for final standings, W–L–T, PF, PA, and historical names;
- `_data/playoffs.yml` for participants, rounds, winners, nullable scores, and
  documented bracket ambiguity;
- `_data/champions.yml` for verified finalists and championship scores;
- `_data/franchises.yml` for stable IDs, public routes, and local identity art;
- `_data/generated/record_book.json` for provenance-aware archive records; and
- `_data/editorial/recaps.yml` for commissioner-approved prose overrides.

Rendered HTML, source screenshots, the old Google Site, current Yahoo output,
and unstructured franchise profile copy are not narrative inputs.

## Supported and unsupported claims

The generator may state a final standing, record, PF/PA total, complete-season
relative PF rank, playoff participation/result, advancing team, final score,
verified championship count within the 2021–2024 archive, and a record-book
fact whose provenance permits publication.

It does not infer trades, injuries, player performances, weekly events, waiver
moves, draft effects, rivalries, streaks, seeding, luck, strategy, emotion,
upsets, comebacks, dominance, bench decisions, game margins, or any other event
not encoded in the canonical sources. Missing playoff scores remain missing.
Final standings rank is described as final placement and is never relabelled as
a playoff seed.

Relative claims are emitted only when every team-season row has the required
value. If one PF value is unavailable, for example, the engine omits the
highest/lowest PF cards and all relative PF prose for that season.

Record references use `_data/generated/record_book.json`. Partial categories are
always phrased as verified within the 2021–2024 archive and never as all-time
league history.

## Generated output

Run:

```powershell
python scripts/build_records.py
python scripts/build_recaps.py
python scripts/validate_recaps.py
```

The generator writes `_data/generated/recaps.json` with five public arrays:

- `seasons`
- `team_recaps`
- `playoff_recaps`
- `championship_recaps`
- `by_the_numbers`

Every narrative entry carries its season, source files, deterministic
`generated_at`, coverage status, structured `facts_used`, warnings, content
source, generated fallback text, and public provenance label. The source date is
derived from canonical verification metadata rather than the machine clock, so
identical inputs produce byte-equivalent narrative content.

Unresolved historical identities keep `franchise_id: null`,
`mapping_status: unresolved`, a null profile path, their exact historical team
name, and an explicit warning. Their verified season results remain readable
without creating a false franchise join.

## Editorial overrides

Commissioner prose belongs in `_data/editorial/recaps.yml`, never in Python.
The file supports `season_recaps`, `team_recaps`, `playoff_recaps`, and
`championship_recaps` arrays. An override must use `status: approved`, identify
the canonical season and item, and contain `text`.

Shape examples:

```yaml
season_recaps:
  - season: 2024
    status: approved
    text: >-
      Commissioner-approved prose grounded in the verified 2024 result.

team_recaps:
  - season: 2024
    franchise_id: turnbull-acs
    status: approved
    text: >-
      Commissioner-approved team recap.

playoff_recaps:
  - season: 2024
    game_id: 2024-final
    status: approved
    text: >-
      Commissioner-approved championship-game copy.
```

For an unresolved team override, use `franchise_id: null` plus the exact
`historical_team_name`. Regeneration preserves approved text as the public
`text` and retains the reproducible fallback in `generated_text`. The selection
order is approved editorial override, deterministic generated copy, then an
unavailable state when canonical facts are insufficient.

Editorial prose must remain within the same factual and privacy boundary. It is
validated for unsafe all-time language, unsupported stat categories, private
fields, and conflicts with structured result facts where those facts are quoted.

## Validation and regeneration

`scripts/validate_recaps.py` regenerates the complete payload in memory and
requires an exact match. It also verifies season/franchise/game references,
unresolved mappings, championship identities and scores, team records and
PF/PA, missing-score behavior, supported number cards, provenance paths,
privacy, forbidden claim categories, and absence of unsupported all-time text.

The CI workflow runs `build_recaps.py --check`, the recap validator, the full
unit suite, Jekyll, rendered-route validation, and internal-link checks. Changes
to canonical history or approved overrides therefore require an intentional
recap regeneration and review.

## Public presentation

The season layout prefers approved editorial text when present, otherwise the
generated paragraphs. It renders the season recap, By the Numbers cards,
standings, bracket, result cards, playoff prose, championship story, and compact
team recap cards from canonical data. Public pages show only the subtle label
“Generated from verified league results”; technical facts and warnings remain
available in the generated JSON and validation documentation.

## Privacy

Narratives describe fantasy franchises and public results. The generator does
not read owner contact data and cannot emit emails, addresses, medical details,
Yahoo account identifiers, invitations, credentials, or private communications.
