"""Shared, privacy-safe Yahoo OAuth and Fantasy API HTTP helpers."""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import Any

import requests


RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30


class YahooApiError(RuntimeError):
    """A sanitized Yahoo failure that never includes URLs or response bodies."""

    def __init__(
        self,
        operation: str,
        status_code: int,
        error_code: str | None = None,
    ) -> None:
        self.operation = operation
        self.status_code = status_code
        self.error_code = error_code
        suffix = f" ({error_code})" if error_code else ""
        super().__init__(f"{operation} failed with HTTP {status_code}{suffix}")


class YahooTransportError(RuntimeError):
    """A sanitized network failure after bounded retry exhaustion."""

    def __init__(self, operation: str, category: str = "network_error") -> None:
        self.operation = operation
        self.category = category
        super().__init__(f"{operation} failed ({category})")


def safe_yahoo_error_code(response: requests.Response) -> str | None:
    """Extract one allowlisted diagnostic code without retaining an error body."""

    try:
        payload = response.json()
    except (requests.RequestException, ValueError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None

    candidates: list[Any] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.casefold() in {"code", "error_code"}:
                    candidates.append(child)
                elif isinstance(child, (dict, list)):
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    for candidate in candidates:
        if isinstance(candidate, str) and re.fullmatch(
            r"[A-Za-z0-9_.-]{1,64}", candidate
        ):
            return candidate
    return None


def _request_json(
    request: Callable[[], requests.Response],
    *,
    operation: str,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    attempts = max(1, max_attempts)
    for attempt in range(1, attempts + 1):
        try:
            response = request()
        except (requests.ConnectionError, requests.Timeout) as error:
            if attempt == attempts:
                category = "timeout" if isinstance(error, requests.Timeout) else "network_error"
                raise YahooTransportError(operation, category) from None
            sleeper(float(2 ** (attempt - 1)))
            continue

        if response.status_code >= 400:
            error = YahooApiError(
                operation,
                response.status_code,
                safe_yahoo_error_code(response),
            )
            if response.status_code not in RETRYABLE_STATUS_CODES or attempt == attempts:
                raise error
            sleeper(float(2 ** (attempt - 1)))
            continue

        if "application/json" not in response.headers.get("Content-Type", ""):
            raise ValueError(f"{operation} returned a non-JSON response")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"{operation} returned malformed JSON")
        return payload

    raise AssertionError("Yahoo request retry loop exited unexpectedly")


def refresh_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleeper: Callable[[float], None] = time.sleep,
) -> str:
    import base64

    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    payload = _request_json(
        lambda: requests.post(
            "https://api.login.yahoo.com/oauth2/get_token",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=DEFAULT_TIMEOUT_SECONDS,
        ),
        operation="Yahoo OAuth token refresh",
        max_attempts=max_attempts,
        sleeper=sleeper,
    )
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise ValueError("Yahoo OAuth token refresh returned no access token")
    return token


def get_json(
    url: str,
    token: str,
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    return _request_json(
        lambda: requests.get(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=DEFAULT_TIMEOUT_SECONDS,
        ),
        operation="Yahoo Fantasy API request",
        max_attempts=max_attempts,
        sleeper=sleeper,
    )
