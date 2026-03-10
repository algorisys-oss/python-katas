"""Ignite Response classes — ASGI-compatible response objects."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Callable


class Response:
    """Base ASGI response that sends a body with status and headers.

    Sending a response in ASGI means calling send() twice:
    1. 'http.response.start' with status + headers
    2. 'http.response.body' with the actual content
    """

    media_type: str | None = None
    charset: str = "utf-8"

    def __init__(
        self,
        content: str | bytes = b"",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.media_type = media_type or self.__class__.media_type

        if isinstance(content, str):
            self.body = content.encode(self.charset)
        else:
            self.body = content

        self.raw_headers = self._build_headers(headers or {})

    def _build_headers(
        self, extra_headers: dict[str, str]
    ) -> list[tuple[bytes, bytes]]:
        """Build ASGI-format headers (list of byte pairs)."""
        headers: dict[str, str] = {}

        if self.media_type:
            ct = self.media_type
            if self.charset and "text" in ct:
                ct += f"; charset={self.charset}"
            headers["content-type"] = ct

        headers["content-length"] = str(len(self.body))

        for key, value in extra_headers.items():
            headers[key.lower()] = value

        return [(k.encode(), v.encode()) for k, v in headers.items()]

    async def __call__(
        self, scope: dict, receive: Callable, send: Callable
    ) -> None:
        """ASGI interface: send the response."""
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": self.raw_headers,
        })
        await send({
            "type": "http.response.body",
            "body": self.body,
        })


class JSONResponse(Response):
    """Response that serializes content as JSON."""

    media_type = "application/json"

    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(content, ensure_ascii=False).encode("utf-8")
        super().__init__(
            content=body,
            status_code=status_code,
            headers=headers,
            media_type=self.media_type,
        )


class HTMLResponse(Response):
    """Response that serves HTML content."""

    media_type = "text/html"

    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=self.media_type,
        )


class PlainTextResponse(Response):
    """Response that serves plain text content."""

    media_type = "text/plain"

    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=self.media_type,
        )


class RedirectResponse(Response):
    """Response that redirects the client to a different URL."""

    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: dict[str, str] | None = None,
    ) -> None:
        redirect_headers = dict(headers) if headers else {}
        redirect_headers["location"] = url
        super().__init__(
            content=b"",
            status_code=status_code,
            headers=redirect_headers,
        )


class StreamingResponse:
    """Response that streams content in chunks.

    Useful for large files or server-sent events where you don't
    want to buffer the entire response in memory.
    """

    def __init__(
        self,
        content_iterator: AsyncIterator,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str = "application/octet-stream",
    ) -> None:
        self.content_iterator = content_iterator
        self.status_code = status_code
        self.media_type = media_type

        raw_headers: dict[str, str] = {"content-type": media_type}
        if headers:
            for k, v in headers.items():
                raw_headers[k.lower()] = v
        self.raw_headers = [
            (k.encode(), v.encode()) for k, v in raw_headers.items()
        ]

    async def __call__(
        self, scope: dict, receive: Callable, send: Callable
    ) -> None:
        """Send the response as a stream of chunks."""
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": self.raw_headers,
        })

        async for chunk in self.content_iterator:
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            await send({
                "type": "http.response.body",
                "body": chunk,
                "more_body": True,
            })

        await send({
            "type": "http.response.body",
            "body": b"",
            "more_body": False,
        })
