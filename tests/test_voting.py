from __future__ import annotations

import unittest

from scripts import build_picks_leaderboard, build_power_rankings, import_vote_results, voting_common


class VotingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.franchises = [
            {"franchise_id": "alpha", "slug": "alpha", "name": "Alpha", "status": "active", "branding": {"identity_image": "/alpha.jpg"}},
            {"franchise_id": "beta", "slug": "beta", "name": "Beta", "status": "active", "branding": {"identity_image": "/beta.jpg"}},
            {"franchise_id": "gamma", "slug": "gamma", "name": "Gamma", "status": "active", "branding": {"identity_image": "/gamma.jpg"}},
        ]
        self.owners = {
            "owner-a": {"owner_id": "owner-a", "display_name": "Alex"},
            "owner-b": {"owner_id": "owner-b", "display_name": "Blair"},
        }
        self.matchups = [
            {
                "matchup_id": "2026-week-01-alpha-vs-beta",
                "season": 2026,
                "week": 1,
                "status": "postevent",
                "participants": [
                    {"franchise_id": "alpha", "display_name": "Alpha"},
                    {"franchise_id": "beta", "display_name": "Beta"},
                ],
                "winner_franchise_id": "alpha",
                "winner_status": "verified",
            }
        ]

    def power_ballot(self, owner: str, submitted: str, rankings: list[str]) -> dict:
        return {"owner_id": owner, "submitted_at": submitted, "rankings": rankings}

    def pick_ballot(self, owner: str, submitted: str, franchise: str) -> dict:
        return {
            "owner_id": owner,
            "submitted_at": submitted,
            "picks": [{"matchup_id": self.matchups[0]["matchup_id"], "franchise_id": franchise}],
        }

    def test_power_ranking_points_and_first_place_votes(self) -> None:
        ballots = [
            self.power_ballot("owner-a", "2026-09-01T10:00:00-04:00", ["alpha", "beta", "gamma"]),
            self.power_ballot("owner-b", "2026-09-01T11:00:00-04:00", ["beta", "alpha", "gamma"]),
        ]
        rankings, accepted, rejected = build_power_rankings.aggregate_rankings(ballots, self.franchises, self.owners)
        alpha = next(item for item in rankings if item["franchise_id"] == "alpha")
        beta = next(item for item in rankings if item["franchise_id"] == "beta")
        self.assertEqual((accepted, rejected), (2, 0))
        self.assertEqual((alpha["total_points"], beta["total_points"]), (5, 5))
        self.assertEqual((alpha["first_place_votes"], beta["first_place_votes"]), (1, 1))
        self.assertEqual(alpha["average_rank"], 1.5)

    def test_power_ranking_exact_tie_shares_competition_rank(self) -> None:
        franchises = self.franchises[:2]
        ballots = [
            self.power_ballot("owner-a", "2026-09-01T10:00:00Z", ["alpha", "beta"]),
            self.power_ballot("owner-b", "2026-09-01T11:00:00Z", ["beta", "alpha"]),
        ]
        rankings, _, _ = build_power_rankings.aggregate_rankings(ballots, franchises, self.owners)
        self.assertEqual([item["franchise_id"] for item in rankings], ["alpha", "beta"])
        self.assertEqual([item["rank"] for item in rankings], [1, 1])
        self.assertTrue(all(item["is_tied"] for item in rankings))

    def test_duplicate_or_missing_power_team_is_rejected(self) -> None:
        duplicate = self.power_ballot("owner-a", "2026-09-01T10:00:00Z", ["alpha", "alpha", "gamma"])
        missing = self.power_ballot("owner-b", "2026-09-01T11:00:00Z", ["alpha", "beta"])
        rankings, accepted, rejected = build_power_rankings.aggregate_rankings([duplicate, missing], self.franchises, self.owners)
        self.assertEqual((rankings, accepted, rejected), ([], 0, 2))

    def test_latest_valid_power_submission_wins(self) -> None:
        ballots = [
            self.power_ballot("owner-a", "2026-09-01T10:00:00Z", ["alpha", "beta", "gamma"]),
            self.power_ballot("owner-a", "2026-09-01T12:00:00Z", ["gamma", "beta", "alpha"]),
        ]
        rankings, accepted, rejected = build_power_rankings.aggregate_rankings(ballots, self.franchises, self.owners)
        self.assertEqual((accepted, rejected), (1, 0))
        self.assertEqual(rankings[0]["franchise_id"], "gamma")

        output = build_power_rankings.build_output(
            {"ballots": ballots},
            {"schema_version": 1, "franchises": self.franchises},
            {"schema_version": 1, "owners": [{**value, "active": True} for value in self.owners.values()]},
        )
        self.assertEqual(output["source"]["superseded_ballots"], 1)

    def test_matchup_pick_rejects_unknown_matchup_and_nonparticipant(self) -> None:
        unknown = {"owner_id": "owner-a", "submitted_at": "2026-09-01T10:00:00Z", "picks": [{"matchup_id": "unknown", "franchise_id": "alpha"}]}
        outsider = self.pick_ballot("owner-b", "2026-09-01T11:00:00Z", "gamma")
        week, accepted, rejected = build_picks_leaderboard.aggregate_week([unknown, outsider], self.matchups, self.owners)
        self.assertEqual((accepted, rejected), (0, 2))
        self.assertEqual(week["manager_results"], [])

    def test_matchup_pick_requires_the_complete_weekly_slate(self) -> None:
        second = {
            **self.matchups[0],
            "matchup_id": "2026-week-01-beta-vs-gamma",
            "participants": [
                {"franchise_id": "beta", "display_name": "Beta"},
                {"franchise_id": "gamma", "display_name": "Gamma"},
            ],
        }
        week, accepted, rejected = build_picks_leaderboard.aggregate_week(
            [self.pick_ballot("owner-a", "2026-09-01T10:00:00Z", "alpha")],
            [*self.matchups, second],
            self.owners,
        )
        self.assertEqual((accepted, rejected), (0, 1))
        self.assertEqual(week["manager_results"], [])

    def test_pick_percentages_remain_hidden_until_publication(self) -> None:
        ballot = self.pick_ballot("owner-a", "2026-09-01T10:00:00Z", "alpha")
        hidden, _, _ = build_picks_leaderboard.aggregate_week(
            [ballot], self.matchups, self.owners, results_visible=False
        )
        visible, _, _ = build_picks_leaderboard.aggregate_week(
            [ballot], self.matchups, self.owners, results_visible=True
        )
        self.assertEqual(hidden["matchups"][0]["pick_results"], [])
        self.assertEqual(visible["matchups"][0]["pick_results"][0]["percentage"], 1.0)

    def test_matchup_pick_totals_and_accuracy(self) -> None:
        ballots = [
            self.pick_ballot("owner-a", "2026-09-01T10:00:00Z", "alpha"),
            self.pick_ballot("owner-b", "2026-09-01T11:00:00Z", "beta"),
        ]
        week, accepted, rejected = build_picks_leaderboard.aggregate_week(ballots, self.matchups, self.owners, results_visible=True)
        results = {item["owner_id"]: item for item in week["manager_results"]}
        self.assertEqual((accepted, rejected), (2, 0))
        self.assertEqual((results["owner-a"]["correct"], results["owner-a"]["accuracy"]), (1, 1.0))
        self.assertEqual((results["owner-b"]["incorrect"], results["owner-b"]["accuracy"]), (1, 0.0))
        percentages = {item["franchise_id"]: item["percentage"] for item in week["matchups"][0]["pick_results"]}
        self.assertEqual(percentages, {"alpha": 0.5, "beta": 0.5})

    def test_picks_leaderboard_accumulates_verified_results(self) -> None:
        week_one, _, _ = build_picks_leaderboard.aggregate_week(
            [self.pick_ballot("owner-a", "2026-09-01T10:00:00Z", "alpha")], self.matchups, self.owners
        )
        week_two = {
            "season": 2026,
            "week": 2,
            "matchups": [],
            "manager_results": [
                {"owner_id": "owner-a", "correct": 0, "incorrect": 1, "no_contests": 0, "total_picks": 1, "weekly_win": False},
                {"owner_id": "owner-b", "correct": 1, "incorrect": 0, "no_contests": 0, "total_picks": 1, "weekly_win": True},
            ],
        }
        leaderboard = build_picks_leaderboard.build_leaderboard([week_one, week_two], self.owners)
        alex = next(item for item in leaderboard if item["owner_id"] == "owner-a")
        self.assertEqual((alex["correct"], alex["incorrect"], alex["total_picks"], alex["accuracy"]), (1, 1, 2, 0.5))
        self.assertEqual(leaderboard[0]["display_name"], "Blair")

    def test_latest_valid_matchup_submission_wins(self) -> None:
        ballots = [
            self.pick_ballot("owner-a", "2026-09-01T10:00:00Z", "beta"),
            self.pick_ballot("owner-a", "2026-09-01T12:00:00Z", "alpha"),
        ]
        week, accepted, _ = build_picks_leaderboard.aggregate_week(ballots, self.matchups, self.owners)
        self.assertEqual(accepted, 1)
        self.assertEqual(week["manager_results"][0]["correct"], 1)

    def test_late_submission_does_not_replace_earlier_valid_ballot(self) -> None:
        ballots = [
            self.pick_ballot("owner-a", "2026-09-01T10:00:00Z", "alpha"),
            self.pick_ballot("owner-a", "2026-09-01T13:00:00Z", "beta"),
        ]
        week, accepted, rejected = build_picks_leaderboard.aggregate_week(
            ballots, self.matchups, self.owners, deadline="2026-09-01T12:00:00Z"
        )
        self.assertEqual((accepted, rejected), (1, 1))
        self.assertEqual(week["manager_results"][0]["correct"], 1)

    def test_general_vote_aggregates_without_voter_identity(self) -> None:
        poll = {
            "vote_id": "award-1", "season": 2026, "title": "Award", "description": "Choose",
            "type": "award", "status": "closed", "open_date": "2026-09-01T00:00:00Z",
            "close_date": "2026-09-02T00:00:00Z", "options": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
            "results_visibility": "public", "anonymous_or_named": "anonymous", "form_url": None,
            "embed_url": None, "result_summary": None, "results_source": "sanitized", "notes": [],
        }
        rows = [
            {"vote_id": "award-1", "owner_id": "owner-a", "submitted_at": "2026-09-01T10:00:00Z", "option_id": "a"},
            {"vote_id": "award-1", "owner_id": "owner-b", "submitted_at": "2026-09-01T11:00:00Z", "option_id": "b"},
        ]
        result, accepted, rejected = import_vote_results.aggregate_poll(poll, rows, set(self.owners))
        self.assertEqual((accepted, rejected, result["ballots_counted"]), (2, 0, 2))
        self.assertNotIn("owner_id", str(result))

    def test_private_fields_are_rejected(self) -> None:
        for field in voting_common.FORBIDDEN_VOTE_KEYS:
            with self.assertRaises(voting_common.BallotError):
                voting_common.reject_private_fields({field: "private"})

    def test_malformed_rejected_row_does_not_break_generation_provenance(self) -> None:
        imported = {
            "ballots": [
                self.power_ballot("owner-a", "2026-09-01T10:00:00Z", ["alpha", "beta", "gamma"]),
                self.power_ballot("unknown", "not-a-time", ["alpha", "beta", "gamma"]),
            ]
        }
        output = build_power_rankings.build_output(
            imported,
            {"schema_version": 1, "franchises": self.franchises},
            {"schema_version": 1, "owners": [{**value, "active": True} for value in self.owners.values()]},
        )
        self.assertEqual(output["generated_at"], "2026-09-01T10:00:00+00:00")
        self.assertEqual(output["source"]["rejected_ballots"], 1)

    def test_empty_and_stale_season_outputs_publish_no_fake_data(self) -> None:
        franchises_data = {"schema_version": 1, "franchises": self.franchises}
        owners_data = {"schema_version": 1, "owners": [{**value, "active": True} for value in self.owners.values()]}
        rankings = build_power_rankings.build_output(None, franchises_data, owners_data)
        picks = build_picks_leaderboard.build_output(
            None,
            {"schema_version": 1, "week": 16, "matchups": []},
            {"schema_version": 1, "season": 2025, "status": "ready"},
            {"schema_version": 1, "current_season": 2026},
            franchises_data,
            owners_data,
        )
        self.assertEqual(rankings["rankings"], [])
        self.assertEqual(rankings["source"]["coverage_status"], "unavailable")
        self.assertIsNone(picks["current_week"])
        self.assertEqual(picks["source"]["matchup_status"], "stale_yahoo_data")


if __name__ == "__main__":
    unittest.main()
