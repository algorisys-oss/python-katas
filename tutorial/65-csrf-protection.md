# Kata 65 -- CSRF Protection

[prev: 64-cors-middleware](./64-cors-middleware.md) | [next: 66-authentication](./66-authentication.md)

---

## What We're Building

**CSRF (Cross-Site Request Forgery) protection** for our Ignite framework. CSRF attacks trick a user's browser into making unintended requests to a site where they're already authenticated. We build:

1. **Token generation** -- cryptographically secure tokens using `secrets`
2. **Signed tokens** -- HMAC-SHA256 signatures to prove the server generated the token
3. **Double-submit cookie pattern** -- token in cookie + token in form/header must match
4. **CSRFMiddleware** -- validates tokens on unsafe methods (POST/PUT/DELETE/PATCH)
5. **Path exemptions** -- skip CSRF for API endpoints that use JWT auth

This is how Django's CSRF protection, Rails' `authenticity_token`, and Express.js `csurf` work.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| CSRF attack | Trick browser into making authenticated requests | Understanding the threat |
| `secrets.token_hex()` | Generate cryptographic random tokens | Security-sensitive tokens |
| Double-submit cookie | Token in cookie + token in form must match | Stateless CSRF protection |
| HMAC signing | Prove the server generated a token | Token authenticity |
| `hmac.compare_digest()` | Constant-time string comparison | Prevent timing attacks |
| Path exemptions | Skip CSRF for certain routes | APIs using JWT/OAuth |
| Safe vs unsafe methods | GET/HEAD are safe; POST/PUT/DELETE are not | When to validate |

## The Code

### 1. Token Generation

```python
import secrets, hmac, hashlib

def generate_csrf_token(nbytes=32):
    return secrets.token_hex(nbytes)  # 64 hex chars

def generate_signed_token(secret, nbytes=32):
    token = secrets.token_hex(nbytes)
    sig = hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()
    return f"{token}.{sig}"

def verify_signed_token(signed, secret):
    token, sig = signed.rsplit(".", 1)
    expected = hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)
```

### 2. The Double-Submit Pattern

```python
# Step 1: Server sets CSRF token in a cookie (JS-readable, no HttpOnly)
Set-Cookie: csrf_token=abc123.signature; SameSite=Strict

# Step 2: Client reads the cookie and includes token in the request
POST /transfer
Cookie: csrf_token=abc123.signature          <- browser sends automatically
X-CSRF-Token: abc123.signature               <- client adds manually
# OR in form data:
csrf_token=abc123.signature

# Step 3: Server verifies cookie token == submitted token
```

### 3. Why This Works

An attacker's site can trigger requests that **send** cookies (the browser does this automatically), but it **cannot read** cookies from another domain (same-origin policy). So the attacker can't include the token in the form/header.

### 4. CSRF Middleware

```python
class CSRFMiddleware:
    UNSAFE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

    def __call__(self, request):
        if self._is_exempt(request.path):
            return self.handler(request)

        if request.method in self.UNSAFE_METHODS:
            if not self._validate_token(request):
                return Response(status_code=403, body={"error": "CSRF invalid"})

        response = self.handler(request)

        # Set CSRF cookie on first visit
        if "csrf_token" not in request.cookies:
            token = generate_signed_token(self.secret)
            response.set_cookie(f"csrf_token={token}; SameSite=Strict")

        return response
```

## Playground

```
python playground/65_csrf_protection.py
```

Expected output:

```
--- Section 1: Token Generation ---
  Random token: a1b2c3d4... (64 hex chars)
  Unique check: tokens differ
  Signed token: token_hex.hmac_signature...
  Verification: valid=True, wrong-secret=False, tampered=False
  [PASS] Token generation works

--- Section 2: Double-Submit Pattern ---
  GET /form: status=200
  CSRF cookie set: csrf_token=...
  POST with valid token: status=200
  POST with form token: status=200
  [PASS] Double-submit pattern works

--- Section 3: Attack Prevention ---
  No token: status=403 -- CSRF token missing or invalid
  Cookie only (no submit): status=403
  Mismatched tokens: status=403
  Forged token: status=403
  [PASS] CSRF attacks blocked

--- Section 4: Exempt Paths ---
  POST /api/users (exempt): status=200
  POST /webhooks/stripe (exempt): status=200
  POST /transfer (protected): status=403
  GET /transfer (safe method): status=200
  [PASS] Path exemption works

--- Section 5: All Unsafe Methods ---
  GET: allowed (safe)
  OPTIONS: allowed (safe)
  POST (no token): blocked
  PUT (no token): blocked
  DELETE (no token): blocked
  PATCH (no token): blocked
  POST (valid token): allowed
  ...
  [PASS] All unsafe methods protected

All 5 sections passed. CSRF protection mastered!
```

## How It Works

### CSRF Attack Scenario

```
1. Alice logs into bank.com (gets session cookie)

2. Alice visits evil.com which has:
   <form action="https://bank.com/transfer" method="POST">
     <input name="to" value="attacker">
     <input name="amount" value="10000">
   </form>
   <script>document.forms[0].submit()</script>

3. Browser sends POST to bank.com WITH Alice's session cookie
   (browser always sends cookies for the target domain)

4. Without CSRF protection: bank processes the transfer!
   With CSRF protection: bank rejects (no valid CSRF token)
```

### Double-Submit Defense

```
                    evil.com                     bank.com
                      |                            |
Alice visits evil.com |                            |
                      |  POST /transfer            |
                      |  Cookie: session=...,      |
                      |    csrf_token=abc.sig       |  <- browser sends cookie
                      |  (no X-CSRF-Token header)   |  <- evil.com can't read it
                      | --------------------------> |
                      |                            |  cookie_token = "abc.sig"
                      |                            |  header_token = None  <- MISSING!
                      |  403 Forbidden             |
                      | <------------------------- |
```

### Validation Flow

```
POST /transfer
  |
  v
Is path exempt? --YES--> Pass through
  | NO
  v
Is method unsafe? --NO--> Pass through (GET, OPTIONS, HEAD)
  | YES
  v
Get cookie token --MISSING--> 403 Forbidden
  | FOUND
  v
Get header/form token --MISSING--> 403 Forbidden
  | FOUND
  v
Tokens match? --NO--> 403 Forbidden (mismatched)
  | YES
  v
Token signature valid? --NO--> 403 Forbidden (forged)
  | YES
  v
Process request
```

## Exercises

1. **Token rotation** -- generate a new CSRF token after each successful POST. This prevents token reuse in case of a leak. The response should set an updated `csrf_token` cookie.

2. **AJAX convenience** -- add middleware that automatically reads the CSRF token from a `<meta>` tag and includes it in all AJAX requests. Show how a frontend framework would integrate.

3. **Per-form tokens** -- instead of one global token, generate unique tokens per form. Bind each token to a specific action (e.g., `/transfer`) so a token for one form cannot be used for another.

4. **Token expiration** -- add a timestamp to the signed token and reject tokens older than a configurable max age. This limits the window of opportunity if a token leaks.

5. **SameSite as CSRF defense** -- explore how `SameSite=Strict` cookies can replace CSRF tokens entirely. When would this not be sufficient?

## What's Next

CSRF protection prevents forged requests. In [Kata 66: Authentication](./66-authentication.md), we'll build JWT (JSON Web Token) authentication from scratch using only stdlib -- creating, signing, verifying, and expiring tokens for user identity.

---

[prev: 64-cors-middleware](./64-cors-middleware.md) | [next: 66-authentication](./66-authentication.md)
