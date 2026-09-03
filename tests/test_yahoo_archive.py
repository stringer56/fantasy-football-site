from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from yahoo_archive import (  # noqa: E402
    ArchiveClient,
    is_login_page,
    parse_available_weeks,
    parse_draft,
    parse_matchups,
    parse_roster,
    parse_standings,
    parse_transactions,
    next_transaction_offset,
)


FIXTURES = ROOT / "tests" / "fixtures" / "yahoo_archive"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, status: int, text: str = "", headers: dict[str, str] | None = None):
        self.status_code = status
        self.text = text
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"status {self.status_code}")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.headers: dict[str, str] = {}
        self.calls = 0

    def get(self, _url: str, timeout: int) -> FakeResponse:
        self.calls += 1
        return self.responses.pop(0)


class YahooArchiveParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mappings = {"461.l.103926.t.1": "alpha", "461.l.103926.t.2": None}

    def test_standings_and_unresolved_mapping(self) -> None:
        rows = parse_standings(
            fixture("standings_matchups.html"), season=2025, game_key="461", league_id="103926", mappings=self.mappings
        )
        self.assertEqual(2, len(rows))
        self.assertEqual((2, 0, 0), (rows[0]["wins"], rows[0]["losses"], rows[0]["ties"]))
        self.assertEqual(250.5, rows[0]["points_for"])
        self.assertEqual("unresolved", rows[1]["mapping_status"])

    def test_available_weeks(self) -> None:
        self.assertEqual([1, 2], parse_available_weeks(fixture("standings_matchups.html")))

    def test_matchup_uses_actual_not_projected_score(self) -> None:
        games = parse_matchups(
            fixture("standings_matchups.html"), season=2025, week=1, game_key="461", league_id="103926",
            mappings=self.mappings, playoff_start_week=14,
        )
        self.assertEqual(125.25, games[0]["team_a"]["score"])
        self.assertEqual(99.75, games[0]["team_b"]["score"])
        self.assertEqual("alpha", games[0]["winner_franchise_id"])
        self.assertFalse(games[0]["is_playoffs"])

    def test_tie_and_playoff_flags(self) -> None:
        mappings = {"414.l.527645.t.1": "alpha", "414.l.527645.t.2": "beta"}
        games = parse_matchups(
            fixture("tie_matchup.html"), season=2022, week=15, game_key="414", league_id="527645",
            mappings=mappings, playoff_start_week=15,
        )
        self.assertTrue(games[0]["tie"])
        self.assertTrue(games[0]["is_playoffs"])
        self.assertIsNone(games[0]["winner_franchise_id"])

    def test_missing_score_is_not_converted_to_zero(self) -> None:
        page = fixture("standings_matchups.html").replace(">99.75</div>", ">--</div>")
        games = parse_matchups(
            page, season=2025, week=1, game_key="461", league_id="103926",
            mappings=self.mappings, playoff_start_week=14,
        )
        self.assertIsNone(games[0]["team_b"]["score"])
        self.assertFalse(games[0]["verified"])
        self.assertIsNone(games[0]["winner_franchise_id"])

    def test_draft_picks_and_unresolved_team(self) -> None:
        picks = parse_draft(
            fixture("draft.html"), season=2025, game_key="461", league_id="103926",
            mappings_by_name={"alpha team": "alpha", "historic mystery": None},
        )
        self.assertEqual([1, 2], [pick["overall_pick"] for pick in picks])
        self.assertEqual("100", picks[0]["player_id"])
        self.assertEqual("unresolved", picks[1]["mapping_status"])

    def test_roster_bench_status_and_points(self) -> None:
        rows = parse_roster(
            fixture("roster.html"), season=2025, week=1, team_key="461.l.103926.t.1",
            franchise_id="alpha", historical_team_name="Alpha Team",
        )
        self.assertEqual(2, len(rows))
        self.assertEqual("starter", rows[0]["starter_or_bench"])
        self.assertEqual("bench", rows[1]["starter_or_bench"])
        self.assertEqual(31.75, rows[1]["fantasy_points"])

    def test_transaction_add_drop_and_pagination(self) -> None:
        page = fixture("transactions.html")
        rows = parse_transactions(
            page, season=2025, game_key="461", league_id="103926", mappings=self.mappings
        )
        self.assertEqual(1, len(rows))
        self.assertEqual("add_drop", rows[0]["transaction_type"])
        self.assertEqual(["add", "drop"], [player["action"] for player in rows[0]["players"]])
        self.assertEqual("alpha", rows[0]["franchise_id"])
        self.assertEqual(25, next_transaction_offset(page))

    def test_malformed_pages_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            parse_standings(fixture("malformed.html"), season=2025, game_key="461", league_id="103926", mappings={})
        with self.assertRaises(ValueError):
            parse_draft(fixture("malformed.html"), season=2025, game_key="461", league_id="103926", mappings_by_name={})

    def test_cache_is_resumable_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            cached = root / "2025" / "page.html"
            cached.parent.mkdir()
            cached.write_text("cached", encoding="utf-8")
            session = FakeSession([])
            client = ArchiveClient(root, session=session, sleeper=lambda _: None)
            self.assertEqual("cached", client.get("https://example.invalid", pathlib.Path("2025/page.html")))
            self.assertEqual(0, session.calls)

    def test_429_retry_then_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = FakeSession([FakeResponse(429, headers={"Retry-After": "1"}), FakeResponse(200, "safe")])
            waits: list[float] = []
            client = ArchiveClient(pathlib.Path(directory), delay_seconds=0, max_retries=1, session=session, sleeper=waits.append)
            value = client.get("https://example.invalid", pathlib.Path("2025/page.html"))
            self.assertEqual("safe", value)
            self.assertEqual(2, session.calls)
            self.assertIn(1.0, waits)

    def test_login_page_is_rejected_from_cached_source(self) -> None:
        login = "<title>Login - Sign in to Yahoo</title><p>Sign in to Yahoo Fantasy</p>"
        self.assertTrue(is_login_page(login))
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            cached = root / "2021" / "page.html"
            cached.parent.mkdir()
            cached.write_text(login, encoding="utf-8")
            client = ArchiveClient(root, session=FakeSession([]), sleeper=lambda _: None)
            with self.assertRaisesRegex(RuntimeError, "requires sign-in"):
                client.get("https://example.invalid", pathlib.Path("2021/page.html"))

    def test_parser_output_is_deterministic(self) -> None:
        args = dict(season=2025, week=1, game_key="461", league_id="103926", mappings=self.mappings, playoff_start_week=14)
        self.assertEqual(parse_matchups(fixture("standings_matchups.html"), **args), parse_matchups(fixture("standings_matchups.html"), **args))


if __name__ == "__main__":
    unittest.main()
