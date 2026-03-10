"""
Kata 63 -- Session Middleware
Run: python playground/63_session_middleware.py

Build session middleware for Ignite. Sign session data with HMAC-SHA256
to prevent tampering. Session class with dict-like interface.
SessionMiddleware that loads session from cookie on request and saves
on response. Support session backends (cookie-based, in-memory).

Completes within 5 seconds.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Session Signing (HMAC-SHA256)
# ===========================================================================
# We sign session data so clients cannot tamper with it.
# The signature is appended to the data: "base64_data.signature"

def sign_data(data: str, secret: str) -> str:
    """Sign a string with HMAC-SHA256.

    Returns: "base64_data.hex_signature"
    The data is base64-encoded so it's safe for cookies.
    """
    # Encode the data as base64
    b64_data = base64.urlsafe_b64encode(data.encode()).decode()

    # Create HMAC-SHA256 signature of the base64 data
    signature = hmac.new(
        secret.encode(),
        b64_data.encode(),
        hashlib.sha256,
    ).hexdigest()

    return f"{b64_data}.{signature}"


def verify_and_decode(signed: str, secret: str) -> str | None:
    """Verify a signed string and return the original data.

    Returns None if the signature is invalid (data was tampered with).
    """
    if "." not in signed:
        return None

    b64_data, signature = signed.rsplit(".", 1)

    # Recompute the expected signature
    expected = hmac.new(
        secret.encode(),
        b64_data.encode(),
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(signature, expected):
        return None

    try:
        return base64.urlsafe_b64decode(b64_data.encode()).decode()
    except Exception:
        return None


# ===========================================================================
# SECTION 2: Session Class (Dict-like Interface)
# ===========================================================================
# Session wraps a dict and tracks whether it has been modified.
# Only modified sessions need to be saved back to the cookie/store.

class Session:
    """Dict-like session object that tracks modifications.

    Supports standard dict operations:
        session["user_id"] = 42
        name = session.get("name", "anonymous")
        del session["temp_key"]
        if "user_id" in session: ...
    """

    def __init__(self, data: dict[str, Any] | None = None):
        self._data: dict[str, Any] = data or {}
        self._modified: bool = False

    @property
    def modified(self) -> bool:
        """Whether the session has been changed since loading."""
        return self._modified

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._modified = True

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self._modified = True

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value with an optional default."""
        return self._data.get(key, default)

    def pop(self, key: str, *args: Any) -> Any:
        """Remove and return a value."""
        result = self._data.pop(key, *args)
        self._modified = True
        return result

    def clear(self) -> None:
        """Remove all session data."""
        self._data.clear()
        self._modified = True

    def to_dict(self) -> dict[str, Any]:
        """Get a copy of the session data."""
        return dict(self._data)

    def __repr__(self) -> str:
        return f"Session({self._data}, modified={self._modified})"


# ===========================================================================
# SECTION 3: Session Backends
# ===========================================================================
# Two backends: CookieBackend stores data in the cookie itself (signed),
# MemoryBackend stores data server-side keyed by session ID.

class SessionBackend:
    """Base interface for session storage backends."""

    def load(self, session_id: str) -> dict[str, Any] | None:
        """Load session data for the given ID. Returns None if not found."""
        raise NotImplementedError

    def save(self, session_id: str, data: dict[str, Any]) -> None:
        """Save session data for the given ID."""
        raise NotImplementedError

    def delete(self, session_id: str) -> None:
        """Delete session data for the given ID."""
        raise NotImplementedError


class CookieBackend(SessionBackend):
    """Store session data directly in a signed cookie.

    Pros: No server-side storage needed, horizontally scalable.
    Cons: Limited to ~4KB, data visible to client (though signed).
    """

    def __init__(self, secret: str):
        self.secret = secret

    def load(self, cookie_value: str) -> dict[str, Any] | None:
        """Decode and verify a signed cookie value."""
        raw = verify_and_decode(cookie_value, self.secret)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None

    def save(self, _session_id: str, data: dict[str, Any]) -> str:
        """Serialize and sign session data. Returns the signed cookie value."""
        raw = json.dumps(data, separators=(",", ":"))
        return sign_data(raw, self.secret)

    def delete(self, _session_id: str) -> None:
        """Cookie backend deletion is handled by clearing the cookie."""
        pass


class MemoryBackend(SessionBackend):
    """Store session data in server memory, keyed by session ID.

    Pros: No size limit, data not visible to client.
    Cons: Lost on restart, not shared across processes.
    """

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    def load(self, session_id: str) -> dict[str, Any] | None:
        """Look up session data by ID."""
        return self._store.get(session_id)

    def save(self, session_id: str, data: dict[str, Any]) -> None:
        """Store session data by ID."""
        self._store[session_id] = data

    def delete(self, session_id: str) -> None:
        """Remove session data."""
        self._store.pop(session_id, None)


# ===========================================================================
# SECTION 4: Session Middleware
# ===========================================================================
# Loads session from cookie on request, saves on response.
# Wraps the ASGI-style request/response cycle.

class Request:
    """Simulated HTTP request with cookies and session."""

    def __init__(self, method: str, path: str, cookies: dict[str, str] | None = None):
        self.method = method
        self.path = path
        self.cookies = cookies or {}
        self.session: Session = Session()  # Populated by middleware


class Response:
    """Simulated HTTP response with headers."""

    def __init__(self, body: Any, status_code: int = 200):
        self.body = body
        self.status_code = status_code
        self.headers: dict[str, str] = {}
        self._cookies: list[str] = []

    def set_cookie(self, header_value: str) -> None:
        """Add a Set-Cookie header."""
        self._cookies.append(header_value)

    @property
    def cookie_headers(self) -> list[str]:
        return list(self._cookies)


class SessionMiddleware:
    """Middleware that manages session loading and saving.

    On each request:
    1. Read the session cookie from the request
    2. Load session data from the backend
    3. Attach a Session object to the request
    4. Call the next handler
    5. If the session was modified, save it and set the cookie
    """

    def __init__(
        self,
        handler: Callable[[Request], Response],
        backend: SessionBackend,
        secret: str,
        cookie_name: str = "session",
        max_age: int = 3600,
    ):
        self.handler = handler
        self.backend = backend
        self.secret = secret
        self.cookie_name = cookie_name
        self.max_age = max_age

    def __call__(self, request: Request) -> Response:
        """Process a request through the session middleware."""
        # Step 1: Load session from cookie
        cookie_value = request.cookies.get(self.cookie_name, "")
        session_data = None

        if cookie_value:
            if isinstance(self.backend, CookieBackend):
                # Cookie backend: the cookie value IS the signed session data
                session_data = self.backend.load(cookie_value)
            else:
                # Server-side backend: cookie value is the session ID
                verified_id = verify_and_decode(cookie_value, self.secret)
                if verified_id:
                    session_data = self.backend.load(verified_id)

        # Step 2: Create Session object
        request.session = Session(session_data)

        # Step 3: Call the actual request handler
        response = self.handler(request)

        # Step 4: Save session if modified
        if request.session.modified:
            data = request.session.to_dict()
            if isinstance(self.backend, CookieBackend):
                # Cookie backend: save returns the signed cookie value
                cookie_val = self.backend.save("", data)
                response.set_cookie(
                    f"{self.cookie_name}={cookie_val}; "
                    f"Path=/; Max-Age={self.max_age}; HttpOnly; SameSite=Lax"
                )
            else:
                # Server-side backend: generate a session ID
                session_id = secrets.token_hex(16)
                self.backend.save(session_id, data)
                signed_id = sign_data(session_id, self.secret)
                response.set_cookie(
                    f"{self.cookie_name}={signed_id}; "
                    f"Path=/; Max-Age={self.max_age}; HttpOnly; SameSite=Lax"
                )

        return response


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_signing():
    """Show HMAC-SHA256 signing and verification."""
    print("--- Section 1: HMAC-SHA256 Signing ---")

    secret = "my-secret-key"
    data = '{"user_id":42,"role":"admin"}'

    # Sign
    signed = sign_data(data, secret)
    print(f"  Original: {data}")
    print(f"  Signed:   {signed[:60]}...")

    # Verify
    decoded = verify_and_decode(signed, secret)
    print(f"  Decoded:  {decoded}")
    assert decoded == data

    # Tamper detection
    tampered = signed[:-1] + ("a" if signed[-1] != "a" else "b")
    result = verify_and_decode(tampered, secret)
    print(f"  Tampered: {result}")
    assert result is None

    # Wrong secret
    result2 = verify_and_decode(signed, "wrong-secret")
    print(f"  Wrong secret: {result2}")
    assert result2 is None

    # Malformed input
    assert verify_and_decode("no-dot-here", secret) is None
    assert verify_and_decode("", secret) is None

    print("  [PASS] Signing and verification works")


def demo_session_class():
    """Show Session dict-like interface."""
    print("\n--- Section 2: Session Class ---")

    session = Session()
    assert not session.modified

    # Set values
    session["user_id"] = 42
    session["username"] = "alice"
    assert session.modified
    print(f"  After set: {session}")

    # Get values
    assert session["user_id"] == 42
    assert session.get("username") == "alice"
    assert session.get("missing", "default") == "default"

    # Contains
    assert "user_id" in session
    assert "missing" not in session

    # Delete
    del session["username"]
    assert "username" not in session

    # Pop
    val = session.pop("user_id", None)
    assert val == 42

    # Clear
    session["temp"] = True
    session.clear()
    assert session.to_dict() == {}
    print(f"  After clear: {session}")

    print("  [PASS] Session class works")


def demo_cookie_backend():
    """Show cookie-based session storage."""
    print("\n--- Section 3: Cookie Backend ---")

    secret = "cookie-secret-key"
    backend = CookieBackend(secret)

    # Save session data (returns signed cookie value)
    data = {"user_id": 42, "role": "admin"}
    cookie_value = backend.save("", data)
    print(f"  Saved cookie: {cookie_value[:50]}...")

    # Load session data
    loaded = backend.load(cookie_value)
    print(f"  Loaded: {loaded}")
    assert loaded == data

    # Tampered cookie
    tampered = cookie_value[:-1] + "X"
    assert backend.load(tampered) is None
    print("  Tampered cookie: rejected")

    print("  [PASS] Cookie backend works")


def demo_memory_backend():
    """Show in-memory session storage."""
    print("\n--- Section 4: Memory Backend ---")

    backend = MemoryBackend()

    # Save
    session_id = "sess_abc123"
    data = {"user_id": 99, "cart": ["item1", "item2"]}
    backend.save(session_id, data)

    # Load
    loaded = backend.load(session_id)
    print(f"  Loaded: {loaded}")
    assert loaded == data

    # Missing session
    assert backend.load("nonexistent") is None

    # Delete
    backend.delete(session_id)
    assert backend.load(session_id) is None
    print("  Deleted session: confirmed gone")

    print("  [PASS] Memory backend works")


def demo_session_middleware():
    """Show full session middleware flow."""
    print("\n--- Section 5: Session Middleware ---")

    secret = "middleware-secret"

    # --- Cookie backend flow ---
    print("  Cookie backend:")

    def login_handler(request: Request) -> Response:
        request.session["user_id"] = 42
        request.session["logged_in"] = True
        return Response({"message": "logged in"})

    middleware = SessionMiddleware(login_handler, CookieBackend(secret), secret)

    # First request: login (no existing cookie)
    req1 = Request("POST", "/login")
    resp1 = middleware(req1)
    print(f"    Login response: {resp1.body}")
    assert len(resp1.cookie_headers) == 1
    cookie_header = resp1.cookie_headers[0]
    print(f"    Set-Cookie: {cookie_header[:60]}...")
    assert "session=" in cookie_header
    assert "HttpOnly" in cookie_header

    # Extract the cookie value for the next request
    cookie_val = cookie_header.split("session=")[1].split(";")[0]

    # Second request: read session from cookie
    def profile_handler(request: Request) -> Response:
        uid = request.session.get("user_id")
        return Response({"user_id": uid})

    middleware2 = SessionMiddleware(profile_handler, CookieBackend(secret), secret)
    req2 = Request("GET", "/profile", cookies={"session": cookie_val})
    resp2 = middleware2(req2)
    print(f"    Profile response: {resp2.body}")
    assert resp2.body["user_id"] == 42

    # --- Memory backend flow ---
    print("  Memory backend:")

    mem_backend = MemoryBackend()

    def mem_login(request: Request) -> Response:
        request.session["user"] = "bob"
        return Response({"ok": True})

    mw = SessionMiddleware(mem_login, mem_backend, secret)
    req3 = Request("POST", "/login")
    resp3 = mw(req3)
    assert len(resp3.cookie_headers) == 1
    mem_cookie = resp3.cookie_headers[0]
    print(f"    Memory Set-Cookie: {mem_cookie[:60]}...")

    # Verify data is in the backend store
    assert len(mem_backend._store) == 1
    stored_data = list(mem_backend._store.values())[0]
    print(f"    Server-side data: {stored_data}")
    assert stored_data["user"] == "bob"

    print("  [PASS] Session middleware works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_signing()
    demo_session_class()
    demo_cookie_backend()
    demo_memory_backend()
    demo_session_middleware()

    print("\n--- Summary ---")
    print("Session middleware gives our Ignite framework:")
    print("  - HMAC-SHA256 signing to prevent tampering")
    print("  - Session class with dict-like interface and modification tracking")
    print("  - Cookie backend (data in signed cookie)")
    print("  - Memory backend (data server-side, ID in cookie)")
    print("  - SessionMiddleware that loads/saves sessions automatically")
    print("\nAll 5 sections passed. Session middleware mastered!")
    print("Next up: Kata 64 -- CORS middleware!")


if __name__ == "__main__":
    main()
