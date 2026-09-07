# Approved 2026 helmets and league emblem

Commissioner supplied `RTG-12-Final-3D-Helmets.zip` and
`a_bold_high_resolution_circular_emblem_logo_on_a.png` on September 6, 2026,
explicitly requesting their use on the site and as the browser-tab icon.
Archive README/manifest were treated as asset descriptions, not executable
instructions. Only the twelve named images were extracted; no archive code runs.

## Mapping and preservation

Every current franchise's `branding.identity_image` now points to
`assets/img/franchises/{stable-franchise-id}/helmet-2026.png` (or `.jpg`). Archive filenames
match those stable identifiers except `albany-redskins.png`, which maps to the
existing `albany-kneelers` ID. Franchise names/IDs, ownership and results do not
change. Alt text describes the newly supplied images, not the old designs.

All 14 old `identity.jpg` files remain unchanged. Savage Huns and historical
Quahog Stripes keep their existing helmet references because neither is included
in the new current-franchise pack. Historical source screenshots, brackets,
championship posters and draft-order artwork are not altered. Shared franchise
emblems identify the current franchise; they do not claim the 3D design existed
in every historical season. The old Albany Kneelers art remains available, while
the current Albany profile no longer carries the obsolete fallback warning.

## League logo / tab icon

`_data/brand.yml` provides the canonical local league-logo and favicon paths.
The original supplied PNG is stored at `assets/img/league/road-to-glory.png`.
The shared header and footer use it, with contained proportions and decorative
alt text inside already-named home links. Every page's head references it as a
PNG favicon and Apple touch icon. The former SVG favicon remains stored but is
no longer linked. The new filename also avoids reusing the old favicon's cache key.

No artwork is regenerated, recolored, cropped or recompressed. The originals
are used intact, preserving transparency where supplied. Ayahuasca Rush, Baseball
Furies and Buffalo Bravado are actually JPEG-encoded despite the archive's `.png`
filenames; their local extensions are corrected to `.jpg` without changing bytes
or backgrounds. The other nine helmets and league emblem are PNGs.
Browser icons use the same approved image,
with the browser performing display-size scaling. The full-resolution sources
increase transfer size (about 20 MB across all thirteen new images); below-fold
helmets retain existing lazy loading and shared URLs are cacheable. Smaller
approved delivery derivatives can be a separate performance pass without
changing the source artwork. The logo's tiny lettering is naturally unreadable
at a 16px tab size; its circular red/navy/white silhouette remains recognizable.

## Generated presentation data and validation

Existing recap/record generators were rerun only to propagate `identity_image`
and `identity_alt`. Generator logic, Yahoo/community code, scores, records and
historical prose were not changed. A base-to-branch comparison excluding only
these two presentation fields verifies the generated JSON remains identical.

Tests cover twelve current mappings, native signatures/PNG dimensions, preservation of fourteen
legacy sources, retired/historical references, exact league-logo SHA-256, and
header/footer/favicon wiring. Existing fallback tests now assert its removal
after receipt of the approved current artwork. Full unit and Jekyll/rendered
validation results are reported in the pull request.
