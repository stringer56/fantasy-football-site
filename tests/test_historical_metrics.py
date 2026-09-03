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
    def setUp(self) -> None:
        self.identities = {name: identity(name) for name in ("alpha", "beta", "gamma")}

    def test_head_to_head_aggregation_and_tie(self) -> None:
        games = [game("g1", 2022, 1, "alpha", "beta", 110, 100), game("g2", 2023, 1, "alpha", "beta", 90, 90)]
        pair = metrics.build_head_to_head(games, self.identities)[0]
        self.assertEqual((pair["meetings"], pair["wins_a"], pair["wins_b"], pair["ties"]), (2, 1, 0, 1))
        self.assertEqual((pair["points_a"], pair["points_b"]), (200.0, 190.0))

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

    def test_tie_breaks_win_streak_but_extends_unbeaten_streak(self) -> None:
        sequence = [(2022, 1, "W"), (2022, 2, "T"), (2022, 3, "W")]
        self.assertEqual(1, metrics.best_streak(sequence, {"W"}, cross_season=False)["games"])
        self.assertEqual(3, metrics.best_streak(sequence, {"W", "T"}, cross_season=False)["games"])

    def test_actual_playoff_output_is_independently_classified(self) -> None:
        payload = metrics.build_payloads()["playoffs"]
        self.assertEqual(17, len(payload["games"]))
        self.assertTrue(all(item["game_type"] == "championship_playoff" and item["playoff_round"] for item in payload["games"]))

    def test_weekly_matchups_are_fully_resolved_after_confirmed_mappings(self) -> None:
        manifest = metrics.build_payloads()["manifest"]
        self.assertEqual(0, manifest["counts"]["excluded_unresolved_matchups"])
        self.assertEqual(78, manifest["counts"]["head_to_head_pairs"])

    def test_2021_is_excluded_from_every_weekly_output(self) -> None:
        payloads = metrics.build_payloads()
        encoded = " ".join(str(payloads[name]) for name in ("head_to_head", "biggest_wins", "closest_games", "weekly_scores", "streaks", "playoffs"))
        self.assertNotIn("'season': 2021", encoded)

    def test_coverage_labels_remain_separate(self) -> None:
        payloads = metrics.build_payloads()
        self.assertEqual("Verified 2021–2025", payloads["franchise_summaries"]["season_level_coverage"]["label"])
        self.assertEqual("Verified 2022–2025", payloads["head_to_head"]["coverage"]["label"])

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
        self.assertEqual(metrics.build_payloads(), copy.deepcopy(metrics.build_payloads()))


if __name__ == "__main__":
    unittest.main()
