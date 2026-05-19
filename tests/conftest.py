"""Shared pytest fixtures and fakes."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import pytest

import mailchannels
from mailchannels.http_client import RequestsClient
from mailchannels.http_client_async import HTTPXClient
from mailchannels.response import SDKResponse

# Non-routable base URL used by the offline test suite. The `.test` TLD is
# reserved by RFC 6761 and is guaranteed never to resolve, so a test that
# accidentally bypasses the fake transport fails fast on DNS instead of
# potentially leaking a request to the production MailChannels API.
OFFLINE_TEST_BASE_URL = "https://api.example.test/tx/v1"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options for the test suite."""
    parser.addoption(
        "--online",
        action="store_true",
        default=False,
        help="Run tests that call the live MailChannels Email API.",
    )
    parser.addoption(
        "--online-destructive",
        action="store_true",
        default=False,
        help="Run live tests that create, update, or delete API resources.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip online tests unless explicitly enabled and configured."""
    online_enabled = config.getoption("--online") and os.environ.get(
        "MAILCHANNELS_API_KEY"
    )
    if not online_enabled:
        reason = (
            "set MAILCHANNELS_API_KEY and pass --online to run live "
            "MailChannels API tests"
        )
        skip_online = pytest.mark.skip(reason=reason)
        for item in items:
            if "online" in item.keywords:
                item.add_marker(skip_online)
        return

    if config.getoption("--online-destructive") and os.environ.get(
        "MAILCHANNELS_ONLINE_DESTRUCTIVE"
    ) == "1":
        return

    reason = (
        "set MAILCHANNELS_ONLINE_DESTRUCTIVE=1 and pass --online-destructive "
        "to run destructive live API tests"
    )
    skip_destructive = pytest.mark.skip(reason=reason)
    for item in items:
        if "online_destructive" in item.keywords:
            item.add_marker(skip_destructive)


@pytest.fixture(autouse=True, scope="session")
def _force_offline_base_url(request: pytest.FixtureRequest) -> Iterator[None]:
    """Force offline tests to use a non-routable base URL.

    Belt-and-suspenders against a misconfigured test: if a Client is created
    without a fake transport, the request fails fast on DNS resolution
    instead of leaking out to the production MailChannels API. Skipped when
    `--online` is enabled so live tests can reach the real API via the
    MAILCHANNELS_API_URL the user configured.
    """
    if request.config.getoption("--online"):
        yield
        return
    original_env = os.environ.get("MAILCHANNELS_API_URL")
    original_module = mailchannels.base_url
    os.environ["MAILCHANNELS_API_URL"] = OFFLINE_TEST_BASE_URL
    mailchannels.base_url = OFFLINE_TEST_BASE_URL
    try:
        yield
    finally:
        mailchannels.base_url = original_module
        if original_env is None:
            os.environ.pop("MAILCHANNELS_API_URL", None)
        else:
            os.environ["MAILCHANNELS_API_URL"] = original_env


class FakeRequestsClient(RequestsClient):
    """Fake sync transport for tests."""

    def __init__(self, response: SDKResponse | None = None) -> None:
        """Create a fake sync transport."""
        super().__init__()
        self.response = response or SDKResponse(202, {"id": "queued_123"}, "{}")
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> SDKResponse:
        """Record a request and return the configured response."""
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "json": json,
                "params": params,
            }
        )
        return self.response


class FakeHTTPXClient(HTTPXClient):
    """Fake async transport for tests."""

    def __init__(self, response: SDKResponse | None = None) -> None:
        """Create a fake async transport."""
        super().__init__()
        self.response = response or SDKResponse(202, {"id": "queued_123"}, "{}")
        self.calls: list[dict[str, Any]] = []

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> SDKResponse:
        """Record an async request and return the configured response."""
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "json": json,
                "params": params,
            }
        )
        return self.response
