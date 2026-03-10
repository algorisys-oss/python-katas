"""
Kata 42 -- Path Parameters
Run: python playground/42_path_parameters.py

Extend the Ignite Router to support path parameters like /users/{user_id}.
Convert path patterns to regex, extract parameters, support type coercion
(int, str), and pass extracted values to route handlers.

Completes within 5 seconds.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Path Pattern Parsing
# ===========================================================================

# Regex to find {param_name} or {param_name:type} in route patterns
PARAM_PATTERN = re.compile(r"\{(\w+)(?::(\w+))?\}")

# Supported type coercions for path parameters
TYPE_COERCIONS: dict[str, type] = {
    "int": int,
    "str": str,
    "float": float,
}

# Default regex fragments for each type
TYPE_REGEXES: dict[str, str] = {
    "int": r"(\d+)",          # digits only
    "str": r"([^/]+)",        # anything except slash
    "float": r"(\d+\.\d+)",   # decimal number
}


@dataclass
class PathParam:
    """Describes a single parameter extracted from a path pattern."""
    name: str
    type_name: str = "str"
    converter: type = str

    def convert(self, raw: str) -> Any:
        """Convert a raw string value to the target type."""
        try:
            return self.converter(raw)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Cannot convert '{raw}' to {self.type_name} "
                f"for parameter '{self.name}'"
            ) from exc


@dataclass
class CompiledRoute:
    """A route pattern compiled into a regex with extracted param metadata."""
    pattern: str           # original pattern, e.g. /users/{user_id:int}
    regex: re.Pattern      # compiled regex
    params: list[PathParam]  # ordered list of parameters
    handler: Callable
    method: str = "GET"

    def match(self, path: str) -> dict[str, Any] | None:
        """Try to match a path. Returns extracted params dict or None."""
        m = self.regex.fullmatch(path)
        if not m:
            return None
        # Convert each captured group using its param converter
        result = {}
        for param, raw_value in zip(self.params, m.groups()):
            result[param.name] = param.convert(raw_value)
        return result


def compile_path(pattern: str, handler: Callable,
                 method: str = "GET") -> CompiledRoute:
    """Compile a path pattern like /users/{user_id:int}/posts/{post_id:int}.

    Converts {param} placeholders into regex capture groups.
    Supports type annotations: {name:int}, {name:str}, {name:float}.
    Defaults to str if no type specified.
    """
    params: list[PathParam] = []
    regex_parts: list[str] = []
    last_end = 0

    for match in PARAM_PATTERN.finditer(pattern):
        # Add the literal part before this parameter
        regex_parts.append(re.escape(pattern[last_end:match.start()]))

        param_name = match.group(1)
        type_name = match.group(2) or "str"

        if type_name not in TYPE_COERCIONS:
            raise ValueError(
                f"Unknown type '{type_name}' for parameter '{param_name}'. "
                f"Supported: {list(TYPE_COERCIONS.keys())}"
            )

        params.append(PathParam(
            name=param_name,
            type_name=type_name,
            converter=TYPE_COERCIONS[type_name],
        ))
        regex_parts.append(TYPE_REGEXES[type_name])
        last_end = match.end()

    # Add any trailing literal part
    regex_parts.append(re.escape(pattern[last_end:]))

    full_regex = "^" + "".join(regex_parts) + "$"
    return CompiledRoute(
        pattern=pattern,
        regex=re.compile(full_regex),
        params=params,
        handler=handler,
        method=method,
    )


def demo_path_parsing():
    """Demonstrate path pattern parsing and regex compilation."""
    dummy = lambda **kw: kw  # placeholder handler

    # Simple parameter
    route1 = compile_path("/users/{user_id:int}", dummy)
    print(f"  Pattern: {route1.pattern}")
    print(f"  Regex:   {route1.regex.pattern}")
    print(f"  Params:  {[(p.name, p.type_name) for p in route1.params]}")

    # Multiple parameters
    route2 = compile_path("/users/{user_id:int}/posts/{post_id:int}", dummy)
    print(f"  Pattern: {route2.pattern}")
    print(f"  Regex:   {route2.regex.pattern}")
    print(f"  Params:  {[(p.name, p.type_name) for p in route2.params]}")

    # String parameter (default type)
    route3 = compile_path("/files/{filename}", dummy)
    print(f"  Pattern: {route3.pattern}")
    print(f"  Regex:   {route3.regex.pattern}")
    print(f"  Params:  {[(p.name, p.type_name) for p in route3.params]}")

    # Verify regex structure
    assert route1.regex.pattern == r"^/users/(\d+)$"
    assert len(route1.params) == 1
    assert route1.params[0].name == "user_id"
    assert route1.params[0].type_name == "int"
    assert len(route2.params) == 2
    assert route3.regex.pattern == r"^/files/([^/]+)$"

    print(f"  [VALID] Path patterns compile to correct regexes")


# ===========================================================================
# SECTION 2: Path Matching & Parameter Extraction
# ===========================================================================

def demo_path_matching():
    """Demonstrate matching paths and extracting typed parameters."""
    dummy = lambda **kw: kw

    route = compile_path("/users/{user_id:int}/posts/{post_id:int}", dummy)

    # Successful match
    params = route.match("/users/42/posts/7")
    print(f"  /users/42/posts/7 -> {params}")
    assert params == {"user_id": 42, "post_id": 7}
    assert isinstance(params["user_id"], int)  # type coercion worked

    # No match -- wrong structure
    no_match = route.match("/users/42")
    print(f"  /users/42 -> {no_match}")
    assert no_match is None

    # No match -- non-numeric for int param
    no_match2 = route.match("/users/abc/posts/7")
    print(f"  /users/abc/posts/7 -> {no_match2}")
    assert no_match2 is None

    # String parameter
    str_route = compile_path("/files/{filename}", dummy)
    params2 = str_route.match("/files/report.pdf")
    print(f"  /files/report.pdf -> {params2}")
    assert params2 == {"filename": "report.pdf"}

    # Float parameter
    float_route = compile_path("/coords/{lat:float}/{lng:float}", dummy)
    params3 = float_route.match("/coords/51.5074/0.1278")
    print(f"  /coords/51.5074/0.1278 -> {params3}")
    assert params3 == {"lat": 51.5074, "lng": 0.1278}
    assert isinstance(params3["lat"], float)

    print(f"  [VALID] Path matching and type coercion work correctly")


# ===========================================================================
# SECTION 3: Router with Path Parameters
# ===========================================================================

@dataclass
class Request:
    """Minimal request object for the Ignite framework."""
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    path_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """Minimal response object for the Ignite framework."""
    status: int = 200
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)


class Router:
    """A router that supports path parameters with type coercion.

    Routes are stored as CompiledRoute objects. On lookup, each route
    is tried in registration order until one matches.
    """

    def __init__(self):
        self._routes: list[CompiledRoute] = []

    def add_route(self, method: str, pattern: str,
                  handler: Callable) -> None:
        """Register a route with a pattern like /users/{user_id:int}."""
        compiled = compile_path(pattern, handler, method=method.upper())
        self._routes.append(compiled)

    def get(self, pattern: str):
        """Decorator for GET routes."""
        def decorator(func: Callable) -> Callable:
            self.add_route("GET", pattern, func)
            return func
        return decorator

    def post(self, pattern: str):
        """Decorator for POST routes."""
        def decorator(func: Callable) -> Callable:
            self.add_route("POST", pattern, func)
            return func
        return decorator

    def resolve(self, method: str, path: str
                ) -> tuple[Callable, dict[str, Any]] | None:
        """Find a matching route and extract path parameters.

        Returns (handler, params_dict) or None if no route matches.
        """
        method = method.upper()
        for route in self._routes:
            if route.method != method:
                continue
            params = route.match(path)
            if params is not None:
                return (route.handler, params)
        return None

    def handle(self, request: Request) -> Response:
        """Dispatch a request to the appropriate handler."""
        result = self.resolve(request.method, request.path)
        if result is None:
            return Response(status=404, body="Not Found")
        handler, params = result
        request.path_params = params
        return handler(request, **params)


def demo_router():
    """Demonstrate a router with path parameters in action."""
    router = Router()

    # Register routes using decorators
    @router.get("/users")
    def list_users(request: Request) -> Response:
        return Response(body="[user1, user2, user3]")

    @router.get("/users/{user_id:int}")
    def get_user(request: Request, user_id: int) -> Response:
        return Response(body=f"User #{user_id}")

    @router.get("/users/{user_id:int}/posts/{post_id:int}")
    def get_post(request: Request, user_id: int,
                 post_id: int) -> Response:
        return Response(body=f"Post #{post_id} by User #{user_id}")

    @router.post("/users/{user_id:int}/follow")
    def follow_user(request: Request, user_id: int) -> Response:
        return Response(status=201, body=f"Followed user #{user_id}")

    @router.get("/files/{filename}")
    def get_file(request: Request, filename: str) -> Response:
        return Response(body=f"File: {filename}")

    # Test: list users (no path params)
    req1 = Request(method="GET", path="/users")
    resp1 = router.handle(req1)
    print(f"  GET /users -> {resp1.status}: {resp1.body}")
    assert resp1.status == 200

    # Test: get specific user (int param)
    req2 = Request(method="GET", path="/users/42")
    resp2 = router.handle(req2)
    print(f"  GET /users/42 -> {resp2.status}: {resp2.body}")
    assert resp2.body == "User #42"
    assert req2.path_params == {"user_id": 42}

    # Test: nested path params
    req3 = Request(method="GET", path="/users/1/posts/99")
    resp3 = router.handle(req3)
    print(f"  GET /users/1/posts/99 -> {resp3.status}: {resp3.body}")
    assert resp3.body == "Post #99 by User #1"

    # Test: POST with path param
    req4 = Request(method="POST", path="/users/5/follow")
    resp4 = router.handle(req4)
    print(f"  POST /users/5/follow -> {resp4.status}: {resp4.body}")
    assert resp4.status == 201

    # Test: string param
    req5 = Request(method="GET", path="/files/readme.txt")
    resp5 = router.handle(req5)
    print(f"  GET /files/readme.txt -> {resp5.status}: {resp5.body}")
    assert resp5.body == "File: readme.txt"

    # Test: 404 for unmatched path
    req6 = Request(method="GET", path="/unknown")
    resp6 = router.handle(req6)
    print(f"  GET /unknown -> {resp6.status}: {resp6.body}")
    assert resp6.status == 404

    # Test: method mismatch
    req7 = Request(method="DELETE", path="/users/42")
    resp7 = router.handle(req7)
    print(f"  DELETE /users/42 -> {resp7.status}: {resp7.body}")
    assert resp7.status == 404  # no DELETE handler registered

    print(f"  [VALID] Router dispatches correctly with path parameters")


# ===========================================================================
# SECTION 4: Edge Cases & Advanced Patterns
# ===========================================================================

def demo_edge_cases():
    """Test edge cases: type errors, overlapping routes, etc."""
    router = Router()

    @router.get("/items/{item_id:int}")
    def get_item(request: Request, item_id: int) -> Response:
        return Response(body=f"Item #{item_id}")

    @router.get("/items/special")
    def special_item(request: Request) -> Response:
        return Response(body="The special item")

    # Static route registered AFTER parameterized -- order matters!
    # /items/special matches /items/{item_id:int}? No, because "special"
    # isn't digits. The int regex only matches \d+.
    req1 = Request(method="GET", path="/items/special")
    resp1 = router.handle(req1)
    print(f"  GET /items/special -> {resp1.body}")
    # "special" doesn't match \d+, so it falls through to the static route
    assert resp1.body == "The special item"

    req2 = Request(method="GET", path="/items/99")
    resp2 = router.handle(req2)
    print(f"  GET /items/99 -> {resp2.body}")
    assert resp2.body == "Item #99"

    # Type coercion error: float route but given non-float
    float_route = compile_path("/weight/{value:float}", lambda **kw: kw)
    result = float_route.match("/weight/notanumber")
    print(f"  /weight/notanumber -> {result}")
    assert result is None  # regex won't match

    # Multiple params of different types
    mixed = compile_path(
        "/api/{version:str}/users/{user_id:int}", lambda **kw: kw
    )
    params = mixed.match("/api/v2/users/100")
    print(f"  /api/v2/users/100 -> {params}")
    assert params == {"version": "v2", "user_id": 100}

    # Route listing -- useful for debugging
    print(f"  Registered routes:")
    for route in router._routes:
        print(f"    {route.method} {route.pattern} -> {route.handler.__name__}")

    print(f"  [VALID] Edge cases handled correctly")


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("--- Section 1: Path Pattern Parsing ---")
    demo_path_parsing()
    print()

    print("--- Section 2: Path Matching & Parameter Extraction ---")
    demo_path_matching()
    print()

    print("--- Section 3: Router with Path Parameters ---")
    demo_router()
    print()

    print("--- Section 4: Edge Cases & Advanced Patterns ---")
    demo_edge_cases()
    print()

    print("--- Summary ---")
    print("Path parameters let routes capture dynamic segments:")
    print("  - {param} captures a string segment")
    print("  - {param:int} captures and converts to int")
    print("  - {param:float} captures and converts to float")
    print("  - Patterns compile to regex for efficient matching")
    print("  - Parameters are passed as keyword arguments to handlers")
    print()
    print("All 4 sections passed. Path parameters mastered!")
    print("Next up: Kata 43 -- Middleware Pipeline")


if __name__ == "__main__":
    main()
