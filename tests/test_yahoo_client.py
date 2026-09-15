from __future__ import annotations

import pathlib
import sys
import unittest
from unittest.mock import Mock, patch

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from yahoo_client import YahooApiError, YahooTransportError, get_json, refresh_access_token  # noqa: E402


def response(status: int, payload: dict, content_type: str = "application/json") -> Mock:
    item = Mock(status_code=status, headers={"Content-Type": content_type})
    item.json.return_value = payload
    return item


class YahooClientTests(unittest.TestCase):
    def test_access_token_refresh_uses_shared_helper(self) -> None:
        with patch(
            "yahoo_client.requests.post",
            return_value=response(200, {"access_token": "short-lived-token"}),
        ) as request:
            token = refresh_access_token("client", "secret", "refresh", sleeper=lambda _: None)
        self.assertEqual(token, "short-lived-token")
        self.assertEqual(request.call_count, 1)

    def test_403_is_sanitized_and_not_retried(self) -> None:
        item = response(
            403,
            {"error": {"code": "ACCOUNT_NOT_AUTHORIZED", "description": "private"}},
        )
        with patch("yahoo_client.requests.get", return_value=item) as request:
            with self.assertRaises(YahooApiError) as raised:
                get_json("https://example.invalid/private", "token", sleeper=lambda _: None)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(raised.exception.error_code, "ACCOUNT_NOT_AUTHORIZED")
        self.assertNotIn("private", str(raised.exception))
        self.assertNotIn("token", str(raised.exception))

    def test_transient_http_failure_retries_then_succeeds(self) -> None:
        responses = [
            response(503, {"error": {"code": "TEMPORARY"}}),
            response(429, {"error": {"code": "RATE_LIMIT"}}),
            response(200, {"fantasy_content": {}}),
        ]
        with patch("yahoo_client.requests.get", side_effect=responses) as request:
            payload = get_json("https://example.invalid", "token", sleeper=lambda _: None)
        self.assertEqual(payload, {"fantasy_content": {}})
        self.assertEqual(request.call_count, 3)

    def test_transport_failure_is_bounded_and_sanitized(self) -> None:
        with patch(
            "yahoo_client.requests.get",
            side_effect=requests.Timeout("private URL and token"),
        ) as request:
            with self.assertRaises(YahooTransportError) as raised:
                get_json("https://example.invalid", "token", sleeper=lambda _: None)
        self.assertEqual(request.call_count, 3)
        self.assertEqual(str(raised.exception), "Yahoo Fantasy API request failed (timeout)")

