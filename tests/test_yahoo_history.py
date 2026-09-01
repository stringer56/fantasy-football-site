import copy
import json
import pathlib
import sys
import unittest

import requests


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "yahoo"
sys.path.insert(0, str(ROOT / "scripts"))

from validate_public_data import validate_payload  # noqa: E402
from backfill_yahoo_history import (  # noqa: E402
    build_head_to_head_document,
    matchup_payload,
    roster_payload,
)
from yahoo_history import (  # noqa: E402
    YahooHistoryClient,
    build_bench_scores,
    build_committed_manifest,
    build_head_to_head,
    build_team_weeks,
    calculate_margins,
    calculate_streaks,
    classify_discovery,
    extract_games,
    extract_leagues,
    load_yaml,
    normalize_history_matchups,
    normalize_history_roster,
    parse_renewal_key,
    resolve_franchise,
)


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


FRANCHISES = [
    {
        "franchise_id": "albany-kneelers",
        "name": "Albany Kneelers",
        "aliases": [],
        "yahoo": {"team_keys": {"2025": "461.l.103926.t.2"}, "team_names": {}},
    },
    {
        "franchise_id": "ayahuasca-rush",
        "name": "Ayahuasca Rush",
        "aliases": [],
        "yahoo": {"team_keys": {"2025": "461.l.103926.t.3"}, "team_names": {}},
    },
    {
        "franchise_id": "buffalo-bravado",
        "name": "Buffalo Bravado",
        "aliases": ["Buffalo Bravados"],
        "yahoo": {"team_keys": {"2025": "461.l.103926.t.4"}, "team_names": {}},
    },
    {
        "franchise_id": "crazy-wazs-team",
        "name": "Crazy Waz's Team",
        "aliases": ["Chris's Crazy Team"],
        "yahoo": {"team_keys": {"2025": "461.l.103926.t.5"}, "team_names": {}},
    },
]


class YahooHistoryTests(unittest.TestCase):
    def normalized_matchups(self):
        return normalize_history_matchups(
            fixture("history_scoreboard.json"),
            season=2025,
            league_key="461.l.103926",
            franchises=FRANCHISES,
        )

    def test_renewal_chain_normalization(self):
        self.assertEqual(parse_renewal_key("449_761310"), "449.l.761310")
        league = extract_leagues(fixture("history_league.json"))[0]
        self.assertEqual(league["previous_league_key"], "449.l.761310")
        self.assertEqual(league["next_league_key"], "473.l.26455")
        self.assertEqual(league["playoff_start_week"], 15)

    def test_user_game_discovery_is_season_scoped(self):
        games = extract_games(fixture("history_games.json"))
        self.assertEqual([row["season"] for row in games], [2024, 2025, 2026])
        self.assertEqual([row["game_key"] for row in games], ["449", "461", "473"])

    def test_ambiguous_leagues_are_not_verified(self):
        discovered = extract_leagues(fixture("history_leagues.json"))
        discovered.append({
            "season": 2025,
            "game_key": "461",
            "league_key": "461.l.888888",
            "league_id": "888888",
            "league_name": "Road To Glory FFL",
            "previous_league_key": None,
            "next_league_key": None,
        })
        result = classify_discovery(discovered, [{"league_key": "461.l.103926", "verified": True}])
        self.assertEqual([row["league_key"] for row in result["verified"]], ["461.l.103926"])
        self.assertEqual({row["league_key"] for row in result["ambiguous"]}, {"461.l.777777", "461.l.888888"})

    def test_weekly_matchups_normalize_scores_and_mappings(self):
        matchups = self.normalized_matchups()
        self.assertEqual(len(matchups), 2)
        first = matchups[0]
        self.assertEqual(first["week"], 2)
        self.assertEqual(first["winner_franchise_id"], "albany-kneelers")
        self.assertEqual(first["team_a"]["score"], 130.5)
        self.assertTrue(first["verified"])

    def test_ties_remain_ties_without_a_winner(self):
        tied = next(row for row in self.normalized_matchups() if row["tie"])
        self.assertIsNone(tied["winner_franchise_id"])
        self.assertEqual(tied["team_a"]["score"], tied["team_b"]["score"])

    def test_missing_scores_are_never_zero(self):
        payload = fixture("history_scoreboard.json")
        payload["fantasy_content"]["league"][1]["scoreboard"]["0"]["matchups"]["0"]["matchup"]["0"]["teams"]["1"]["team"][1]["team_points"]["total"] = None
        matchup = normalize_history_matchups(
            payload, season=2025, league_key="461.l.103926", franchises=FRANCHISES
        )[0]
        self.assertIsNone(matchup["team_b"]["score"])

    def test_playoff_flags_are_preserved(self):
        payload = fixture("history_scoreboard.json")
        payload["fantasy_content"]["league"][1]["scoreboard"]["0"]["matchups"]["0"]["matchup"]["is_playoffs"] = "1"
        matchup = normalize_history_matchups(
            payload, season=2025, league_key="461.l.103926", franchises=FRANCHISES
        )[0]
        self.assertTrue(matchup["is_playoffs"])

    def test_mapping_prefers_team_key_then_verified_alias(self):
        keyed = resolve_franchise(
            season=2025, team_key="461.l.103926.t.2", team_name="Different", franchises=FRANCHISES
        )
        alias = resolve_franchise(
            season=2024, team_key="449.l.1.t.4", team_name="Buffalo Bravados", franchises=FRANCHISES
        )
        unresolved = resolve_franchise(
            season=2024, team_key="449.l.1.t.9", team_name="The Swagger Daggers", franchises=FRANCHISES
        )
        self.assertEqual(keyed["mapping_basis"], "season_team_key")
        self.assertEqual(alias["franchise_id"], "buffalo-bravado")
        self.assertEqual(unresolved["mapping_status"], "unresolved")

    def test_weekly_team_scores_include_result_and_margin(self):
        rows = build_team_weeks(self.normalized_matchups())
        albany = next(row for row in rows if row.get("franchise_id") == "albany-kneelers")
        tied = [row for row in rows if row.get("result") == "tie"]
        self.assertEqual(albany["result"], "win")
        self.assertEqual(albany["margin"], 30.25)
        self.assertEqual(len(tied), 2)

    def test_head_to_head_totals_are_deterministic(self):
        first = self.normalized_matchups()[0]
        second = copy.deepcopy(first)
        second["week"] = 3
        second["matchup_id"] = "2025-w03-2-3"
        second["team_a"]["score"] = 100.0
        second["team_b"]["score"] = 120.0
        second["winner_yahoo_team_key"] = second["team_b"]["yahoo_team_key"]
        second["winner_franchise_id"] = second["team_b"]["franchise_id"]
        pair = build_head_to_head([first, second])[0]
        self.assertEqual(pair["games"], 2)
        self.assertEqual((pair["wins_a"], pair["wins_b"], pair["ties"]), (1, 1, 0))
        self.assertEqual(pair["points_a"], 230.5)
        self.assertEqual(pair["points_b"], 220.25)

    def test_margin_calculation_excludes_ties(self):
        margins = calculate_margins(self.normalized_matchups())
        self.assertEqual(len(margins["regular_season"]), 1)
        self.assertEqual(margins["regular_season"][0]["margin"], 30.25)
        self.assertEqual(margins["playoffs"], [])

    def test_streaks_break_on_ties_and_season_boundaries(self):
        rows = [
            {"season": 2024, "week": 1, "franchise_id": "a", "result": "win", "playoff": False},
            {"season": 2024, "week": 2, "franchise_id": "a", "result": "win", "playoff": False},
            {"season": 2024, "week": 3, "franchise_id": "a", "result": "tie", "playoff": False},
            {"season": 2024, "week": 4, "franchise_id": "a", "result": "loss", "playoff": False},
            {"season": 2025, "week": 1, "franchise_id": "a", "result": "win", "playoff": False},
        ]
        streaks = calculate_streaks(rows)
        by_season = {row["season"]: row for row in streaks}
        self.assertEqual(by_season[2024]["longest_win_streak"], 2)
        self.assertEqual(by_season[2024]["longest_loss_streak"], 1)
        self.assertEqual(by_season[2025]["longest_win_streak"], 1)

    def test_bench_roster_and_weekly_points_are_explicit(self):
        players = normalize_history_roster(
            fixture("history_roster.json"),
            season=2025,
            week=2,
            team_identity={
                "franchise_id": "albany-kneelers",
                "historical_team_name": "Albany Kneelers",
                "yahoo_team_key": "461.l.103926.t.2",
            },
        )
        bench = next(row for row in players if row["player_name"] == "Bench Player")
        missing = next(row for row in players if row["player_name"] == "Unscored Bench Player")
        self.assertEqual(bench["starter_or_bench"], "bench")
        self.assertEqual(bench["fantasy_points"], 32.75)
        self.assertIsNone(missing["fantasy_points"])
        scores = build_bench_scores(players)
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0]["points_missed"], 32.75)

    def test_retry_uses_bounded_backoff_for_429(self):
        class Response:
            def __init__(self, status, payload=None):
                self.status_code = status
                self.headers = {"Content-Type": "application/json", "Retry-After": "0"}
                self._payload = payload or {}

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise requests.HTTPError(f"status {self.status_code}")

            def json(self):
                return self._payload

        class Session:
            def __init__(self):
                self.responses = [Response(429), Response(200, {"fantasy_content": {}})]
                self.calls = 0

            def get(self, *args, **kwargs):
                self.calls += 1
                return self.responses.pop(0)

        session = Session()
        sleeps = []
        client = YahooHistoryClient(
            "fixture-token", session=session, request_delay=0, max_retries=2, sleep=sleeps.append
        )
        result = client.get_json("league/fixture")
        self.assertEqual(result, {"fantasy_content": {}})
        self.assertEqual(session.calls, 2)
        self.assertEqual(sleeps, [0.0])

    def test_permanent_api_errors_are_not_retried(self):
        class Response:
            status_code = 401
            headers = {"Content-Type": "application/json"}

            def raise_for_status(self):
                error = requests.HTTPError("status 401")
                error.response = self
                raise error

        class Session:
            def __init__(self):
                self.calls = 0

            def get(self, *args, **kwargs):
                self.calls += 1
                return Response()

        session = Session()
        client = YahooHistoryClient("fixture-token", session=session, request_delay=0, max_retries=4)
        with self.assertRaises(requests.HTTPError):
            client.get_json("league/fixture")
        self.assertEqual(session.calls, 1)

    def test_public_outputs_strip_private_fields(self):
        matchups = {"schema_version": 1, "matchups": self.normalized_matchups()}
        self.assertEqual(validate_payload(pathlib.Path("fixture.json"), matchups), [])
        serialized = json.dumps(matchups).lower()
        self.assertNotIn("manager_id", serialized)
        self.assertNotIn("refresh_token", serialized)

    def test_committed_manifest_generation_is_deterministic(self):
        leagues = load_yaml(ROOT / "_data" / "yahoo_leagues.yml")
        site = load_yaml(ROOT / "_data" / "site.yml")
        first = build_committed_manifest(leagues, site)
        second = build_committed_manifest(leagues, site)
        self.assertEqual(first, second)
        self.assertEqual([row["season"] for row in first["verified_leagues"]], [2024, 2025])

    def test_coverage_requires_every_expected_week_and_score(self):
        matchups = self.normalized_matchups()
        complete = matchup_payload(
            season=2025,
            league_key="461.l.103926",
            expected_weeks=[2],
            playoff_start_week=15,
            matchups=matchups,
            failed_weeks=[],
        )
        incomplete = matchup_payload(
            season=2025,
            league_key="461.l.103926",
            expected_weeks=[1, 2],
            playoff_start_week=15,
            matchups=matchups,
            failed_weeks=[1],
        )
        self.assertTrue(complete["coverage"]["regular_season_complete"])
        self.assertFalse(incomplete["coverage"]["regular_season_complete"])
        self.assertEqual(incomplete["coverage"]["missing_weeks"], [1])

    def test_head_to_head_output_is_gated_and_deterministic(self):
        matchups = self.normalized_matchups()
        complete = matchup_payload(
            season=2025,
            league_key="461.l.103926",
            expected_weeks=[2],
            playoff_start_week=15,
            matchups=matchups,
            failed_weeks=[],
        )
        first = build_head_to_head_document([complete])
        second = build_head_to_head_document([complete])
        self.assertEqual(first, second)
        self.assertEqual(first["coverage"]["status"], "complete")
        self.assertEqual(first["coverage"]["games_counted"], 2)

    def test_bench_publication_requires_complete_player_points(self):
        players = normalize_history_roster(
            fixture("history_roster.json"),
            season=2025,
            week=2,
            team_identity={
                "franchise_id": "albany-kneelers",
                "historical_team_name": "Albany Kneelers",
                "yahoo_team_key": "461.l.103926.t.2",
            },
        )
        incomplete = roster_payload(
            season=2025,
            league_key="461.l.103926",
            expected_requests=1,
            completed_requests=1,
            player_weeks=players,
            include_player_stats=True,
        )
        complete_players = [row for row in players if row["fantasy_points"] is not None]
        complete = roster_payload(
            season=2025,
            league_key="461.l.103926",
            expected_requests=1,
            completed_requests=1,
            player_weeks=complete_players,
            include_player_stats=True,
        )
        self.assertFalse(incomplete["coverage"]["bench_reconstruction_possible"])
        self.assertEqual(incomplete["bench_scores"], [])
        self.assertTrue(complete["coverage"]["bench_reconstruction_possible"])
        self.assertEqual(complete["bench_scores"][0]["player_name"], "Bench Player")


if __name__ == "__main__":
    unittest.main()
