from __future__ import annotations

import json
import unittest
from collections import defaultdict
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Season2021HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.season = next(item for item in load_yaml("_data/seasons.yml")["seasons"] if item["year"] == 2021)
        cls.champion = next(item for item in load_yaml("_data/champions.yml")["champions"] if item["year"] == 2021)
        cls.playoff = next(item for item in load_yaml("_data/playoffs.yml")["playoffs"] if item["season"] == 2021)
        cls.franchises = {item["franchise_id"]: item for item in load_yaml("_data/franchises.yml")["franchises"]}
        cls.source = load_json("_data/generated/history/2021/standings.json")
        cls.teams = load_json("_data/generated/history/2021/teams.json")["teams"]
        cls.weeks = load_json("_data/generated/history/2021/weeks.json")
        cls.recaps = load_json("_data/generated/recaps.json")
        cls.draft = next(item for item in load_yaml("_data/drafts.yml")["drafts"] if item["year"] == 2021)

    def test_ten_complete_standings_rows_match_verified_source(self) -> None:
        rows = self.season["standings"]
        self.assertEqual(self.season["data_mode"], "detailed")
        self.assertEqual(len(rows), 10)
        self.assertEqual([row["rank"] for row in rows], list(range(1, 11)))
        source = {row["franchise_id"]: row for row in self.source["standings"]}
        for row in rows:
            self.assertIn(row["franchise_id"], self.franchises)
            for field in (
                "rank", "wins", "losses", "ties", "win_percentage", "points_for",
                "points_against", "streak", "playoff_seed", "playoff_finish",
            ):
                self.assertEqual(row[field], source[row["franchise_id"]][field])
            self.assertNotIn(0, (row["points_for"], row["points_against"]))

    def test_every_historical_identity_is_resolved_and_season_accurate(self) -> None:
        self.assertEqual(len(self.teams), 10)
        self.assertTrue(all(row["mapping_status"] == "verified" for row in self.teams))
        self.assertTrue(all(row["franchise_id"] in self.franchises for row in self.teams))
        names = {row["franchise_id"]: row["historical_team_name"] for row in self.teams}
        self.assertEqual(names["buffalo-bravado"], "The Swagger Daggers")
        self.assertEqual(names["vegas-vandals"], "Matthew's Optimal Team")
        self.assertEqual(names["new-jersey-giants"], "Quahog Stripes")

    def test_weekly_archive_contains_all_authenticated_results(self) -> None:
        self.assertTrue(self.weeks["coverage"]["complete"])
        self.assertEqual(self.weeks["coverage"]["recovered_weeks"], list(range(1, 17)))
        matchups = [game for week in self.weeks["weeks"] for game in week["matchups"]]
        self.assertEqual(len(matchups), 78)
        self.assertTrue(all(game["verified"] and isinstance(game["team_a"]["score"], (int, float)) and isinstance(game["team_b"]["score"], (int, float)) for game in matchups))
        for game in matchups:
            a, b = game["team_a"], game["team_b"]
            expected_winner = a["franchise_id"] if a["score"] > b["score"] else b["franchise_id"]
            self.assertEqual(game["winner_franchise_id"], expected_winner)
            self.assertEqual(game["margin"], round(abs(a["score"] - b["score"]), 2))
            self.assertNotIn(0, (a["score"], b["score"]))
        self.assertEqual(self.season["weeks_data_path"], "_data/generated/history/2021/weeks.json")
        recap = next(item for item in self.recaps["seasons"] if item["season"] == 2021)
        self.assertEqual(recap["weekly_archive"]["matchup_count"], 78)

    def test_regular_season_results_reconcile_to_standings(self) -> None:
        totals = defaultdict(lambda: {"wins": 0, "losses": 0, "ties": 0, "pf": 0.0, "pa": 0.0})
        for week in self.weeks["weeks"][:14]:
            for game in week["matchups"]:
                for side, opponent in ((game["team_a"], game["team_b"]), (game["team_b"], game["team_a"])):
                    row = totals[side["franchise_id"]]
                    row["pf"] += side["score"]
                    row["pa"] += opponent["score"]
                    if game["tie"]:
                        row["ties"] += 1
                    elif game["winner_franchise_id"] == side["franchise_id"]:
                        row["wins"] += 1
                    else:
                        row["losses"] += 1
        for standing in self.season["standings"]:
            actual = totals[standing["franchise_id"]]
            self.assertEqual((actual["wins"], actual["losses"], actual["ties"]), (standing["wins"], standing["losses"], standing["ties"]))
            self.assertEqual(round(actual["pf"], 2), standing["points_for"])
            self.assertEqual(round(actual["pa"], 2), standing["points_against"])

    def test_verified_playoff_field_uses_authenticated_yahoo_seeds(self) -> None:
        self.assertEqual(self.playoff["byes"], [])
        self.assertEqual(
            [(item["seed"], item["franchise_id"]) for item in self.playoff["playoff_field"]],
            [
                (1, "albany-kneelers"),
                (2, "greendale-human-beings"),
                (3, "savage-huns"),
                (4, "buffalo-bravado"),
            ],
        )
        self.assertEqual(len(self.playoff["games"]), 8)
        self.assertEqual(sum(game["bracket_type"] == "championship" for game in self.playoff["games"]), 3)
        self.assertEqual(sum(game["bracket_type"] == "placement" for game in self.playoff["games"]), 5)
        source_by_week_pair = {
            (game["week"], frozenset((game["team_a"]["franchise_id"], game["team_b"]["franchise_id"]))): game
            for week in self.weeks["weeks"] for game in week["matchups"]
        }
        for game in self.playoff["games"]:
            source = source_by_week_pair[(
                game["week"],
                frozenset((game["team_one_franchise_id"], game["team_two_franchise_id"])),
            )]
            self.assertEqual(game["winner_franchise_id"], source["winner_franchise_id"])
            self.assertEqual(
                {game["team_one_score"], game["team_two_score"]},
                {source["team_a"]["score"], source["team_b"]["score"]},
            )
        semifinal_scores = [
            (game["team_one_score"], game["team_two_score"])
            for game in self.playoff["games"] if game["round"] == "Semifinal"
        ]
        self.assertEqual(semifinal_scores, [(128.48, 73.26), (80.04, 93.58)])

    def test_champion_and_all_scored_playoff_games_match(self) -> None:
        final = next(game for game in self.playoff["games"] if game["round"] == "Championship")
        self.assertEqual(self.champion["champion_franchise_id"], "albany-kneelers")
        self.assertEqual(self.champion["runner_up_franchise_id"], "savage-huns")
        self.assertEqual((self.champion["champion_score"], self.champion["runner_up_score"]), (121.50, 118.70))
        self.assertEqual(final["winner_franchise_id"], self.champion["champion_franchise_id"])
        self.assertEqual((final["team_one_score"], final["team_two_score"]), (121.50, 118.70))
        self.assertEqual(sum(game["team_one_score"] is not None for game in self.playoff["games"]), 8)

    def test_narrative_team_recaps_and_numbers_use_only_supported_facts(self) -> None:
        season_recap = next(item for item in self.recaps["seasons"] if item["season"] == 2021)
        self.assertGreaterEqual(len(season_recap["paragraphs"]), 3)
        self.assertLessEqual(len(season_recap["paragraphs"]), 5)
        team_recaps = [item for item in self.recaps["team_recaps"] if item["season"] == 2021]
        self.assertEqual(len(team_recaps), 10)
        self.assertTrue(all(item["mapping_status"] == "resolved" and item["path"] for item in team_recaps))
        self.assertTrue(all(item["weekly_metrics"] for item in team_recaps))
        numbers = [item for item in self.recaps["by_the_numbers"] if item["season"] == 2021]
        self.assertEqual(len(numbers), 15)
        weekly_fact_types = {
            "weekly_archive_coverage", "highest_weekly_score", "lowest_weekly_score",
            "biggest_victory", "closest_game", "highest_combined_score", "verified_weekly_metrics",
        }
        self.assertTrue(
            any({fact["fact_type"] for fact in entry["facts_used"]} & weekly_fact_types for entry in numbers)
        )
        prose = " ".join(item["text"] for item in team_recaps).casefold()
        self.assertIn("won the third place game", prose)
        for unsupported in ("injury caused", "trade caused", "manager strategy", "draft powered", "waiver move"):
            self.assertNotIn(unsupported, prose)

    def test_approved_assets_draft_summary_and_routes_exist(self) -> None:
        for field in (
            "standings_asset", "bracket_asset", "championship_portrait_asset",
            "championship_matchup_asset",
        ):
            asset = ROOT / self.season[field].lstrip("/")
            self.assertTrue(asset.is_file())
            self.assertGreater(asset.stat().st_size, 1024)
        self.assertEqual(self.draft["pick_data_status"], "image_only_unverified")
        self.assertEqual(len(self.draft["results_assets"]), 3)
        self.assertTrue((ROOT / "_seasons/2021.md").is_file())
        self.assertTrue((ROOT / "_drafts/2021.md").is_file())
        layout = (ROOT / "_layouts/season.html").read_text(encoding="utf-8")
        self.assertIn("individual selections remain image-only", layout)
        self.assertIn("'/cup/'", layout)


if __name__ == "__main__":
    unittest.main()
