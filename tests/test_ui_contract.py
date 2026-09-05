"""Presentation contracts without changing canonical league behavior."""
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class PublicationContractTests(unittest.TestCase):
    def test_navigation_has_all_community_destinations(self):
        text = (ROOT / '_layouts/default.html').read_text(encoding='utf-8')
        for route in ('/power-rankings/', '/picks/', '/votes/', '/retired/'):
            self.assertIn(f'href="{{{{ \'{route}\' | relative_url }}}}"', text)

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
