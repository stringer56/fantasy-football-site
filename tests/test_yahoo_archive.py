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
    is_login_url,
    parse_available_weeks,
    parse_draft,
    parse_matchups,
    parse_roster,
    parse_standings,
    parse_transactions,
    next_transaction_offset,
)
from backfill_yahoo_history import apply_2021_canonical_fallback, coverage_scopes, remap_payload  # noqa: E402


FIXTURES = ROOT / "tests" / "fixtures" / "yahoo_archive"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, status: int, text: str = "", headers: dict[str, str] | None = None,
                 url: str = "https://football.fantasysports.yahoo.com/"):
        self.status_code = status
        self.text = text
        self.headers = headers or {}
        self.url = url

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

    def test_2021_login_redirect_is_rejected_even_without_login_markup(self) -> None:
        self.assertTrue(is_login_url("https://login.yahoo.com/config/login?.src=sports"))
        self.assertFalse(is_login_url("https://football.fantasysports.yahoo.com/2021/f1/12928"))
        with tempfile.TemporaryDirectory() as directory:
            response = FakeResponse(200, "generic authentication page", url="https://login.yahoo.com/config/login")
            client = ArchiveClient(
                pathlib.Path(directory), delay_seconds=0, max_retries=0,
                session=FakeSession([response]), sleeper=lambda _: None,
            )
            with self.assertRaisesRegex(RuntimeError, "requires sign-in"):
                client.get(
                    "https://football.fantasysports.yahoo.com/2021/f1/12928",
                    pathlib.Path("2021/page.html"),
                )
            self.assertFalse((pathlib.Path(directory) / "2021" / "page.html").exists())

    def test_2021_canonical_fallback_remains_partial(self) -> None:
        result = apply_2021_canonical_fallback(
            {"sections": {}}, "2026-09-03T00:00:00Z", write_outputs=False
        )
        self.assertEqual("C", result["recovery_level"])
        self.assertEqual(16, result["weeks_expected"])
        self.assertEqual(0, result["weeks_fetched"])
        self.assertEqual(10, result["sections"]["standings"]["rows"])
        self.assertEqual(10, result["sections"]["standings"]["yahoo_rows"])
        self.assertEqual(10, result["franchise_mapping"]["yahoo_team_keys_recovered"])
        self.assertEqual(1, result["sections"]["playoffs"]["scored_games"])
        self.assertEqual(0, result["sections"]["draft"]["picks"])
        self.assertEqual(
            ["Matthew's Optimal Team", "The Swagger Daggers"],
            result["unresolved_franchise_mappings"],
        )

    def test_coverage_scopes_keep_season_and_weekly_windows_separate(self) -> None:
        scopes = coverage_scopes()
        season_scope = scopes["season_level_metrics"]
        weekly_scope = scopes["weekly_derived_metrics"]
        self.assertEqual("Verified 2021–2025", season_scope["label"])
        self.assertEqual([2021, 2022, 2023, 2024, 2025], season_scope["source_years"])
        self.assertEqual("Verified 2022–2025", weekly_scope["label"])
        self.assertEqual([2022, 2023, 2024, 2025], weekly_scope["source_years"])
        self.assertEqual([2021], weekly_scope["excluded_years"])
        self.assertNotIn("all-time", " ".join(scope["label"] for scope in scopes.values()).casefold())

    def test_remap_payload_applies_only_approved_aliases(self) -> None:
        payload = {
            "team_a": {
                "historical_team_name": "Dilly Dilly",
                "franchise_id": None,
                "mapping_status": "unresolved",
            },
            "team_b": {
                "historical_team_name": "The Swagger Daggers",
                "franchise_id": None,
                "mapping_status": "unresolved",
            },
            "winner_historical_name": "Dilly Dilly",
            "winner_franchise_id": None,
        }
        changes = remap_payload(
            payload,
            {"dilly dilly": "buffalo-bravado", "the swagger daggers": None},
        )
        self.assertGreater(changes, 0)
        self.assertEqual(payload["team_a"]["franchise_id"], "buffalo-bravado")
        self.assertEqual(payload["team_a"]["mapping_status"], "verified")
        self.assertIsNone(payload["team_b"]["franchise_id"])
        self.assertEqual(payload["winner_franchise_id"], "buffalo-bravado")

    def test_parser_output_is_deterministic(self) -> None:
        args = dict(season=2025, week=1, game_key="461", league_id="103926", mappings=self.mappings, playoff_start_week=14)
        self.assertEqual(parse_matchups(fixture("standings_matchups.html"), **args), parse_matchups(fixture("standings_matchups.html"), **args))


if __name__ == "__main__":
    unittest.main()
