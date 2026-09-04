from __future__ import annotations

import copy
import unittest

from scripts import build_recaps


class RecapGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = build_recaps.generate()

    def season_recap(self, year: int) -> dict:
        return next(item for item in self.payload["seasons"] if item["season"] == year)

    def team_recap(self, year: int, name: str) -> dict:
        return next(
            item for item in self.payload["team_recaps"]
            if item["season"] == year and item["historical_team_name"] == name
        )

    def playoff_recap(self, game_id: str) -> dict:
        return next(item for item in self.payload["playoff_recaps"] if item["game_id"] == game_id)

    def championship_recap(self, year: int) -> dict:
        return next(item for item in self.payload["championship_recaps"] if item["season"] == year)

    def numbers(self, year: int) -> dict[str, dict]:
        return {
            item["stat_id"]: item
            for item in self.payload["by_the_numbers"]
            if item["season"] == year
        }

    def test_expected_recap_counts(self) -> None:
        self.assertEqual(len(self.payload["seasons"]), 5)
        self.assertEqual(len(self.payload["team_recaps"]), 58)
        self.assertEqual(len(self.payload["playoff_recaps"]), 28)
        self.assertEqual(len(self.payload["championship_recaps"]), 5)
        self.assertEqual(len(self.payload["by_the_numbers"]), 69)

    def test_2025_complete_weekly_archive_and_narrative(self) -> None:
        recap = self.season_recap(2025)
        weekly = recap["weekly_archive"]
        self.assertEqual(weekly["week_count"], 16)
        self.assertEqual(weekly["matchup_count"], 92)
        self.assertEqual([item["week"] for item in weekly["weeks"]], list(range(1, 17)))
        self.assertGreaterEqual(len(recap["paragraphs"]), 3)
        self.assertLessEqual(len(recap["paragraphs"]), 6)

    def test_2025_verified_weekly_metrics(self) -> None:
        metrics = self.season_recap(2025)["weekly_archive"]["season_metrics"]
        self.assertEqual((metrics["highest_weekly_score"]["name"], metrics["highest_weekly_score"]["score"]), ("Greendale Human Beings", 178.02))
        self.assertEqual(metrics["biggest_victory"]["margin"], 92.24)
        self.assertEqual(metrics["closest_game"]["margin"], 0.20)
        self.assertEqual(metrics["highest_combined_score"]["combined_score"], 307.78)

    def test_2024_complete_weekly_archive_and_narrative(self) -> None:
        recap = self.season_recap(2024)
        weekly = recap["weekly_archive"]
        self.assertEqual(weekly["week_count"], 16)
        self.assertEqual(weekly["matchup_count"], 92)
        self.assertEqual([item["week"] for item in weekly["weeks"]], list(range(1, 17)))
        self.assertIn("Turnbull AC's and Ayahuasca Rush earning the two first-round byes", recap["generated_text"])

    def test_all_2025_franchises_have_weekly_mini_recap_metrics(self) -> None:
        recaps = [item for item in self.payload["team_recaps"] if item["season"] == 2025]
        self.assertEqual(len(recaps), 12)
        self.assertTrue(all(item["weekly_metrics"] for item in recaps))

    def test_season_champion_and_runner_up_are_correct(self) -> None:
        recap = self.season_recap(2024)
        result = next(fact for fact in recap["facts_used"] if fact["fact_type"] == "championship_result")
        self.assertEqual(result["champion_franchise_id"], "turnbull-acs")
        self.assertEqual(result["runner_up_franchise_id"], "crazy-wazs-team")
        self.assertIn("Turnbull AC's defeating Chris's Crazy Team", recap["generated_text"])

    def test_verified_record_reference_and_partial_wording(self) -> None:
        recap = self.season_recap(2022)
        record = next(fact for fact in recap["facts_used"] if fact["fact_type"] == "archive_record")
        self.assertEqual(record["record_id"], "highest_points_for")
        self.assertEqual(record["value"], 1935.92)
        self.assertEqual(record["coverage_status"], "partial")
        self.assertIn("highest verified total in the 2021–2025 archive", recap["generated_text"])
        self.assertIn("category remains partial", recap["generated_text"])

    def test_team_record_is_inserted_exactly(self) -> None:
        recap = self.team_recap(2022, "THE SAVAGE HUNS")
        self.assertEqual(recap["record"], {"wins": 4, "losses": 9, "ties": 1})
        self.assertIn("4–9–1", recap["generated_text"])

    def test_team_pf_and_pa_are_inserted_exactly(self) -> None:
        recap = self.team_recap(2024, "Maine Moose")
        self.assertEqual((recap["points_for"], recap["points_against"]), (1654.34, 1421.10))
        self.assertIn("1,654.34 points for", recap["generated_text"])
        self.assertIn("1,421.10 points against", recap["generated_text"])

    def test_playoff_winner_is_correct(self) -> None:
        recap = self.playoff_recap("2024-w15-semifinal-1")
        self.assertEqual(recap["winner_display_name"], "Turnbull AC's")
        self.assertEqual(recap["loser_display_name"], "Maine Moose")
        self.assertIn("Turnbull AC's defeated Maine Moose 160.30–106.54", recap["generated_text"])

    def test_championship_score_is_correct_and_recap_is_rich(self) -> None:
        recap = self.championship_recap(2023)
        self.assertEqual((recap["champion_score"], recap["runner_up_score"]), (132.82, 132.74))
        self.assertIn("132.82–132.74", recap["generated_text"])
        self.assertGreaterEqual(len(recap["generated_text"].split()), 100)
        self.assertLessEqual(len(recap["generated_text"].split()), 200)

    def test_missing_playoff_score_is_not_invented(self) -> None:
        recap = self.playoff_recap("2021-sf-1")
        self.assertIsNone(recap["winner_score"])
        self.assertIsNone(recap["loser_score"])
        self.assertIn("does not publish a score", recap["generated_text"])
        self.assertNotRegex(recap["generated_text"], r"\d+\.\d{2}–\d+\.\d{2}")

    def test_commissioner_confirmed_legacy_franchise_is_linked(self) -> None:
        recap = self.team_recap(2021, "The Swagger Daggers")
        self.assertEqual(recap["franchise_id"], "buffalo-bravado")
        self.assertEqual(recap["path"], "/teams/buffalo-bravado/")
        self.assertEqual(recap["mapping_status"], "resolved")
        self.assertNotIn("unresolved_franchise_mapping", recap["warnings"])

    def test_tied_best_records_are_preserved(self) -> None:
        card = self.numbers(2021)["best_record"]
        self.assertIn("Albany Kneelers", card["display_value"])
        self.assertIn("Greendale Human Beings", card["display_value"])
        self.assertIn("10–4–0", card["display_value"])

    def test_missing_pf_removes_relative_scoring_claims(self) -> None:
        seasons = copy.deepcopy(build_recaps.load_yaml("_data/seasons.yml"))
        season = next(item for item in seasons["seasons"] if item["year"] == 2024)
        row = next(item for item in season["standings"] if item["franchise_id"] == "baseball-furies")
        row["points_for"] = None
        payload = build_recaps.generate(seasons_data=seasons)
        recap = next(item for item in payload["seasons"] if item["season"] == 2024)
        stats = {item["stat_id"] for item in payload["by_the_numbers"] if item["season"] == 2024}
        team = next(item for item in payload["team_recaps"] if item["season"] == 2024 and item["franchise_id"] == "baseball-furies")
        self.assertNotIn("led the 12-team field", recap["generated_text"])
        self.assertNotIn("highest_pf", stats)
        self.assertNotIn("lowest_pf", stats)
        self.assertIn("missing_pf_or_pa", team["warnings"])

    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(build_recaps.generate(), build_recaps.generate())

    def test_approved_editorial_override_has_priority_and_survives_regeneration(self) -> None:
        editorial = {
            "schema_version": 1,
            "season_recaps": [{
                "season": 2024,
                "status": "approved",
                "text": "Commissioner-approved season copy based on the verified 2024 results.",
            }],
            "team_recaps": [],
            "playoff_recaps": [],
            "championship_recaps": [],
        }
        first = build_recaps.generate(editorial_data=editorial)
        second = build_recaps.generate(editorial_data=editorial)
        recap = next(item for item in first["seasons"] if item["season"] == 2024)
        self.assertEqual(first, second)
        self.assertEqual(recap["content_source"], "editorial_override")
        self.assertEqual(recap["text"], editorial["season_recaps"][0]["text"])
        self.assertIn("The 2024 Road to Glory season ended", recap["generated_text"])
        self.assertIn("_data/editorial/recaps.yml", recap["source_files"])

    def test_no_unsupported_player_or_editorial_claim(self) -> None:
        prose = " ".join(
            entry["generated_text"]
            for key in ("seasons", "team_recaps", "playoff_recaps", "championship_recaps")
            for entry in self.payload[key]
        ).casefold()
        self.assertNotIn("winning streak", prose)
        self.assertNotIn("losing streak", prose)
        self.assertNotIn("biggest blowout", prose)
        self.assertNotIn("bench blunder", prose)
        self.assertNotIn("injury", prose)
        self.assertNotIn("manager strategy", prose)

    def test_no_external_ai_or_runtime_api_is_required(self) -> None:
        self.assertEqual(self.payload["engine"]["type"], "deterministic_template_rules")
        self.assertFalse(self.payload["engine"]["external_ai_required"])


if __name__ == "__main__":
    unittest.main()
