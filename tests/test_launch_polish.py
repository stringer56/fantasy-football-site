"""Static launch contracts without adding a runtime or changing canonical data."""
from pathlib import Path
import unittest

from scripts.validate_built_site import LinkParser, metadata_errors

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://stringer56.github.io'
URL = ORIGIN + '/fantasy-football-site/picks/'


class LaunchPolishTests(unittest.TestCase):
    def parser(self, extra=''):
        parser = LinkParser()
        parser.feed(f'<link rel="canonical" href="{URL}"><link rel="icon" href="/favicon.svg">'
                    f'<meta property="og:url" content="{URL}"><meta property="og:type" content="website">'
                    f'<meta property="og:image" content="{ORIGIN}/fantasy-football-site/assets/img/cup/brew-crew-cup.jpg">'
                    + ''.join(f'<meta property="{key}" content="League archive">' for key in
                              ('description', 'og:title', 'og:description', 'og:site_name', 'og:image:alt')) + extra)
        return parser

    def test_valid_public_metadata(self):
        self.assertEqual(metadata_errors(self.parser(), URL, ORIGIN), [])

    def test_wrong_canonical_and_remote_art_are_rejected(self):
        parser = self.parser()
        parser.links[0]['href'] = 'http://localhost/picks/'
        parser.meta['og:image'] = 'https://unapproved.example/art.png'
        errors = metadata_errors(parser, URL, ORIGIN)
        self.assertEqual(len(errors), 2)

    def test_missing_description_and_unsafe_new_tab_are_rejected(self):
        parser = self.parser('<a href="https://example.com" target="_blank">Source</a>')
        parser.meta.pop('description')
        self.assertEqual(len(metadata_errors(parser, URL, ORIGIN)), 2)

    def test_compatibility_routes_point_to_primary_canonical(self):
        for filename, destination in [('pickem.md', '/picks/'), ('picks-legacy.md', '/picks/'),
                                      ('power-rankings-legacy.md', '/power-rankings/'), ('seasons.md', '/history/')]:
            self.assertIn(f'canonical_path: {destination}', (ROOT / filename).read_text(encoding='utf-8'))

    def test_countdown_is_loaded_only_on_its_homepage(self):
        layout = (ROOT / '_layouts/default.html').read_text(encoding='utf-8')
        self.assertIn("{% if page.url == '/' %}<script src=\"{{ '/assets/js/countdown.js'", layout)
        self.assertIn('include social-meta.html', layout)

    def test_approved_current_helmet_replaces_obsolete_fallback_note(self):
        text = (ROOT / '_layouts/franchise.html').read_text(encoding='utf-8')
        self.assertNotIn('Featuring the archived Albany Kneelers helmet.', text)
        self.assertNotIn('aria-describedby="archived-helmet-note"', text)
        self.assertIn('branding.identity_image', text)

    def test_obsolete_analysis_css_is_removed(self):
        self.assertNotIn('draft-analysis-hooks', (ROOT / 'assets/css/style.css').read_text(encoding='utf-8'))

    def test_screenshot_budget_can_be_restricted(self):
        text = (ROOT / 'scripts/audit_browser.py').read_text(encoding='utf-8')
        self.assertIn("choices=('all', 'representative', 'none')", text)
        self.assertIn('--widths', text)

    def test_homepage_franchises_precede_cup_feature(self):
        text = (ROOT / 'index.md').read_text(encoding='utf-8')
        self.assertLess(text.index('home-franchises-heading'), text.index('class="cup-feature"'))
        self.assertIn('width="961" height="1366"', text)

    def test_draft_and_roster_scroll_regions_are_named_and_focusable(self):
        for filename, marker in [('_layouts/draft.html', 'table-scroll'),
                                 ('_includes/live-matchup-card.html', 'live-roster-table-wrap')]:
            text = (ROOT / filename).read_text(encoding='utf-8')
            self.assertIn(f'class="{marker}" tabindex="0" role="region" aria-label=', text)
            self.assertIn('<table aria-label=', text)

    def test_rules_use_canonical_sentence_case_typography(self):
        text = (ROOT / 'assets/css/publication.css').read_text(encoding='utf-8')
        self.assertIn('.rules-page .prose h2, .rules-page .migration-card h2', text)

    def test_footer_metadata_uses_light_text_on_navy(self):
        text = (ROOT / 'assets/css/style.css').read_text(encoding='utf-8')
        self.assertIn('.site-footer__meta span { color: var(--slate-300); }', text)


if __name__ == '__main__':
    unittest.main()
