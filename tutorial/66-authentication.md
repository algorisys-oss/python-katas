# Kata 66 -- Authentication

[prev: 65-csrf-protection](./65-csrf-protection.md) | [next: 67-hot-reload](./67-hot-reload.md)

---

## What We're Building

**JWT authentication** for our Ignite framework -- implemented entirely from scratch using only Python's standard library. No PyJWT, no third-party dependencies. We build:

1. **Base64URL encoding** -- the encoding format required by the JWT specification
2. **JWT creation** -- build `header.payload.signature` tokens with HMAC-SHA256
3. **JWT verification** -- validate signatures and check expiration
4. **AuthMiddleware** -- extract tokens from `Authorization: Bearer` headers
5. **Dependencies** -- `get_current_user()` and `require_role()` for Depends()
6. **Protected decorator** -- `@protected(secret)` for route-level auth

This JWT-based approach mirrors Express.js `passport-jwt` and the bearer-token flows you build on FastAPI's `OAuth2PasswordBearer`. Note the details differ in practice: FastAPI's `OAuth2PasswordBearer` only *extracts* the bearer token from the header (you verify it yourself), and Django REST Framework's built-in `TokenAuthentication` uses opaque, database-backed tokens -- not JWTs -- by default.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| JWT structure | `header.payload.signature` (3 base64url parts) | Token-based auth |
| Base64URL | URL-safe base64 without padding | JWT encoding format |
| HMAC-SHA256 | Symmetric signing algorithm | Proving token authenticity |
| `iat` claim | Issued-at timestamp | Auditing token creation |
| `exp` claim | Expiration timestamp | Auto-expiring tokens |
| `sub` claim | Subject (user ID) | Identifying the user |
| Bearer scheme | `Authorization: Bearer <token>` header | Standard token transport |
| Middleware | Cross-cutting auth logic | Protecting all routes |
| Dependencies | `get_current_user()` for Depends() | Route-level user access |

## The Code

### 1. Base64URL Encoding

```python
import base64

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def base64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)
```

Standard base64 uses `+/=`. Base64URL uses `-_` and strips padding. This makes tokens safe for URLs and cookies.

### 2. Creating a JWT

```python
def create_token(payload, secret, expires_in=3600):
    # Header: {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header).encode())

    # Payload with timestamps
    full_payload = {"iat": now, "exp": now + expires_in, **payload}
    payload_b64 = base64url_encode(json.dumps(full_payload).encode())

    # Signature: HMAC-SHA256 of "header.payload"
    sig = hmac.new(secret.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256).digest()
    sig_b64 = base64url_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"
```

### 3. Verifying a JWT

```python
def verify_token(token, secret):
    header_b64, payload_b64, sig_b64 = token.split(".")

    # Recompute signature
    expected = hmac.new(secret.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256).digest()

    if not hmac.compare_digest(base64url_encode(expected), sig_b64):
        return None  # Invalid signature

    payload = json.loads(base64url_decode(payload_b64))

    if time.time() > payload.get("exp", 0):
        return None  # Expired

    return payload
```

### 4. Auth Middleware

```python
class AuthMiddleware:
    def __call__(self, request):
        if self._is_public(request.path):
            return self.handler(request)

        auth = request.get_header("authorization")
        if not auth or not auth.startswith("Bearer "):
            return Response(status_code=401)

        payload = verify_token(auth[7:], self.secret)
        if not payload:
            return Response(status_code=401)

        request.user = User(
            user_id=payload["sub"],
            username=payload["username"],
            role=payload.get("role", "user"),
        )
        return self.handler(request)
```

### 5. Dependencies

```python
def get_current_user(request):
    if request.user is None:
        raise ValueError("Not authenticated")
    return request.user

def require_role(role):
    def dep(request):
        user = get_current_user(request)
        if user.role != role:
            raise PermissionError(f"Role '{role}' required")
        return user
    return dep
```

## Playground

```
python playground/66_authentication.py
```

Expected output:

```
--- Section 1: Base64URL Encoding ---
  Encoded: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
  Decoded: {"alg":"HS256","typ":"JWT"}
  [PASS] Base64URL encoding works

--- Section 2: JWT Create & Verify ---
  Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOj...
  Parts: header(36), payload(XX), sig(43)
  Payload: {'iat': ..., 'exp': ..., 'sub': 'user_42', 'username': 'alice', 'role': 'admin'}
  Wrong secret: rejected
  Tampered token: rejected
  Malformed token: rejected
  [PASS] JWT create & verify works

--- Section 3: Token Expiration ---
  Expired token: None
  Valid token: sub=user_2
  [PASS] Token expiration works

--- Section 4: Auth Middleware ---
  GET / (public): status=200
  GET /dashboard (no token): status=401
  GET /dashboard (valid): status=200, body={'user': 'alice', 'role': 'admin'}
  GET /dashboard (invalid): status=401
  GET /dashboard (Basic auth): status=401
  [PASS] Auth middleware works

--- Section 5: Dependencies ---
  Current user: User(id='u42', username='bob', role='editor')
  require_role('editor'): OK
  require_role('admin'): Role 'admin' required, have 'editor'
  No user: Not authenticated
  [PASS] Dependencies work

--- Section 6: Protected Decorator ---
  No token: status=401
  Valid token: status=200, body={'admin': 'admin_alice'}
  Expired token: status=401
  [PASS] Protected decorator works

All 6 sections passed. Authentication mastered!
```

## How It Works

### JWT Structure

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.    <- Header (base64url)
eyJpYXQiOjE3MDk4NTYwMDAsImV4cCI6MTcw.    <- Payload (base64url)
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQ    <- Signature (base64url)

Header:  {"alg": "HS256", "typ": "JWT"}
Payload: {"iat": 1709856000, "exp": 1709859600, "sub": "user_42", "role": "admin"}
Signature: HMAC-SHA256(header.payload, secret)
```

### Authentication Flow

```
1. Login
   Client: POST /login {username, password}
   Server: Verify credentials
   Server: token = create_token({"sub": user_id, ...}, secret)
   Server: Return {"token": "eyJ..."}

2. Authenticated Request
   Client: GET /dashboard
           Authorization: Bearer eyJ...
   Server: AuthMiddleware extracts token
   Server: verify_token(token, secret) -> payload
   Server: request.user = User(payload)
   Server: Handler runs with request.user available

3. Expired Token
   Client: GET /dashboard
           Authorization: Bearer eyJ... (expired)
   Server: verify_token -> None (exp < now)
   Server: 401 Unauthorized
```

### Security Considerations

| Concern | Our Approach | Why |
|---|---|---|
| Signature verification | `hmac.compare_digest()` | Constant-time, no timing attacks |
| Token expiration | `exp` claim checked on every request | Limits breach window |
| Secret strength | Use long, random secrets in production | Prevents brute-force signing |
| Token storage | Client stores in memory or httpOnly cookie | Prevent XSS token theft |
| Algorithm | HS256 only (symmetric) | Simple, no algorithm confusion |

### JWT vs Session Cookies

| Feature | JWT | Session Cookie |
|---|---|---|
| Server state | Stateless | Server stores session data |
| Scalability | No shared state needed | Requires shared session store |
| Revocation | Hard (wait for expiry) | Easy (delete from store) |
| Size | Larger (carries claims) | Small (just session ID) |
| Use case | APIs, microservices | Traditional web apps |

## Exercises

1. **Refresh tokens** -- implement a refresh token flow. The access token expires in 15 minutes, but a long-lived refresh token (7 days) can be used to get a new access token without re-login.

2. **Token blacklist** -- implement a token revocation list. When a user logs out, add their token's `jti` (JWT ID) to a blacklist. Check the blacklist during verification.

3. **RS256 signatures** -- research how RS256 (RSA) differs from HS256 (HMAC). When would you use asymmetric signing? (Answer: when the verifier shouldn't be able to create tokens.)

4. **Password hashing** -- add `hash_password()` and `verify_password()` using `hashlib.pbkdf2_hmac` with a random salt. Store hashed passwords, never plaintext.

5. **OAuth2 scopes** -- extend the JWT payload with a `scopes` claim (e.g., `["read:users", "write:posts"]`). Build a `require_scope("read:users")` dependency that checks for specific permissions.

## What's Next

With authentication complete, our Ignite framework now handles the full security stack: cookies, sessions, CORS, CSRF, and JWT auth. In [Kata 67: Hot Reload](./67-hot-reload.md), we'll build a development server that automatically restarts when you change your code.

---

[prev: 65-csrf-protection](./65-csrf-protection.md) | [next: 67-hot-reload](./67-hot-reload.md)
