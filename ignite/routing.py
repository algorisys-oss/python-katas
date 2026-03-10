"""Ignite Router — path matching, parameter extraction, and dispatch."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from .request import Request
from .response import JSONResponse, Response


# ---------------------------------------------------------------------------
# Path parameter parsing
# ---------------------------------------------------------------------------

# Regex to find {param_name} or {param_name:type} in route patterns
PARAM_PATTERN = re.compile(r"\{(\w+)(?::(\w+))?\}")

TYPE_COERCIONS: dict[str, type] = {
    "int": int,
    "str": str,
    "float": float,
}

TYPE_REGEXES: dict[str, str] = {
    "int": r"(\d+)",
    "str": r"([^/]+)",
    "float": r"(\d+\.?\d*)",
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
class Route:
    """A compiled route with regex matching and param extraction."""
    pattern: str
    regex: re.Pattern[str]
    params: list[PathParam]
    handler: Callable
    method: str = "GET"

    def match(self, path: str) -> dict[str, Any] | None:
        """Try to match a path. Returns extracted params dict or None."""
        m = self.regex.fullmatch(path)
        if not m:
            return None
        result: dict[str, Any] = {}
        for param, raw_value in zip(self.params, m.groups()):
            result[param.name] = param.convert(raw_value)
        return result

    def __repr__(self) -> str:
        return f"<Route {self.method} {self.pattern} -> {self.handler.__name__}>"


def compile_path(
    pattern: str, handler: Callable, method: str = "GET"
) -> Route:
    """Compile a path pattern like /users/{user_id:int} into a Route.

    Converts {param} placeholders into regex capture groups.
    Supports: {name:int}, {name:str}, {name:float}. Defaults to str.
    """
    params: list[PathParam] = []
    regex_parts: list[str] = []
    last_end = 0

    for match in PARAM_PATTERN.finditer(pattern):
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

    regex_parts.append(re.escape(pattern[last_end:]))
    full_regex = "^" + "".join(regex_parts) + "$"

    return Route(
        pattern=pattern,
        regex=re.compile(full_regex),
        params=params,
        handler=handler,
        method=method.upper(),
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class Router:
    """Maps HTTP requests to handler functions with path parameter support.

    Supports:
    - Static paths: /users, /api/health
    - Parameterized paths: /users/{user_id:int}
    - Method-based dispatch with 404 and 405 responses
    - Decorator shortcuts: @router.get(), @router.post(), etc.
    """

    def __init__(self) -> None:
        self.routes: list[Route] = []

    # -- Registration ----------------------------------------------------------

    def add_route(
        self, method: str, pattern: str, handler: Callable
    ) -> None:
        """Register a route with a pattern like /users/{user_id:int}."""
        compiled = compile_path(pattern, handler, method=method)
        self.routes.append(compiled)

    def route(
        self, path: str, methods: list[str] | None = None
    ) -> Callable:
        """Decorator to register a handler for one or more methods."""
        if methods is None:
            methods = ["GET"]

        def decorator(handler: Callable) -> Callable:
            for method in methods:
                self.add_route(method, path, handler)
            return handler
        return decorator

    def get(self, path: str) -> Callable:
        """Decorator shortcut for GET routes."""
        return self.route(path, methods=["GET"])

    def post(self, path: str) -> Callable:
        """Decorator shortcut for POST routes."""
        return self.route(path, methods=["POST"])

    def put(self, path: str) -> Callable:
        """Decorator shortcut for PUT routes."""
        return self.route(path, methods=["PUT"])

    def delete(self, path: str) -> Callable:
        """Decorator shortcut for DELETE routes."""
        return self.route(path, methods=["DELETE"])

    def patch(self, path: str) -> Callable:
        """Decorator shortcut for PATCH routes."""
        return self.route(path, methods=["PATCH"])

    # -- Dispatch --------------------------------------------------------------

    def resolve(
        self, method: str, path: str
    ) -> tuple[Route, dict[str, Any]] | None:
        """Find a matching route and extract path parameters.

        Returns (route, params_dict) or None if no route matches.
        """
        method = method.upper()
        for route in self.routes:
            if route.method != method:
                continue
            params = route.match(path)
            if params is not None:
                return (route, params)
        return None

    def _find_routes_for_path(self, path: str) -> list[Route]:
        """Find all routes that match a path regardless of method."""
        matching: list[Route] = []
        for route in self.routes:
            if route.match(path) is not None:
                matching.append(route)
        return matching

    async def dispatch(self, request: Request) -> Response:
        """Dispatch a request to the matching handler.

        Returns:
        - The handler's response if a matching route is found.
        - 405 Method Not Allowed if the path exists but method doesn't.
        - 404 Not Found if no route matches the path.
        """
        method = request.method
        path = request.path

        result = self.resolve(method, path)
        if result is not None:
            route, params = result
            request.path_params = params
            return await route.handler(request)

        # Path exists but wrong method -> 405
        routes_for_path = self._find_routes_for_path(path)
        if routes_for_path:
            allowed = sorted(set(r.method for r in routes_for_path))
            return JSONResponse(
                content={
                    "error": "Method Not Allowed",
                    "detail": f"{method} {path} not allowed",
                    "allowed_methods": allowed,
                },
                status_code=405,
            )

        # No matching path -> 404
        return JSONResponse(
            content={"error": "Not Found", "detail": f"{path} not found"},
            status_code=404,
        )

    # -- Utility ---------------------------------------------------------------

    def list_routes(self) -> list[str]:
        """Return a list of registered routes as strings."""
        return [f"{r.method} {r.pattern}" for r in self.routes]
