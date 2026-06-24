# Kata 42 -- Path Parameters

[prev: 41-router](./41-router.md) | [next: 43-middleware-pipeline](./43-middleware-pipeline.md)

---

## What We're Building

A **path parameter system** for the Ignite framework -- the ability to define routes like `/users/{user_id:int}` and have the framework automatically extract, type-convert, and inject those values into handler functions.

We'll build four components:
1. **Path pattern compiler** -- convert `/users/{user_id:int}` into a regex with capture groups
2. **Parameter extraction** -- match incoming paths and extract typed values
3. **Router integration** -- dispatch requests to handlers with path params as keyword arguments
4. **Edge case handling** -- overlapping routes, type mismatches, mixed parameter types

This is how frameworks like FastAPI, Flask, and Django handle dynamic URL segments. The key insight: path patterns are just syntactic sugar over regular expressions.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Path parameters | Capture dynamic URL segments like `{user_id}` | Any REST API with resource IDs |
| Type coercion | Convert `"42"` to `int`, `"3.14"` to `float` | Ensuring handlers receive correct types |
| Regex compilation | Convert pattern syntax to `re.compile()` | Efficient repeated matching |
| `re.fullmatch()` | Match entire string against pattern | Route matching (no partial matches) |
| Route precedence | First-match wins when multiple routes could match | Controlling which handler runs |
| `**kwargs` injection | Pass extracted params as keyword arguments | Clean handler signatures |

## The Code

### 1. Pattern Syntax

Path parameters use curly braces with an optional type annotation:

```python
"/users/{user_id}"          # str by default
"/users/{user_id:int}"      # converted to int
"/coords/{lat:float}"       # converted to float
"/users/{id:int}/posts/{post_id:int}"  # multiple params
```

Each `{param:type}` placeholder becomes a regex capture group:

```python
import re

PARAM_PATTERN = re.compile(r"\{(\w+)(?::(\w+))?\}")

TYPE_REGEXES = {
    "int": r"(\d+)",          # digits only
    "str": r"([^/]+)",        # anything except slash
    "float": r"(\d+\.\d+)",   # decimal number
}

# /users/{user_id:int} becomes ^/users/(\d+)$
# The regex captures "42" from /users/42
```

### 2. Compiling Path Patterns

The compiler walks through the pattern, replacing each `{param}` with the corresponding regex:

```python
def compile_path(pattern: str, handler, method="GET"):
    params = []
    regex_parts = []
    last_end = 0

    for match in PARAM_PATTERN.finditer(pattern):
        # Literal text before this param (escaped for regex safety)
        regex_parts.append(re.escape(pattern[last_end:match.start()]))

        param_name = match.group(1)    # "user_id"
        type_name = match.group(2) or "str"  # "int" or default "str"

        params.append(PathParam(name=param_name, type_name=type_name))
        regex_parts.append(TYPE_REGEXES[type_name])
        last_end = match.end()

    regex_parts.append(re.escape(pattern[last_end:]))
    full_regex = "^" + "".join(regex_parts) + "$"
    return CompiledRoute(regex=re.compile(full_regex), params=params, ...)
```

### 3. Matching and Extracting

When a request comes in, try each compiled route until one matches:

```python
def match(self, path: str) -> dict | None:
    m = self.regex.fullmatch(path)
    if not m:
        return None
    result = {}
    for param, raw_value in zip(self.params, m.groups()):
        result[param.name] = param.convert(raw_value)  # "42" -> 42
    return result
```

### 4. Router Integration

The router passes extracted parameters as keyword arguments to handlers:

```python
@router.get("/users/{user_id:int}")
def get_user(request: Request, user_id: int) -> Response:
    return Response(body=f"User #{user_id}")

# When GET /users/42 arrives:
# 1. Router tries each route's regex against "/users/42"
# 2. Matches ^/users/(\d+)$ -> captures "42"
# 3. Converts "42" to int -> 42
# 4. Calls get_user(request, user_id=42)
```

### 5. Type Safety Through Regex

The `{param:int}` type annotation does double duty:
- **Matching**: `\d+` only matches digits, so `/users/abc` won't match an int route
- **Conversion**: matched values are converted via `int()`, `float()`, etc.

This means a route like `/items/{item_id:int}` naturally coexists with `/items/special` -- the string "special" doesn't match `\d+`, so it falls through to the static route.

## Playground

```bash
python playground/42_path_parameters.py
```

Expected output:

```
--- Section 1: Path Pattern Parsing ---
  Pattern: /users/{user_id:int}
  Regex:   ^/users/(\d+)$
  Params:  [('user_id', 'int')]
  Pattern: /users/{user_id:int}/posts/{post_id:int}
  Regex:   ^/users/(\d+)/posts/(\d+)$
  Params:  [('user_id', 'int'), ('post_id', 'int')]
  Pattern: /files/{filename}
  Regex:   ^/files/([^/]+)$
  Params:  [('filename', 'str')]
  [VALID] Path patterns compile to correct regexes

--- Section 2: Path Matching & Parameter Extraction ---
  /users/42/posts/7 -> {'user_id': 42, 'post_id': 7}
  /users/42 -> None
  /users/abc/posts/7 -> None
  /files/report.pdf -> {'filename': 'report.pdf'}
  /coords/51.5074/0.1278 -> {'lat': 51.5074, 'lng': 0.1278}
  [VALID] Path matching and type coercion work correctly

--- Section 3: Router with Path Parameters ---
  GET /users -> 200: [user1, user2, user3]
  GET /users/42 -> 200: User #42
  GET /users/1/posts/99 -> 200: Post #99 by User #1
  POST /users/5/follow -> 201: Followed user #5
  GET /files/readme.txt -> 200: File: readme.txt
  GET /unknown -> 404: Not Found
  DELETE /users/42 -> 404: Not Found
  [VALID] Router dispatches correctly with path parameters

--- Section 4: Edge Cases & Advanced Patterns ---
  GET /items/special -> The special item
  GET /items/99 -> Item #99
  /weight/notanumber -> None
  /api/v2/users/100 -> {'version': 'v2', 'user_id': 100}
  Registered routes:
    GET /items/{item_id:int} -> get_item
    GET /items/special -> special_item
  [VALID] Edge cases handled correctly

--- Summary ---
Path parameters let routes capture dynamic segments:
  - {param} captures a string segment
  - {param:int} captures and converts to int
  - {param:float} captures and converts to float
  - Patterns compile to regex for efficient matching
  - Parameters are passed as keyword arguments to handlers

All 4 sections passed. Path parameters mastered!
Next up: Kata 43 -- Middleware Pipeline
```

## How It Works

### Pattern-to-Regex Compilation

```
Pattern:  /users/{user_id:int}/posts/{post_id:int}
                 ^^^^^^^^^^^^^^      ^^^^^^^^^^^^^^^
                 param 1             param 2

Step 1: Escape literal parts
  /users/ -> \/users\/
  /posts/ -> \/posts\/

Step 2: Replace params with capture groups
  {user_id:int}  -> (\d+)
  {post_id:int}  -> (\d+)

Step 3: Assemble regex
  ^\/users\/(\d+)\/posts\/(\d+)$

Step 4: Match /users/42/posts/7
  Group 1: "42" -> int("42") -> 42
  Group 2: "7"  -> int("7")  -> 7
  Result: {"user_id": 42, "post_id": 7}
```

### Route Resolution Order

```
Routes registered:
  1. GET /users              (static)
  2. GET /users/{id:int}     (parameterized)
  3. GET /items/{id:int}     (parameterized)
  4. GET /items/special      (static)

Request: GET /items/special
  Route 3: /items/{id:int} -> regex (\d+) won't match "special" -> SKIP
  Route 4: /items/special  -> exact match -> HANDLE

Request: GET /items/99
  Route 3: /items/{id:int} -> regex (\d+) matches "99" -> HANDLE
```

## Exercises

1. **Add a `uuid` type** -- extend `TYPE_COERCIONS` and `TYPE_REGEXES` to support `{id:uuid}` that matches UUID strings (e.g., `550e8400-e29b-41d4-a716-446655440000`) and converts them to `uuid.UUID` objects.

2. **Wildcard paths** -- add support for a `{path:path}` type that matches everything including slashes (regex: `(.+)`). This is useful for catch-all routes like `/files/{filepath:path}` matching `/files/docs/api/readme.md`.

3. **Route conflict detection** -- write a function that takes a list of route patterns and detects potential conflicts (e.g., `/users/{id:str}` and `/users/{name:str}` would both match the same paths).

4. **Named route generation** -- add a `url_for(route_name, **params)` method to the Router that generates a URL from a route name and parameters (reverse routing). For example, `url_for("get_user", user_id=42)` returns `/users/42`.

5. **Optional parameters** -- extend the syntax to support `{param?:int}` where the parameter is optional. The route `/users/{user_id:int}/posts/{page?:int}` should match both `/users/1/posts/5` and `/users/1/posts`.

## What's Next

With path parameters working, our routes can capture dynamic data from URLs. In [Kata 43: Middleware Pipeline](./43-middleware-pipeline.md), we build an ASGI middleware system -- composable layers that can intercept every request and response for logging, timing, CORS, authentication, and more.

---

[prev: 41-router](./41-router.md) | [next: 43-middleware-pipeline](./43-middleware-pipeline.md)
