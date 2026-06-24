# Kata 64 -- CORS Middleware

[prev: 63-session-middleware](./63-session-middleware.md) | [next: 65-csrf-protection](./65-csrf-protection.md)

---

## What We're Building

**CORS (Cross-Origin Resource Sharing) middleware** for our Ignite framework. When a frontend app at `https://myapp.com` calls an API at `https://api.myapp.com`, the browser's same-origin policy steps in: for "simple" requests it still sends them but blocks JavaScript from *reading the response* unless the right CORS headers are present, and for non-simple requests it sends a preflight `OPTIONS` first and blocks the real request if the response doesn't allow it. CORS headers tell the browser which cross-origin requests are allowed. We build:

1. **CORSConfig** -- configurable allowed origins, methods, headers, and credentials
2. **Preflight handling** -- respond to OPTIONS requests with CORS permissions
3. **Response headers** -- add `Access-Control-Allow-*` headers to actual responses
4. **Credentials mode** -- handle cookies and auth headers in cross-origin requests

This is exactly what FastAPI's `CORSMiddleware`, Express.js `cors`, and Django's `django-cors-headers` do.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Same-origin policy | Browser blocks cross-origin requests by default | Understanding CORS need |
| Preflight request | Browser sends OPTIONS before "unsafe" requests | POST/PUT/DELETE with custom headers |
| `Access-Control-Allow-Origin` | Tells browser which origins can read the response | Every CORS response |
| `Access-Control-Allow-Methods` | Which HTTP methods are allowed | Preflight responses |
| `Access-Control-Allow-Headers` | Which request headers are allowed | Preflight responses |
| `Access-Control-Expose-Headers` | Which response headers JS can read | Custom response headers |
| `Access-Control-Allow-Credentials` | Allow cookies in cross-origin requests | Authenticated APIs |
| `Access-Control-Max-Age` | Cache preflight results (seconds) | Reducing preflight requests |
| `Vary: Origin` | Tell caches response varies by origin | Non-wildcard origins |

## The Code

### 1. CORS Configuration

```python
class CORSConfig:
    def __init__(self,
        allow_origins=["*"],           # Which origins can access
        allow_methods=["GET", "POST"], # Which methods are allowed
        allow_headers=["Content-Type"],# Which request headers
        expose_headers=[],             # Which response headers JS sees
        allow_credentials=False,       # Allow cookies?
        max_age=600,                   # Cache preflight (seconds)
    ): ...

    def is_origin_allowed(self, origin):
        return "*" in self.allow_origins or origin in self.allow_origins
```

### 2. Preflight Handling

```python
def _handle_preflight(self, request, origin):
    response = Response(status_code=204)  # No Content

    # Check requested method
    method = request.get_header("access-control-request-method")
    if not self.config.is_method_allowed(method):
        return response  # No CORS headers = browser blocks it

    # Add all CORS headers
    self._add_cors_headers(response, origin)
    response.set_header("Access-Control-Allow-Methods", "GET, POST, PUT")
    response.set_header("Access-Control-Allow-Headers", "Content-Type")
    response.set_header("Access-Control-Max-Age", "600")
    return response
```

### 3. CORS Headers

```python
def _add_cors_headers(self, response, origin):
    if self.config.allow_credentials or "*" not in self.config.allow_origins:
        response.set_header("Access-Control-Allow-Origin", origin)
        response.set_header("Vary", "Origin")
    else:
        response.set_header("Access-Control-Allow-Origin", "*")

    if self.config.allow_credentials:
        response.set_header("Access-Control-Allow-Credentials", "true")
```

## Playground

```
python playground/64_cors_middleware.py
```

Expected output:

```
--- Section 1: CORS Configuration ---
  Default config: all origins allowed
  Restricted config: only specific origins/methods
  [PASS] CORS configuration works

--- Section 2: Preflight Handling ---
  Preflight response: status=204
  Headers: {'Access-Control-Allow-Origin': 'https://myapp.com', ...}
  Disallowed origin: no CORS headers
  Disallowed method (DELETE): status=204
  [PASS] Preflight handling works

--- Section 3: Actual Requests ---
  Allowed: {...'Access-Control-Allow-Origin': 'https://myapp.com'...}
  Disallowed origin: CORS headers absent
  No Origin: passed through, no CORS headers
  [PASS] Actual request handling works

--- Section 4: Wildcard Origin ---
  Wildcard: *
  [PASS] Wildcard origin works

--- Section 5: Credentials Mode ---
  Origin: https://myapp.com
  Credentials: true
  Preflight with credentials: correct headers set
  [PASS] Credentials mode works

--- Section 6: Full CORS Flow ---
  1. Preflight: status=204
     Allow-Origin: https://spa.example.com
     Allow-Methods: GET, POST, PUT
     Max-Age: 7200
  2. Actual: status=200
     Allow-Origin: https://spa.example.com
     Expose-Headers: X-Request-Id
  [PASS] Full CORS flow works

All 6 sections passed. CORS middleware mastered!
```

## How It Works

### The Full CORS Flow

```
Frontend (https://spa.com)              Backend (https://api.com)
    |                                        |
    |  1. Preflight (automatic by browser)   |
    |  OPTIONS /api/users                    |
    |  Origin: https://spa.com               |
    |  Access-Control-Request-Method: POST   |
    |  Access-Control-Request-Headers:       |
    |    Content-Type, Authorization         |
    | -------------------------------------> |
    |                                        |  Check origin: allowed?
    |  204 No Content                        |  Check method: allowed?
    |  Access-Control-Allow-Origin: spa.com  |
    |  Access-Control-Allow-Methods: ...     |
    |  Access-Control-Max-Age: 7200          |
    | <------------------------------------- |
    |                                        |
    |  2. Actual request (if preflight OK)   |
    |  POST /api/users                       |
    |  Origin: https://spa.com               |
    |  Content-Type: application/json        |
    | -------------------------------------> |
    |                                        |
    |  200 OK                                |
    |  Access-Control-Allow-Origin: spa.com  |
    |  Access-Control-Expose-Headers: X-Req  |
    | <------------------------------------- |
```

### When Does the Browser Send a Preflight?

| Request Type | Preflight? | Example |
|---|---|---|
| Simple GET/POST with standard headers | No | `fetch("/api")` |
| POST with `Content-Type: application/json` | Yes | Custom content type |
| Any request with custom headers | Yes | `Authorization: Bearer ...` |
| PUT, DELETE, PATCH | Yes | Non-simple methods |

### Wildcard vs Specific Origin

```
allow_origins=["*"]
  -> Access-Control-Allow-Origin: *
  -> No Vary header needed
  -> Cannot use with credentials!

allow_origins=["https://myapp.com"]
  -> Access-Control-Allow-Origin: https://myapp.com
  -> Vary: Origin (tells caches)
  -> Can use with credentials
```

## Exercises

1. **Origin pattern matching** -- support wildcard patterns like `*.myapp.com` to allow all subdomains. Use `fnmatch` or implement simple pattern matching.

2. **Per-route CORS** -- instead of global CORS config, allow different CORS settings per route. `/api/public` might allow all origins while `/api/admin` restricts to specific origins.

3. **CORS error responses** -- instead of silently omitting CORS headers for disallowed origins, return a 403 with a descriptive error message for easier debugging.

4. **Logging middleware** -- add logging that records CORS decisions: allowed/denied origins, preflight cache hits, and credential mode warnings.

5. **CORS tester** -- build a function that takes a CORSConfig and a list of test requests, and prints a report showing which requests would be allowed/denied by the browser.

## What's Next

CORS controls which origins can access our API. In [Kata 65: CSRF Protection](./65-csrf-protection.md), we'll protect against Cross-Site Request Forgery attacks using the double-submit cookie pattern with signed tokens.

---

[prev: 63-session-middleware](./63-session-middleware.md) | [next: 65-csrf-protection](./65-csrf-protection.md)
