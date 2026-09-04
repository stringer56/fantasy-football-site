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


class Season2024HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.season = next(item for item in load_yaml("_data/seasons.yml")["seasons"] if item["year"] == 2024)
        cls.champion = next(item for item in load_yaml("_data/champions.yml")["champions"] if item["year"] == 2024)
        cls.playoff = next(item for item in load_yaml("_data/playoffs.yml")["playoffs"] if item["season"] == 2024)
        cls.franchises = {item["franchise_id"]: item for item in load_yaml("_data/franchises.yml")["franchises"]}
        cls.source_standings = load_json("_data/generated/history/2024/standings.json")["standings"]
        cls.source_weeks = load_json("_data/generated/history/2024/weeks.json")
        cls.recaps = load_json("_data/generated/recaps.json")

    def test_all_twelve_standings_rows_match_verified_yahoo_values(self) -> None:
        self.assertEqual(len(self.season["standings"]), 12)
        self.assertEqual([row["rank"] for row in self.season["standings"]], list(range(1, 13)))
        source = {row["franchise_id"]: row for row in self.source_standings}
        for row in self.season["standings"]:
            self.assertIn(row["franchise_id"], self.franchises)
            self.assertIn(row["franchise_id"], source)
            for field in ("rank", "wins", "losses", "ties", "win_percentage", "points_for", "points_against"):
                self.assertEqual(row[field], source[row["franchise_id"]][field])
            self.assertNotIn(0, (row["points_for"], row["points_against"]))

    def test_all_sixteen_weeks_and_ninety_two_scores_are_verified(self) -> None:
        weeks = self.source_weeks["weeks"]
        games = [game for week in weeks for game in week["matchups"]]
        self.assertEqual([week["week"] for week in weeks], list(range(1, 17)))
        self.assertEqual(len(games), 92)
        for game in games:
            scores = (game["team_a"]["score"], game["team_b"]["score"])
            self.assertTrue(game["verified"])
            self.assertTrue(all(isinstance(score, (int, float)) and score > 0 for score in scores))
            self.assertEqual(game["margin"], round(abs(scores[0] - scores[1]), 2))
            if game["tie"]:
                self.assertEqual(scores[0], scores[1])
                self.assertIsNone(game["winner_franchise_id"])
            else:
                expected_winner = game["team_a"]["franchise_id"] if scores[0] > scores[1] else game["team_b"]["franchise_id"]
                self.assertEqual(game["winner_franchise_id"], expected_winner)

    def test_playoff_games_match_weekly_archive_and_keep_placement_separate(self) -> None:
        source_by_week_pair = {
            (week["week"], frozenset((game["team_a"]["franchise_id"], game["team_b"]["franchise_id"]))): game
            for week in self.source_weeks["weeks"] for game in week["matchups"]
        }
        self.assertEqual(len(self.playoff["games"]), 7)
        self.assertEqual(sum(game["bracket_type"] == "championship" for game in self.playoff["games"]), 5)
        self.assertEqual(sum(game["bracket_type"] == "placement" for game in self.playoff["games"]), 2)
        for game in self.playoff["games"]:
            pair = frozenset((game["team_one_franchise_id"], game["team_two_franchise_id"]))
            source = source_by_week_pair[(game["week"], pair)]
            expected = {
                source["team_a"]["franchise_id"]: source["team_a"]["score"],
                source["team_b"]["franchise_id"]: source["team_b"]["score"],
            }
            self.assertEqual(game["team_one_score"], expected[game["team_one_franchise_id"]])
            self.assertEqual(game["team_two_score"], expected[game["team_two_franchise_id"]])
            self.assertEqual(game["winner_franchise_id"], source["winner_franchise_id"])

    def test_champion_final_and_approved_bracket_agree(self) -> None:
        finals = [game for game in self.playoff["games"] if game["round"] == "Championship"]
        self.assertEqual(len(finals), 1)
        final = finals[0]
        self.assertEqual(self.champion["champion_franchise_id"], "turnbull-acs")
        self.assertEqual(self.champion["runner_up_franchise_id"], "crazy-wazs-team")
        self.assertEqual((self.champion["champion_score"], self.champion["runner_up_score"]), (148.18, 140.98))
        self.assertEqual(final["winner_franchise_id"], self.champion["champion_franchise_id"])
        self.assertEqual((final["team_one_score"], final["team_two_score"]), (148.18, 140.98))
        for field in ("standings_asset", "bracket_asset", "championship_portrait_asset", "championship_matchup_asset"):
            asset = ROOT / self.season[field].lstrip("/")
            self.assertTrue(asset.is_file())
            self.assertGreater(asset.stat().st_size, 1024)

    def test_every_franchise_resolves_and_has_a_weekly_mini_recap(self) -> None:
        source = {row["franchise_id"]: row for row in self.source_standings}
        self.assertTrue(all(row["mapping_status"] == "verified" for row in source.values()))
        recaps = [item for item in self.recaps["team_recaps"] if item["season"] == 2024]
        self.assertEqual(len(recaps), 12)
        self.assertEqual({item["franchise_id"] for item in recaps}, set(source))
        self.assertTrue(all(item["mapping_status"] == "resolved" and item["path"] and item["weekly_metrics"] for item in recaps))
        collection_documents = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "_franchises").glob("*.md"))
        for item in recaps:
            self.assertIn(f"franchise_id: {item['franchise_id']}", collection_documents)

    def test_route_draft_link_numbers_and_safe_prose(self) -> None:
        route = (ROOT / "_seasons/2024.md").read_text(encoding="utf-8")
        self.assertIn("permalink: /history/2024/", route)
        self.assertTrue((ROOT / "_drafts/2024.md").is_file())
        numbers = [item for item in self.recaps["by_the_numbers"] if item["season"] == 2024]
        self.assertEqual(len(numbers), 15)
        recaps = [item for item in self.recaps["team_recaps"] if item["season"] == 2024]
        prose = " ".join(item["text"] for item in recaps).casefold()
        for unsupported in ("injury", "trade caused", "manager strategy", "draft powered"):
            self.assertNotIn(unsupported, prose)


if __name__ == "__main__":
    unittest.main()
