"""
Kata 62 -- Cookie Handling
Run: python playground/62_cookie_handling.py

Build cookie handling for Ignite. Parse Cookie headers into dicts,
build Set-Cookie headers with all attributes (path, domain, max-age,
expires, secure, httponly, samesite), Cookie class with builder pattern,
and delete cookies by setting max-age=0.

Completes within 5 seconds.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


# ===========================================================================
# SECTION 1: Parse Cookie Header
# ===========================================================================
# The Cookie header sent by browsers is a simple key=value; key=value string.
# We parse it into a Python dict for easy access.

def parse_cookie_header(header: str) -> dict[str, str]:
    """Parse a Cookie request header into a dict.

    Format: "name1=value1; name2=value2; name3=value3"
    Values may contain '=' (e.g., base64 data), so we split on first '=' only.
    """
    cookies: dict[str, str] = {}
    if not header or not header.strip():
        return cookies

    for pair in header.split(";"):
        pair = pair.strip()
        if "=" in pair:
            name, value = pair.split("=", 1)
            cookies[name.strip()] = value.strip()
        elif pair:
            # Cookie with no value (rare but valid)
            cookies[pair.strip()] = ""

    return cookies


# ===========================================================================
# SECTION 2: Cookie Class with Builder Pattern
# ===========================================================================
# A Cookie object that builds a proper Set-Cookie header string.
# Uses a builder (fluent) pattern: cookie.secure().httponly().samesite("Strict")

class Cookie:
    """Represents a Set-Cookie header with all standard attributes.

    Builder pattern lets you chain attribute setters:
        Cookie("session", "abc123").path("/").secure().httponly().samesite("Lax")
    """

    def __init__(self, name: str, value: str = ""):
        self.name = name
        self.value = value
        self._path: str | None = None
        self._domain: str | None = None
        self._max_age: int | None = None
        self._expires: str | None = None
        self._is_secure: bool = False
        self._is_httponly: bool = False
        self._samesite: str | None = None  # "Strict", "Lax", or "None"

    # -- Builder methods (each returns self for chaining) --

    def path(self, path: str) -> Cookie:
        """Set the Path attribute (URL scope for the cookie)."""
        self._path = path
        return self

    def domain(self, domain: str) -> Cookie:
        """Set the Domain attribute (which domains receive the cookie)."""
        self._domain = domain
        return self

    def max_age(self, seconds: int) -> Cookie:
        """Set Max-Age in seconds (how long the cookie lives)."""
        self._max_age = seconds
        return self

    def expires(self, dt: datetime) -> Cookie:
        """Set the Expires attribute from a datetime object.

        Converts to HTTP date format: Thu, 01 Jan 2099 00:00:00 GMT
        """
        # HTTP date format per RFC 7231
        self._expires = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        return self

    def secure(self) -> Cookie:
        """Set the Secure flag (cookie only sent over HTTPS)."""
        self._is_secure = True
        return self

    def httponly(self) -> Cookie:
        """Set the HttpOnly flag (cookie not accessible via JavaScript)."""
        self._is_httponly = True
        return self

    def samesite(self, policy: str) -> Cookie:
        """Set SameSite attribute: 'Strict', 'Lax', or 'None'.

        - Strict: cookie only sent for same-site requests
        - Lax: cookie sent for same-site + top-level navigations
        - None: cookie sent for all requests (requires Secure flag)
        """
        if policy not in ("Strict", "Lax", "None"):
            raise ValueError(f"SameSite must be Strict, Lax, or None; got {policy!r}")
        self._samesite = policy
        return self

    def to_header(self) -> str:
        """Build the full Set-Cookie header value.

        Format: name=value; Path=/; Domain=.example.com; Max-Age=3600; ...
        """
        parts = [f"{self.name}={self.value}"]

        if self._path is not None:
            parts.append(f"Path={self._path}")
        if self._domain is not None:
            parts.append(f"Domain={self._domain}")
        if self._max_age is not None:
            parts.append(f"Max-Age={self._max_age}")
        if self._expires is not None:
            parts.append(f"Expires={self._expires}")
        if self._is_secure:
            parts.append("Secure")
        if self._is_httponly:
            parts.append("HttpOnly")
        if self._samesite is not None:
            parts.append(f"SameSite={self._samesite}")

        return "; ".join(parts)

    def __repr__(self) -> str:
        return f"Cookie({self.name!r}, {self.value!r})"


# ===========================================================================
# SECTION 3: Delete Cookie Helper
# ===========================================================================
# Deleting a cookie means setting Max-Age=0 and an empty value.
# The browser removes the cookie when it receives this response.

def delete_cookie(name: str, path: str = "/", domain: str | None = None) -> Cookie:
    """Create a Set-Cookie that tells the browser to delete a cookie.

    Sets value to empty and Max-Age=0. Path and Domain must match
    the original cookie for the browser to actually delete it.
    """
    cookie = Cookie(name, "").path(path).max_age(0)
    if domain:
        cookie.domain(domain)
    return cookie


# ===========================================================================
# SECTION 4: CookieJar (Request/Response Integration)
# ===========================================================================
# A CookieJar manages cookies for a simulated request/response cycle.

class CookieJar:
    """Manages cookies for request parsing and response building.

    Usage:
        jar = CookieJar()
        jar.load("session=abc; theme=dark")      # parse request Cookie header
        jar.set("token", "xyz").secure().httponly()  # add response cookie
        headers = jar.response_headers()          # get Set-Cookie headers
    """

    def __init__(self):
        self._request_cookies: dict[str, str] = {}
        self._response_cookies: list[Cookie] = []

    def load(self, cookie_header: str) -> None:
        """Parse a Cookie request header and store the values."""
        self._request_cookies = parse_cookie_header(cookie_header)

    def get(self, name: str, default: str | None = None) -> str | None:
        """Get a cookie value from the parsed request cookies."""
        return self._request_cookies.get(name, default)

    def set(self, name: str, value: str) -> Cookie:
        """Create a response cookie. Returns the Cookie for chaining."""
        cookie = Cookie(name, value)
        self._response_cookies.append(cookie)
        return cookie

    def delete(self, name: str, path: str = "/") -> None:
        """Add a delete-cookie header to the response."""
        self._response_cookies.append(delete_cookie(name, path))

    def response_headers(self) -> list[tuple[str, str]]:
        """Get all Set-Cookie headers for the response."""
        return [
            ("Set-Cookie", cookie.to_header())
            for cookie in self._response_cookies
        ]

    @property
    def request_cookies(self) -> dict[str, str]:
        """All parsed request cookies."""
        return dict(self._request_cookies)


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_parse_cookie_header():
    """Show parsing Cookie request headers."""
    print("--- Section 1: Parse Cookie Header ---")

    # Simple cookies
    header = "session=abc123; theme=dark; lang=en"
    cookies = parse_cookie_header(header)
    print(f"  Parsed: {cookies}")
    assert cookies == {"session": "abc123", "theme": "dark", "lang": "en"}

    # Value with equals sign (e.g., base64)
    header2 = "token=eyJhbGc=; id=42"
    cookies2 = parse_cookie_header(header2)
    print(f"  With '=' in value: {cookies2}")
    assert cookies2["token"] == "eyJhbGc="
    assert cookies2["id"] == "42"

    # Empty header
    assert parse_cookie_header("") == {}
    assert parse_cookie_header("   ") == {}

    # Single cookie
    cookies3 = parse_cookie_header("name=value")
    assert cookies3 == {"name": "value"}

    print("  [PASS] Cookie header parsing works")


def demo_cookie_builder():
    """Show Cookie class with builder pattern."""
    print("\n--- Section 2: Cookie Builder Pattern ---")

    # Basic cookie
    c1 = Cookie("session", "abc123")
    print(f"  Basic: {c1.to_header()}")
    assert c1.to_header() == "session=abc123"

    # Full-featured cookie with chaining
    c2 = (
        Cookie("session", "abc123")
        .path("/")
        .domain(".example.com")
        .max_age(3600)
        .secure()
        .httponly()
        .samesite("Lax")
    )
    header = c2.to_header()
    print(f"  Full: {header}")
    assert "Path=/" in header
    assert "Domain=.example.com" in header
    assert "Max-Age=3600" in header
    assert "Secure" in header
    assert "HttpOnly" in header
    assert "SameSite=Lax" in header

    # Cookie with expires
    future = datetime(2099, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    c3 = Cookie("remember", "yes").expires(future)
    header3 = c3.to_header()
    print(f"  Expires: {header3}")
    assert "Expires=" in header3

    # SameSite=None requires Secure
    c4 = Cookie("cross", "val").samesite("None").secure()
    header4 = c4.to_header()
    print(f"  SameSite=None: {header4}")
    assert "SameSite=None" in header4
    assert "Secure" in header4

    # Invalid SameSite
    try:
        Cookie("x", "y").samesite("Invalid")
        assert False, "Should have raised"
    except ValueError as e:
        print(f"  Invalid SameSite caught: {e}")

    print("  [PASS] Cookie builder works")


def demo_delete_cookie():
    """Show cookie deletion."""
    print("\n--- Section 3: Delete Cookie ---")

    dc = delete_cookie("session")
    header = dc.to_header()
    print(f"  Delete header: {header}")
    assert "session=" in header
    assert "Max-Age=0" in header
    assert "Path=/" in header

    # With domain
    dc2 = delete_cookie("tracker", path="/app", domain=".example.com")
    header2 = dc2.to_header()
    print(f"  Delete with domain: {header2}")
    assert "Domain=.example.com" in header2
    assert "Path=/app" in header2
    assert "Max-Age=0" in header2

    print("  [PASS] Cookie deletion works")


def demo_cookie_jar():
    """Show CookieJar for request/response integration."""
    print("\n--- Section 4: CookieJar ---")

    jar = CookieJar()

    # Simulate incoming request with cookies
    jar.load("session=old_token; theme=dark")
    print(f"  Request cookies: {jar.request_cookies}")
    assert jar.get("session") == "old_token"
    assert jar.get("theme") == "dark"
    assert jar.get("missing") is None
    assert jar.get("missing", "default") == "default"

    # Set new response cookies
    jar.set("session", "new_token").path("/").secure().httponly()
    jar.set("preference", "compact").path("/").max_age(86400)

    # Delete a cookie
    jar.delete("theme")

    # Get response headers
    headers = jar.response_headers()
    print(f"  Response headers ({len(headers)}):")
    for name, value in headers:
        print(f"    {name}: {value}")

    assert len(headers) == 3
    assert headers[0][0] == "Set-Cookie"
    assert "session=new_token" in headers[0][1]
    assert "Secure" in headers[0][1]
    assert "preference=compact" in headers[1][1]
    assert "Max-Age=0" in headers[2][1]  # delete

    print("  [PASS] CookieJar works")


def demo_secure_cookie_scenarios():
    """Show real-world cookie security patterns."""
    print("\n--- Section 5: Security Scenarios ---")

    # Scenario 1: Session cookie (strictest security)
    session = (
        Cookie("__Host-session", "encrypted_data")
        .path("/")
        .secure()
        .httponly()
        .samesite("Strict")
    )
    header = session.to_header()
    print(f"  Session: {header}")
    assert "Secure" in header
    assert "HttpOnly" in header
    assert "SameSite=Strict" in header

    # Scenario 2: CSRF cookie (readable by JavaScript, same-site)
    csrf = (
        Cookie("csrf_token", "random_token_value")
        .path("/")
        .samesite("Strict")
        .max_age(3600)
    )
    header2 = csrf.to_header()
    print(f"  CSRF: {header2}")
    assert "HttpOnly" not in header2  # JS needs to read this
    assert "SameSite=Strict" in header2

    # Scenario 3: Remember-me cookie (long-lived)
    remember = (
        Cookie("remember_me", "user_hash")
        .path("/")
        .max_age(30 * 24 * 3600)  # 30 days
        .secure()
        .httponly()
        .samesite("Lax")
    )
    header3 = remember.to_header()
    print(f"  Remember-me: {header3}")
    assert "Max-Age=2592000" in header3

    # Scenario 4: Third-party cookie (cross-origin)
    tracking = (
        Cookie("_analytics", "visitor_id")
        .path("/")
        .domain(".analytics.example.com")
        .samesite("None")
        .secure()  # Required with SameSite=None
    )
    header4 = tracking.to_header()
    print(f"  Third-party: {header4}")
    assert "SameSite=None" in header4
    assert "Secure" in header4

    print("  [PASS] Security scenarios work")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_parse_cookie_header()
    demo_cookie_builder()
    demo_delete_cookie()
    demo_cookie_jar()
    demo_secure_cookie_scenarios()

    print("\n--- Summary ---")
    print("Cookie handling gives our Ignite framework:")
    print("  - Parse Cookie request headers into dicts")
    print("  - Cookie class with builder pattern for Set-Cookie headers")
    print("  - All attributes: Path, Domain, Max-Age, Expires, Secure, HttpOnly, SameSite")
    print("  - Delete cookies by setting Max-Age=0")
    print("  - CookieJar for request/response integration")
    print("  - Security patterns for sessions, CSRF, and cross-origin cookies")
    print("\nAll 5 sections passed. Cookie handling mastered!")
    print("Next up: Kata 63 -- session middleware!")


if __name__ == "__main__":
    main()
