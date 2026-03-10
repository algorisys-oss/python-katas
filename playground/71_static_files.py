"""
Kata 71 -- Static Files
Run: python playground/71_static_files.py

Build static file serving: map URL paths to filesystem, MIME type
detection with mimetypes module, cache headers (ETag, Last-Modified,
Cache-Control), 304 Not Modified support, and path traversal security.

Completes within 5 seconds.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import tempfile
import time
from datetime import datetime, timezone
from email.utils import formatdate, parsedate_to_datetime
from typing import Any


# ===========================================================================
# SECTION 1: MIME Type Detection
# ===========================================================================
# Map file extensions to content types using Python's mimetypes module.

# Ensure common web types are registered
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")


def guess_content_type(filepath: str) -> str:
    """Guess the MIME type of a file based on its extension.

    Falls back to 'application/octet-stream' for unknown types.
    """
    content_type, _ = mimetypes.guess_type(filepath)
    return content_type or "application/octet-stream"


# ===========================================================================
# SECTION 2: Path Security
# ===========================================================================
# Prevent path traversal attacks (../ in the URL path).

class PathTraversalError(Exception):
    """Raised when a path traversal attack is detected."""
    pass


def safe_join(base_dir: str, *paths: str) -> str:
    """Safely join paths, preventing traversal outside base_dir.

    This is critical for security: without it, a request for
    '../../../etc/passwd' could expose system files.

    Args:
        base_dir: The root directory (e.g., './static/')
        *paths: Path components from the URL

    Returns:
        The resolved absolute path, guaranteed to be within base_dir.

    Raises:
        PathTraversalError: If the resolved path escapes base_dir.
    """
    # Normalize the base directory to an absolute path
    base = os.path.realpath(base_dir)

    # Join and resolve the requested path
    requested = os.path.realpath(os.path.join(base, *paths))

    # Verify the resolved path is within the base directory
    if not requested.startswith(base + os.sep) and requested != base:
        raise PathTraversalError(
            f"Path traversal detected: {paths!r} escapes {base_dir!r}"
        )

    return requested


# ===========================================================================
# SECTION 3: Cache Headers
# ===========================================================================
# Generate cache-related HTTP headers: ETag, Last-Modified, Cache-Control.

class CacheHeaders:
    """Generate cache-related HTTP headers for static files."""

    def __init__(
        self,
        max_age: int = 3600,
        immutable: bool = False,
        public: bool = True,
    ):
        self.max_age = max_age
        self.immutable = immutable
        self.public = public

    def generate_etag(self, filepath: str) -> str:
        """Generate an ETag based on file content hash.

        Uses MD5 of (file size + mtime) for speed. For truly
        content-based ETags, hash the file content itself.
        """
        stat = os.stat(filepath)
        # Use size + mtime as a fast fingerprint
        fingerprint = f"{stat.st_size}-{stat.st_mtime}".encode()
        return hashlib.md5(fingerprint).hexdigest()

    def get_last_modified(self, filepath: str) -> str:
        """Get the Last-Modified header value in HTTP date format."""
        mtime = os.stat(filepath).st_mtime
        return formatdate(mtime, usegmt=True)

    def get_cache_control(self) -> str:
        """Build the Cache-Control header value."""
        parts: list[str] = []
        parts.append("public" if self.public else "private")
        parts.append(f"max-age={self.max_age}")
        if self.immutable:
            parts.append("immutable")
        return ", ".join(parts)

    def build_headers(self, filepath: str) -> dict[str, str]:
        """Build all cache headers for a file."""
        return {
            "ETag": f'"{self.generate_etag(filepath)}"',
            "Last-Modified": self.get_last_modified(filepath),
            "Cache-Control": self.get_cache_control(),
        }

    def is_not_modified(
        self,
        filepath: str,
        request_headers: dict[str, str],
    ) -> bool:
        """Check if the file has not been modified (for 304 responses).

        Checks two mechanisms:
        1. If-None-Match: compare ETag
        2. If-Modified-Since: compare modification time
        """
        # Check ETag (If-None-Match)
        if_none_match = request_headers.get("If-None-Match", "")
        if if_none_match:
            current_etag = f'"{self.generate_etag(filepath)}"'
            if if_none_match == current_etag:
                return True

        # Check Last-Modified (If-Modified-Since)
        if_modified_since = request_headers.get("If-Modified-Since", "")
        if if_modified_since:
            try:
                since = parsedate_to_datetime(if_modified_since)
                mtime = datetime.fromtimestamp(
                    os.stat(filepath).st_mtime, tz=timezone.utc
                )
                # Compare with second precision (HTTP dates are seconds)
                if mtime.replace(microsecond=0) <= since.replace(microsecond=0):
                    return True
            except (ValueError, OSError):
                pass

        return False


# ===========================================================================
# SECTION 4: Static File Handler
# ===========================================================================
# The main handler that serves static files from a directory.

class Response:
    """Simplified HTTP response."""
    def __init__(
        self,
        body: bytes = b"",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}

    def __repr__(self) -> str:
        return (f"Response(status={self.status_code}, "
                f"body_len={len(self.body)}, "
                f"headers={list(self.headers.keys())})")


class StaticFileHandler:
    """Serve static files from a directory.

    Features:
    - MIME type detection
    - Cache headers (ETag, Last-Modified, Cache-Control)
    - 304 Not Modified responses
    - Path traversal protection
    - Index file support (index.html)

    Usage:
        handler = StaticFileHandler('./static', url_prefix='/static')
        response = handler.handle('/static/css/style.css', {})
    """

    def __init__(
        self,
        directory: str,
        url_prefix: str = "/static",
        max_age: int = 3600,
        index_file: str = "index.html",
    ):
        self.directory = os.path.realpath(directory)
        self.url_prefix = url_prefix.rstrip("/")
        self.cache = CacheHeaders(max_age=max_age)
        self.index_file = index_file

    def handle(
        self,
        path: str,
        request_headers: dict[str, str] | None = None,
    ) -> Response:
        """Handle a request for a static file.

        Args:
            path: URL path (e.g., '/static/css/style.css')
            request_headers: HTTP request headers (for 304 checks)

        Returns:
            Response with file content or appropriate error.
        """
        request_headers = request_headers or {}

        # Strip the URL prefix to get the file path
        if not path.startswith(self.url_prefix):
            return Response(
                body=b"Not Found",
                status_code=404,
                headers={"Content-Type": "text/plain"},
            )

        relative_path = path[len(self.url_prefix):].lstrip("/")
        if not relative_path:
            relative_path = self.index_file

        # Resolve the path safely
        try:
            filepath = safe_join(self.directory, relative_path)
        except PathTraversalError:
            return Response(
                body=b"Forbidden",
                status_code=403,
                headers={"Content-Type": "text/plain"},
            )

        # Check if file exists
        if not os.path.isfile(filepath):
            # Try index file for directories
            if os.path.isdir(filepath):
                index_path = os.path.join(filepath, self.index_file)
                if os.path.isfile(index_path):
                    filepath = index_path
                else:
                    return Response(
                        body=b"Not Found",
                        status_code=404,
                        headers={"Content-Type": "text/plain"},
                    )
            else:
                return Response(
                    body=b"Not Found",
                    status_code=404,
                    headers={"Content-Type": "text/plain"},
                )

        # Check for 304 Not Modified
        if self.cache.is_not_modified(filepath, request_headers):
            return Response(
                status_code=304,
                headers=self.cache.build_headers(filepath),
            )

        # Serve the file
        try:
            with open(filepath, "rb") as f:
                content = f.read()
        except OSError:
            return Response(
                body=b"Internal Server Error",
                status_code=500,
                headers={"Content-Type": "text/plain"},
            )

        content_type = guess_content_type(filepath)
        headers = self.cache.build_headers(filepath)
        headers["Content-Type"] = content_type
        headers["Content-Length"] = str(len(content))

        return Response(
            body=content,
            status_code=200,
            headers=headers,
        )


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def create_test_static_dir() -> str:
    """Create a temporary static directory with test files."""
    tmpdir = tempfile.mkdtemp()

    # CSS file
    css_dir = os.path.join(tmpdir, "css")
    os.makedirs(css_dir)
    with open(os.path.join(css_dir, "style.css"), "w") as f:
        f.write("body { font-family: sans-serif; color: #333; }\n")

    # JS file
    js_dir = os.path.join(tmpdir, "js")
    os.makedirs(js_dir)
    with open(os.path.join(js_dir, "app.js"), "w") as f:
        f.write("console.log('Hello from Ignite!');\n")

    # HTML file
    with open(os.path.join(tmpdir, "index.html"), "w") as f:
        f.write("<html><body><h1>Welcome to Ignite</h1></body></html>\n")

    # Image (binary)
    img_dir = os.path.join(tmpdir, "images")
    os.makedirs(img_dir)
    with open(os.path.join(img_dir, "logo.png"), "wb") as f:
        # Minimal PNG header (not a real image, just for MIME test)
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

    # JSON file
    with open(os.path.join(tmpdir, "manifest.json"), "w") as f:
        f.write('{"name": "Ignite App", "version": "1.0.0"}\n')

    return tmpdir


def demo_mime_types():
    """Show MIME type detection."""
    print("--- Section 1: MIME Type Detection ---")

    test_files = [
        ("style.css", "text/css"),
        ("app.js", "application/javascript"),
        ("index.html", "text/html"),
        ("logo.png", "image/png"),
        ("photo.jpg", "image/jpeg"),
        ("data.json", "application/json"),
        ("icon.svg", "image/svg+xml"),
        ("font.woff2", "font/woff2"),
        ("readme.txt", "text/plain"),
        ("unknown.qzx", "application/octet-stream"),
    ]

    for filename, expected in test_files:
        detected = guess_content_type(filename)
        status = "ok" if detected == expected else f"MISMATCH: got {detected}"
        print(f"  {filename:<20} -> {detected:<30} [{status}]")
        assert detected == expected, (
            f"Expected {expected} for {filename}, got {detected}"
        )

    print("  [PASS] MIME type detection works")


def demo_path_security():
    """Show path traversal prevention."""
    print("\n--- Section 2: Path Traversal Security ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file inside the directory
        safe_file = os.path.join(tmpdir, "safe.txt")
        with open(safe_file, "w") as f:
            f.write("safe content")

        # Safe paths should work
        result = safe_join(tmpdir, "safe.txt")
        assert result == os.path.realpath(safe_file)
        print(f"  safe_join(base, 'safe.txt') -> OK")

        result2 = safe_join(tmpdir, "subdir", "file.txt")
        print(f"  safe_join(base, 'subdir', 'file.txt') -> OK")

        # Traversal attacks should be blocked
        attack_paths = [
            ("../../../etc/passwd",),
            ("..", "..", "etc", "passwd"),
            ("subdir", "..", "..", "secret.key"),
        ]

        for parts in attack_paths:
            try:
                safe_join(tmpdir, *parts)
                assert False, f"Should have raised PathTraversalError for {parts}"
            except PathTraversalError as e:
                print(f"  safe_join(base, {parts!r}) -> BLOCKED: {e}")

    print("  [PASS] Path traversal security works")


def demo_cache_headers():
    """Show cache header generation."""
    print("\n--- Section 3: Cache Headers ---")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".css",
                                      delete=False) as f:
        f.write("body { color: red; }\n")
        temp_path = f.name

    try:
        cache = CacheHeaders(max_age=86400, public=True)

        headers = cache.build_headers(temp_path)
        print(f"  Cache headers for {os.path.basename(temp_path)}:")
        for key, value in headers.items():
            print(f"    {key}: {value}")

        assert "ETag" in headers
        assert headers["ETag"].startswith('"') and headers["ETag"].endswith('"')
        assert "Last-Modified" in headers
        assert "Cache-Control" in headers
        assert "max-age=86400" in headers["Cache-Control"]
        assert "public" in headers["Cache-Control"]

        # Immutable cache
        immutable_cache = CacheHeaders(max_age=31536000, immutable=True)
        cc = immutable_cache.get_cache_control()
        print(f"\n  Immutable cache: {cc}")
        assert "immutable" in cc
        assert "max-age=31536000" in cc

        # Private cache
        private_cache = CacheHeaders(max_age=0, public=False)
        cc2 = private_cache.get_cache_control()
        print(f"  Private cache: {cc2}")
        assert "private" in cc2

    finally:
        os.unlink(temp_path)

    print("  [PASS] Cache headers work")


def demo_304_not_modified():
    """Show 304 Not Modified responses."""
    print("\n--- Section 4: 304 Not Modified ---")

    tmpdir = create_test_static_dir()
    try:
        handler = StaticFileHandler(tmpdir, url_prefix="/static")

        # First request -- should return 200
        resp1 = handler.handle("/static/css/style.css")
        assert resp1.status_code == 200
        print(f"  First request: {resp1.status_code} "
              f"({len(resp1.body)} bytes)")

        # Second request with ETag -- should return 304
        etag = resp1.headers["ETag"]
        resp2 = handler.handle(
            "/static/css/style.css",
            request_headers={"If-None-Match": etag},
        )
        assert resp2.status_code == 304
        assert len(resp2.body) == 0
        print(f"  With ETag ({etag}): {resp2.status_code} (not modified)")

        # With If-Modified-Since
        last_modified = resp1.headers["Last-Modified"]
        resp3 = handler.handle(
            "/static/css/style.css",
            request_headers={"If-Modified-Since": last_modified},
        )
        assert resp3.status_code == 304
        print(f"  With If-Modified-Since: {resp3.status_code} (not modified)")

        # With stale ETag -- should return 200
        resp4 = handler.handle(
            "/static/css/style.css",
            request_headers={"If-None-Match": '"stale-etag"'},
        )
        assert resp4.status_code == 200
        print(f"  With stale ETag: {resp4.status_code} (full response)")

    finally:
        import shutil
        shutil.rmtree(tmpdir)

    print("  [PASS] 304 Not Modified works")


def demo_static_handler():
    """Show the full static file handler."""
    print("\n--- Section 5: Static File Handler ---")

    tmpdir = create_test_static_dir()
    try:
        handler = StaticFileHandler(tmpdir, url_prefix="/static")

        # Serve CSS
        resp = handler.handle("/static/css/style.css")
        assert resp.status_code == 200
        assert resp.headers["Content-Type"] == "text/css"
        assert b"font-family" in resp.body
        print(f"  GET /static/css/style.css -> {resp.status_code} "
              f"({resp.headers['Content-Type']})")

        # Serve JS
        resp2 = handler.handle("/static/js/app.js")
        assert resp2.status_code == 200
        assert resp2.headers["Content-Type"] == "application/javascript"
        print(f"  GET /static/js/app.js -> {resp2.status_code} "
              f"({resp2.headers['Content-Type']})")

        # Serve PNG (binary)
        resp3 = handler.handle("/static/images/logo.png")
        assert resp3.status_code == 200
        assert resp3.headers["Content-Type"] == "image/png"
        print(f"  GET /static/images/logo.png -> {resp3.status_code} "
              f"({resp3.headers['Content-Type']})")

        # Serve JSON
        resp4 = handler.handle("/static/manifest.json")
        assert resp4.status_code == 200
        assert resp4.headers["Content-Type"] == "application/json"
        print(f"  GET /static/manifest.json -> {resp4.status_code} "
              f"({resp4.headers['Content-Type']})")

        # Index file
        resp5 = handler.handle("/static/")
        assert resp5.status_code == 200
        assert b"Welcome to Ignite" in resp5.body
        print(f"  GET /static/ -> {resp5.status_code} (index.html)")

        # 404 for missing file
        resp6 = handler.handle("/static/missing.txt")
        assert resp6.status_code == 404
        print(f"  GET /static/missing.txt -> {resp6.status_code}")

        # 403 for path traversal
        resp7 = handler.handle("/static/../../../etc/passwd")
        assert resp7.status_code == 403
        print(f"  GET /static/../../../etc/passwd -> {resp7.status_code}")

        # 404 for wrong prefix
        resp8 = handler.handle("/assets/style.css")
        assert resp8.status_code == 404
        print(f"  GET /assets/style.css -> {resp8.status_code} (wrong prefix)")

    finally:
        import shutil
        shutil.rmtree(tmpdir)

    print("  [PASS] Static file handler works")


def demo_cache_strategies():
    """Show different caching strategies."""
    print("\n--- Section 6: Cache Strategies ---")

    print("  Strategy 1: Development (no caching)")
    dev_cache = CacheHeaders(max_age=0, public=False)
    print(f"    Cache-Control: {dev_cache.get_cache_control()}")

    print("\n  Strategy 2: Standard (1 hour)")
    std_cache = CacheHeaders(max_age=3600, public=True)
    print(f"    Cache-Control: {std_cache.get_cache_control()}")

    print("\n  Strategy 3: Aggressive (1 year, immutable)")
    print("    For fingerprinted assets: style.a1b2c3.css")
    agg_cache = CacheHeaders(max_age=31536000, immutable=True)
    print(f"    Cache-Control: {agg_cache.get_cache_control()}")

    print("\n  Strategy 4: Private (user-specific)")
    priv_cache = CacheHeaders(max_age=300, public=False)
    print(f"    Cache-Control: {priv_cache.get_cache_control()}")

    print("  [PASS] Cache strategies demonstrated")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_mime_types()
    demo_path_security()
    demo_cache_headers()
    demo_304_not_modified()
    demo_static_handler()
    demo_cache_strategies()

    print("\n--- Summary ---")
    print("Static file serving gives our Ignite framework:")
    print("  - MIME type detection for all common web file types")
    print("  - Path traversal protection (prevents ../ attacks)")
    print("  - Cache headers: ETag, Last-Modified, Cache-Control")
    print("  - 304 Not Modified for bandwidth savings")
    print("  - Index file support for directories")
    print("  - Multiple caching strategies (dev/standard/aggressive)")
    print("\nAll 6 sections passed. Static files mastered!")
    print("Next up: Kata 72 -- template rendering!")


if __name__ == "__main__":
    main()
