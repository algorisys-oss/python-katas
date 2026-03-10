"""
Ignite Static Files

ASGI application that serves static files from a directory on disk.
Features MIME-type detection, path-traversal protection, ETag / Last-Modified
cache headers, and 304 Not Modified support.

Self-contained -- only stdlib imports.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
from email.utils import formatdate, parsedate_to_datetime
from datetime import datetime, timezone
from typing import Any, Callable

# Ensure common web MIME types are registered
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class PathTraversalError(Exception):
    """Raised when a path traversal attack is detected."""


def _guess_content_type(filepath: str) -> str:
    """Return the MIME type for *filepath* based on its extension."""
    content_type, _ = mimetypes.guess_type(filepath)
    return content_type or "application/octet-stream"


def _safe_join(base_dir: str, *paths: str) -> str:
    """Join *paths* under *base_dir* and verify the result stays inside.

    Raises :class:`PathTraversalError` if the resolved path escapes.
    """
    base = os.path.realpath(base_dir)
    requested = os.path.realpath(os.path.join(base, *paths))
    if not requested.startswith(base + os.sep) and requested != base:
        raise PathTraversalError(
            f"Path traversal detected: {paths!r} escapes {base_dir!r}"
        )
    return requested


def _generate_etag(filepath: str) -> str:
    """Return a weak ETag based on file size and mtime."""
    stat = os.stat(filepath)
    fingerprint = f"{stat.st_size}-{stat.st_mtime}".encode()
    return hashlib.md5(fingerprint).hexdigest()


# ---------------------------------------------------------------------------
# StaticFiles ASGI application
# ---------------------------------------------------------------------------

class StaticFiles:
    """ASGI application that serves static files from a directory.

    Usage::

        app = StaticFiles(directory="./static", url_prefix="/static")

    Configuration:

    *  ``directory``  -- filesystem path containing the files.
    *  ``url_prefix`` -- URL path prefix (requests must start with this).
    *  ``max_age``    -- ``Cache-Control`` max-age in seconds.
    *  ``index_file`` -- fallback file for directory requests.
    """

    def __init__(
        self,
        directory: str,
        url_prefix: str = "/static",
        max_age: int = 3600,
        index_file: str = "index.html",
    ) -> None:
        self.directory = os.path.realpath(directory)
        self.url_prefix = url_prefix.rstrip("/")
        self.max_age = max_age
        self.index_file = index_file

    # -- ASGI entry point ----------------------------------------------------

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        assert scope["type"] == "http"
        path: str = scope.get("path", "")

        # Must match prefix
        if not path.startswith(self.url_prefix):
            await self._send_text(send, 404, b"Not Found")
            return

        relative = path[len(self.url_prefix) :].lstrip("/")
        if not relative:
            relative = self.index_file

        # Resolve safely
        try:
            filepath = _safe_join(self.directory, relative)
        except PathTraversalError:
            await self._send_text(send, 403, b"Forbidden")
            return

        # Find the file (support directory -> index fallback)
        if os.path.isdir(filepath):
            index_path = os.path.join(filepath, self.index_file)
            if os.path.isfile(index_path):
                filepath = index_path
            else:
                await self._send_text(send, 404, b"Not Found")
                return
        elif not os.path.isfile(filepath):
            await self._send_text(send, 404, b"Not Found")
            return

        # Check 304 Not Modified
        request_headers = self._parse_headers(scope.get("headers", []))
        etag = f'"{_generate_etag(filepath)}"'

        if_none_match = request_headers.get("if-none-match", "")
        if if_none_match and if_none_match == etag:
            await self._send_304(send, filepath, etag)
            return

        if_modified_since = request_headers.get("if-modified-since", "")
        if if_modified_since:
            try:
                since = parsedate_to_datetime(if_modified_since)
                mtime = datetime.fromtimestamp(
                    os.stat(filepath).st_mtime, tz=timezone.utc
                )
                if mtime.replace(microsecond=0) <= since.replace(microsecond=0):
                    await self._send_304(send, filepath, etag)
                    return
            except (ValueError, OSError):
                pass

        # Serve file
        try:
            with open(filepath, "rb") as fh:
                content = fh.read()
        except OSError:
            await self._send_text(send, 500, b"Internal Server Error")
            return

        content_type = _guess_content_type(filepath)
        last_modified = formatdate(os.stat(filepath).st_mtime, usegmt=True)
        cache_control = f"public, max-age={self.max_age}"

        response_headers = [
            (b"content-type", content_type.encode()),
            (b"content-length", str(len(content)).encode()),
            (b"etag", etag.encode()),
            (b"last-modified", last_modified.encode()),
            (b"cache-control", cache_control.encode()),
        ]

        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": response_headers,
        })
        await send({
            "type": "http.response.body",
            "body": content,
        })

    # -- Internal helpers ----------------------------------------------------

    @staticmethod
    def _parse_headers(raw: list[tuple[bytes, bytes]]) -> dict[str, str]:
        """Convert ASGI raw headers to a lowercase dict."""
        return {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in raw
        }

    @staticmethod
    async def _send_text(
        send: Callable,
        status: int,
        body: bytes,
    ) -> None:
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"text/plain")],
        })
        await send({"type": "http.response.body", "body": body})

    async def _send_304(
        self,
        send: Callable,
        filepath: str,
        etag: str,
    ) -> None:
        last_modified = formatdate(os.stat(filepath).st_mtime, usegmt=True)
        cache_control = f"public, max-age={self.max_age}"
        headers = [
            (b"etag", etag.encode()),
            (b"last-modified", last_modified.encode()),
            (b"cache-control", cache_control.encode()),
        ]
        await send({
            "type": "http.response.start",
            "status": 304,
            "headers": headers,
        })
        await send({"type": "http.response.body", "body": b""})
