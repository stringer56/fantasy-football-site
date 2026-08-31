import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "yahoo"
sys.path.insert(0, str(ROOT / "scripts"))

from yahoo_normalize import (  # noqa: E402
    build_public_payloads,
    normalize_league,
    normalize_matchups,
    normalize_roster,
    normalize_standings,
    normalize_teams,
)


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class YahooNormalizerTests(unittest.TestCase):
    def test_league_metadata_is_allowlisted(self):
        result = normalize_league(fixture("league.json"))
        league = result["league"]
        self.assertEqual(league["league_key"], "999.l.26455")
        self.assertEqual(league["league_id"], "26455")
        self.assertEqual(league["season"], 2026)
        self.assertEqual(league["number_of_teams"], 12)
        self.assertFalse(league["is_finished"])
        self.assertNotIn("short_invitation_url", league)

    def test_twelve_nested_teams_are_parsed(self):
        result = normalize_teams(fixture("teams.json"))
        self.assertEqual(len(result["teams"]), 12)
        first = result["teams"][0]
        self.assertEqual(first["team_key"], "999.l.26455.t.1")
        self.assertEqual(first["team_name"], "Fixture Team 01")
        self.assertEqual(first["managers"], [{"display_name": "Manager 01"}])
        self.assertEqual(first["team_logo_url"], "https://example.invalid/team-01.png")

    def test_standings_and_numeric_points_are_parsed(self):
        result = normalize_standings(fixture("standings.json"))
        self.assertEqual(len(result["standings"]), 2)
        leader = result["standings"][0]
        self.assertEqual(leader["rank"], 1)
        self.assertEqual(leader["wins"], 2)
        self.assertIsInstance(leader["points_for"], float)
        self.assertIsInstance(leader["points_against"], float)
        self.assertEqual(leader["streak"], {"type": "win", "value": 2})

    def test_matchup_teams_scores_and_projection_are_parsed(self):
        result = normalize_matchups(fixture("scoreboard.json"))
        self.assertEqual(result["week"], 1)
        self.assertEqual(len(result["matchups"]), 1)
        matchup = result["matchups"][0]
        self.assertEqual(matchup["status"], "postevent")
        self.assertEqual(matchup["winner_team_key"], "999.l.26455.t.1")
        self.assertEqual(len(matchup["teams"]), 2)
        self.assertEqual(matchup["teams"][0]["score"], 125.5)
        self.assertEqual(matchup["teams"][1]["projected_score"], 119.0)

    def test_roster_players_and_optional_fields_are_parsed(self):
        roster = normalize_roster(fixture("roster.json"))
        self.assertEqual(roster["team_key"], "999.l.26455.t.1")
        self.assertEqual(len(roster["players"]), 2)
        first = roster["players"][0]
        self.assertEqual(first["player_name"], "Fixture Player One")
        self.assertEqual(first["nfl_team"], "BUF")
        self.assertEqual(first["primary_position"], "QB")
        self.assertEqual(first["selected_position"], "QB")
        self.assertEqual(first["status"], "Q")
        self.assertIsNone(roster["players"][1]["status"])

    def test_missing_optional_and_malformed_structures_fail_gracefully(self):
        self.assertEqual(normalize_teams(None)["teams"], [])
        self.assertEqual(normalize_standings({"fantasy_content": {}})["standings"], [])
        self.assertEqual(normalize_matchups({"unexpected": []})["matchups"], [])
        roster = normalize_roster({"fantasy_content": {"team": "bad"}})
        self.assertEqual(roster["players"], [])

    def test_combined_public_payloads_are_schema_versioned(self):
        team_key = "999.l.26455.t.1"
        payloads = build_public_payloads(
            league_data=fixture("league.json"),
            teams_data=fixture("teams.json"),
            standings_data=fixture("standings.json"),
            scoreboard_data=fixture("scoreboard.json"),
            roster_payloads={team_key: fixture("roster.json")},
        )
        self.assertEqual(set(payloads), {
            "manifest.json",
            "league.json",
            "teams.json",
            "standings.json",
            "matchups.json",
            "rosters.json",
        })
        for payload in payloads.values():
            self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(len(payloads["rosters.json"]["teams"][0]["players"]), 2)


if __name__ == "__main__":
    unittest.main()
