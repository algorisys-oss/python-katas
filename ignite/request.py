"""Ignite Request — wraps ASGI scope and receive into a clean interface."""

from __future__ import annotations

import json
from typing import Any, Callable
from urllib.parse import parse_qs


class Request:
    """Wraps an ASGI scope and receive callable into a developer-friendly object.

    Properties: method, path, headers, query_params, query_string, url, scope.
    Async methods: body(), json(), text(), form().
    """

    def __init__(self, scope: dict[str, Any], receive: Callable) -> None:
        self._scope = scope
        self._receive = receive
        self._body: bytes | None = None
        self.path_params: dict[str, Any] = {}

    # -- Basic properties ------------------------------------------------------

    @property
    def method(self) -> str:
        """HTTP method (GET, POST, PUT, DELETE, etc.)."""
        return self._scope.get("method", "GET")

    @property
    def path(self) -> str:
        """Request path, e.g. '/users/42'."""
        return self._scope.get("path", "/")

    @property
    def query_string(self) -> str:
        """Raw query string, decoded from bytes."""
        raw = self._scope.get("query_string", b"")
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        return raw

    @property
    def url(self) -> str:
        """Full URL path including query string."""
        qs = self.query_string
        if qs:
            return f"{self.path}?{qs}"
        return self.path

    # -- Headers ---------------------------------------------------------------

    @property
    def headers(self) -> dict[str, str]:
        """Parse ASGI headers into a dict with lowercase keys.

        ASGI headers arrive as a list of [name, value] byte pairs.
        Duplicate header names: last value wins.
        """
        raw_headers = self._scope.get("headers", [])
        result: dict[str, str] = {}
        for name, value in raw_headers:
            key = name.decode("utf-8") if isinstance(name, bytes) else name
            val = value.decode("utf-8") if isinstance(value, bytes) else value
            result[key.lower()] = val
        return result

    # -- Query parameters ------------------------------------------------------

    @property
    def query_params(self) -> dict[str, list[str]]:
        """Parse query string into a dict of lists.

        Example: '?color=red&size=lg&color=blue'
        Returns: {'color': ['red', 'blue'], 'size': ['lg']}
        """
        return parse_qs(self.query_string)

    def get_query_param(self, key: str, default: str | None = None) -> str | None:
        """Get a single query parameter value (first occurrence)."""
        values = self.query_params.get(key)
        if values:
            return values[0]
        return default

    # -- Body reading ----------------------------------------------------------

    async def body(self) -> bytes:
        """Read the full request body.

        ASGI delivers the body in chunks via the receive callable.
        The result is cached so multiple calls return the same bytes.
        """
        if self._body is not None:
            return self._body

        chunks: list[bytes] = []
        while True:
            message = await self._receive()
            body_chunk = message.get("body", b"")
            if body_chunk:
                chunks.append(body_chunk)
            if not message.get("more_body", False):
                break

        self._body = b"".join(chunks)
        return self._body

    async def json(self) -> Any:
        """Read the body and parse it as JSON."""
        raw = await self.body()
        return json.loads(raw)

    async def text(self) -> str:
        """Read the body and decode it as UTF-8 text."""
        raw = await self.body()
        return raw.decode("utf-8")

    async def form(self) -> dict[str, list[str]]:
        """Read the body as URL-encoded form data."""
        raw = await self.body()
        return parse_qs(raw.decode("utf-8"))

    # -- Scope access ----------------------------------------------------------

    @property
    def scope(self) -> dict[str, Any]:
        """Direct access to the raw ASGI scope (escape hatch)."""
        return self._scope

    def __repr__(self) -> str:
        return f"<Request {self.method} {self.path}>"
