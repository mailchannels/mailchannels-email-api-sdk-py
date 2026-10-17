"""Exercise redirect policy through real loopback HTTP connections, never the API."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from mailchannels.http_client import RequestsClient
from mailchannels.http_client_async import HTTPXClient


@contextmanager
def redirect_server(
    status: int, cross_origin: bool
) -> Iterator[tuple[str, list[tuple[str, str, str | None, bytes]]]]:
    """Record source and destination requests, including synthetic credentials."""
    calls: list[tuple[str, str, str | None, bytes]] = []

    class Handler(BaseHTTPRequestHandler):
        """Serve a redirect followed by a successful destination response."""

        def handle_request(self) -> None:
            """Read the body and record every attempted HTTP request."""
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            calls.append((self.command, self.path, self.headers.get("X-Api-Key"), body))
            redirected = self.path.startswith("/destination")
            self.send_response(200 if redirected else status)
            if not redirected:
                port = destination.server_port if cross_origin else source.server_port
                self.send_header("Location", f"http://127.0.0.1:{port}/destination")
            payload = b'{"message":"redirect fixture"}'
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = handle_request

        def log_message(self, format: str, *args: object) -> None:
            """Suppress HTTP fixture access logs."""

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as source:
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as destination:
            threads = [
                Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
                for server in (source, destination)
            ]
            for thread in threads:
                thread.start()
            try:
                yield f"http://127.0.0.1:{source.server_port}/original", calls
            finally:
                source.shutdown()
                destination.shutdown()
                for thread in threads:
                    thread.join()


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("cross_origin", [False, True])
@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_sync_redirect_is_not_followed(
    status: int, cross_origin: bool, method: str
) -> None:
    """A redirect cannot forward credentials or replay a send/management request."""
    with redirect_server(status, cross_origin) as (url, calls):
        with RequestsClient(timeout=2) as transport:
            response = transport.request(
                method, url, headers={"X-Api-Key": "synthetic-key"},
                json={"synthetic": "payload"}, params={"dry-run": "true"},
            )
    assert len(calls) == 1
    assert calls[0][:3] == (method, "/original?dry-run=true", "synthetic-key")
    assert b'"synthetic"' in calls[0][3]
    assert response.status_code == status
    assert response.data == {"message": "redirect fixture"}
    assert response.text == '{"message":"redirect fixture"}'
    assert response.headers["Location"].endswith("/destination")


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("cross_origin", [False, True])
@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
async def test_async_redirect_is_not_followed(
    status: int, cross_origin: bool, method: str
) -> None:
    """The async transport preserves the same no-follow response contract."""
    with redirect_server(status, cross_origin) as (url, calls):
        async with HTTPXClient(timeout=2) as transport:
            response = await transport.request(
                method, url, headers={"X-Api-Key": "synthetic-key"},
                json={"synthetic": "payload"}, params={"dry-run": "true"},
            )
    assert len(calls) == 1
    assert calls[0][:3] == (method, "/original?dry-run=true", "synthetic-key")
    assert b'"synthetic"' in calls[0][3]
    assert response.status_code == status
    assert response.data == {"message": "redirect fixture"}
    assert response.text == '{"message":"redirect fixture"}'
    assert response.headers["location"].endswith("/destination")


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
async def test_client_surfaces_redirect_as_api_error(status: int) -> None:
    """Both Client entry points report the original redirect as an API error."""
    from mailchannels.client import Client
    from mailchannels.exceptions import ApiError

    with redirect_server(status, True) as (url, calls):
        with Client(api_key="synthetic-key", base_url=url) as client:
            with pytest.raises(ApiError) as sync_error:
                client.request("POST", "/send", json={"synthetic": "payload"})
        async with Client(api_key="synthetic-key", base_url=url) as client:
            with pytest.raises(ApiError) as async_error:
                await client.request_async(
                    "POST", "/send", json={"synthetic": "payload"}
                )
    assert len(calls) == 2
    for error in (sync_error, async_error):
        assert error.value.status_code == status
        assert error.value.response == {"message": "redirect fixture"}
        assert any(key.lower() == "location" for key in error.value.headers)
