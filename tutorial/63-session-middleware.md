# Kata 63 -- Session Middleware

[prev: 62-cookie-handling](./62-cookie-handling.md) | [next: 64-cors-middleware](./64-cors-middleware.md)

---

## What We're Building

**Session middleware** for our Ignite framework. Sessions let you store user-specific data across multiple HTTP requests (which are stateless by nature). We build:

1. **HMAC-SHA256 signing** -- sign session data so clients cannot tamper with it
2. **Session class** -- dict-like interface with modification tracking
3. **Session backends** -- cookie-based (data in the cookie) and in-memory (data on the server)
4. **SessionMiddleware** -- automatically loads session on request and saves on response

This is how Flask's signed cookies, Django's session framework, and Express.js sessions work -- but we build it from scratch.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| HMAC-SHA256 | Keyed hash for data integrity | Signing cookies and tokens |
| `hmac.compare_digest()` | Constant-time string comparison | Preventing timing attacks |
| Base64 encoding | Binary-safe text encoding | Storing data in cookies |
| Session tracking | Modification flag on data changes | Only save when needed |
| Cookie backend | Store session data in the cookie itself | Simple apps, no server state |
| Memory backend | Store session data server-side | Larger sessions, sensitive data |
| Middleware pattern | Wrap request/response processing | Cross-cutting concerns |

## The Code

### 1. Signing with HMAC-SHA256

```python
import base64, hmac, hashlib

def sign_data(data: str, secret: str) -> str:
    b64 = base64.urlsafe_b64encode(data.encode()).decode()
    sig = hmac.new(secret.encode(), b64.encode(), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"

def verify_and_decode(signed: str, secret: str) -> str | None:
    b64, sig = signed.rsplit(".", 1)
    expected = hmac.new(secret.encode(), b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None  # Tampered!
    return base64.urlsafe_b64decode(b64).decode()
```

### 2. Session Class

```python
class Session:
    def __init__(self, data=None):
        self._data = data or {}
        self._modified = False

    def __setitem__(self, key, value):
        self._data[key] = value
        self._modified = True  # Track changes

    def __getitem__(self, key):
        return self._data[key]

    # Also: __delitem__, __contains__, get, pop, clear
```

### 3. Session Backends

```python
class CookieBackend:
    """Data lives in the signed cookie itself."""
    def load(self, cookie_value):
        raw = verify_and_decode(cookie_value, self.secret)
        return json.loads(raw) if raw else None

    def save(self, _, data):
        return sign_data(json.dumps(data), self.secret)

class MemoryBackend:
    """Data lives on the server, cookie holds only the session ID."""
    def load(self, session_id):
        return self._store.get(session_id)

    def save(self, session_id, data):
        self._store[session_id] = data
```

### 4. Session Middleware

```python
class SessionMiddleware:
    def __call__(self, request):
        # 1. Load session from cookie
        cookie = request.cookies.get("session")
        data = self.backend.load(cookie) if cookie else None

        # 2. Attach session to request
        request.session = Session(data)

        # 3. Process request
        response = self.handler(request)

        # 4. Save if modified
        if request.session.modified:
            cookie_val = self.backend.save(session_id, request.session.to_dict())
            response.set_cookie(f"session={cookie_val}; HttpOnly; ...")

        return response
```

## Playground

```
python playground/63_session_middleware.py
```

Expected output:

```
--- Section 1: HMAC-SHA256 Signing ---
  Original: {"user_id":42,"role":"admin"}
  Signed:   eyJ1c2VyX2lkIjo0Miwicm9sZSI6ImFkbWluIn0=.a1b2c3...
  Decoded:  {"user_id":42,"role":"admin"}
  Tampered: None
  Wrong secret: None
  [PASS] Signing and verification works

--- Section 2: Session Class ---
  After set: Session({'user_id': 42, 'username': 'alice'}, modified=True)
  After clear: Session({}, modified=True)
  [PASS] Session class works

--- Section 3: Cookie Backend ---
  Saved cookie: eyJ1c2VyX2lkIjo0Miwicm9sZSI6ImFkbWluIn0...
  Loaded: {'user_id': 42, 'role': 'admin'}
  Tampered cookie: rejected
  [PASS] Cookie backend works

--- Section 4: Memory Backend ---
  Loaded: {'user_id': 99, 'cart': ['item1', 'item2']}
  Deleted session: confirmed gone
  [PASS] Memory backend works

--- Section 5: Session Middleware ---
  Cookie backend:
    Login response: {'message': 'logged in'}
    Set-Cookie: session=...; Path=/; ...HttpOnly...
    Profile response: {'user_id': 42}
  Memory backend:
    Server-side data: {'user': 'bob'}
  [PASS] Session middleware works

All 5 sections passed. Session middleware mastered!
```

## How It Works

### Cookie Backend Flow

```
Request 1 (Login):
  Browser -> Server: POST /login (no session cookie)
  Server: session["user_id"] = 42
  Server: sign(json({"user_id": 42})) -> "b64data.signature"
  Server -> Browser: Set-Cookie: session=b64data.signature

Request 2 (Profile):
  Browser -> Server: GET /profile (Cookie: session=b64data.signature)
  Server: verify signature -> OK
  Server: decode -> {"user_id": 42}
  Server: request.session["user_id"] -> 42
```

### Memory Backend Flow

```
Request 1 (Login):
  Browser -> Server: POST /login
  Server: generate session_id = "abc123"
  Server: store["abc123"] = {"user_id": 42}
  Server: sign("abc123") -> "signed_id"
  Server -> Browser: Set-Cookie: session=signed_id

Request 2 (Profile):
  Browser -> Server: GET /profile (Cookie: session=signed_id)
  Server: verify(signed_id) -> "abc123"
  Server: store["abc123"] -> {"user_id": 42}
```

### Backend Comparison

| Feature | Cookie Backend | Memory Backend |
|---|---|---|
| Server storage | None | Dict in memory |
| Size limit | ~4KB (cookie limit) | Unlimited |
| Data visibility | Client can see (but not modify) | Server-only |
| Scalability | Works across servers | Single process only |
| Persistence | Browser manages | Lost on restart |

### Why HMAC, Not Just Hashing?

```
Hash:  SHA256("data")              -> Anyone can compute this
HMAC:  SHA256(secret + "data")     -> Only someone with the secret can
```

Without a secret, an attacker could modify the data and recompute the hash. HMAC ensures only the server (which knows the secret) can create valid signatures.

## Exercises

1. **Session expiration** -- add a `created_at` timestamp to session data. In the middleware, reject sessions older than `max_age` seconds even if the signature is valid.

2. **Flash messages** -- implement `session.flash("message")` that stores a message that is auto-deleted after being read once. Used for "form submitted successfully" messages.

3. **Redis backend** -- design (but simulate) a Redis session backend. The interface is the same as MemoryBackend, but data would persist across restarts and work across processes.

4. **Session regeneration** -- implement `regenerate_id()` that creates a new session ID while keeping the same data. Important after login to prevent session fixation attacks.

5. **Encrypted sessions** -- instead of just signing, encrypt the session data so clients cannot even read it. Use `hashlib.pbkdf2_hmac` to derive an encryption key from the secret.

## What's Next

With sessions working, we can store user state across requests. In [Kata 64: CORS Middleware](./64-cors-middleware.md), we'll build Cross-Origin Resource Sharing middleware that controls which frontend origins can call our API.

---

[prev: 62-cookie-handling](./62-cookie-handling.md) | [next: 64-cors-middleware](./64-cors-middleware.md)
