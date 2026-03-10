"""
Kata 46 -- Query Parameter Parsing
Run: python playground/skeletons/46_query_parameters.py

Build automatic query parameter extraction from function signatures.
Parse query strings, coerce types based on annotations, handle defaults,
support list parameters (e.g., ?tag=a&tag=b), and Optional types.

Completes within 5 seconds.
"""

from __future__ import annotations

import inspect
import typing
from typing import Any, Optional, get_type_hints
from urllib.parse import parse_qs, urlencode


# ===========================================================================
# SECTION 1: Query String Parser
# ===========================================================================
# The query string is everything after '?' in a URL. Python's parse_qs
# handles the raw parsing; we add type coercion and signature binding.

def parse_query_string(query: str) -> dict[str, list[str]]:
    """Parse a raw query string into a dict of key -> list[str].

    Uses urllib.parse.parse_qs which always returns lists (because
    the same key can appear multiple times: ?tag=a&tag=b).
    """
    # TODO: Use parse_qs() to parse the query string
    # Pass keep_blank_values=True to preserve empty values
    # HINT: return parse_qs(query, keep_blank_values=True)
    pass


# ===========================================================================
# SECTION 2: Type Coercion for Query Parameters
# ===========================================================================

def _is_optional(annotation: type) -> tuple[bool, type]:
    """Check if a type is Optional[X] and return (True, X)."""
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is typing.Union and type(None) in args:
        real_types = [a for a in args if a is not type(None)]
        if len(real_types) == 1:
            return True, real_types[0]
    return False, annotation


def _is_list_type(annotation: type) -> tuple[bool, type]:
    """Check if a type is list[X] and return (True, X)."""
    # TODO: Use typing.get_origin() to check if the origin is list
    # If so, use typing.get_args() to get the item type
    # Return (True, item_type) or (False, annotation)
    # HINT: origin = typing.get_origin(annotation); if origin is list: ...
    pass
    return False, annotation


def coerce_query_value(
    raw_values: list[str],
    target_type: type,
    param_name: str,
) -> Any:
    """Coerce a list of raw query string values to the target type.

    For scalar types (int, float, str, bool), uses the last value.
    For list types, coerces each element.
    """
    is_list, item_type = _is_list_type(target_type)

    if is_list:
        # TODO: Coerce each element in raw_values to item_type
        # HINT: return [_coerce_single(v, item_type, param_name) for v in raw_values]
        pass

    # Scalar: use the last value (standard behavior)
    if not raw_values:
        raise QueryParamError(param_name, "no value provided")

    # TODO: Coerce the last value in raw_values to target_type
    # HINT: return _coerce_single(raw_values[-1], target_type, param_name)
    pass


def _coerce_single(value: str, target_type: type, param_name: str) -> Any:
    """Coerce a single string value to the target type."""
    if target_type is str:
        return value

    # TODO: Handle bool coercion
    # "true", "1", "yes", "on" -> True
    # "false", "0", "no", "off", "" -> False
    # Otherwise raise QueryParamError

    # TODO: Handle int coercion
    # try: return int(value) except ValueError: raise QueryParamError

    # TODO: Handle float coercion
    # try: return float(value) except ValueError: raise QueryParamError

    raise QueryParamError(
        param_name, f"unsupported query parameter type: {target_type}"
    )


class QueryParamError(Exception):
    """Raised when a query parameter cannot be parsed."""

    def __init__(self, param: str, message: str):
        self.param = param
        self.message = message
        super().__init__(f"Query parameter '{param}': {message}")


# ===========================================================================
# SECTION 3: Signature-Based Query Extraction
# ===========================================================================
# The key feature: inspect a function's signature + type hints, then
# automatically extract and coerce query parameters to match.

def extract_query_params(
    func: Any,
    query_string: str,
    *,
    skip_params: set[str] | None = None,
) -> dict[str, Any]:
    """Extract query parameters from a query string based on function signature.

    Inspects the function's type hints and parameters to determine:
    - Which query params to extract
    - What types to coerce them to
    - Which have defaults (optional) vs required
    - Which are list types (collect all values)
    """
    skip = skip_params or set()
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    raw_params = parse_query_string(query_string)
    result: dict[str, Any] = {}
    errors: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in skip:
            continue

        annotation = hints.get(param_name, str)
        is_optional, inner_type = _is_optional(annotation)

        if is_optional:
            annotation = inner_type

        has_default = param.default is not inspect.Parameter.empty
        default_value = param.default if has_default else None

        # TODO: Check if param_name is in raw_params
        # If yes: coerce the value using coerce_query_value()
        #         (wrap in try/except QueryParamError to collect errors)
        # If no and has_default: use default_value
        # If no and is_optional: use None
        # Otherwise: append an error "required but not provided"

    if errors:
        raise QueryParamError("__multiple__", "; ".join(errors))

    return result


# ===========================================================================
# SECTION 4: Ignite Framework Integration
# ===========================================================================

class Request:
    """Simulated HTTP request with query string."""

    def __init__(self, method: str, path: str, query_string: str = ""):
        self.method = method
        if "?" in path and not query_string:
            self.path, self.query_string = path.split("?", 1)
        else:
            self.path = path
            self.query_string = query_string

    @property
    def query_params(self) -> dict[str, list[str]]:
        """Parsed query parameters (raw, as lists of strings)."""
        return parse_query_string(self.query_string)


class Route:
    """A route that auto-extracts query parameters for its handler."""

    def __init__(self, path: str, method: str, handler: Any):
        self.path = path
        self.method = method
        self.handler = handler

    def handle(self, request: Request) -> dict[str, Any]:
        """Call the handler with auto-extracted query params."""
        # TODO: Use extract_query_params() to get params from request.query_string
        # Skip the "request" parameter, then call self.handler(request=request, **params)
        # HINT: params = extract_query_params(self.handler, request.query_string,
        #                                     skip_params={"request"})
        pass


# ===========================================================================
# SECTION 5: Demo Functions
# ===========================================================================

def demo_basic_parsing():
    """Show basic query string parsing."""
    print("--- Section 1: Basic Query String Parsing ---")

    qs = "name=Alice&age=30&active=true"
    parsed = parse_query_string(qs)
    print(f"  Query: {qs!r}")
    print(f"  Parsed: {parsed}")
    assert parsed == {"name": ["Alice"], "age": ["30"], "active": ["true"]}

    qs2 = "tag=python&tag=web&tag=api"
    parsed2 = parse_query_string(qs2)
    print(f"  Query: {qs2!r}")
    print(f"  Parsed: {parsed2}")
    assert parsed2 == {"tag": ["python", "web", "api"]}

    qs3 = "q=hello+world&empty=&encoded=%2Fpath"
    parsed3 = parse_query_string(qs3)
    print(f"  Query: {qs3!r}")
    print(f"  Parsed: {parsed3}")
    assert "hello world" in parsed3["q"][0]

    print("  [PASS] Basic parsing works")


def demo_type_coercion():
    """Show type coercion for query parameters."""
    print("\n--- Section 2: Type Coercion ---")

    result = coerce_query_value(["42"], int, "page")
    print(f"  '42' -> int: {result} (type={type(result).__name__})")
    assert result == 42 and isinstance(result, int)

    result = coerce_query_value(["3.14"], float, "price")
    print(f"  '3.14' -> float: {result} (type={type(result).__name__})")
    assert result == 3.14

    for val, expected in [("true", True), ("false", False),
                          ("1", True), ("0", False), ("yes", True)]:
        result = coerce_query_value([val], bool, "flag")
        print(f"  '{val}' -> bool: {result}")
        assert result == expected

    result = coerce_query_value(["hello"], str, "name")
    assert result == "hello"

    try:
        coerce_query_value(["abc"], int, "page")
    except QueryParamError as e:
        print(f"  'abc' -> int: {e.message}")

    print("  [PASS] Type coercion works")


def demo_signature_extraction():
    """Show automatic extraction from function signatures."""
    print("\n--- Section 3: Signature-Based Extraction ---")

    def search_items(
        request: Request,
        q: str,
        page: int = 1,
        limit: int = 20,
        sort: str = "relevance",
        active: Optional[bool] = None,
    ) -> dict:
        return {
            "q": q, "page": page, "limit": limit,
            "sort": sort, "active": active,
        }

    qs = "q=python+tutorial&page=3&limit=50"
    params = extract_query_params(
        search_items, qs, skip_params={"request"}
    )
    print(f"  Query: {qs!r}")
    print(f"  Extracted: {params}")
    assert params["q"] == "python tutorial"
    assert params["page"] == 3
    assert params["limit"] == 50
    assert params["sort"] == "relevance"
    assert params["active"] is None

    qs2 = "q=web&active=true"
    params2 = extract_query_params(
        search_items, qs2, skip_params={"request"}
    )
    print(f"  Query: {qs2!r}")
    print(f"  active = {params2['active']} (coerced from 'true')")
    assert params2["active"] is True

    print("  [PASS] Signature extraction works")


def demo_list_parameters():
    """Show list parameter support."""
    print("\n--- Section 4: List Parameters ---")

    def filter_products(
        request: Request,
        category: list[str],
        min_price: float = 0.0,
        tags: list[str] = [],
    ) -> dict:
        return {"category": category, "min_price": min_price, "tags": tags}

    qs = "category=electronics&category=computers&min_price=99.99&tags=sale&tags=new"
    params = extract_query_params(
        filter_products, qs, skip_params={"request"}
    )
    print(f"  Query: {qs!r}")
    print(f"  category = {params['category']}")
    print(f"  min_price = {params['min_price']}")
    print(f"  tags = {params['tags']}")
    assert params["category"] == ["electronics", "computers"]
    assert params["min_price"] == 99.99
    assert params["tags"] == ["sale", "new"]

    def get_items(request: Request, ids: list[int]) -> dict:
        return {"ids": ids}

    qs2 = "ids=1&ids=2&ids=3"
    params2 = extract_query_params(
        get_items, qs2, skip_params={"request"}
    )
    print(f"  ids (list[int]) = {params2['ids']}")
    assert params2["ids"] == [1, 2, 3]
    assert all(isinstance(i, int) for i in params2["ids"])

    print("  [PASS] List parameters work")


def demo_error_handling():
    """Show error handling for missing/invalid query params."""
    print("\n--- Section 5: Error Handling ---")

    def get_user(request: Request, user_id: int) -> dict:
        return {"user_id": user_id}

    try:
        extract_query_params(get_user, "", skip_params={"request"})
    except QueryParamError as e:
        print(f"  Missing required: {e}")
        assert "required" in str(e)

    try:
        extract_query_params(
            get_user, "user_id=abc", skip_params={"request"}
        )
    except QueryParamError as e:
        print(f"  Invalid type: {e}")
        assert "cannot convert" in str(e)

    print("  [PASS] Error handling works")


def demo_route_integration():
    """Show integration with Ignite's route system."""
    print("\n--- Section 6: Route Integration ---")

    def list_articles(
        request: Request,
        page: int = 1,
        per_page: int = 10,
        author: Optional[str] = None,
        tags: list[str] = [],
    ) -> dict:
        return {
            "page": page,
            "per_page": per_page,
            "author": author,
            "tags": tags,
        }

    route = Route("/articles", "GET", list_articles)

    request = Request("GET", "/articles?page=2&per_page=25&author=alice&tags=python&tags=web")
    result = route.handle(request)
    print(f"  GET /articles?page=2&per_page=25&author=alice&tags=python&tags=web")
    print(f"  Result: {result}")
    assert result["page"] == 2
    assert result["per_page"] == 25
    assert result["author"] == "alice"
    assert result["tags"] == ["python", "web"]

    request2 = Request("GET", "/articles")
    result2 = route.handle(request2)
    print(f"  GET /articles (no query params)")
    print(f"  Result: {result2}")
    assert result2["page"] == 1
    assert result2["per_page"] == 10
    assert result2["author"] is None
    assert result2["tags"] == []

    print("  [PASS] Route integration works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    try:
        demo_basic_parsing()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_type_coercion()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_signature_extraction()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_list_parameters()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_error_handling()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_route_integration()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print("\n--- Summary ---")
    print("Query parameter parsing gives our Ignite framework:")
    print("  - Automatic query string parsing with urllib.parse")
    print("  - Type coercion from annotations (str, int, float, bool)")
    print("  - Default values from function signatures")
    print("  - Optional[T] support for nullable params")
    print("  - list[T] for repeated query params (?tag=a&tag=b)")
    print("  - Signature inspection to auto-bind params to handlers")
    print("  - Clear error messages for missing/invalid params")
    print("\nImplement the TODOs above to make all 6 sections pass!")
    print("Next up: Kata 47 -- response models!")


if __name__ == "__main__":
    main()
