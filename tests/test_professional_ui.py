"""Contracts for the professional identity presentation; no data generation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProfessionalIdentityTests(unittest.TestCase):
    def test_directory_excerpt_ends_on_word_boundaries(self):
        text = (ROOT / '_includes/franchise-card.html').read_text(encoding='utf-8')
        self.assertIn('truncatewords: 24', text)
        self.assertNotIn('truncate: 165', text)

    def test_sortable_dark_table_header_keeps_interaction_contrast(self):
        text = (ROOT / 'assets/css/publication.css').read_text(encoding='utf-8')
        self.assertIn('.record-table th button:hover, .record-table th button:focus-visible { color: #fff;', text)

    def test_mobile_profile_spacing_is_explicit(self):
        text = (ROOT / 'assets/css/franchises.css').read_text(encoding='utf-8')
        self.assertIn('.franchise-hero__grid { padding-block: 1.5rem; gap: 1.25rem;', text)
        self.assertIn('.franchise-identity { height: 17rem; width: 100%;', text)

    def test_enlarged_text_can_reflow_in_editorial_components(self):
        text = (ROOT / 'assets/css/publication.css').read_text(encoding='utf-8')
        self.assertIn('.record-subhead > div { min-width: 0; max-width: 100%;', text)
        self.assertIn('.news-strip__title { white-space: normal;', text)
        self.assertIn('.season-archive-card__body > div { flex-wrap: wrap;', text)

    def test_portrait_and_venue_captions_label_the_canonical_field(self):
        card = (ROOT / '_includes/franchise-card.html').read_text(encoding='utf-8')
        gallery = (ROOT / '_includes/franchise-gallery.html').read_text(encoding='utf-8')
        archive = (ROOT / 'retired/quahog-stripes.md').read_text(encoding='utf-8')
        self.assertIn('Home Field: {{ card.profile.home_field | escape }}', card)
        self.assertIn('Home Field: {{ profile.home_field | escape }}', gallery)
        self.assertIn('Home Field: Quahog Dome', archive)

    def test_directory_groups_venue_and_identity(self):
        text = (ROOT / '_includes/franchise-card.html').read_text(encoding='utf-8')
        self.assertIn('franchise-card__visual', text)
        self.assertIn('card.branding.primary_color', text)
        self.assertIn('card.branding.identity_alt | escape', text)

    def test_profile_ledger_uses_existing_metrics_with_coverage(self):
        text = (ROOT / '_layouts/franchise.html').read_text(encoding='utf-8')
        ledger = text.split('<section class="franchise-ledger"', 1)[1].split('</section>', 1)[0]
        for field in ('wins', 'losses', 'ties', 'win_percentage', 'championships'):
            self.assertIn('historical_metrics.season_history.' + field, ledger)
        self.assertIn('2021–2025', ledger)
        self.assertIn('historical_metrics.season_history.season_count > 0', text)
        self.assertNotIn('default: 0', ledger)

    def test_champion_spotlight_resolves_canonical_identity(self):
        text = (ROOT / 'index.md').read_text(encoding='utf-8')
        self.assertIn('latest_champion.champion_franchise_id', text)
        self.assertIn('defending_franchise.branding.identity_image', text)
        self.assertIn('class="defending-champion"', text)

    def test_helmet_and_photo_have_separate_sizing(self):
        text = (ROOT / 'assets/css/publication.css').read_text(encoding='utf-8')
        self.assertIn('.home-trophy > img', text)
        self.assertIn('.home-trophy .defending-champion img', text)
        self.assertIn('object-fit: contain', text)

    def test_compact_mobile_ledger_and_record_grid(self):
        text = (ROOT / 'assets/css/franchises.css').read_text(encoding='utf-8')
        self.assertIn('.franchise-ledger dl { gap: .5rem;', text)
        self.assertIn('.franchise-record-grid { grid-template-columns: repeat(2, minmax(0, 1fr));', text)

    def test_mobile_ranking_source_has_full_width(self):
        text = (ROOT / 'assets/css/publication.css').read_text(encoding='utf-8')
        self.assertIn('.ranking-method dl div:last-child { grid-column: 1 / -1;', text)


if __name__ == '__main__':
    unittest.main()
