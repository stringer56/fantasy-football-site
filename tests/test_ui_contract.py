"""Presentation contracts without changing canonical league behavior."""
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class PublicationContractTests(unittest.TestCase):
    def test_navigation_has_all_community_destinations(self):
        text = (ROOT / '_layouts/default.html').read_text(encoding='utf-8')
        text += (ROOT / '_includes/community-nav.html').read_text(encoding='utf-8')
        for route in ('/power-rankings/', '/picks/', '/votes/', '/retired/'):
            self.assertIn(f'href="{{{{ \'{route}\' | relative_url }}}}"', text)

    def test_home_reuses_scoreboard_and_canonical_archive_components(self):
        text = (ROOT / 'index.md').read_text(encoding='utf-8')
        for component in ('live-matchup-card', 'champion-card', 'record-spotlights'):
            self.assertIn(f'include {component}.html', text)
        for section in ('weekly-matchups', 'home-franchises-heading', 'home-history-heading',
                        'home-records-heading', 'home-draft-heading', 'home-community-heading'):
            self.assertIn(section, text)
        self.assertIn('official_yahoo_public_page_fallback', text)
        self.assertIn('site.data.league.draft_datetime', text)

    def test_archive_cards_preserve_art_and_verified_final(self):
        text = (ROOT / '_includes/champion-card.html').read_text(encoding='utf-8')
        for field in ('season.year', 'final.champion_score', 'final.runner_up_score',
                      'champion.branding.identity_image'):
            self.assertIn(field, text)
        self.assertIn('loading="lazy"', text)
        self.assertIn('include champion-card.html', (ROOT / 'history.md').read_text(encoding='utf-8'))

    def test_no_visitor_facing_setup_or_future_data_hooks(self):
        paths = ('index.md', 'votes.md', '2026.md', '_layouts/draft.html',
                 '_includes/live-power-preview.html', '_includes/pickem-preview.html')
        for path in paths:
            text = (ROOT / path).read_text(encoding='utf-8')
            for prohibited in ('Ballot setup is pending', 'ballot setup is pending',
                               'Data hook reserved', 'Built for a static league site',
                               'Foundation Ready'):
                self.assertNotIn(prohibited, text, path)

    def test_responsive_review_includes_six_widths_and_all_routes(self):
        text = (ROOT / 'scripts/audit_browser.py').read_text(encoding='utf-8')
        self.assertIn('1440, 1024, 768, 430, 390, 360', text)
        self.assertIn('--all-routes', text)

    def test_stadium_is_decorative_while_identity_remains_accessible(self):
        text = (ROOT / '_layouts/franchise.html').read_text(encoding='utf-8')
        self.assertIn('class="franchise-hero__venue"', text)
        self.assertIn('alt="{{ branding.identity_alt | escape }}"', text)
        self.assertIn('Franchise Timeline', text)

    def test_profile_story_is_not_duplicated(self):
        text = (ROOT / '_layouts/franchise.html').read_text(encoding='utf-8')
        self.assertEqual(text.count('{{ profile.summary }}'), 1)
        self.assertEqual(text.count('include franchise-gallery.html'), 1)
        self.assertNotIn('width="680" height="630"', text)

    def test_badges_read_canonical_champions(self):
        for path in ('_layouts/franchise.html', '_includes/franchise-card.html'):
            text = (ROOT / path).read_text(encoding='utf-8')
            self.assertIn('site.data.champions.champions', text)
            self.assertNotIn('profile.championship_seasons', text)

    def test_identity_assets_and_colors_are_local(self):
        rows = yaml.safe_load((ROOT / '_data/franchises.yml').read_text(encoding='utf-8'))['franchises']
        self.assertEqual(sum(row['status'] == 'active' for row in rows), 12)
        for row in rows:
            branding = row['branding']
            if branding.get('primary_color'):
                self.assertRegex(branding['primary_color'], r'^#[0-9a-fA-F]{6}$')
            for key in ('identity_image', 'venue_image', 'honors_image'):
                if branding.get(key):
                    self.assertTrue(branding[key].startswith('/assets/img/'))
                    self.assertTrue((ROOT / branding[key].lstrip('/')).is_file())
                    self.assertTrue(branding.get(key.replace('_image', '_alt')))

    def test_css_modules_are_loaded_and_legacy_crest_removed(self):
        layout = (ROOT / '_layouts/default.html').read_text(encoding='utf-8')
        for sheet in ('publication', 'franchises'):
            self.assertIn(f'/assets/css/{sheet}.css', layout)
            self.assertTrue((ROOT / f'assets/css/{sheet}.css').is_file())
        self.assertNotIn('hero-crest', (ROOT / 'index.md').read_text(encoding='utf-8'))
        self.assertNotIn('.hero-crest', (ROOT / 'assets/css/style.css').read_text(encoding='utf-8'))

    def test_archive_identity_is_not_a_new_franchise(self):
        text = (ROOT / 'retired/quahog-stripes.md').read_text(encoding='utf-8')
        self.assertIn('Historical identity', text)
        self.assertIn('/teams/new-jersey-giants/', text)


if __name__ == '__main__':
    unittest.main()
