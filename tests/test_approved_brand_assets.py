"""Contracts for the commissioner's supplied helmet pack and league emblem."""
from pathlib import Path
import hashlib
import struct
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ApprovedBrandAssetsTests(unittest.TestCase):
    def test_all_twelve_active_franchises_use_supplied_originals(self):
        teams = yaml.safe_load((ROOT / '_data/franchises.yml').read_text(encoding='utf-8'))['franchises']
        active = [team for team in teams if team['status'] == 'active']
        self.assertEqual(len(active), 12)
        for team in active:
            path = team['branding']['identity_image']
            native_jpeg = team['franchise_id'] in {'ayahuasca-rush', 'baseball-furies', 'buffalo-bravado'}
            extension = 'jpg' if native_jpeg else 'png'
            self.assertEqual(path, f"/assets/img/franchises/{team['franchise_id']}/helmet-2026.{extension}")
            content = (ROOT / path.lstrip('/')).read_bytes()
            if native_jpeg:
                self.assertEqual(content[:3], b'\xff\xd8\xff')
            else:
                self.assertEqual(content[:8], b'\x89PNG\r\n\x1a\n')
                self.assertEqual(struct.unpack('>II', content[16:24]), (1312, 1199))
            self.assertIn('3D football helmet', team['branding']['identity_alt'])

    def test_legacy_helmets_remain_available(self):
        self.assertEqual(len(list((ROOT / 'assets/img/franchises').glob('*/identity.jpg'))), 14)
        teams = yaml.safe_load((ROOT / '_data/franchises.yml').read_text(encoding='utf-8'))['franchises']
        retired = next(team for team in teams if team['franchise_id'] == 'savage-huns')
        self.assertTrue(retired['branding']['identity_image'].endswith('/identity.jpg'))
        giants = next(team for team in teams if team['franchise_id'] == 'new-jersey-giants')
        self.assertEqual(giants['historical_identities'][0]['identity_image'], '/assets/img/franchises/quahog-stripes/identity.jpg')

    def test_league_logo_matches_commissioner_original(self):
        brand = yaml.safe_load((ROOT / '_data/brand.yml').read_text(encoding='utf-8'))
        content = (ROOT / brand['league_logo'].lstrip('/')).read_bytes()
        self.assertEqual(hashlib.sha256(content).hexdigest(), 'b0286156f9467859e5495e4c25923b1fc8957b62eb612669acb8f8cd22a8f6a6')
        self.assertEqual(brand['favicon'], brand['league_logo'])

    def test_header_footer_and_browser_icon_use_canonical_brand(self):
        layout = (ROOT / '_layouts/default.html').read_text(encoding='utf-8')
        mark = (ROOT / '_includes/league-mark.html').read_text(encoding='utf-8')
        self.assertIn('site.data.brand.league_logo | relative_url', mark)
        self.assertIn('site.data.brand.favicon | relative_url', layout)
        self.assertIn('type="image/png"', layout)
        self.assertIn('footer-brand--emblem', layout)
        self.assertNotIn('favicon.svg', layout)
        self.assertNotIn('<svg', mark)


if __name__ == '__main__':
    unittest.main()
