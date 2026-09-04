from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Season2025HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.season = next(item for item in load_yaml("_data/seasons.yml")["seasons"] if item["year"] == 2025)
        cls.champion = next(item for item in load_yaml("_data/champions.yml")["champions"] if item["year"] == 2025)
        cls.playoff = next(item for item in load_yaml("_data/playoffs.yml")["playoffs"] if item["season"] == 2025)
        cls.source_standings = load_json("_data/generated/history/2025/standings.json")["standings"]
        cls.source_weeks = load_json("_data/generated/history/2025/weeks.json")
        cls.source_playoffs = load_json("_data/generated/history/2025/playoffs.json")
        cls.recaps = load_json("_data/generated/recaps.json")

    def test_champion_and_score_match_verified_playoff_source(self) -> None:
        source_final = next(item for item in self.source_playoffs["games"] if item["round"] == "Championship")
        self.assertEqual(self.champion["champion_franchise_id"], source_final["winner_franchise_id"])
        self.assertEqual((self.champion["champion_score"], self.champion["runner_up_score"]), (107.12, 106.72))
        self.assertEqual(self.season["champion_franchise_id"], "greendale-human-beings")

    def test_all_twelve_standings_rows_match_yahoo(self) -> None:
        self.assertEqual(len(self.season["standings"]), 12)
        sources = {item["franchise_id"]: item for item in self.source_standings}
        for row in self.season["standings"]:
            source = sources[row["franchise_id"]]
            for field in ("rank", "wins", "losses", "ties", "win_percentage", "points_for", "points_against", "playoff_seed"):
                self.assertEqual(row[field], source[field])

    def test_all_sixteen_weeks_and_scores_are_complete(self) -> None:
        weeks = self.source_weeks["weeks"]
        games = [game for week in weeks for game in week["matchups"]]
        self.assertEqual([week["week"] for week in weeks], list(range(1, 17)))
        self.assertEqual(len(games), 92)
        self.assertTrue(all(game["verified"] and game["team_a"]["score"] is not None and game["team_b"]["score"] is not None for game in games))

    def test_playoff_and_placement_games_preserve_source_classification(self) -> None:
        source = {item["game_id"]: item for item in self.source_playoffs["games"]}
        self.assertEqual(len(self.playoff["games"]), 7)
        for game in self.playoff["games"]:
            original = source[game["game_id"]]
            self.assertEqual(game["bracket_type"], original["bracket_type"])
            self.assertEqual(game["winner_franchise_id"], original["winner_franchise_id"])
        self.assertEqual(sum(game["bracket_type"] == "placement" for game in self.playoff["games"]), 2)

    def test_all_twelve_team_mini_recaps_exist_without_player_claims(self) -> None:
        recaps = [item for item in self.recaps["team_recaps"] if item["season"] == 2025]
        self.assertEqual(len(recaps), 12)
        self.assertTrue(all(item["franchise_id"] and item["weekly_metrics"] for item in recaps))
        prose = " ".join(item["text"] for item in recaps).casefold()
        self.assertNotIn("injury", prose)
        self.assertNotIn("draft powered", prose)

    def test_required_cross_links_and_data_driven_bracket_route_exist(self) -> None:
        layout = (ROOT / "_layouts/season.html").read_text(encoding="utf-8")
        self.assertEqual(self.season["bracket_path"], "/history/2025/#bracket")
        self.assertIn("'/cup/'", layout)
        self.assertIn("'/drafts/'", layout)
        self.assertTrue((ROOT / "_drafts/2025.md").is_file())
        self.assertTrue((ROOT / "_seasons/2025.md").is_file())


if __name__ == "__main__":
    unittest.main()
