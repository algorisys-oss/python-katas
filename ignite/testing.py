"""
Ignite Testing Utilities

``TestClient`` simulates ASGI requests against an Ignite application
without starting a real HTTP server.  Also provides assertion helpers
and a dependency-override context manager.

Imports from sibling ignite modules: request, response.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from ignite.request import Request
from ignite.response import Response


# ---------------------------------------------------------------------------
# ASGI scope / message helpers
# ---------------------------------------------------------------------------

def _build_scope(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    query_params: dict[str, str] | None = None,
    client_ip: str = "testclient",
) -> dict[str, Any]:
    """Build a minimal ASGI HTTP scope dict."""
    raw_headers: list[tuple[bytes, bytes]] = []
    for k, v in (headers or {}).items():
        raw_headers.append((k.lower().encode(), v.encode()))

    qs = ""
    if query_params:
        qs = "&".join(f"{k}={v}" for k, v in query_params.items())

    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method.upper(),
        "path": path,
        "root_path": "",
        "query_string": qs.encode(),
        "headers": raw_headers,
        "client": (client_ip, 0),
    }


# ---------------------------------------------------------------------------
# TestResponse
# ---------------------------------------------------------------------------

class TestResponse:
    """Wraps the raw ASGI response captured from the application."""

    def __init__(self) -> None:
        self.status_code: int = 200
        self.headers: dict[str, str] = {}
        self._body_parts: list[bytes] = []

    def feed_start(self, message: dict[str, Any]) -> None:
        self.status_code = message.get("status", 200)
        for k, v in message.get("headers", []):
            self.headers[k.decode("latin-1").lower()] = v.decode("latin-1")

    def feed_body(self, message: dict[str, Any]) -> None:
        self._body_parts.append(message.get("body", b""))

    @property
    def body(self) -> bytes:
        return b"".join(self._body_parts)

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    @property
    def json(self) -> Any:
        return json.loads(self.body)

    def __repr__(self) -> str:
        return f"TestResponse(status={self.status_code})"


# ---------------------------------------------------------------------------
# TestClient
# ---------------------------------------------------------------------------

class TestClient:
    """Simulate ASGI requests against an Ignite application.

    Usage::

        from ignite import Ignite
        from ignite.testing import TestClient

        app = Ignite()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    # -- Public API ----------------------------------------------------------

    def get(self, path: str, **kwargs: Any) -> TestResponse:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> TestResponse:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> TestResponse:
        return self._request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> TestResponse:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> TestResponse:
        return self._request("DELETE", path, **kwargs)

    # -- Internal ------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        json_body: Any | None = None,
        client_ip: str = "testclient",
    ) -> TestResponse:
        """Send a simulated ASGI request and collect the response."""
        scope = _build_scope(
            method, path,
            headers=headers,
            query_params=query_params,
            client_ip=client_ip,
        )

        # Prepare the request body (if any)
        body_bytes = b""
        if json_body is not None:
            body_bytes = json.dumps(json_body).encode()
            # Inject Content-Type if not already set
            scope_headers: list[tuple[bytes, bytes]] = scope["headers"]
            has_ct = any(k == b"content-type" for k, _ in scope_headers)
            if not has_ct:
                scope_headers.append(
                    (b"content-type", b"application/json")
                )

        response = TestResponse()

        async def receive() -> dict[str, Any]:
            return {
                "type": "http.request",
                "body": body_bytes,
                "more_body": False,
            }

        async def send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                response.feed_start(message)
            elif message["type"] == "http.response.body":
                response.feed_body(message)

        # Run the ASGI app
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already inside an event loop -- use a nested helper
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(
                    asyncio.run,
                    self.app(scope, receive, send),
                ).result()
        else:
            asyncio.run(self.app(scope, receive, send))

        return response


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

def assert_status(response: TestResponse, expected: int, msg: str = "") -> None:
    """Assert that *response* has the expected status code."""
    assert response.status_code == expected, (
        f"Expected status {expected}, got {response.status_code}"
        + (f": {msg}" if msg else "")
    )


def assert_json_contains(
    response: TestResponse,
    key: str,
    value: Any = ...,
) -> None:
    """Assert the JSON body contains *key* (optionally with *value*)."""
    data = response.json
    assert key in data, f"Key {key!r} not found in {data}"
    if value is not ...:
        assert data[key] == value, (
            f"Expected {key}={value!r}, got {data[key]!r}"
        )


def assert_error(
    response: TestResponse,
    status_code: int,
    detail_contains: str = "",
) -> None:
    """Assert that *response* is an error with the given status."""
    assert_status(response, status_code)
    data = response.json
    assert "error" in data, f"No 'error' key in {data}"
    if detail_contains:
        detail = data["error"].get("detail", "")
        assert detail_contains in detail, (
            f"Expected detail to contain {detail_contains!r}, got {detail!r}"
        )
