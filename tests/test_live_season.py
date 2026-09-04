from __future__ import annotations

import unittest

from scripts import build_live_season, validate_live_season, yahoo_live


class LiveSeasonTests(unittest.TestCase):
    @staticmethod
    def team(team_id: int, score: float, projected: float = 100.0) -> dict:
        return {
            "franchise_id": f"team-{team_id}",
            "display_name": f"Team {team_id}",
            "team_key": f"470.l.26455.t.{team_id}",
            "score": score,
            "projected_score": projected,
        }

    def game(self, status: str, score_a: float, score_b: float) -> dict:
        return {
            "matchup_id": "2026-w01-team-1--team-2",
            "week": 1,
            "status": status,
            "teams": [self.team(1, score_a), self.team(2, score_b)],
        }

    def thresholds(self) -> dict:
        return {
            "thresholds": {
                "highest_weekly_score": 237.18,
                "tenth_highest_weekly_score": 173.82,
                "twenty_fifth_highest_weekly_score": 162.2,
                "largest_margin": 113.66,
                "tenth_largest_margin": 74.5,
                "highest_combined_matchup_score": 376.72,
                "highest_losing_score": 173.82,
            },
            "franchises": [],
        }

    def test_current_score_can_trigger_watch_but_projection_cannot_promote(self) -> None:
        live = self.game("live", 150.0, 80.0)
        events = build_live_season.record_watch_events([live], self.thresholds())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["level"], "Record Watch")
        self.assertFalse(events[0]["final"])
        live["teams"][0]["projected_score"] = 300.0
        self.assertNotIn("record", " ".join(event["level"].lower() for event in events if event["final"]))

    def test_only_final_score_promotes_verified_records_and_deduplicates(self) -> None:
        final = self.game("final", 240.0, 180.0)
        events = build_live_season.record_watch_events([final, final], self.thresholds())
        event_ids = [row["event_id"] for row in events]
        self.assertEqual(len(event_ids), len(set(event_ids)))
        self.assertTrue(all(row["final"] for row in events))
        self.assertTrue(any(row["level"] == "New verified league record" for row in events))

    def test_weekly_facts_and_league_wire_are_deterministic(self) -> None:
        facts = build_live_season.weekly_facts([self.game("live", 120.0, 119.5)], [])
        self.assertEqual({row["fact_id"] for row in facts}, {"highest-score", "lowest-score", "highest-combined", "biggest-win", "closest-game"})
        wire = build_live_season.build_league_wire(1, [self.game("live", 120.0, 119.5)], facts, [])
        self.assertEqual(wire[0]["headline_id"], "week-1:high-score")
        self.assertEqual(wire[0]["source"], "normalized_yahoo")

    def test_public_page_normalizes_blank_preseason_ranks_and_full_slate(self) -> None:
        standings = []
        matchups = []
        for team_id in range(1, 13):
            standings.append(
                f'<tr data-target="/f1/26455/{team_id}"><td></td><td><a href="/f1/26455/{team_id}">Team {team_id}</a></td>'
                '<td>0-0-0</td><td>0.00</td><td>0.00</td><td>-</td><td>1</td><td>0</td></tr>'
            )
        for team_id in range(1, 13, 2):
            matchups.append(
                f'<li data-target="/matchup?mid1={team_id}&mid2={team_id + 1}">'
                f'<a class="F-link" href="/f1/26455/{team_id}">Team {team_id}</a>'
                f'<a class="F-link" href="/f1/26455/{team_id + 1}">Team {team_id + 1}</a>'
                '<div class="Fz-lg">0.00</div><div class="F-shade">101.25</div>'
                '<div class="Fz-lg">0.00</div><div class="F-shade">99.75</div></li>'
            )
        page = (
            '<option value="?matchup_week=1" selected>Week 1</option>'
            '<option value="?matchup_week=16">Week 16</option>'
            '<table id="standingstable">' + "".join(standings) + '</table>'
            '<section id="matchupweek"><h2>Not Started</h2>' + "".join(matchups) + '</section>'
            '<section id="scoreboard"></section>'
        )
        payloads = yahoo_live.build_public_page_payloads(
            page, season=2026, game_key="470", league_id="26455", league_name="RTG", generated_at="2026-09-01T00:00:00Z"
        )
        self.assertEqual(len(payloads["standings.json"]["standings"]), 12)
        self.assertTrue(all(row["rank"] is None for row in payloads["standings.json"]["standings"]))
        self.assertEqual(len(payloads["matchups.json"]["matchups"]), 6)
        self.assertTrue(all(row["status"] == "preevent" for row in payloads["matchups.json"]["matchups"]))

    def test_stale_state_is_explicit(self) -> None:
        franchises = [f"team-{index}" for index in range(1, 13)]
        live = {
            "schema_version": 1, "season": 2026, "data_status": "stale",
            "freshness": {"status": "stale"}, "standings": [], "matchups": [],
            "franchise_summaries": [], "record_watch": [],
        }
        errors = validate_live_season.validate(live, {"schema_version": 1, "season": 2026, "items": []})
        self.assertIn("a ready/stale 2026 hub must contain 12 standings rows", errors)
        live["data_status"] = "unavailable"
        self.assertNotIn("unavailable live data must not publish synthetic results", validate_live_season.validate(live, {"schema_version": 1, "season": 2026, "items": []}))


if __name__ == "__main__":
    unittest.main()
