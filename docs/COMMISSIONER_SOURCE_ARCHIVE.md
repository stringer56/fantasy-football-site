# Commissioner Source Archive Audit

Audit date: **2026-09-03**

The commissioner-provided local archive is a source library, not a directory to
publish wholesale. This audit records what was reviewed, what was imported, and
what remains intentionally private or editorially unapproved.

## Inventory

- **282 files / 62.1 MB**
- **258 images** (`.jpg`, `.png`, `.gif`, and `.webp`)
- **5 Word documents**
- **10 text files**
- **4 Python files**, plus environment/API support files
- Team source folders for all current managers, retired-team material, helmet
  working files, four draft-recap folders, and Brew Crew Cup photography

The five Word documents were rendered and visually reviewed page by page. The
2023 and 2024 playoff documents match the already migrated bracket paths and do
not publish the missing semifinal or quarterfinal scores.

## Imported in this pass

| Source | Public destination | Decision |
|---|---|---|
| `draft order 2025.png` | `assets/img/drafts/2025/draft-order.png` | Published with the new 2025 draft route |
| `league trophy.jpg` | `assets/img/cup/brew-crew-cup.jpg` | Published as the Cup's primary photograph |
| `brew crew history image.jpg` | `assets/img/cup/brew-crew-history.jpg` | Published as league-history artwork |
| `Draft order 2025.txt` | `_data/drafts.yml` | Date, time, and all 12 slots normalized |
| `2021 Draft Order.txt` | Franchise/history mappings | Used to close the final two 2021 identity gaps |
| `trophy text.txt` | `cup.md` | Edited into public-facing Cup history copy |

The 2022–2024 draft-order text files agree with the existing canonical order.
`2023 Draft Order real.txt` is the valid 2023 order. The similarly named
`2023 Draft Order.txt` repeats the 2022 order and is treated as an obsolete
working copy.

## Already represented

The archive contains the source material behind the site's existing:

- 2021–2024 final standings, brackets, championship portraits, and title-game
  screenshots;
- twelve 2021–2024 draft-result captures;
- active and historical franchise helmets, identity art, and venue imagery;
- Road to Glory marks and championship artwork.

Many repository copies have been cropped, renamed, or re-encoded for consistent
web presentation, so byte-for-byte hashes are not used as the sole identity
test. Existing curated assets remain in place unless a source file clearly adds
new information or higher-value presentation.

## Excluded from publication

- `.env`, environment examples, Yahoo/API scripts, cached packages, and archives;
- OAuth identifiers, secrets, tokens, or any developer-machine configuration;
- a champion template containing private mailing information;
- personal draft-strategy notes in the 2022 cheatsheet;
- mugshots, personal portraits, and other identifiable-person imagery without a
  specific editorial decision to publish it;
- generic web downloads, intermediate helmet-editing files, duplicate exports,
  and low-resolution navigation graphics.

These files remain outside the repository. Their presence in the commissioner
archive does not make them public-site content.

## Data decisions unlocked by the archive

1. The 2025 draft is now tied to the correct 12-team Road to Glory Yahoo league,
   with an August 28, 2025, 8:00 p.m. EDT start and 180 verified selections.
2. The 2021 order aligns `Matthew's Optimal Team` with Vegas Vandals and `The
   Swagger Daggers` with Buffalo Bravado. All 2021 standings and draft identities
   now resolve to stable franchise records.
3. The Cup's travel-and-engraving tradition is now represented with the actual
   trophy photograph and commissioner copy rather than a placeholder-only page.

## Deferred editorial review

Team folders contain additional venue photographs, alternate helmet concepts,
personal photos, and jokes. They should be reviewed manager by manager before
replacing the current curated profile imagery. That work should preserve the
original files in the commissioner archive and import only approved final
selections with descriptive alternative text.
