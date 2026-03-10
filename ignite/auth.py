"""
Ignite Authentication Module

JWT implementation using only the standard library (base64url + HMAC-SHA256).
Provides ``create_token()``, ``verify_token()``, and ``AuthMiddleware``.

Imports from sibling ignite modules: middleware, request, response, exceptions.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Callable

from ignite.exceptions import HTTPException
from ignite.middleware import Middleware
from ignite.request import Request
from ignite.response import JSONResponse, Response


# ---------------------------------------------------------------------------
# Base64-URL helpers (JWT spec requires unpadded URL-safe base64)
# ---------------------------------------------------------------------------

def _base64url_encode(data: bytes) -> str:
    """Base64url-encode *data* without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(s: str) -> bytes:
    """Base64url-decode *s*, re-adding padding as needed."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


# ---------------------------------------------------------------------------
# Token creation / verification
# ---------------------------------------------------------------------------

def create_token(
    payload: dict[str, Any],
    secret: str,
    *,
    expires_in: int = 3600,
) -> str:
    """Create a JWT signed with HMAC-SHA256.

    Args:
        payload:    Claims to include (``sub``, ``role``, etc.).
        secret:     Signing key.
        expires_in: Lifetime in seconds (default 3600).

    Returns:
        A ``header.payload.signature`` JWT string.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(
        json.dumps(header, separators=(",", ":")).encode()
    )

    now = int(time.time())
    full_payload = {
        "iat": now,
        "exp": now + expires_in,
        **payload,
    }
    payload_b64 = _base64url_encode(
        json.dumps(full_payload, separators=(",", ":")).encode()
    )

    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()
    signature_b64 = _base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_token(token: str, secret: str) -> dict[str, Any] | None:
    """Verify a JWT and return the payload, or ``None`` on failure.

    Checks structure, HMAC signature, and ``exp`` expiration.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None

    header_b64, payload_b64, signature_b64 = parts

    # Verify signature
    signing_input = f"{header_b64}.{payload_b64}"
    expected_sig = hmac.new(
        secret.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()
    expected_b64 = _base64url_encode(expected_sig)

    if not hmac.compare_digest(signature_b64, expected_b64):
        return None

    # Decode payload
    try:
        payload_bytes = _base64url_decode(payload_b64)
        payload: dict[str, Any] = json.loads(payload_bytes)
    except (json.JSONDecodeError, ValueError):
        return None

    # Check expiration
    exp = payload.get("exp")
    if exp is not None and int(time.time()) > exp:
        return None

    return payload


def decode_token_unsafe(token: str) -> dict[str, Any] | None:
    """Decode the payload **without** verifying the signature.

    Useful for debugging -- never use for authentication.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        return json.loads(_base64url_decode(parts[1]))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# AuthMiddleware
# ---------------------------------------------------------------------------

class AuthMiddleware(Middleware):
    """ASGI middleware that verifies JWT Bearer tokens.

    Requests to *public_paths* are passed through without checks.
    All other requests must include an ``Authorization: Bearer <token>``
    header.  On success the decoded payload is stored in
    ``scope["user"]``.
    """

    def __init__(
        self,
        app: Any,
        secret: str,
        *,
        public_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.secret = secret
        self.public_paths: set[str] = set(public_paths or [])

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Public paths skip authentication
        if request.path in self.public_paths:
            await self.app(scope, receive, send)
            return

        # Extract bearer token
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            response = JSONResponse(
                {"error": {"status_code": 401, "detail": "Missing authentication token"}},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        token = auth_header[7:]
        payload = verify_token(token, self.secret)

        if payload is None:
            response = JSONResponse(
                {"error": {"status_code": 401, "detail": "Invalid or expired token"}},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        # Attach user payload to scope for downstream handlers
        scope["user"] = payload
        await self.app(scope, receive, send)
