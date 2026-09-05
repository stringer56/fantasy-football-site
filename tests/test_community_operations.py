from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_live_season, build_picks_leaderboard, build_power_rankings, community_week, import_vote_results, voting_common


FIXTURE = Path(__file__).parent / "fixtures" / "community" / "dry_run.json"


class CommunityOperationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def setUp(self) -> None:
        f = self.fixture
        self.owners = {
            owner: {"owner_id": owner, "display_name": owner.title()}
            for owner in f["owners"]
        }
        self.franchises = [
            {"franchise_id": team, "slug": team, "name": team.title(), "status": "active", "branding": {"identity_image": "/test.png"}}
            for team in f["franchises"]
        ]
        self.matchup = {
            "matchup_id": f["matchup_id"], "season": 2099, "week": 1,
            "status": "midevent", "winner_franchise_id": None, "winner_status": "pending",
            "participants": [{"franchise_id": team, "display_name": team.title()} for team in f["franchises"]],
        }

    def power_ballot(self, owner: str, rankings: list[str], time: str = "2099-09-01T10:00:00-04:00") -> dict:
        return {"owner_id": owner, "submitted_at": time, "season": 2099, "week": 1, "rankings": rankings}

    def pick_ballot(self, owner: str, matchup: str | None = None, choice: str | None = None, time: str = "2099-09-01T10:00:00-04:00") -> dict:
        return {"owner_id": owner, "submitted_at": time, "season": 2099, "week": 1, "picks": [{"matchup_id": matchup or self.matchup["matchup_id"], "franchise_id": choice or "test-alpha"}]}

    def test_power_dry_run_complete_tie_and_invalid_scenarios(self) -> None:
        complete = self.fixture["power_rankings"]["complete"]
        ballots = [self.power_ballot("test-owner-a", complete), self.power_ballot("test-owner-b", list(reversed(complete)))]
        rankings, accepted, rejected = build_power_rankings.aggregate_rankings(ballots, self.franchises, self.owners)
        self.assertEqual((accepted, rejected), (2, 0))
        self.assertEqual([row["rank"] for row in rankings], [1, 1])
        for key in ("duplicate_rank", "missing_franchise", "invalid_franchise"):
            result = build_power_rankings.aggregate_rankings([self.power_ballot("test-owner-a", self.fixture["power_rankings"][key])], self.franchises, self.owners)
            self.assertEqual(result[1:], (0, 1))
        selected, rejected_rows, _ = voting_common.select_latest_valid_report(
            [self.power_ballot("test-unknown", complete)], set(self.owners),
            lambda row: build_power_rankings.validate_ballot(row, {team["franchise_id"] for team in self.franchises}),
        )
        self.assertFalse(selected)
        self.assertIn("unknown owner_id", rejected_rows[0]["reason"])

    def test_pick_dry_run_complete_partial_duplicate_invalid_and_post_lock(self) -> None:
        valid = self.pick_ballot("test-owner-a")
        week, accepted, rejected = build_picks_leaderboard.aggregate_week([valid], [self.matchup], self.owners)
        self.assertEqual((accepted, rejected), (1, 0))
        self.assertEqual(len(week["manager_results"]), 1)
        for ballot in (
            {**valid, "picks": []},
            {**valid, "picks": valid["picks"] * 2},
            self.pick_ballot("test-owner-a", self.fixture["pickem"]["unknown_matchup"]),
            self.pick_ballot("test-owner-a", choice=self.fixture["pickem"]["invalid_choice"]),
        ):
            self.assertEqual(build_picks_leaderboard.aggregate_week([ballot], [self.matchup], self.owners)[1:], (0, 1))
        self.assertEqual(build_picks_leaderboard.aggregate_week([self.pick_ballot("test-owner-a", time="2099-09-01T13:00:00-04:00")], [self.matchup], self.owners, deadline="2099-09-01T12:00:00-04:00")[1:], (0, 1))

    def test_verified_pick_scoring_and_private_prelock_aggregate(self) -> None:
        hidden, _, _ = build_picks_leaderboard.aggregate_week([self.pick_ballot("test-owner-a")], [self.matchup], self.owners, results_visible=False)
        self.assertEqual(hidden["matchups"][0]["pick_results"], [])
        final_matchup = {**self.matchup, "status": "postevent", "winner_franchise_id": "test-alpha", "winner_status": "verified"}
        graded, _, _ = build_picks_leaderboard.aggregate_week([self.pick_ballot("test-owner-a")], [final_matchup], self.owners, results_visible=True)
        self.assertEqual(graded["manager_results"][0]["correct"], 1)

    def test_pick_archive_requires_explicit_audited_override(self) -> None:
        week, _, _ = build_picks_leaderboard.aggregate_week([self.pick_ballot("test-owner-a")], [self.matchup], self.owners, results_visible=True)
        week.update({"lock_at": "2099-09-01T12:00:00-04:00", "results_visibility": "public_after_lock", "manager_picks_visibility": "private"})
        archived = build_picks_leaderboard.finalized_week_payload({"source": {"accepted_ballots": 1}, "current_week": week}, generated_at="2099-09-01T12:01:00-04:00", state="locked")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = build_picks_leaderboard.persist_finalized_week(archived, root)
            changed = copy.deepcopy(archived)
            changed["ballots_counted"] = 2
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                build_picks_leaderboard.persist_finalized_week(changed, root)
            with self.assertRaisesRegex(ValueError, "override_reason"):
                build_picks_leaderboard.persist_finalized_week(changed, root, override=True)
            build_picks_leaderboard.persist_finalized_week(changed, root, override=True, override_reason="Commissioner reviewed corrected export")
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["audit"][-1]["action"], "override")
            self.assertTrue(saved["audit"][-1]["previous_fingerprint"])

    def test_power_archive_requires_explicit_audited_override_and_week_one_has_no_movement(self) -> None:
        ballots = [self.power_ballot("test-owner-a", self.fixture["power_rankings"]["complete"])]
        payload = build_power_rankings.build_output({"season": 2099, "week": 1, "ballots": ballots}, {"schema_version": 1, "franchises": self.franchises}, {"schema_version": 1, "owners": [{**owner, "active": True} for owner in self.owners.values()]})
        self.assertTrue(all(row["previous_rank"] is None and row["movement"] is None for row in payload["rankings"]))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = build_power_rankings.persist_finalized_week(payload, root, published_at="2099-09-01T12:00:00-04:00")
            changed = copy.deepcopy(payload)
            changed["rankings"][0]["total_points"] = 99
            changed["rankings"][0]["ranking_points"] = 99
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                build_power_rankings.persist_finalized_week(changed, root, published_at="2099-09-01T12:01:00-04:00")
            with self.assertRaisesRegex(ValueError, "override_reason"):
                build_power_rankings.persist_finalized_week(changed, root, override=True, published_at="2099-09-01T12:01:00-04:00")
            build_power_rankings.persist_finalized_week(changed, root, override=True, published_at="2099-09-01T12:01:00-04:00", override_reason="Commissioner reviewed corrected export")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["audit"][-1]["action"], "override")

    def test_leaderboard_uses_shared_rank_for_exact_ties(self) -> None:
        week = {"manager_results": [{"owner_id": owner, "correct": 1, "incorrect": 1, "no_contests": 0, "total_picks": 2, "weekly_win": True} for owner in self.owners]}
        leaderboard = build_picks_leaderboard.build_leaderboard([week], self.owners)
        self.assertEqual([row["rank"] for row in leaderboard], [1, 1])
        self.assertTrue(all(row["is_tied"] for row in leaderboard))

    def test_general_vote_valid_invalid_duplicate_closed_and_unknown(self) -> None:
        f = self.fixture["general_vote"]
        poll = {"vote_id": f["poll_id"], "close_date": "2099-09-01T12:00:00-04:00", "options": [{"id": f["valid_option"], "label": "Yes"}]}
        valid = {"vote_id": f["poll_id"], "owner_id": "test-owner-a", "submitted_at": "2099-09-01T10:00:00-04:00", "option_id": f["valid_option"]}
        duplicate = {**valid, "submitted_at": "2099-09-01T11:00:00-04:00"}
        invalid = {**valid, "owner_id": "test-owner-b", "option_id": f["invalid_option"]}
        closed = {**valid, "owner_id": "test-owner-b", "submitted_at": "2099-09-01T13:00:00-04:00"}
        report = import_vote_results.poll_selection_report(poll, [valid, duplicate, invalid, closed], set(self.owners))
        self.assertEqual((len(report["selected"]), len(report["superseded"]), len(report["rejected"])), (1, 1, 2))
        config = {"schema_version": 1, "polls": [{**poll, "season": 2099, "title": "Test", "description": "Test", "type": "award", "status": "open", "open_date": None, "results_visibility": "hidden", "anonymous_or_named": "anonymous", "form_url": None, "embed_url": None}]}
        output = import_vote_results.build_output(config, {"owners": [{**owner, "active": True} for owner in self.owners.values()]}, {"rows": [{**valid, "vote_id": f["unknown_poll"]}]})
        self.assertEqual(output["source"]["rejected_ballots"], 1)

    def test_preview_receipt_contains_no_ballot_and_detects_changed_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "test.csv"
            source.write_text("safe,test\n", encoding="utf-8")
            old_root = voting_common.PRIVATE_STATE_ROOT
            voting_common.PRIVATE_STATE_ROOT = Path(directory) / "state"
            try:
                path = voting_common.write_preview_receipt(kind="pickem", season=2099, week=1, input_path=source, accepted=1, rejected=0, superseded=0, missing=1)
                saved = path.read_text(encoding="utf-8")
                self.assertNotIn("franchise_id", saved)
                self.assertTrue(json.loads(saved)["finalization_permitted"])
            finally:
                voting_common.PRIVATE_STATE_ROOT = old_root

    def test_status_reports_unconfigured_and_configured_forms_without_urls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "_data" / "generated").mkdir(parents=True)
            (root / "_data" / "community.yml").write_text(
                "schema_version: 1\nseason: 2026\npower_rankings:\n  status: upcoming\n  form_url:\npickem:\n  status: open\n  form_url: https://forms.gle/test-public\nleague_votes:\n  status: unconfigured\n  form_url:\n",
                encoding="utf-8",
            )
            (root / "_data" / "votes.yml").write_text("schema_version: 1\npolls: []\n", encoding="utf-8")
            (root / "_data" / "generated" / "matchups.json").write_text('{"week": 1}\n', encoding="utf-8")
            (root / "_data" / "generated" / "manifest.json").write_text('{"status":"ready","season":2026,"source_update_timestamp":"2026-09-01T10:00:00-04:00"}\n', encoding="utf-8")
            status = community_week.build_status(root=root, season=2026, week=1, now=datetime(2026, 9, 1, 15, tzinfo=timezone.utc))
            self.assertFalse(status["features"]["power-rankings"]["form_configured"])
            self.assertTrue(status["features"]["pickem"]["form_configured"])
            self.assertFalse(status["features"]["league-votes"]["form_configured"])
            self.assertEqual(status["yahoo"]["status"], "current")

    def test_malformed_csv_is_loaded_safely_then_rejected(self) -> None:
        imported = voting_common.load_import(Path(__file__).parent / "fixtures" / "community" / "malformed.csv")
        selected, rejected, _ = voting_common.select_latest_valid_report(
            imported["rows"], set(self.owners), lambda row: None
        )
        self.assertFalse(selected)
        self.assertIn("submitted_at must be ISO-8601", rejected[0]["reason"])

    def test_weekly_snapshot_keeps_relevant_public_poll(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            old_generated = build_live_season.GENERATED
            build_live_season.GENERATED = Path(directory)
            try:
                path = build_live_season.persist_week({
                    "schema_version": 1, "season": 2026, "current_week": 1,
                    "data_status": "ready", "active_vote": {"vote_id": "test-public-poll"},
                })
                saved = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(saved["active_vote"]["vote_id"], "test-public-poll")
            finally:
                build_live_season.GENERATED = old_generated


if __name__ == "__main__":
    unittest.main()
