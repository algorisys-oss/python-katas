# Kata 71 -- Static Files

[prev: 70-cli-tool](./70-cli-tool.md) | [next: 72-template-rendering](./72-template-rendering.md)

---

## What We're Building

A **static file server** for our Ignite framework. Serve CSS, JavaScript, images, and other assets from a directory with proper HTTP semantics:

1. **MIME type detection** -- serve files with correct `Content-Type` headers
2. **Path traversal security** -- prevent `../../../etc/passwd` attacks
3. **Cache headers** -- ETag, Last-Modified, Cache-Control for performance
4. **304 Not Modified** -- save bandwidth when files haven't changed

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `mimetypes.guess_type()` | Map file extension to MIME type | Setting Content-Type |
| `os.path.realpath()` | Resolve symlinks and `..` | Path traversal prevention |
| ETag headers | Content fingerprint for caching | Conditional requests |
| `If-None-Match` | Client sends cached ETag | 304 Not Modified |
| `If-Modified-Since` | Client sends cached timestamp | 304 Not Modified |
| `Cache-Control` | Cache policy directives | Browser/CDN caching |

## The Code

### 1. MIME Type Detection

```python
import mimetypes

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")

def guess_content_type(filepath):
    content_type, _ = mimetypes.guess_type(filepath)
    return content_type or "application/octet-stream"

# guess_content_type("style.css")   -> "text/css"
# guess_content_type("app.js")      -> "application/javascript"
# guess_content_type("unknown.qzx") -> "application/octet-stream"
```

### 2. Path Traversal Security

```python
def safe_join(base_dir, *paths):
    base = os.path.realpath(base_dir)
    requested = os.path.realpath(os.path.join(base, *paths))

    if not requested.startswith(base + os.sep) and requested != base:
        raise PathTraversalError(f"Path escapes {base_dir}")

    return requested

# safe_join("/static", "css/style.css") -> "/static/css/style.css"
# safe_join("/static", "../../etc/passwd") -> PathTraversalError!
```

### 3. Cache Headers

```python
class CacheHeaders:
    def generate_etag(self, filepath):
        stat = os.stat(filepath)
        fingerprint = f"{stat.st_size}-{stat.st_mtime}"
        return hashlib.md5(fingerprint.encode()).hexdigest()

    def is_not_modified(self, filepath, request_headers):
        if_none_match = request_headers.get("If-None-Match")
        if if_none_match == f'"{self.generate_etag(filepath)}"':
            return True  # Client has current version
        return False
```

### 4. Static File Handler

```python
class StaticFileHandler:
    def handle(self, path, request_headers=None):
        # Strip URL prefix -> relative path
        # Resolve safely with safe_join()
        # Check 304 Not Modified
        # Read file and serve with correct headers
        ...
```

## Playground

```bash
python playground/71_static_files.py
```

Expected output:

```
--- Section 1: MIME Type Detection ---
  style.css            -> text/css                       [ok]
  app.js               -> application/javascript         [ok]
  ...
  [PASS] MIME type detection works

--- Section 2: Path Traversal Security ---
  safe_join(base, 'safe.txt') -> OK
  safe_join(base, ('../../../etc/passwd',)) -> BLOCKED
  [PASS] Path traversal security works

--- Section 5: Static File Handler ---
  GET /static/css/style.css -> 200 (text/css)
  GET /static/js/app.js -> 200 (application/javascript)
  GET /static/../../../etc/passwd -> 403
  [PASS] Static file handler works
```

## How It Works

### Request Flow

```
GET /static/css/style.css
    |
    v
Strip prefix "/static" -> "css/style.css"
    |
    v
safe_join(directory, "css/style.css")
    |  Resolves to absolute path
    |  Checks it's within directory
    v
File exists?
    |
    +-- NO -> 404 Not Found
    |
    +-- YES
          |
          v
        Client has If-None-Match or If-Modified-Since?
          |
          +-- YES, matches -> 304 Not Modified (empty body)
          |
          +-- NO
                |
                v
              Read file content
              Detect MIME type
              Generate cache headers
                |
                v
              200 OK
              Content-Type: text/css
              ETag: "a1b2c3..."
              Cache-Control: public, max-age=3600
              Body: [file content]
```

### Path Traversal Attack

```
Attacker requests: /static/../../../etc/passwd

Without protection:
  os.path.join("/app/static", "../../../etc/passwd")
  -> "/etc/passwd"  (EXPOSED!)

With safe_join():
  base = "/app/static"
  resolved = os.path.realpath("/app/static/../../../etc/passwd")
  -> "/etc/passwd"
  Does "/etc/passwd" start with "/app/static/"?
  -> NO! Raise PathTraversalError -> 403 Forbidden
```

### Cache Header Timeline

```
First request:
  Client: GET /static/style.css
  Server: 200 OK
          ETag: "abc123"
          Last-Modified: Mon, 15 Jan 2024 10:30:00 GMT

Second request (file unchanged):
  Client: GET /static/style.css
          If-None-Match: "abc123"
  Server: 304 Not Modified (no body sent!)

After file is edited:
  Client: GET /static/style.css
          If-None-Match: "abc123"
  Server: 200 OK (new ETag: "def456")
```

## Exercises

1. **Add range requests** -- support `Range: bytes=0-1023` headers for partial file downloads. Return 206 Partial Content with the requested byte range.

2. **Add directory listing** -- when a directory is requested without an index file, generate an HTML page listing the directory contents.

3. **Add file compression** -- support `Accept-Encoding: gzip` and serve pre-compressed `.gz` files if they exist, or compress on-the-fly for text files.

4. **Add asset fingerprinting** -- generate fingerprinted filenames like `style.a1b2c3.css` and serve them with immutable caching (max-age=1 year).

5. **Add security headers** -- add `X-Content-Type-Options: nosniff` and `Content-Security-Policy` headers to prevent MIME sniffing and XSS attacks.

## What's Next

With static file serving, our Ignite framework can serve CSS, JavaScript, and images alongside dynamic routes. In [Kata 72: Template Rendering](./72-template-rendering.md), we'll build a minimal template engine with variable substitution, control flow, template inheritance, and filters.

---

[prev: 70-cli-tool](./70-cli-tool.md) | [next: 72-template-rendering](./72-template-rendering.md)
