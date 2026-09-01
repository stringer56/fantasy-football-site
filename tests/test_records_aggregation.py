from __future__ import annotations

import copy
import unittest

from scripts import build_records


class RecordsAggregationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seasons = build_records.load_yaml("seasons.yml")
        cls.champions = build_records.load_yaml("champions.yml")
        cls.playoffs = build_records.load_yaml("playoffs.yml")
        cls.franchises = build_records.load_yaml("franchises.yml")
        cls.config = build_records.load_yaml("records.yml")
        cls.identities = build_records.franchise_index(cls.franchises["franchises"])

    def test_cumulative_wins_and_losses(self) -> None:
        entries, _ = build_records.build_career_totals(
            self.seasons["seasons"], self.champions["champions"], self.identities
        )
        albany = next(item for item in entries if item["franchise_id"] == "albany-kneelers")
        self.assertEqual((albany["wins"], albany["losses"], albany["ties"]), (35, 19, 0))

    def test_win_percentage_accounts_for_ties(self) -> None:
        self.assertEqual(build_records.calculate_win_pct(4, 5, 1), 0.45)
        self.assertIsNone(build_records.calculate_win_pct(0, 0, 0))

    def test_championship_counts(self) -> None:
        titles, _ = build_records.build_championship_leaderboards(
            self.champions["champions"], self.identities
        )
        self.assertEqual(len(titles), 4)
        self.assertTrue(all(item["rank"] == 1 and item["championships"] == 1 for item in titles))

    def test_finals_appearance_counts(self) -> None:
        _, finals = build_records.build_championship_leaderboards(
            self.champions["champions"], self.identities
        )
        leaders = {item["franchise_id"]: item["finals_appearances"] for item in finals}
        self.assertEqual(leaders["albany-kneelers"], 2)
        self.assertEqual(leaders["turnbull-acs"], 2)

    def test_single_season_points_for_record(self) -> None:
        _, scoring = build_records.build_season_records(self.seasons["seasons"], self.identities)
        highest = next(item for item in scoring if item["record_id"] == "highest_points_for")
        self.assertEqual(highest["holders"][0]["value"], 1935.92)
        self.assertEqual(highest["holders"][0]["franchise_id"], "ayahuasca-rush")

    def test_tied_records_use_competition_ranks(self) -> None:
        entries = build_records.rank_entries(
            [
                {"display_name": "Alpha", "value": 5},
                {"display_name": "Beta", "value": 5},
                {"display_name": "Gamma", "value": 3},
            ],
            lambda item: item["value"],
        )
        self.assertEqual([item["rank"] for item in entries], [1, 1, 3])

    def test_unresolved_standings_rows_are_excluded(self) -> None:
        entries, unresolved = build_records.build_career_totals(
            self.seasons["seasons"], self.champions["champions"], self.identities
        )
        self.assertEqual(unresolved, 5)
        self.assertNotIn(None, {item["franchise_id"] for item in entries})

    def test_missing_points_are_not_converted_to_zero(self) -> None:
        seasons = copy.deepcopy(self.seasons["seasons"])
        seasons[0]["standings"][0]["points_for"] = None
        seasons[0]["standings"][0]["points_against"] = None
        entries, _ = build_records.build_career_totals(seasons, self.champions["champions"], self.identities)
        turnbull = next(item for item in entries if item["franchise_id"] == "turnbull-acs")
        self.assertEqual(turnbull["points_for"], 4703.42)
        self.assertEqual(turnbull["points_against"], 4520.68)

    def test_missing_playoff_scores_do_not_prevent_verified_results(self) -> None:
        entries, unresolved = build_records.build_playoff_results(self.playoffs["playoffs"], self.identities)
        greendale = next(item for item in entries if item["franchise_id"] == "greendale-human-beings")
        self.assertEqual((greendale["wins"], greendale["losses"], greendale["appearances"]), (3, 3, 4))
        self.assertEqual(unresolved, 1)

    def test_partial_coverage_never_claims_all_time(self) -> None:
        payload = build_records.build_payload(
            self.seasons, self.champions, self.playoffs, self.franchises, self.config
        )
        partial = [
            group
            for group in [*payload["leaderboards"].values(), *payload["records"].values()]
            if group["provenance"]["coverage_status"] == "partial"
        ]
        self.assertTrue(partial)
        self.assertTrue(all("all-time" not in str(group).casefold() for group in partial))

    def test_unavailable_categories_and_bench_schema_are_empty(self) -> None:
        payload = build_records.build_payload(
            self.seasons, self.champions, self.playoffs, self.franchises, self.config
        )
        self.assertTrue(all(category["entries"] == [] for category in payload["unavailable_categories"]))
        self.assertEqual(payload["bench_blunders"]["entries"], [])
        self.assertIn("points_missed", payload["bench_blunders"]["required_fields"])


if __name__ == "__main__":
    unittest.main()
