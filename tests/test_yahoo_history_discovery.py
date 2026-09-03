from __future__ import annotations

import json
import pathlib
import sys
import unittest
from unittest.mock import Mock, patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from discover_yahoo_history import (  # noqa: E402
    build_committed_baseline,
    local_archive_coverage,
    sanitized_failure_status,
)
from pull_yahoo import YahooApiError, get_json, refresh_access_token  # noqa: E402
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
        self.assertEqual(
            [row["season"] for row in first["seasons"]],
            [2021, 2022, 2023, 2024, 2025, 2026],
        )
        self.assertEqual(first["league_founded_season"], 2021)
        self.assertEqual(
            first["linked_history_chain"],
            [
                "406.l.12928",
                "414.l.527645",
                "423.l.161807",
                "449.l.761310",
                "461.l.103926",
                "470.l.26455",
            ],
        )
        self.assertEqual(first["access_status"]["oauth_refresh"], "succeeded")
        self.assertEqual(
            first["access_status"]["authenticated_user_fantasy_resource"],
            "http_403",
        )
        self.assertEqual(
            [row["operation"] for row in first["authorization_probes"]],
            ["authenticated_user_fantasy_resource"],
        )
        self.assertFalse(first["authorization_probes"][0]["success"])
        season_2021 = first["seasons"][0]
        self.assertEqual(
            season_2021["capabilities"]["weekly_matchups"],
            "unavailable_public_authentication_required",
        )
        self.assertEqual(
            season_2021["capabilities"]["standings"],
            "available_commissioner_supplied_authenticated_archive",
        )
        self.assertEqual(10, len(season_2021["team_mappings"]))
        self.assertEqual(8, sum(row["status"] == "verified" for row in season_2021["team_mappings"]))
        self.assertEqual(
            "complete_commissioner_supplied_yahoo",
            season_2021["archive_coverage"]["standings"],
        )
        self.assertTrue(all(
            value == "available_public_history"
            for season in first["seasons"][1:5]
            for value in season["capabilities"].values()
        ))
        mappings = first["seasons"][4]["team_mappings"]
        self.assertEqual(len(mappings), 12)
        self.assertTrue(all(row["status"] == "verified" for row in mappings))

    def test_public_history_team_mappings_do_not_guess_unknown_names(self):
        baseline = build_committed_baseline()
        season_2022 = next(row for row in baseline["seasons"] if row["season"] == 2022)
        unresolved_2022 = {
            row["yahoo_team_name"]
            for row in season_2022["team_mappings"]
            if row["status"] == "unresolved"
        }
        self.assertEqual(unresolved_2022, {"Broncos Country Let’s Ride", "Dilly Dilly"})
        season_2026 = next(row for row in baseline["seasons"] if row["season"] == 2026)
        albany = next(
            row for row in season_2026["team_mappings"]
            if row["yahoo_team_name"] == "Albany Redskins"
        )
        self.assertEqual(albany["status"], "unresolved")
        self.assertIsNone(albany["candidate_franchise_id"])

    def test_api_http_failures_are_sanitized(self):
        response = Mock(status_code=403, headers={"Content-Type": "application/json"})
        response.json.return_value = {
            "fantasy_content": {
                "error": {
                    "code": "ACCOUNT_NOT_AUTHORIZED",
                    "description": "must never be included",
                }
            }
        }
        response.raise_for_status.side_effect = __import__("requests").HTTPError("unsafe URL")
        with patch("pull_yahoo.requests.get", return_value=response):
            with self.assertRaises(YahooApiError) as raised:
                get_json("https://example.invalid/private-league-key", "private-token")
        self.assertEqual(
            str(raised.exception),
            "Yahoo Fantasy API request failed with HTTP 403 (ACCOUNT_NOT_AUTHORIZED)",
        )
        self.assertNotIn("private", str(raised.exception))
        self.assertNotIn("description", str(raised.exception))
        self.assertEqual(raised.exception.error_code, "ACCOUNT_NOT_AUTHORIZED")
        self.assertEqual(sanitized_failure_status(raised.exception), "http_403")

    def test_oauth_http_failures_are_sanitized(self):
        response = Mock(status_code=400)
        response.json.return_value = {"error": "invalid_grant"}
        response.raise_for_status.side_effect = __import__("requests").HTTPError("unsafe body")
        with patch("pull_yahoo.requests.post", return_value=response):
            with self.assertRaises(YahooApiError) as raised:
                refresh_access_token("client", "secret", "refresh")
        self.assertEqual(str(raised.exception), "Yahoo OAuth token refresh failed with HTTP 400")

    def test_non_allowlisted_error_text_is_not_retained(self):
        response = Mock(status_code=403, headers={"Content-Type": "application/json"})
        response.json.return_value = {
            "error": {"code": "contains spaces and secret material"}
        }
        response.raise_for_status.side_effect = __import__("requests").HTTPError("unsafe")
        with patch("pull_yahoo.requests.get", return_value=response):
            with self.assertRaises(YahooApiError) as raised:
                get_json("https://example.invalid/private", "private-token")
        self.assertIsNone(raised.exception.error_code)
        self.assertEqual(str(raised.exception), "Yahoo Fantasy API request failed with HTTP 403")

    def test_commissioner_confirmed_2025_playoffs_are_complete_and_safe(self):
        path = ROOT / "_data" / "generated" / "history" / "2025" / "playoffs.json"
        playoffs = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_safe_output(playoffs), [])
        self.assertEqual(playoffs["coverage"]["status"], "complete_championship_playoff_bracket")
        self.assertEqual(len(playoffs["games"]), 7)
        self.assertEqual(len(playoffs["byes"]), 2)
        final = next(game for game in playoffs["games"] if game["round"] == "Championship")
        self.assertEqual(final["winner_franchise_id"], "greendale-human-beings")
        self.assertEqual(final["team_one"]["score"], 107.12)
        self.assertEqual(final["team_two"]["score"], 106.72)
        self.assertEqual([row["place"] for row in playoffs["final_placements"]], list(range(1, 7)))
        participants = {
            side["franchise_id"]
            for game in playoffs["games"]
            for side in (game["team_one"], game["team_two"])
        }
        self.assertEqual(len(participants), 6)
        coverage = local_archive_coverage(2025)
        self.assertEqual(coverage["scored_playoff_games"], 7)
        self.assertEqual(coverage["source_file"], "_data/generated/history/2025/playoffs.json")


if __name__ == "__main__":
    unittest.main()
