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


class Season2022HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.season = next(item for item in load_yaml("_data/seasons.yml")["seasons"] if item["year"] == 2022)
        cls.champion = next(item for item in load_yaml("_data/champions.yml")["champions"] if item["year"] == 2022)
        cls.playoff = next(item for item in load_yaml("_data/playoffs.yml")["playoffs"] if item["season"] == 2022)
        cls.franchises = {item["franchise_id"]: item for item in load_yaml("_data/franchises.yml")["franchises"]}
        cls.source_standings = load_json("_data/generated/history/2022/standings.json")["standings"]
        cls.source_teams = load_json("_data/generated/history/2022/teams.json")["teams"]
        cls.source_weeks = load_json("_data/generated/history/2022/weeks.json")
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

    def test_every_2022_identity_is_verified_and_season_accurate(self) -> None:
        self.assertEqual(len(self.source_teams), 12)
        self.assertTrue(all(row["mapping_status"] == "verified" for row in self.source_teams))
        self.assertTrue(all(row["franchise_id"] in self.franchises for row in self.source_teams))
        names = {row["franchise_id"]: row["historical_team_name"] for row in self.source_teams}
        self.assertEqual(names["new-jersey-giants"], "Quahog Stripes")
        self.assertEqual(names["buffalo-bravado"], "Dilly Dilly")
        self.assertEqual(names["vegas-vandals"], "Broncos Country Let’s Ride")

    def test_all_sixteen_weeks_and_ninety_two_scores_are_authoritative(self) -> None:
        weeks = self.source_weeks["weeks"]
        games = [game for week in weeks for game in week["matchups"]]
        self.assertEqual([week["week"] for week in weeks], list(range(1, 17)))
        self.assertEqual(len(games), 92)
        self.assertEqual(len({game["matchup_id"] for game in games}), 92)
        for game in games:
            scores = (game["team_a"]["score"], game["team_b"]["score"])
            self.assertTrue(game["verified"])
            self.assertTrue(all(isinstance(score, (int, float)) and score > 0 for score in scores))
            self.assertEqual(game["margin"], round(abs(scores[0] - scores[1]), 2))
            if game["tie"]:
                self.assertEqual(scores[0], scores[1])
                self.assertIsNone(game["winner_franchise_id"])
            else:
                expected = game["team_a"]["franchise_id"] if scores[0] > scores[1] else game["team_b"]["franchise_id"]
                self.assertEqual(game["winner_franchise_id"], expected)

    def test_regular_season_boundary_is_week_fourteen(self) -> None:
        self.assertEqual(self.season["regular_season_weeks"], 14)
        games_by_team: dict[str, list[tuple[int, str]]] = {}
        for week in self.source_weeks["weeks"]:
            for game in week["matchups"]:
                for side in (game["team_a"], game["team_b"]):
                    result = "T" if game["tie"] else ("W" if game["winner_franchise_id"] == side["franchise_id"] else "L")
                    games_by_team.setdefault(side["franchise_id"], []).append((week["week"], result))

        def longest(values: list[tuple[int, str]], result: str) -> int:
            best = current = 0
            for _, outcome in sorted(item for item in values if item[0] <= 14):
                current = current + 1 if outcome == result else 0
                best = max(best, current)
            return best

        recaps = {
            item["franchise_id"]: item
            for item in self.recaps["team_recaps"]
            if item["season"] == 2022
        }
        self.assertEqual(recaps["turnbull-acs"]["weekly_metrics"]["longest_regular_season_win_streak"], 5)
        self.assertEqual(recaps["van-cortlant-rangers"]["weekly_metrics"]["longest_regular_season_loss_streak"], 5)
        for franchise_id, values in games_by_team.items():
            metrics = recaps[franchise_id]["weekly_metrics"]
            self.assertEqual(metrics["longest_regular_season_win_streak"], longest(values, "W"))
            self.assertEqual(metrics["longest_regular_season_loss_streak"], longest(values, "L"))

    def test_weekly_archive_labels_regular_classified_and_unclassified_games(self) -> None:
        season_recap = next(item for item in self.recaps["seasons"] if item["season"] == 2022)
        archived = {
            game["matchup_id"]: game
            for week in season_recap["weekly_archive"]["weeks"]
            for game in week["matchups"]
        }
        self.assertEqual(sum(game["game_type"] == "regular_season" for game in archived.values()), 84)
        self.assertEqual(sum(game["game_type"] == "championship_playoff" for game in archived.values()), 3)
        self.assertEqual(sum(game["game_type"] == "placement" for game in archived.values()), 1)
        self.assertEqual(sum(game["game_type"] == "postseason_unclassified" for game in archived.values()), 4)
        archived_by_week_pair = {
            (
                game["week"],
                frozenset((game["team_one"]["franchise_id"], game["team_two"]["franchise_id"])),
            ): game
            for game in archived.values()
        }
        for game in self.playoff["games"]:
            pair = frozenset((game["team_one_franchise_id"], game["team_two_franchise_id"]))
            archived_game = archived_by_week_pair[(game["week"], pair)]
            expected_type = "championship_playoff" if game["bracket_type"] == "championship" else "placement"
            self.assertEqual(archived_game["game_type"], expected_type)
            self.assertEqual(archived_game["playoff_round"], game["round"])
        self.assertTrue(all(game["status"] == "final" and game["game_label"].startswith("Final ·") for game in archived.values()))
        tie = next(game for game in archived.values() if game["tie"])
        self.assertEqual(tie["margin"], 0.0)
        self.assertIn("Tie game", tie["notable_labels"])
        closest = next(
            item for item in self.recaps["by_the_numbers"]
            if item["season"] == 2022 and item["stat_id"] == "closest_game"
        )
        self.assertIn("Tie", closest["display_value"])

    def test_four_team_playoff_field_and_third_place_game_are_classified(self) -> None:
        self.assertEqual(self.playoff["byes"], [])
        self.assertEqual(
            [(item["seed"], item["franchise_id"]) for item in self.playoff["playoff_field"]],
            [
                (1, "ayahuasca-rush"),
                (2, "greendale-human-beings"),
                (3, "turnbull-acs"),
                (4, "new-jersey-giants"),
            ],
        )
        self.assertEqual(sum(game["bracket_type"] == "championship" for game in self.playoff["games"]), 3)
        placement = [game for game in self.playoff["games"] if game["bracket_type"] == "placement"]
        self.assertEqual(len(placement), 1)
        self.assertEqual(placement[0]["round"], "Third Place Game")
        self.assertEqual(placement[0]["winner_franchise_id"], "greendale-human-beings")

    def test_playoff_scores_match_yahoo_and_champion_matches_final(self) -> None:
        source_by_week_pair = {
            (week["week"], frozenset((game["team_a"]["franchise_id"], game["team_b"]["franchise_id"]))): game
            for week in self.source_weeks["weeks"]
            for game in week["matchups"]
        }
        for game in self.playoff["games"]:
            pair = frozenset((game["team_one_franchise_id"], game["team_two_franchise_id"]))
            source = source_by_week_pair[(game["week"], pair)]
            scores = {
                source["team_a"]["franchise_id"]: source["team_a"]["score"],
                source["team_b"]["franchise_id"]: source["team_b"]["score"],
            }
            self.assertEqual(game["team_one_score"], scores[game["team_one_franchise_id"]])
            self.assertEqual(game["team_two_score"], scores[game["team_two_franchise_id"]])
            self.assertEqual(game["winner_franchise_id"], source["winner_franchise_id"])
        final = next(game for game in self.playoff["games"] if game["round"] == "Championship")
        self.assertEqual(self.champion["champion_franchise_id"], "ayahuasca-rush")
        self.assertEqual(self.champion["runner_up_franchise_id"], "turnbull-acs")
        self.assertEqual((self.champion["champion_score"], self.champion["runner_up_score"]), (115.20, 69.16))
        self.assertEqual(final["winner_franchise_id"], self.champion["champion_franchise_id"])

    def test_assets_recaps_metrics_and_cross_links_are_complete(self) -> None:
        for field in ("standings_asset", "bracket_asset", "championship_portrait_asset", "championship_matchup_asset"):
            asset = ROOT / self.season[field].lstrip("/")
            self.assertTrue(asset.is_file())
            self.assertGreater(asset.stat().st_size, 1024)
        team_recaps = [item for item in self.recaps["team_recaps"] if item["season"] == 2022]
        self.assertEqual(len(team_recaps), 12)
        self.assertTrue(all(item["mapping_status"] == "resolved" and item["path"] and item["weekly_metrics"] for item in team_recaps))
        season_recap = next(item for item in self.recaps["seasons"] if item["season"] == 2022)
        self.assertGreaterEqual(len(season_recap["paragraphs"]), 3)
        self.assertLessEqual(len(season_recap["paragraphs"]), 6)
        self.assertEqual(len([item for item in self.recaps["by_the_numbers"] if item["season"] == 2022]), 15)
        prose = " ".join(item["text"] for item in team_recaps).casefold()
        for unsupported in ("injury caused", "trade caused", "manager strategy", "draft powered", "waiver move"):
            self.assertNotIn(unsupported, prose)
        layout = (ROOT / "_layouts/season.html").read_text(encoding="utf-8")
        self.assertIn("'/cup/'", layout)
        self.assertIn("'/drafts/'", layout)
        self.assertTrue((ROOT / "_drafts/2022.md").is_file())
        self.assertTrue((ROOT / "_seasons/2022.md").is_file())


if __name__ == "__main__":
    unittest.main()
