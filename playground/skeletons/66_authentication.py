"""
Kata 66 -- Authentication
Run: python playground/skeletons/66_authentication.py

Build JWT authentication for Ignite WITHOUT PyJWT -- implement JWT
manually using stdlib (base64url encode header+payload, HMAC-SHA256
signature). Build: create_token(), verify_token(), AuthMiddleware,
get_current_user() dependency for Depends(). Protected route decorator.

Completes within 5 seconds.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Base64URL Encoding (JWT Requirement)
# ===========================================================================
# JWT uses base64url encoding (RFC 4648): URL-safe base64 without padding.
# Standard base64 uses +/ and = padding; base64url uses -_ and no padding.

def base64url_encode(data: bytes) -> str:
    """Base64url encode without padding (as required by JWT spec)."""
    # TODO: Use base64.urlsafe_b64encode, strip "=" padding, decode to str
    pass


def base64url_decode(s: str) -> bytes:
    """Base64url decode, adding back padding as needed."""
    # TODO: Add "=" padding so length is multiple of 4, then decode
    # padding = 4 - len(s) % 4
    # if padding != 4: s += "=" * padding
    pass


# ===========================================================================
# SECTION 2: JWT Creation and Verification
# ===========================================================================
# A JWT has three parts separated by dots: header.payload.signature
#
# Header:  {"alg": "HS256", "typ": "JWT"} -- base64url encoded
# Payload: {"sub": "user_id", "exp": 1234567890, ...} -- base64url encoded
# Signature: HMAC-SHA256(header.payload, secret) -- base64url encoded

def create_token(
    payload: dict[str, Any],
    secret: str,
    expires_in: int = 3600,
) -> str:
    """Create a JWT token with HMAC-SHA256 signature.

    Args:
        payload: Claims to include (sub, name, role, etc.)
        secret: Secret key for signing
        expires_in: Token lifetime in seconds (default 1 hour)

    Returns:
        JWT string: "header.payload.signature"
    """
    # TODO: Step 1 -- Build the header {"alg": "HS256", "typ": "JWT"}
    #       JSON-encode with separators=(",", ":") and base64url_encode

    # TODO: Step 2 -- Build the payload
    #       Add "iat" (current timestamp) and "exp" (iat + expires_in)
    #       Merge with user-provided payload, JSON-encode and base64url_encode

    # TODO: Step 3 -- Create the signature
    #       signing_input = f"{header_b64}.{payload_b64}"
    #       HMAC-SHA256 of signing_input using secret
    #       base64url_encode the signature bytes

    # TODO: Step 4 -- Return f"{header_b64}.{payload_b64}.{signature_b64}"
    pass


def verify_token(token: str, secret: str) -> dict[str, Any] | None:
    """Verify a JWT token and return the payload.

    Checks:
    1. Token has three parts
    2. Signature is valid (HMAC-SHA256)
    3. Token has not expired (exp claim)

    Returns None if verification fails.
    """
    # TODO: Step 1 -- Split token on "." and verify 3 parts

    # TODO: Step 2 -- Verify signature
    #       Recompute HMAC-SHA256 of header.payload
    #       Compare with base64url_decode(signature) using hmac.compare_digest

    # TODO: Step 3 -- Decode payload from base64url to JSON

    # TODO: Step 4 -- Check expiration (if exp > 0 and time.time() > exp, return None)

    # TODO: Return payload dict
    pass


def decode_token_unsafe(token: str) -> dict[str, Any] | None:
    """Decode a JWT payload WITHOUT verifying the signature.

    Useful for inspecting tokens during debugging.
    NEVER use this for authentication.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        return json.loads(base64url_decode(parts[1]))
    except Exception:
        return None


# ===========================================================================
# SECTION 3: User and Auth Context
# ===========================================================================

class User:
    """Represents an authenticated user extracted from a JWT."""

    def __init__(self, user_id: str, username: str, role: str = "user"):
        self.user_id = user_id
        self.username = username
        self.role = role

    def __repr__(self) -> str:
        return f"User(id={self.user_id!r}, username={self.username!r}, role={self.role!r})"


# ===========================================================================
# SECTION 4: Request / Response / Middleware
# ===========================================================================

class Request:
    """Simulated HTTP request with auth support."""

    def __init__(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
    ):
        self.method = method.upper()
        self.path = path
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        self.user: User | None = None

    def get_header(self, name: str) -> str | None:
        return self.headers.get(name.lower())


class Response:
    """Simulated HTTP response."""

    def __init__(self, body: Any = None, status_code: int = 200):
        self.body = body
        self.status_code = status_code

    def __repr__(self) -> str:
        return f"Response(status={self.status_code}, body={self.body})"


class AuthMiddleware:
    """Middleware that extracts and verifies JWT from the Authorization header.

    Reads the "Authorization: Bearer <token>" header, verifies the JWT,
    and attaches a User object to request.user.
    """

    def __init__(
        self,
        handler: Callable[[Request], Response],
        secret: str,
        public_paths: list[str] | None = None,
    ):
        self.handler = handler
        self.secret = secret
        self.public_paths = set(public_paths or [])

    def __call__(self, request: Request) -> Response:
        """Process request through authentication."""
        # TODO: 1. If path is public, pass through to self.handler

        # TODO: 2. Extract "Authorization" header
        #       If missing or doesn't start with "Bearer ", return 401

        # TODO: 3. Extract token (remove "Bearer " prefix)
        #       Verify with verify_token(). If None, return 401

        # TODO: 4. Create User from payload (sub, username, role)
        #       Attach to request.user

        # TODO: 5. Call and return self.handler(request)
        pass

    def _is_public(self, path: str) -> bool:
        """Check if a path is public (no auth required)."""
        return path in self.public_paths


# ===========================================================================
# SECTION 5: get_current_user() Dependency
# ===========================================================================

def get_current_user(request: Request) -> User:
    """Dependency that returns the authenticated user.

    Raises ValueError if no user is attached (not authenticated).
    """
    # TODO: If request.user is None, raise ValueError("Not authenticated")
    #       Otherwise return request.user
    pass


def require_role(role: str) -> Callable[[Request], User]:
    """Create a dependency that requires a specific role.

    Usage: admin_user = Depends(require_role("admin"))
    """
    # TODO: Return a function that:
    #   1. Calls get_current_user(request) to get the user
    #   2. If user.role != role, raise PermissionError
    #   3. Return the user
    pass


# ===========================================================================
# SECTION 6: Protected Route Decorator
# ===========================================================================

def protected(secret: str):
    """Decorator that protects a route with JWT authentication.

    Usage:
        @protected("my-secret")
        def admin_panel(request):
            return Response({"user": request.user.username})
    """
    # TODO: Return a decorator that wraps a handler function.
    # The wrapper should:
    #   1. Extract Authorization header, check for "Bearer "
    #   2. Verify the token
    #   3. Create User from payload and attach to request.user
    #   4. Call the original function
    #   5. Return 401 if any auth step fails
    pass


# ===========================================================================
# SECTION 7: Demos
# ===========================================================================

def demo_base64url():
    """Show base64url encoding used by JWT."""
    print("--- Section 1: Base64URL Encoding ---")
    try:
        data = b'{"alg":"HS256","typ":"JWT"}'
        encoded = base64url_encode(data)
        print(f"  Encoded: {encoded}")
        assert "=" not in encoded  # No padding
        assert "+" not in encoded  # URL-safe
        assert "/" not in encoded

        decoded = base64url_decode(encoded)
        assert decoded == data
        print(f"  Decoded: {decoded.decode()}")

        print("  [PASS] Base64URL encoding works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_create_verify_token():
    """Show JWT creation and verification."""
    print("\n--- Section 2: JWT Create & Verify ---")
    try:
        secret = "my-jwt-secret"

        # Create a token
        token = create_token(
            payload={"sub": "user_42", "username": "alice", "role": "admin"},
            secret=secret,
            expires_in=3600,
        )
        print(f"  Token: {token[:50]}...")
        parts = token.split(".")
        assert len(parts) == 3
        print(f"  Parts: header({len(parts[0])}), payload({len(parts[1])}), sig({len(parts[2])})")

        # Verify the token
        payload = verify_token(token, secret)
        print(f"  Payload: {payload}")
        assert payload is not None
        assert payload["sub"] == "user_42"
        assert payload["username"] == "alice"
        assert payload["role"] == "admin"
        assert "iat" in payload
        assert "exp" in payload

        # Wrong secret
        assert verify_token(token, "wrong-secret") is None
        print("  Wrong secret: rejected")

        # Tampered token
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        assert verify_token(tampered, secret) is None
        print("  Tampered token: rejected")

        # Malformed token
        assert verify_token("not.a.valid.token", secret) is None
        assert verify_token("onlyonepart", secret) is None
        print("  Malformed token: rejected")

        # Decode without verification (for debugging)
        unsafe = decode_token_unsafe(token)
        print(f"  Unsafe decode: {unsafe}")
        assert unsafe["sub"] == "user_42"

        print("  [PASS] JWT create & verify works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_expired_token():
    """Show token expiration handling."""
    print("\n--- Section 3: Token Expiration ---")
    try:
        secret = "expiry-secret"

        # Create an already-expired token (expires_in = -10 seconds)
        token = create_token(
            payload={"sub": "user_1"},
            secret=secret,
            expires_in=-10,  # Already expired
        )
        result = verify_token(token, secret)
        print(f"  Expired token: {result}")
        assert result is None

        # Create a valid token (expires in 1 hour)
        token2 = create_token(
            payload={"sub": "user_2"},
            secret=secret,
            expires_in=3600,
        )
        result2 = verify_token(token2, secret)
        print(f"  Valid token: sub={result2['sub']}")
        assert result2 is not None

        print("  [PASS] Token expiration works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_auth_middleware():
    """Show AuthMiddleware protecting routes."""
    print("\n--- Section 4: Auth Middleware ---")
    try:
        secret = "auth-secret"

        def handler(request: Request) -> Response:
            if request.user:
                return Response(body={"user": request.user.username, "role": request.user.role})
            return Response(body={"message": "public page"})

        middleware = AuthMiddleware(
            handler, secret,
            public_paths=["/", "/login", "/health"],
        )

        # Public path -- no auth needed
        req1 = Request("GET", "/")
        resp1 = middleware(req1)
        print(f"  GET / (public): status={resp1.status_code}")
        assert resp1.status_code == 200

        # Protected path -- no token
        req2 = Request("GET", "/dashboard")
        resp2 = middleware(req2)
        print(f"  GET /dashboard (no token): status={resp2.status_code}")
        assert resp2.status_code == 401

        # Protected path -- valid token
        token = create_token(
            {"sub": "u1", "username": "alice", "role": "admin"},
            secret,
        )
        req3 = Request("GET", "/dashboard", headers={"Authorization": f"Bearer {token}"})
        resp3 = middleware(req3)
        print(f"  GET /dashboard (valid): status={resp3.status_code}, body={resp3.body}")
        assert resp3.status_code == 200
        assert resp3.body["user"] == "alice"

        # Protected path -- invalid token
        req4 = Request("GET", "/dashboard", headers={"Authorization": "Bearer invalid.token.here"})
        resp4 = middleware(req4)
        print(f"  GET /dashboard (invalid): status={resp4.status_code}")
        assert resp4.status_code == 401

        # Wrong auth scheme
        req5 = Request("GET", "/dashboard", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        resp5 = middleware(req5)
        print(f"  GET /dashboard (Basic auth): status={resp5.status_code}")
        assert resp5.status_code == 401

        print("  [PASS] Auth middleware works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_dependencies():
    """Show get_current_user() and require_role() dependencies."""
    print("\n--- Section 5: Dependencies ---")
    try:
        secret = "dep-secret"

        # Simulate authenticated request
        token = create_token(
            {"sub": "u42", "username": "bob", "role": "editor"},
            secret,
        )
        req = Request("GET", "/me", headers={"Authorization": f"Bearer {token}"})

        # Simulate middleware setting user
        payload = verify_token(token, secret)
        req.user = User(
            user_id=payload["sub"],
            username=payload["username"],
            role=payload["role"],
        )

        # get_current_user
        user = get_current_user(req)
        print(f"  Current user: {user}")
        assert user.username == "bob"
        assert user.role == "editor"

        # require_role -- matching role
        editor_dep = require_role("editor")
        editor_user = editor_dep(req)
        assert editor_user.username == "bob"
        print(f"  require_role('editor'): OK")

        # require_role -- wrong role
        admin_dep = require_role("admin")
        try:
            admin_dep(req)
            assert False, "Should have raised"
        except PermissionError as e:
            print(f"  require_role('admin'): {e}")

        # Unauthenticated request
        req2 = Request("GET", "/me")
        try:
            get_current_user(req2)
            assert False, "Should have raised"
        except ValueError as e:
            print(f"  No user: {e}")

        print("  [PASS] Dependencies work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_protected_decorator():
    """Show @protected route decorator."""
    print("\n--- Section 6: Protected Decorator ---")
    try:
        secret = "decorator-secret"

        @protected(secret)
        def admin_panel(request: Request) -> Response:
            return Response(body={"admin": request.user.username})

        # Without token
        req1 = Request("GET", "/admin")
        resp1 = admin_panel(req1)
        print(f"  No token: status={resp1.status_code}")
        assert resp1.status_code == 401

        # With valid token
        token = create_token(
            {"sub": "a1", "username": "admin_alice", "role": "admin"},
            secret,
        )
        req2 = Request("GET", "/admin", headers={"Authorization": f"Bearer {token}"})
        resp2 = admin_panel(req2)
        print(f"  Valid token: status={resp2.status_code}, body={resp2.body}")
        assert resp2.status_code == 200
        assert resp2.body["admin"] == "admin_alice"

        # With expired token
        expired = create_token({"sub": "a1", "username": "alice"}, secret, expires_in=-10)
        req3 = Request("GET", "/admin", headers={"Authorization": f"Bearer {expired}"})
        resp3 = admin_panel(req3)
        print(f"  Expired token: status={resp3.status_code}")
        assert resp3.status_code == 401

        print("  [PASS] Protected decorator works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_base64url()
    demo_create_verify_token()
    demo_expired_token()
    demo_auth_middleware()
    demo_dependencies()
    demo_protected_decorator()

    print("\n--- Summary ---")
    print("Authentication gives our Ignite framework:")
    print("  - Manual JWT implementation (no PyJWT dependency)")
    print("  - Base64URL encoding per the JWT spec")
    print("  - HMAC-SHA256 token signing and verification")
    print("  - Token expiration with 'exp' claim")
    print("  - AuthMiddleware with public/protected paths")
    print("  - get_current_user() and require_role() dependencies")
    print("  - @protected decorator for route-level auth")
    print("\nAll 6 sections passed. Authentication mastered!")
    print("Next up: Kata 67 -- hot reload!")


if __name__ == "__main__":
    main()
