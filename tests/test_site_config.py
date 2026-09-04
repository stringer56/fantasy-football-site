from __future__ import annotations

import pathlib
import tempfile
import unittest

import yaml

from scripts import pull_yahoo, validate_site_config, yahoo_live


class SiteYahooConfigTests(unittest.TestCase):
    def config(self) -> dict:
        return {
            "current_season": 2026,
            "yahoo": dict(validate_site_config.CANONICAL_2026),
        }

    def test_repository_configuration_is_canonical(self) -> None:
        config = yaml.safe_load(validate_site_config.SITE_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(validate_site_config.validate_yahoo_config(config), [])

    def test_private_or_api_url_is_rejected(self) -> None:
        for unsafe in (
            "https://football.fantasysports.yahoo.com/f1/26455/invitation?key=private",
            "https://fantasysports.yahooapis.com/fantasy/v2/league/470.l.26455",
            "https://football.fantasysports.yahoo.com/f1/26455/commish/tools",
        ):
            config = self.config()
            config["yahoo"]["league_url"] = unsafe
            self.assertTrue(validate_site_config.validate_yahoo_config(config))

    def test_inconsistent_identifiers_are_rejected(self) -> None:
        config = self.config()
        config["yahoo"]["league_key"] = "999.l.26455"
        errors = validate_site_config.validate_yahoo_config(config)
        self.assertTrue(any("league_key" in error for error in errors))

    def test_presentation_source_cannot_hardcode_yahoo_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "index.md").write_text(
                "https://football.fantasysports.yahoo.com/f1/26455",
                encoding="utf-8",
            )
            errors = validate_site_config.validate_template_usage(root)
        self.assertTrue(any("hardcodes" in error for error in errors))

    def test_public_fallback_uses_reviewed_configuration(self) -> None:
        config = self.config()
        manifest = {
            "seasons": [
                {
                    "season": 2026,
                    "game_key": "470",
                    "league_id": "26455",
                    "league_key": "470.l.26455",
                    "league_name": "Road To Glory FFL",
                }
            ]
        }
        season, record = yahoo_live.canonical_current_season_record(config, manifest)
        self.assertEqual(season, 2026)
        self.assertEqual(record["league_url"], validate_site_config.CANONICAL_2026["league_url"])

    def test_api_alias_and_normalized_identity_match_configuration(self) -> None:
        configured = self.config()["yahoo"]
        payload = {
            "league": {
                "season": 2026,
                "league_key": "470.l.26455",
                "league_id": "26455",
            }
        }
        pull_yahoo.validate_requested_and_normalized_identity(
            configured, "nfl.l.26455", payload
        )
        with self.assertRaisesRegex(RuntimeError, "LEAGUE_KEY"):
            pull_yahoo.validate_requested_and_normalized_identity(
                configured, "nfl.l.99999", payload
            )
        payload["league"]["league_key"] = "999.l.26455"
        with self.assertRaisesRegex(RuntimeError, "response identity"):
            pull_yahoo.validate_requested_and_normalized_identity(
                configured, "nfl.l.26455", payload
            )


if __name__ == "__main__":
    unittest.main()
