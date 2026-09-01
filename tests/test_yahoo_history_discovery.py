from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from discover_yahoo_history import build_committed_baseline  # noqa: E402
from yahoo_history_discovery import (  # noqa: E402
    extract_games,
    extract_leagues,
    map_team,
    parse_league_key,
    parse_renewal_key,
    renewal_chain,
    safe_league,
    validate_safe_output,
)


FIXTURE = ROOT / "tests" / "fixtures" / "yahoo" / "history_discovery.json"


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class YahooHistoryDiscoveryTests(unittest.TestCase):
    def test_multi_season_game_and_league_discovery(self):
        payload = fixture()
        games = extract_games(payload["games"])
        leagues = extract_leagues(payload["leagues"])
        self.assertEqual([row["season"] for row in games], [2024, 2025, 2026])
        self.assertEqual(
            [row["league_key"] for row in leagues],
            ["449.l.761310", "461.l.103926", "461.l.999999", "472.l.26455"],
        )

    def test_duplicate_leagues_are_removed(self):
        leagues = extract_leagues(fixture()["leagues"])
        self.assertEqual(sum(row["league_key"] == "461.l.103926" for row in leagues), 1)
        row = next(row for row in leagues if row["league_key"] == "461.l.103926")
        self.assertEqual(row["number_of_teams"], 12)

    def test_key_and_renewal_parsing(self):
        self.assertEqual(parse_league_key("461.l.103926"), ("461", "103926"))
        self.assertEqual(parse_renewal_key("449_761310"), "449.l.761310")
        self.assertEqual(parse_renewal_key("472.l.26455"), "472.l.26455")
        self.assertIsNone(parse_league_key("nfl.l.bad"))
        self.assertIsNone(parse_renewal_key("not-a-key"))

    def test_explicit_renewal_chain_is_followed(self):
        leagues = extract_leagues(fixture()["leagues"])
        chain, missing = renewal_chain(leagues, "472.l.26455")
        self.assertEqual(chain, ["449.l.761310", "461.l.103926", "472.l.26455"])
        self.assertEqual(missing, [])

    def test_unrelated_same_account_league_is_not_in_chain(self):
        leagues = extract_leagues(fixture()["leagues"])
        chain, _ = renewal_chain(leagues, "472.l.26455")
        self.assertNotIn("461.l.999999", chain)

    def test_known_season_team_key_maps_verified(self):
        franchises = [{
            "franchise_id": "albany-kneelers",
            "name": "Albany Kneelers",
            "aliases": [],
            "yahoo": {"team_keys": {"2025": "461.l.103926.t.2"}, "team_names": {}},
        }]
        result = map_team(
            season=2025,
            team_key="461.l.103926.t.2",
            team_name="Renamed Team",
            franchises=franchises,
        )
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["candidate_franchise_id"], "albany-kneelers")

    def test_unknown_team_remains_unresolved(self):
        franchises = [{
            "franchise_id": "albany-kneelers",
            "name": "Albany Kneelers",
            "aliases": [],
            "yahoo": {"team_keys": {}, "team_names": {}},
        }]
        result = map_team(
            season=2024,
            team_key="449.l.761310.t.99",
            team_name="Mystery Historical Team",
            franchises=franchises,
        )
        self.assertEqual(result["status"], "unresolved")
        self.assertIsNone(result["candidate_franchise_id"])

    def test_public_league_is_strictly_allowlisted(self):
        unsafe = {
            "season": 2025,
            "league_key": "461.l.103926",
            "league_id": "103926",
            "league_name": "Road To Glory FFL",
            "password": "should-not-survive",
            "short_invitation_url": "https://example.test/invitation?key=secret",
        }
        public = safe_league(unsafe, verification_status="verified")
        serialized = json.dumps(public).casefold()
        self.assertNotIn("password", serialized)
        self.assertNotIn("invitation", serialized)
        self.assertEqual(validate_safe_output(public), [])

    def test_secret_leakage_is_rejected(self):
        errors = validate_safe_output({"schema_version": 1, "refresh_token": "secret"})
        self.assertTrue(errors)
        errors = validate_safe_output({"schema_version": 1, "note": "Authorization: Bearer secret"})
        self.assertTrue(errors)

    def test_committed_baseline_is_safe_and_deterministic(self):
        first = build_committed_baseline()
        second = build_committed_baseline()
        self.assertEqual(first, second)
        self.assertEqual(validate_safe_output(first), [])
        self.assertEqual([row["season"] for row in first["seasons"]], [2024, 2025])
        mappings = first["seasons"][1]["team_mappings"]
        self.assertEqual(len(mappings), 12)
        self.assertTrue(all(row["status"] == "verified" for row in mappings))


if __name__ == "__main__":
    unittest.main()
