from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_picks_leaderboard, import_vote_results, voting_common


class CommunityWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.owners = {
            "owner-a": {"owner_id": "owner-a", "display_name": "Alex"},
            "owner-b": {"owner_id": "owner-b", "display_name": "Blair"},
        }
        self.matchup = {
            "matchup_id": "2026-week-01-alpha-vs-beta",
            "season": 2026,
            "week": 1,
            "status": "midevent",
            "participants": [
                {"franchise_id": "beta", "display_name": "Beta"},
                {"franchise_id": "alpha", "display_name": "Alpha"},
            ],
            "winner_franchise_id": None,
            "winner_status": "pending",
        }

    def ballot(self, owner: str, submitted: str, choice: str = "alpha") -> dict:
        return {
            "owner_id": owner,
            "submitted_at": submitted,
            "season": 2026,
            "week": 1,
            "picks": [{"matchup_id": self.matchup["matchup_id"], "franchise_id": choice}],
        }

    def test_preview_report_preserves_rejection_and_superseded_row_numbers(self) -> None:
        selected, rejected, superseded = voting_common.select_latest_valid_report(
            [
                self.ballot("owner-a", "2026-09-01T10:00:00Z"),
                self.ballot("owner-a", "2026-09-01T11:00:00Z", "beta"),
                self.ballot("unknown", "2026-09-01T12:00:00Z"),
            ],
            set(self.owners),
            lambda row: build_picks_leaderboard.validate_pick_ballot(
                row, {self.matchup["matchup_id"]: self.matchup}
            ),
        )
        self.assertEqual(selected[0]["picks"][0]["franchise_id"], "beta")
        self.assertEqual(superseded, [{"row": 2, "owner_id": "owner-a"}])
        self.assertEqual(rejected[0]["row"], 4)
        self.assertIn("unknown owner_id", rejected[0]["reason"])

    def test_stable_matchup_id_is_independent_of_yahoo_team_order(self) -> None:
        franchises = {
            "franchises": [
                {"franchise_id": "alpha", "slug": "alpha", "name": "Alpha", "branding": {}, "yahoo": {"team_keys": {"2026": "470.l.1.t.1"}}},
                {"franchise_id": "beta", "slug": "beta", "name": "Beta", "branding": {}, "yahoo": {"team_keys": {"2026": "470.l.1.t.2"}}},
            ]
        }
        source = {
            "week": 1,
            "matchups": [{"status": "midevent", "teams": [{"team_key": "470.l.1.t.2"}, {"team_key": "470.l.1.t.1"}]}],
        }
        result, status = build_picks_leaderboard.canonical_matchups_from_yahoo(
            source, {"status": "ready", "season": 2026}, 2026, franchises
        )
        self.assertEqual(status, "ready")
        self.assertEqual(result[0]["matchup_id"], "2026-week-01-alpha-vs-beta")

    def test_pick_archive_locks_selections_then_allows_verified_scoring_once(self) -> None:
        pending, accepted, _ = build_picks_leaderboard.aggregate_week(
            [self.ballot("owner-a", "2026-09-01T10:00:00Z")],
            [self.matchup],
            self.owners,
            results_visible=True,
        )
        pending.update({"lock_at": "2026-09-01T12:00:00Z", "results_visibility": "public_after_lock", "manager_picks_visibility": "private"})
        payload = {"source": {"accepted_ballots": accepted}, "current_week": pending}
        locked = build_picks_leaderboard.finalized_week_payload(payload, generated_at="2026-09-01T12:00:00Z", state="locked")

        final_matchup = {**self.matchup, "status": "postevent", "winner_franchise_id": "alpha", "winner_status": "verified"}
        final_week, _, _ = build_picks_leaderboard.aggregate_week(
            [self.ballot("owner-a", "2026-09-01T10:00:00Z")],
            [final_matchup],
            self.owners,
            results_visible=True,
        )
        final_week.update({"lock_at": pending["lock_at"], "results_visibility": "public_after_lock", "manager_picks_visibility": "private"})
        final = build_picks_leaderboard.finalized_week_payload(
            {"source": {"accepted_ballots": 1}, "current_week": final_week},
            generated_at="2026-09-02T12:00:00Z",
            state="final",
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = build_picks_leaderboard.persist_finalized_week(locked, root)
            build_picks_leaderboard.persist_finalized_week(final, root)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["state"], "final")
            self.assertEqual(saved["weekly_winners"][0]["display_name"], "Alex")
            changed = copy.deepcopy(final)
            changed["matchups"][0]["pick_results"][0]["vote_count"] = 99
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                build_picks_leaderboard.persist_finalized_week(changed, root)

    def test_after_close_general_vote_visibility(self) -> None:
        poll = {
            "vote_id": "rule-1", "season": 2026, "title": "Rule", "description": "Choose",
            "type": "league_rule", "status": "open", "open_date": "2026-09-01T00:00:00Z",
            "close_date": "2026-09-02T00:00:00Z", "options": [{"id": "yes", "label": "Yes"}],
            "results_visibility": "after_close", "anonymous_or_named": "anonymous", "form_url": None,
            "embed_url": None, "result_summary": None, "results_source": "sanitized", "notes": [],
        }
        rows = [{"vote_id": "rule-1", "owner_id": "owner-a", "submitted_at": "2026-09-01T10:00:00Z", "option_id": "yes"}]
        hidden, _, _ = import_vote_results.aggregate_poll(poll, rows, set(self.owners))
        closed, _, _ = import_vote_results.aggregate_poll({**poll, "status": "closed"}, rows, set(self.owners))
        self.assertEqual(hidden["results"], [])
        self.assertEqual(closed["results"][0]["vote_count"], 1)

    def test_general_vote_preview_reports_duplicates_and_missing_managers(self) -> None:
        poll = {
            "vote_id": "award-1", "close_date": "2026-09-02T00:00:00Z",
            "options": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
        }
        rows = [
            {"vote_id": "award-1", "owner_id": "owner-a", "submitted_at": "2026-09-01T10:00:00Z", "option_id": "a"},
            {"vote_id": "award-1", "owner_id": "owner-a", "submitted_at": "2026-09-01T11:00:00Z", "option_id": "b"},
        ]
        report = import_vote_results.poll_selection_report(poll, rows, set(self.owners))
        self.assertEqual(report["selected"][0]["option_id"], "b")
        self.assertEqual(len(report["superseded"]), 1)
        self.assertEqual(report["missing_owner_ids"], ["owner-b"])


if __name__ == "__main__":
    unittest.main()
