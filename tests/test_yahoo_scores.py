from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pull_yahoo_scores as scores  # noqa: E402
from yahoo_client import YahooApiError, YahooTransportError  # noqa: E402


def valid_payload() -> dict:
    return {
        "schema_version": 1,
        "week": 1,
        "matchups": [
            {
                "week": 1,
                "status": "midevent",
                "winner_team_key": None,
                "teams": [
                    {
                        "team_key": "470.l.26455.t.1",
                        "team_name": "One",
                        "score": 10.0,
                        "projected_score": 100.0,
                    },
                    {
                        "team_key": "470.l.26455.t.2",
                        "team_name": "Two",
                        "score": 20.0,
                        "projected_score": 110.0,
                    },
                ],
            }
        ],
    }


def valid_sync() -> dict:
    return {
        "schema_version": 1,
        "status": "ready",
        "source": "official_yahoo_public_page_fallback",
        "week": 1,
        "fetched_at": "2026-09-15T00:00:00Z",
    }


class YahooScoreRefreshTests(unittest.TestCase):
    def test_403_uses_official_public_fallback(self) -> None:
        environment = {
            "YAHOO_CLIENT_ID": "client",
            "YAHOO_CLIENT_SECRET": "secret",
            "YAHOO_REFRESH_TOKEN": "refresh",
            "LEAGUE_KEY": "nfl.l.26455",
        }
        configured = {"alias": "nfl.l.26455", "league_key": "470.l.26455"}
        with (
            patch.object(scores, "required_environment", return_value=environment),
            patch.object(scores, "configured_yahoo_identity", return_value=configured),
            patch.object(
                scores,
                "authenticated_score_payloads",
                side_effect=YahooApiError("Yahoo Fantasy API request", 403),
            ),
            patch.object(
                scores,
                "load_public_score_payloads",
                return_value=(valid_payload(), valid_sync()),
            ) as fallback,
        ):
            payload, sync = scores.fetch_score_payloads()
        self.assertEqual(payload["week"], 1)
        self.assertEqual(sync["source"], "official_yahoo_public_page_fallback")
        fallback.assert_called_once_with(refresh=True)

    def test_invalid_response_never_replaces_last_good_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory)
            previous_matchups = {"schema_version": 1, "week": 1, "matchups": [{"safe": True}]}
            previous_sync = valid_sync()
            (output / "matchups.json").write_text(json.dumps(previous_matchups), encoding="utf-8")
            (output / "live_sync.json").write_text(json.dumps(previous_sync), encoding="utf-8")
            with (
                patch.object(scores, "fetch_score_payloads", return_value=(
                    {"schema_version": 1, "week": 1, "matchups": []},
                    valid_sync(),
                )),
                patch.object(
                    scores,
                    "configured_yahoo_identity",
                    return_value={"league_key": "470.l.26455"},
                ),
                self.assertRaises(ValueError),
            ):
                scores.refresh_once(output)
            self.assertEqual(
                json.loads((output / "matchups.json").read_text(encoding="utf-8")),
                previous_matchups,
            )
            self.assertEqual(
                json.loads((output / "live_sync.json").read_text(encoding="utf-8")),
                previous_sync,
            )

    def test_network_failure_retains_last_good_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory)
            before = b'{"last":"good"}\n'
            (output / "matchups.json").write_bytes(before)
            with patch.object(
                scores,
                "fetch_score_payloads",
                side_effect=YahooTransportError("Yahoo public scoreboard", "timeout"),
            ), self.assertRaises(YahooTransportError):
                scores.refresh_once(output)
            self.assertEqual((output / "matchups.json").read_bytes(), before)
            self.assertFalse((output / "live_sync.json").exists())

    def test_full_and_fast_workflows_share_concurrency_group(self) -> None:
        fast = yaml.safe_load(
            (ROOT / ".github/workflows/live-yahoo-scores.yml").read_text(encoding="utf-8")
        )
        full = yaml.safe_load(
            (ROOT / ".github/workflows/update.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            fast["concurrency"]["group"],
            full["concurrency"]["group"],
        )
        self.assertFalse(fast["concurrency"]["cancel-in-progress"])
        self.assertFalse(full["concurrency"]["cancel-in-progress"])
        fast_checkout = fast["jobs"]["scores"]["steps"][0]
        full_checkout = full["jobs"]["update"]["steps"][0]
        self.assertEqual(fast_checkout["with"]["ref"], "main")
        self.assertEqual(full_checkout["with"]["ref"], "main")
        self.assertEqual(fast[True]["schedule"][0]["cron"], "*/5 * * * *")
        self.assertEqual(full[True]["schedule"][0]["cron"], "*/15 * * * *")
        publish = next(
            step for step in fast["jobs"]["scores"]["steps"]
            if step["name"] == "Publish changed scores"
        )
        self.assertIn("_data/generated/matchups.json", publish["run"])
        self.assertIn("_data/generated/live_sync.json", publish["run"])
        self.assertNotIn("rosters.json", publish["run"])

    def test_freshness_metadata_must_match_score_week(self) -> None:
        sync = valid_sync()
        sync["week"] = 2
        with self.assertRaises(ValueError):
            scores.validate_sync_payload(sync, 1)

    def test_score_only_refresh_retains_standings_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory)
            existing = valid_payload()
            existing["matchups"][0]["teams"][0]["record"] = "4-1-0"
            (output / "matchups.json").write_text(json.dumps(existing), encoding="utf-8")
            incoming = valid_payload()
            with patch.object(
                scores,
                "fetch_score_payloads",
                return_value=(incoming, valid_sync()),
            ):
                scores.refresh_once(output)
            saved = json.loads((output / "matchups.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["matchups"][0]["teams"][0]["record"], "4-1-0")
