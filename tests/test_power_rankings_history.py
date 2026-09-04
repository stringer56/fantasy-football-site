from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_power_rankings


class PowerRankingsHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.franchises = [
            {
                "franchise_id": f"team-{index:02d}",
                "slug": f"team-{index:02d}",
                "name": f"Team {index:02d}",
                "short_name": f"T{index:02d}",
                "status": "active",
                "branding": {"identity_image": f"/{index}.jpg", "primary_color": "#123456"},
            }
            for index in range(1, 13)
        ]
        self.owners = {
            "owner-1": {"owner_id": "owner-1", "display_name": "Owner One"},
            "owner-2": {"owner_id": "owner-2", "display_name": "Owner Two"},
        }

    def ballot(self, owner: str, submitted: str, order: list[str]) -> dict:
        return {"owner_id": owner, "submitted_at": submitted, "rankings": order}

    def output(self, week: int, order: list[str], previous: dict | None = None) -> dict:
        return build_power_rankings.build_output(
            {"season": 2026, "week": week, "ballots": [self.ballot("owner-1", f"2026-09-{week:02d}T12:00:00Z", order)]},
            {"schema_version": 1, "franchises": self.franchises},
            {"schema_version": 1, "owners": [{**value, "active": True} for value in self.owners.values()]},
            previous=previous,
        )

    def test_twelve_to_one_scoring_average_and_first_place_vote(self) -> None:
        order = [row["franchise_id"] for row in self.franchises]
        rankings, accepted, rejected = build_power_rankings.aggregate_rankings(
            [self.ballot("owner-1", "2026-09-01T12:00:00Z", order)], self.franchises, self.owners
        )
        self.assertEqual((accepted, rejected), (1, 0))
        self.assertEqual(rankings[0]["ranking_points"], 12)
        self.assertEqual(rankings[-1]["ranking_points"], 1)
        self.assertEqual(rankings[0]["average_rank"], 1.0)
        self.assertEqual(rankings[0]["first_place_votes"], 1)

    def test_previous_rank_movement_and_history_facts(self) -> None:
        order = [row["franchise_id"] for row in self.franchises]
        first = self.output(1, order)
        second = self.output(2, list(reversed(order)), previous=first)
        top = second["rankings"][0]
        bottom = second["rankings"][-1]
        self.assertEqual((top["previous_rank"], top["movement"]), (12, 11))
        self.assertEqual((bottom["previous_rank"], bottom["movement"]), (1, -11))
        weeks = [build_power_rankings.finalized_week_payload(first), build_power_rankings.finalized_week_payload(second)]
        history = build_power_rankings.build_history(2026, self.franchises, weeks)
        facts = {row["metric"]: row for row in history["season_facts"]}
        self.assertEqual(facts["biggest_rise"]["value"], 11)
        self.assertEqual(facts["biggest_fall"]["value"], 11)
        self.assertEqual(history["finalized_weeks"], [1, 2])

    def test_duplicate_manager_submission_counts_latest_once(self) -> None:
        order = [row["franchise_id"] for row in self.franchises]
        ballots = [
            self.ballot("owner-1", "2026-09-01T10:00:00Z", order),
            self.ballot("owner-1", "2026-09-01T11:00:00Z", list(reversed(order))),
        ]
        rankings, accepted, rejected = build_power_rankings.aggregate_rankings(ballots, self.franchises, self.owners)
        self.assertEqual((accepted, rejected), (1, 0))
        self.assertEqual(rankings[0]["franchise_id"], "team-12")

    def test_weekly_persistence_is_immutable_and_ordered_with_gap(self) -> None:
        order = [row["franchise_id"] for row in self.franchises]
        first = self.output(1, order)
        third = self.output(3, list(reversed(order)), previous=first)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = build_power_rankings.persist_finalized_week(first, root)
            build_power_rankings.persist_finalized_week(third, root)
            self.assertEqual(path.name, "week-01.json")
            weeks = build_power_rankings.load_finalized_weeks(2026, root)
            history = build_power_rankings.build_history(2026, self.franchises, weeks)
            self.assertEqual(history["finalized_weeks"], [1, 3])
            self.assertEqual(history["missing_weeks"], [2])
            changed = copy.deepcopy(first)
            changed["rankings"][0]["ranking_points"] = 999
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                build_power_rankings.persist_finalized_week(changed, root)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["week"], 1)


if __name__ == "__main__":
    unittest.main()
