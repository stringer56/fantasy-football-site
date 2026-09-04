from __future__ import annotations

import copy
import unittest
from unittest import mock

from scripts import build_historical_metrics as metrics


def identity(franchise_id: str) -> dict:
    return {
        "franchise_id": franchise_id,
        "display_name": franchise_id.title(),
        "short_name": franchise_id,
        "path": f"/teams/{franchise_id}/",
        "identity_image": f"/{franchise_id}.png",
    }


def game(matchup_id: str, season: int, week: int, a: str, b: str, a_score: float, b_score: float,
         *, game_type: str = "regular_season") -> dict:
    identities = {a: identity(a), b: identity(b)}
    winner = None if a_score == b_score else identities[a if a_score > b_score else b]
    loser = None if winner is None else identities[b if winner["franchise_id"] == a else a]
    return {
        "matchup_id": matchup_id, "season": season, "week": week, "game_type": game_type,
        "playoff_round": "Semifinal" if game_type == "championship_playoff" else None,
        "tie": a_score == b_score, "team_a": {**identities[a], "score": a_score},
        "team_b": {**identities[b], "score": b_score}, "historical_team_a": a,
        "historical_team_b": b, "team_a_score": a_score, "team_b_score": b_score,
        "combined_score": round(a_score + b_score, 2), "margin": round(abs(a_score - b_score), 2),
        "winner": winner, "loser": loser,
        "winner_score": max(a_score, b_score) if winner else None,
        "loser_score": min(a_score, b_score) if loser else None,
    }


class HistoricalMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payloads = metrics.build_payloads()

    def setUp(self) -> None:
        self.identities = {name: identity(name) for name in ("alpha", "beta", "gamma")}

    def test_head_to_head_aggregation_and_tie(self) -> None:
        games = [game("g1", 2022, 1, "alpha", "beta", 110, 100), game("g2", 2023, 1, "alpha", "beta", 90, 90)]
        pair = metrics.build_head_to_head(games, self.identities)[0]
        self.assertEqual((pair["meetings"], pair["wins_a"], pair["wins_b"], pair["ties"]), (2, 1, 0, 1))
        self.assertEqual((pair["points_a"], pair["points_b"]), (200.0, 190.0))
        self.assertEqual(pair["first_meeting"]["matchup_id"], "g1")
        self.assertEqual(pair["most_recent_meeting"]["matchup_id"], "g2")
        self.assertIsNone(pair["current_series_streak"])
        self.assertEqual(pair["longest_series_streak"]["wins"], 1)
        self.assertIsNone(pair["rivalry_title"])
        self.assertIsNone(pair["editorial_history"])

    def test_biggest_and_closest_sorting(self) -> None:
        games = [game("g1", 2022, 1, "alpha", "beta", 120, 100), game("g2", 2022, 2, "alpha", "beta", 101, 100)]
        self.assertEqual(["g1", "g2"], [item["matchup_id"] for item in metrics.ranked(games, lambda row: row["margin"])])
        self.assertEqual(["g2", "g1"], [item["matchup_id"] for item in metrics.ranked(games, lambda row: row["margin"], reverse=False)])

    def test_weekly_score_sorting(self) -> None:
        entries = [{"matchup_id": "g1", "season": 2022, "week": 1, "score": 80}, {"matchup_id": "g2", "season": 2022, "week": 2, "score": 140}]
        self.assertEqual(140, metrics.ranked(entries, lambda row: row["score"])[0]["score"])

    def test_decimal_ties_round_consistently_across_python_versions(self) -> None:
        self.assertEqual(118.113, metrics.rounded(118.1125, 3))

    def test_streak_calculation_and_cross_season_boundary(self) -> None:
        sequence = [(2022, 13, "W"), (2023, 1, "W"), (2023, 2, "L")]
        self.assertEqual(1, metrics.best_streak(sequence, {"W"}, cross_season=False)["games"])
        self.assertEqual(2, metrics.best_streak(sequence, {"W"}, cross_season=True)["games"])

    def test_cross_season_streak_rejects_unrepresented_gap(self) -> None:
        sequence = [(2022, 13, "W"), (2024, 1, "W")]
        self.assertEqual(1, metrics.best_streak(sequence, {"W"}, cross_season=True)["games"])

    def test_tie_breaks_win_streak_but_extends_unbeaten_streak(self) -> None:
        sequence = [(2022, 1, "W"), (2022, 2, "T"), (2022, 3, "W")]
        self.assertEqual(1, metrics.best_streak(sequence, {"W"}, cross_season=False)["games"])
        self.assertEqual(3, metrics.best_streak(sequence, {"W", "T"}, cross_season=False)["games"])

    def test_actual_playoff_output_is_independently_classified(self) -> None:
        payload = self.payloads["playoffs"]
        self.assertEqual(21, len(payload["games"]))
        self.assertTrue(all(item["game_type"] == "championship_playoff" and item["playoff_round"] for item in payload["games"]))
        self.assertNotIn("placement", {str(item["playoff_round"]).casefold() for item in payload["games"]})
        self.assertEqual(21, sum(row["playoff_wins"] for row in payload["franchises"]))
        self.assertEqual(21, sum(row["playoff_losses"] for row in payload["franchises"]))

    def test_weekly_matchups_are_fully_resolved_after_confirmed_mappings(self) -> None:
        manifest = self.payloads["manifest"]
        self.assertEqual(446, manifest["counts"]["weekly_matchups_input"])
        self.assertEqual(0, manifest["counts"]["excluded_unresolved_matchups"])
        self.assertEqual(78, manifest["counts"]["head_to_head_pairs"])

    def test_2021_is_included_in_weekly_outputs(self) -> None:
        encoded = " ".join(str(self.payloads[name]) for name in ("head_to_head", "biggest_wins", "closest_games", "weekly_scores", "streaks", "playoffs"))
        self.assertIn("'season': 2021", encoded)

    def test_coverage_labels_remain_separate(self) -> None:
        self.assertEqual("Verified 2021–2025", self.payloads["franchise_career"]["season_level_coverage"]["label"])
        self.assertEqual("Verified 2021–2025", self.payloads["head_to_head"]["coverage"]["label"])

    def test_franchise_career_aggregation_and_name_continuity(self) -> None:
        career = self.payloads["franchise_career"]["franchises"]
        self.assertEqual(13, len(career))
        self.assertEqual(len(career), len({row["franchise_id"] for row in career}))
        buffalo = next(row for row in career if row["franchise_id"] == "buffalo-bravado")
        self.assertIn("The Swagger Daggers", {row["historical_team_name"] for row in buffalo["season_history"]["seasons"]})
        self.assertEqual((25, 41, 1), (buffalo["season_history"]["wins"], buffalo["season_history"]["losses"], buffalo["season_history"]["ties"]))
        self.assertIn("playoff_appearance", {event["event_type"] for event in buffalo["timeline_events"]})

    def test_all_matchups_appear_once_across_head_to_head_pairs(self) -> None:
        matchup_ids = [
            game["matchup_id"]
            for pair in self.payloads["head_to_head"]["pairs"]
            for game in pair["all_meetings"]
        ]
        self.assertEqual(446, len(matchup_ids))
        self.assertEqual(446, len(set(matchup_ids)))

    def test_highest_losing_and_lowest_winning_scores(self) -> None:
        scores = self.payloads["weekly_scores"]
        self.assertEqual((173.82, "van-cortlant-rangers"), (scores["highest_losing_scores"][0]["score"], scores["highest_losing_scores"][0]["franchise_id"]))
        self.assertEqual((74.64, "new-jersey-giants"), (scores["lowest_winning_scores"][0]["score"], scores["lowest_winning_scores"][0]["franchise_id"]))
        self.assertEqual(25, len(scores["highest_team_scores"]))
        self.assertEqual(25, len(scores["lowest_team_scores"]))

    def test_championship_aggregation(self) -> None:
        championships = self.payloads["championships"]
        self.assertEqual([2025, 2024, 2023, 2022, 2021], [row["season"] for row in championships["championships"]])
        greendale = next(row for row in championships["leaderboards"]["most_championships"] if row["franchise_id"] == "greendale-human-beings")
        self.assertEqual((2, 2), (greendale["championships"], greendale["appearances"]))

    def test_season_comparison_records(self) -> None:
        comparisons = self.payloads["season_leaders"]["comparisons"]
        self.assertEqual((2023, "albany-kneelers"), (comparisons["best_single_season_records"][0]["season"], comparisons["best_single_season_records"][0]["franchise_id"]))
        self.assertEqual(2022, comparisons["most_dominant_champions"][0]["season"])
        self.assertEqual(2023, comparisons["closest_championships"][0]["season"])

    def test_record_watch_thresholds_match_rankings(self) -> None:
        thresholds = self.payloads["record_thresholds"]["thresholds"]
        scores = self.payloads["weekly_scores"]
        wins = self.payloads["biggest_wins"]
        self.assertEqual(scores["highest_team_scores"][0]["score"], thresholds["highest_weekly_score"])
        self.assertEqual(scores["highest_team_scores"][9]["score"], thresholds["tenth_highest_weekly_score"])
        self.assertEqual(scores["highest_team_scores"][24]["score"], thresholds["twenty_fifth_highest_weekly_score"])
        self.assertEqual(wins["overall"][9]["margin"], thresholds["tenth_largest_margin"])
        self.assertFalse(self.payloads["record_thresholds"]["live_data_dependency"])

    def test_championship_appearance_streak_is_omitted_when_not_meaningful(self) -> None:
        self.assertEqual([], self.payloads["streaks"]["championship_appearance_streaks"])

    def test_canonical_championship_is_not_duplicated_by_archive_fallback(self) -> None:
        facts = metrics.championship_facts()
        self.assertEqual([2021, 2022, 2023, 2024, 2025], [item["season"] for item in facts])
        self.assertEqual(2, sum(item["champion_franchise_id"] == "greendale-human-beings" for item in facts))
        self.assertEqual(
            3,
            sum(
                "albany-kneelers" in (item["champion_franchise_id"], item["runner_up_franchise_id"])
                for item in facts
            ),
        )

    def test_duplicate_matchup_ids_are_rejected(self) -> None:
        with mock.patch.object(metrics, "WEEKLY_YEARS", [2022, 2022]):
            with self.assertRaisesRegex(ValueError, "duplicate matchup_id"):
                metrics.load_weekly_games()

    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(metrics.build_payloads(), copy.deepcopy(self.payloads))


if __name__ == "__main__":
    unittest.main()
