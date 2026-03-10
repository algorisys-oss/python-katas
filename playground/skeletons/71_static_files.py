"""
Kata 71 -- Static Files
Run: python playground/skeletons/71_static_files.py

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

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")


def guess_content_type(filepath: str) -> str:
    """Guess the MIME type of a file based on its extension."""
    # TODO: Use mimetypes.guess_type(filepath) to get the content type.
    # Return the content type, or "application/octet-stream" if unknown.
    return "application/octet-stream"


# ===========================================================================
# SECTION 2: Path Security
# ===========================================================================

class PathTraversalError(Exception):
    """Raised when a path traversal attack is detected."""
    pass


def safe_join(base_dir: str, *paths: str) -> str:
    """Safely join paths, preventing traversal outside base_dir.

    Args:
        base_dir: The root directory (e.g., './static/')
        *paths: Path components from the URL

    Returns:
        The resolved absolute path, guaranteed to be within base_dir.

    Raises:
        PathTraversalError: If the resolved path escapes base_dir.
    """
    # TODO: Implement path traversal protection:
    # 1. Normalize base_dir to absolute path: os.path.realpath(base_dir)
    # 2. Join and resolve the requested path:
    #    os.path.realpath(os.path.join(base, *paths))
    # 3. Check that resolved path starts with base + os.sep (or equals base)
    # 4. If not, raise PathTraversalError
    # 5. Return the resolved path
    return os.path.join(base_dir, *paths)


# ===========================================================================
# SECTION 3: Cache Headers
# ===========================================================================

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
        """Generate an ETag based on file content hash."""
        # TODO: Use os.stat(filepath) to get size and mtime.
        # Create a fingerprint string f"{size}-{mtime}" and
        # return its MD5 hex digest.
        return ""

    def get_last_modified(self, filepath: str) -> str:
        """Get the Last-Modified header value in HTTP date format."""
        # TODO: Get mtime from os.stat(filepath).st_mtime
        # Format with formatdate(mtime, usegmt=True)
        return ""

    def get_cache_control(self) -> str:
        """Build the Cache-Control header value."""
        # TODO: Build Cache-Control string from self.public,
        # self.max_age, and self.immutable.
        # Example: "public, max-age=3600" or "private, max-age=0"
        return ""

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

        Checks:
        1. If-None-Match: compare ETag
        2. If-Modified-Since: compare modification time
        """
        # TODO: Check If-None-Match header against current ETag.
        # If they match, return True.
        #
        # TODO: Check If-Modified-Since header against file mtime.
        # Parse the date with parsedate_to_datetime(), compare to
        # file mtime from os.stat(). If file hasn't changed, return True.
        #
        # Return False if neither condition is met.
        return False


# ===========================================================================
# SECTION 4: Static File Handler
# ===========================================================================

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
    """Serve static files from a directory."""

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
        """Handle a request for a static file."""
        request_headers = request_headers or {}

        # TODO: Implement the static file handler:
        #
        # 1. Check that path starts with self.url_prefix
        #    If not, return 404
        #
        # 2. Strip the prefix to get the relative file path
        #    If empty, use self.index_file
        #
        # 3. Resolve the path safely with safe_join()
        #    If PathTraversalError, return 403
        #
        # 4. Check if file exists (os.path.isfile)
        #    If directory, try index_file inside it
        #    If not found, return 404
        #
        # 5. Check for 304 Not Modified
        #    If self.cache.is_not_modified(filepath, request_headers),
        #    return Response(status_code=304, headers=cache_headers)
        #
        # 6. Read the file content (open in "rb" mode)
        #    Detect content type with guess_content_type()
        #    Build cache headers
        #    Return Response with body, 200, and headers

        return Response(body=b"Not Found", status_code=404,
                        headers={"Content-Type": "text/plain"})


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def create_test_static_dir() -> str:
    """Create a temporary static directory with test files."""
    tmpdir = tempfile.mkdtemp()

    css_dir = os.path.join(tmpdir, "css")
    os.makedirs(css_dir)
    with open(os.path.join(css_dir, "style.css"), "w") as f:
        f.write("body { font-family: sans-serif; color: #333; }\n")

    js_dir = os.path.join(tmpdir, "js")
    os.makedirs(js_dir)
    with open(os.path.join(js_dir, "app.js"), "w") as f:
        f.write("console.log('Hello from Ignite!');\n")

    with open(os.path.join(tmpdir, "index.html"), "w") as f:
        f.write("<html><body><h1>Welcome to Ignite</h1></body></html>\n")

    img_dir = os.path.join(tmpdir, "images")
    os.makedirs(img_dir)
    with open(os.path.join(img_dir, "logo.png"), "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

    with open(os.path.join(tmpdir, "manifest.json"), "w") as f:
        f.write('{"name": "Ignite App", "version": "1.0.0"}\n')

    return tmpdir


def demo_mime_types():
    """Show MIME type detection."""
    print("--- Section 1: MIME Type Detection ---")

    try:
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
            assert detected == expected

        print("  [PASS] MIME type detection works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_path_security():
    """Show path traversal prevention."""
    print("\n--- Section 2: Path Traversal Security ---")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_file = os.path.join(tmpdir, "safe.txt")
            with open(safe_file, "w") as f:
                f.write("safe content")

            result = safe_join(tmpdir, "safe.txt")
            assert result == os.path.realpath(safe_file)
            print(f"  safe_join(base, 'safe.txt') -> OK")

            result2 = safe_join(tmpdir, "subdir", "file.txt")
            print(f"  safe_join(base, 'subdir', 'file.txt') -> OK")

            attack_paths = [
                ("../../../etc/passwd",),
                ("..", "..", "etc", "passwd"),
                ("subdir", "..", "..", "secret.key"),
            ]

            for parts in attack_paths:
                try:
                    safe_join(tmpdir, *parts)
                    assert False, f"Should have raised for {parts}"
                except PathTraversalError as e:
                    print(f"  safe_join(base, {parts!r}) -> BLOCKED: {e}")

        print("  [PASS] Path traversal security works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_cache_headers():
    """Show cache header generation."""
    print("\n--- Section 3: Cache Headers ---")

    try:
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

            immutable_cache = CacheHeaders(max_age=31536000, immutable=True)
            cc = immutable_cache.get_cache_control()
            print(f"\n  Immutable cache: {cc}")
            assert "immutable" in cc

            private_cache = CacheHeaders(max_age=0, public=False)
            cc2 = private_cache.get_cache_control()
            print(f"  Private cache: {cc2}")
            assert "private" in cc2

        finally:
            os.unlink(temp_path)

        print("  [PASS] Cache headers work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_304_not_modified():
    """Show 304 Not Modified responses."""
    print("\n--- Section 4: 304 Not Modified ---")

    try:
        tmpdir = create_test_static_dir()
        try:
            handler = StaticFileHandler(tmpdir, url_prefix="/static")

            resp1 = handler.handle("/static/css/style.css")
            assert resp1.status_code == 200
            print(f"  First request: {resp1.status_code} "
                  f"({len(resp1.body)} bytes)")

            etag = resp1.headers["ETag"]
            resp2 = handler.handle(
                "/static/css/style.css",
                request_headers={"If-None-Match": etag},
            )
            assert resp2.status_code == 304
            assert len(resp2.body) == 0
            print(f"  With ETag ({etag}): {resp2.status_code} (not modified)")

            last_modified = resp1.headers["Last-Modified"]
            resp3 = handler.handle(
                "/static/css/style.css",
                request_headers={"If-Modified-Since": last_modified},
            )
            assert resp3.status_code == 304
            print(f"  With If-Modified-Since: {resp3.status_code} (not modified)")

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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_static_handler():
    """Show the full static file handler."""
    print("\n--- Section 5: Static File Handler ---")

    try:
        tmpdir = create_test_static_dir()
        try:
            handler = StaticFileHandler(tmpdir, url_prefix="/static")

            resp = handler.handle("/static/css/style.css")
            assert resp.status_code == 200
            assert resp.headers["Content-Type"] == "text/css"
            assert b"font-family" in resp.body
            print(f"  GET /static/css/style.css -> {resp.status_code} "
                  f"({resp.headers['Content-Type']})")

            resp2 = handler.handle("/static/js/app.js")
            assert resp2.status_code == 200
            assert resp2.headers["Content-Type"] == "application/javascript"
            print(f"  GET /static/js/app.js -> {resp2.status_code} "
                  f"({resp2.headers['Content-Type']})")

            resp3 = handler.handle("/static/images/logo.png")
            assert resp3.status_code == 200
            assert resp3.headers["Content-Type"] == "image/png"
            print(f"  GET /static/images/logo.png -> {resp3.status_code} "
                  f"({resp3.headers['Content-Type']})")

            resp4 = handler.handle("/static/manifest.json")
            assert resp4.status_code == 200
            assert resp4.headers["Content-Type"] == "application/json"
            print(f"  GET /static/manifest.json -> {resp4.status_code} "
                  f"({resp4.headers['Content-Type']})")

            resp5 = handler.handle("/static/")
            assert resp5.status_code == 200
            assert b"Welcome to Ignite" in resp5.body
            print(f"  GET /static/ -> {resp5.status_code} (index.html)")

            resp6 = handler.handle("/static/missing.txt")
            assert resp6.status_code == 404
            print(f"  GET /static/missing.txt -> {resp6.status_code}")

            resp7 = handler.handle("/static/../../../etc/passwd")
            assert resp7.status_code == 403
            print(f"  GET /static/../../../etc/passwd -> {resp7.status_code}")

            resp8 = handler.handle("/assets/style.css")
            assert resp8.status_code == 404
            print(f"  GET /assets/style.css -> {resp8.status_code} (wrong prefix)")

        finally:
            import shutil
            shutil.rmtree(tmpdir)

        print("  [PASS] Static file handler works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_cache_strategies():
    """Show different caching strategies."""
    print("\n--- Section 6: Cache Strategies ---")

    try:
        print("  Strategy 1: Development (no caching)")
        dev_cache = CacheHeaders(max_age=0, public=False)
        print(f"    Cache-Control: {dev_cache.get_cache_control()}")

        print("\n  Strategy 2: Standard (1 hour)")
        std_cache = CacheHeaders(max_age=3600, public=True)
        print(f"    Cache-Control: {std_cache.get_cache_control()}")

        print("\n  Strategy 3: Aggressive (1 year, immutable)")
        agg_cache = CacheHeaders(max_age=31536000, immutable=True)
        print(f"    Cache-Control: {agg_cache.get_cache_control()}")

        print("\n  Strategy 4: Private (user-specific)")
        priv_cache = CacheHeaders(max_age=300, public=False)
        print(f"    Cache-Control: {priv_cache.get_cache_control()}")

        print("  [PASS] Cache strategies demonstrated")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


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
    print("\nAll 6 sections attempted. Static files skeleton ready!")
    print("Next up: Kata 72 -- template rendering!")


if __name__ == "__main__":
    main()
