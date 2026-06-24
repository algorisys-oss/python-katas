# Kata 62 -- Cookie Handling

[prev: 61-pubsub](./61-pubsub.md) | [next: 63-session-middleware](./63-session-middleware.md)

---

## What We're Building

The **cookie handling system** for our Ignite framework. Cookies are how the web maintains state between requests -- the browser sends them with every request, and the server can set, update, or delete them. We build:

1. **Cookie parser** -- parse the `Cookie` request header into a Python dict
2. **Cookie class** -- builder pattern for constructing `Set-Cookie` response headers with all attributes
3. **Delete helper** -- delete cookies by setting `Max-Age=0`
4. **CookieJar** -- request/response integration for managing cookies

This is the foundation for sessions (Kata 63), CSRF protection (Kata 65), and authentication (Kata 66).

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `Cookie` header | `name=value; name2=value2` sent by browser | Reading cookies from requests |
| `Set-Cookie` header | Server instructs browser to store a cookie | Setting cookies in responses |
| `Path` | URL scope for the cookie | Limit cookie to specific routes |
| `Domain` | Which domains receive the cookie | Cross-subdomain cookies |
| `Max-Age` | Lifetime in seconds | Session vs persistent cookies |
| `Expires` | Absolute expiration date | Legacy browser support |
| `Secure` | Only sent over HTTPS | Production security |
| `HttpOnly` | Not accessible via JavaScript | Prevent XSS token theft |
| `SameSite` | Cross-site request policy | CSRF protection |
| Builder pattern | Fluent method chaining | Clean API design |

## The Code

### 1. Parsing the Cookie Header

```python
def parse_cookie_header(header: str) -> dict[str, str]:
    cookies = {}
    for pair in header.split(";"):
        pair = pair.strip()
        if "=" in pair:
            name, value = pair.split("=", 1)  # maxsplit=1 for base64 values
            cookies[name.strip()] = value.strip()
    return cookies

# "session=abc123; theme=dark" -> {"session": "abc123", "theme": "dark"}
```

### 2. Cookie Builder Pattern

```python
class Cookie:
    def __init__(self, name, value=""):
        self.name = name
        self.value = value
        # ... attributes initialized to None/False

    def path(self, path):     self._path = path;       return self
    def domain(self, domain): self._domain = domain;   return self
    def max_age(self, secs):  self._max_age = secs;    return self
    def secure(self):         self._is_secure = True;   return self
    def httponly(self):        self._is_httponly = True;  return self
    def samesite(self, p):    self._samesite = p;      return self

    def to_header(self):
        parts = [f"{self.name}={self.value}"]
        if self._path:    parts.append(f"Path={self._path}")
        if self._is_secure: parts.append("Secure")
        # ... etc
        return "; ".join(parts)

# Usage with chaining:
cookie = (Cookie("session", "abc")
    .path("/").secure().httponly().samesite("Lax"))
```

### 3. Delete Cookies

```python
def delete_cookie(name, path="/"):
    return Cookie(name, "").path(path).max_age(0)

# Browser removes the cookie when it receives Max-Age=0
```

### 4. CookieJar

*Excerpt — core logic only (some details elided); not a standalone runnable snippet.*

```python
class CookieJar:
    def load(self, header):        # Parse Cookie request header
    def get(self, name):           # Read a request cookie
    def set(self, name, value):    # Add a response cookie
    def delete(self, name):        # Delete a cookie
    def response_headers(self):    # Get Set-Cookie header list
```

## Playground

```
python playground/62_cookie_handling.py
```

Expected output:

```
--- Section 1: Parse Cookie Header ---
  Parsed: {'session': 'abc123', 'theme': 'dark', 'lang': 'en'}
  With '=' in value: {'token': 'eyJhbGc=', 'id': '42'}
  [PASS] Cookie header parsing works

--- Section 2: Cookie Builder Pattern ---
  Basic: session=abc123
  Full: session=abc123; Path=/; Domain=.example.com; Max-Age=3600; Secure; HttpOnly; SameSite=Lax
  Expires: remember=yes; Expires=Thu, 01 Jan 2099 00:00:00 GMT
  SameSite=None: cross=val; Secure; SameSite=None
  Invalid SameSite caught: ...
  [PASS] Cookie builder works

--- Section 3: Delete Cookie ---
  Delete header: session=; Path=/; Max-Age=0
  Delete with domain: tracker=; Path=/app; Domain=.example.com; Max-Age=0
  [PASS] Cookie deletion works

--- Section 4: CookieJar ---
  Request cookies: {'session': 'old_token', 'theme': 'dark'}
  Response headers (3):
    Set-Cookie: session=new_token; Path=/; Secure; HttpOnly
    Set-Cookie: preference=compact; Path=/; Max-Age=86400
    Set-Cookie: theme=; Path=/; Max-Age=0
  [PASS] CookieJar works

--- Section 5: Security Scenarios ---
  Session: __Host-session=encrypted_data; Path=/; Secure; HttpOnly; SameSite=Strict
  CSRF: csrf_token=random_token_value; Path=/; Max-Age=3600; SameSite=Strict
  Remember-me: ...Max-Age=2592000...
  Third-party: ...SameSite=None; Secure...
  [PASS] Security scenarios work

All 5 sections passed. Cookie handling mastered!
```

## How It Works

### Cookie Flow

```
Browser                           Server
  |                                 |
  |  GET /page                      |
  |  Cookie: session=abc; theme=dk  |
  | ------------------------------> |
  |                                 |  parse_cookie_header()
  |                                 |  -> {"session": "abc", "theme": "dk"}
  |                                 |
  |  200 OK                         |
  |  Set-Cookie: session=xyz;       |
  |    Path=/; Secure; HttpOnly     |
  | <------------------------------ |
  |                                 |
  |  (browser stores new cookie)    |
  |                                 |
```

### SameSite Policies

| Policy | Cross-site Form POST | Cross-site Link Click | Same-site Request |
|---|---|---|---|
| `Strict` | Cookie NOT sent | Cookie NOT sent | Cookie sent |
| `Lax` | Cookie NOT sent | Cookie sent | Cookie sent |
| `None` | Cookie sent | Cookie sent | Cookie sent |

### Security Best Practices

| Cookie Type | Flags | Why |
|---|---|---|
| Session | `Secure; HttpOnly; SameSite=Strict` | Prevent XSS + CSRF |
| CSRF token | `SameSite=Strict` (no HttpOnly) | JS needs to read it |
| Remember-me | `Secure; HttpOnly; SameSite=Lax; Max-Age=...` | Long-lived, secure |
| Third-party | `Secure; SameSite=None` | Cross-origin requires both |

## Exercises

1. **URL-encode cookie values** -- cookie values cannot contain spaces, commas, or semicolons. Add `url_encode()`/`url_decode()` methods using `urllib.parse.quote`/`unquote`.

2. **Cookie prefix validation** -- implement `__Host-` and `__Secure-` prefix rules. `__Host-` cookies must have `Secure`, `Path=/`, and no `Domain`. `__Secure-` cookies must have `Secure`.

3. **Cookie size limits** -- add a `to_header()` check that warns if the header exceeds 4096 bytes (browser limit). Raise an error if it exceeds 8192 bytes.

4. **Parse Set-Cookie header** -- write a `parse_set_cookie()` function that takes a `Set-Cookie` header string and returns a `Cookie` object with all attributes populated.

5. **Cookie middleware** -- build a middleware that automatically parses request cookies and provides a `request.cookies` dict, similar to how Express.js `cookie-parser` works.

## What's Next

With cookies in place, we can build higher-level abstractions on top. In [Kata 63: Session Middleware](./63-session-middleware.md), we'll use signed cookies to implement server-side sessions with HMAC-SHA256 tamper protection.

---

[prev: 61-pubsub](./61-pubsub.md) | [next: 63-session-middleware](./63-session-middleware.md)
