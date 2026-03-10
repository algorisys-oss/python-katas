# Kata 48 -- Error Handling & Exception Handlers

[prev: 47-response-models](./47-response-models.md) | [next: 49-route-decorators](./49-route-decorators.md)

---

## What We're Building

The **error handling system** for our Ignite framework. Every web framework needs a way to catch exceptions, map them to HTTP responses, and format error details for clients. We build three layers:

1. **HTTPException** -- raise HTTP errors as Python exceptions with status codes
2. **Exception handler registry** -- map exception types to handler functions using MRO-based lookup
3. **App integration** -- a try/except pipeline that catches any exception and returns a structured JSON error

This is how FastAPI, Starlette, and Django REST Framework handle errors -- but we build it from scratch to see the elegant use of Python's Method Resolution Order (MRO).

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `HTTPException` | Exception that maps to an HTTP status code | Signaling HTTP errors |
| Exception hierarchy | Subclasses for common errors (404, 403, etc.) | Clean route handler code |
| Handler registry | Maps `type -> handler_function` | Customizable error responses |
| MRO-based lookup | Walks `__mro__` to find the closest handler | Handler inheritance |
| Validation errors | Structured field-level error formatting | 422 responses |
| Custom handlers | Application-specific exception handling | Business logic errors |
| Error pipeline | try/except wrapping the entire request | Catching all failures |

## The Code

### 1. HTTPException

The base of all HTTP error signaling:

```python
class HTTPException(Exception):
    def __init__(self, status_code, detail=None, headers=None):
        self.status_code = status_code
        self.detail = detail or HTTP_STATUS_PHRASES[status_code]
        self.headers = headers or {}

    def to_response(self):
        return {
            "error": {
                "status_code": self.status_code,
                "detail": self.detail,
                "type": HTTP_STATUS_PHRASES[self.status_code],
            }
        }

# Usage in route handlers:
raise HTTPException(404, detail="User not found")
raise HTTPException(429, headers={"Retry-After": "60"})
```

### 2. Convenience Subclasses

```python
class NotFoundError(HTTPException):
    def __init__(self, detail="Not Found"):
        super().__init__(404, detail)

class ForbiddenError(HTTPException):
    def __init__(self, detail="Forbidden"):
        super().__init__(403, detail)

# Clean handler code:
raise NotFoundError(f"User {user_id} not found")
raise ForbiddenError("Admin access required")
```

### 3. Validation Error Formatting

Structured errors with field-level details (matching FastAPI's format):

```python
class ValidationError(Exception):
    def to_response(self):
        return {
            "error": {
                "status_code": 422,
                "detail": "Validation Error",
                "errors": [
                    {"loc": ["body", err["field"]], "msg": err["message"]}
                    for err in self.errors
                ]
            }
        }
```

### 4. Exception Handler Registry

The key design: a registry that maps exception types to handler functions, with MRO-based fallback:

```python
class ExceptionHandlerRegistry:
    def __init__(self):
        self._handlers = {}
        # Register defaults for HTTPException, ValidationError, Exception

    def add(self, exc_class, handler):
        self._handlers[exc_class] = handler

    def handle(self, request, exc):
        exc_type = type(exc)

        # Exact match first
        if exc_type in self._handlers:
            return self._handlers[exc_type](request, exc)

        # Walk MRO for parent class match
        for cls in exc_type.__mro__:
            if cls in self._handlers:
                return self._handlers[cls](request, exc)
```

### 5. MRO-Based Lookup

This is the elegant part -- you register a handler for a parent class, and all its children are automatically caught:

```python
class AppError(Exception): ...
class DatabaseError(AppError): ...
class ConnectionError(DatabaseError): ...

registry.add(AppError, handle_app_error)

# ConnectionError.__mro__ = [ConnectionError, DatabaseError, AppError, Exception, ...]
# Walks MRO -> finds AppError handler -> uses it

registry.add(DatabaseError, handle_db_error)
# Now ConnectionError matches DatabaseError first (closer in MRO)
```

### 6. App Integration

```python
class IgniteApp:
    def handle_request(self, request):
        try:
            handler = self._routes.get(request.path)
            if handler is None:
                raise NotFoundError(f"No route: '{request.path}'")
            result = handler(request)
            return Response(body=result, status_code=200)
        except Exception as exc:
            return self.exception_handlers.handle(request, exc)
```

## Playground

```python
python playground/48_error_handling.py
```

Expected output:

```
--- Section 1: HTTPException ---
  HTTPException(status_code=404, detail='User not found')
  Response: {'error': {'status_code': 404, 'detail': 'User not found', 'type': 'Not Found'}}
  Default detail: 'Internal Server Error'
  With headers: {'Retry-After': '60'}
  Convenience classes: NotFound=404, BadRequest=400, Unauthorized=401, Forbidden=403, Conflict=409
  [PASS] HTTPException works

--- Section 2: Validation Error Formatting ---
  Validation error with 3 fields:
    loc=['body', 'name'], msg=field is required
    loc=['body', 'age'], msg=value must be >= 0
    loc=['body', 'email'], msg=invalid email format
  [PASS] Validation error formatting works

--- Section 3: Exception Handler Registry ---
  HTTPException(403): status=403
  NotFoundError: status=404 (via MRO)
  ValidationError: status=422
  RuntimeError: status=500 (generic handler)
  RateLimitError (custom): status=429
  [PASS] Handler registry works

--- Section 4: MRO-Based Lookup ---
  DatabaseError -> AppError handler: type=application_error
  ConnectionError_ -> AppError handler (2 levels up)
  DatabaseError -> own handler: type=database_error
  ConnectionError_ -> DatabaseError handler (closer match)
  [PASS] MRO-based lookup works

--- Section 5: App Integration ---
  GET /users -> 200: {'users': ['Alice', 'Bob']}
  GET /users/1 -> 404: User 1 not found
  GET /nonexistent -> 404: No route matches '/nonexistent'
  GET /admin -> 403: Admin access required
  GET /crash -> 500: Internal Server Error
  POST /validate -> 422: validation errors
  [PASS] App integration works

--- Section 6: Custom App Handlers ---
  Custom handler: status=402
  Body: {'error': {'status_code': 402, 'detail': 'Insufficient funds: have 10.0, need 49.99', ...}}
  [PASS] Custom app handlers work

All 6 sections passed. Error handling & exception handlers mastered!
```

## How It Works

### Error Handling Pipeline

```
Client Request
     |
     v
 +---------+     Route found?     +------------------+
 | Routing  | ----NO-----------> | NotFoundError(404) |
 +---------+                      +------------------+
     | YES                              |
     v                                  |
 +---------+     Handler raises?   +----|-------------+
 | Handler  | ----YES-----------> | Exception Handler |
 +---------+                      | Registry          |
     | OK                         |                   |
     v                            | Walk MRO:         |
 +----------+                     |  1. Exact type    |
 | Response |                     |  2. Parent class  |
 | (200 OK) |                     |  3. Exception     |
 +----------+                     +-------------------+
                                       |
                                       v
                                  +----------+
                                  | Error    |
                                  | Response |
                                  | (4xx/5xx)|
                                  +----------+
```

### MRO Lookup Visualization

```
ConnectionError raised.

ConnectionError.__mro__:
  [0] ConnectionError  -> not in registry
  [1] DatabaseError    -> FOUND! use handle_db_error
  [2] AppError         -> (would match if [1] didn't)
  [3] Exception        -> (generic fallback)
  [4] BaseException
  [5] object
```

### Default Handler Map

| Exception Type | Handler | Status Code |
|---|---|---|
| `HTTPException` | Returns `exc.to_response()` | `exc.status_code` |
| `ValidationError` | Returns structured field errors | 422 |
| `Exception` (generic) | Returns "Internal Server Error" | 500 |

## Exercises

1. **Add error logging** -- extend the generic exception handler to log the full traceback (using `traceback.format_exc()`) while returning a clean 500 response to the client. Never expose internal details.

2. **Implement `@app.exception_handler` decorator** -- add a decorator syntax for registering handlers: `@app.exception_handler(RateLimitError)` instead of `app.add_exception_handler(...)`.

3. **Add error response content negotiation** -- check the request's `Accept` header and return either JSON or plain text error responses. Default to JSON.

4. **Build a `ProblemDetail` response** -- implement RFC 7807 "Problem Details for HTTP APIs" format with fields: `type`, `title`, `status`, `detail`, `instance`.

5. **Add error middleware** -- implement an error-counting middleware that tracks how many of each error type have occurred, accessible via `GET /errors/stats`.

## What's Next

With error handling in place, our Ignite framework now gracefully handles every failure case. In [Kata 49: Route Decorators](./49-route-decorators.md), we'll build the decorator-based routing system -- `@app.get("/users")`, `@app.post("/users")` -- that ties together routing, validation, query params, response models, and error handling into a clean developer API.

---

[prev: 47-response-models](./47-response-models.md) | [next: 49-route-decorators](./49-route-decorators.md)
