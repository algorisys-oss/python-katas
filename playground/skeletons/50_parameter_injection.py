"""
Kata 50 -- Automatic Parameter Injection
Run: python playground/skeletons/50_parameter_injection.py

Use inspect.signature() to automatically inject parameters into handler
functions based on their annotations and names. Path params from URL,
query params from query string, body from request body (if annotated with
a model class), dependencies from Depends().

Completes within 5 seconds.
"""

import inspect
import json
import re
from typing import Any, Callable, get_type_hints
from urllib.parse import parse_qs


# ===========================================================================
# SECTION 1: Request & Response
# ===========================================================================

class Request:
    """Simulated HTTP request with path, query, and body data."""

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        body: bytes = b"",
        headers: dict[str, str] | None = None,
        query_string: str = "",
    ):
        self.method = method.upper()
        self.path = path
        self.body = body
        self.headers = headers or {}
        self.query_string = query_string

    @property
    def json_body(self) -> dict[str, Any]:
        """Parse body as JSON."""
        if not self.body:
            return {}
        return json.loads(self.body)

    @property
    def query_params(self) -> dict[str, str]:
        """Parse query string into a dict (first value only)."""
        parsed = parse_qs(self.query_string)
        return {k: v[0] for k, v in parsed.items()}


class Response:
    """Simulated HTTP response."""

    def __init__(self, body: Any = None, status_code: int = 200):
        self.body = body
        self.status_code = status_code


# ===========================================================================
# SECTION 2: Body Model Base Class
# ===========================================================================
# Any parameter annotated with a BaseModel subclass is treated as a
# request body parameter and populated from JSON.

class BaseModel:
    """Simple model base class for request body parsing.

    Subclasses define fields as class annotations. The model is
    constructed from a dict (typically parsed from JSON).
    """

    def __init__(self, **kwargs: Any):
        hints = get_type_hints(type(self))
        for field, field_type in hints.items():
            if field.startswith("_"):
                continue
            value = kwargs.get(field, getattr(type(self), field, None))
            if value is None and field not in kwargs:
                raise ValueError(f"Missing required field: {field}")
            setattr(self, field, value)

    def dict(self) -> dict[str, Any]:
        hints = get_type_hints(type(self))
        return {f: getattr(self, f) for f in hints if not f.startswith("_")}

    def __repr__(self) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in self.dict().items())
        return f"{type(self).__name__}({fields})"


# ===========================================================================
# SECTION 3: Depends() -- Dependency Injection Marker
# ===========================================================================

class Depends:
    """Marker for dependency injection.

    Usage in handler signatures:
        def handler(db: Session = Depends(get_db)):
            ...

    The injector calls get_db() and passes the result as 'db'.
    """

    def __init__(self, dependency: Callable):
        self.dependency = dependency

    def __repr__(self) -> str:
        return f"Depends({self.dependency.__name__})"


# ===========================================================================
# SECTION 4: Parameter Injector
# ===========================================================================
# The core engine: inspect handler signatures and fill in values from
# the request's path params, query params, body, or dependencies.

class ParameterInjector:
    """Inspects handler signatures and injects parameters automatically.

    Parameter sources (in priority order):
    1. **Depends** -- default value is Depends(func) -> call the dependency
    2. **Body model** -- annotation is a BaseModel subclass -> parse from JSON
    3. **Path params** -- name matches a {param} in the route path
    4. **Query params** -- remaining simple-type params come from query string
    5. **Request** -- if annotated as Request, pass the raw request object
    """

    def __init__(self, path_template: str, handler: Callable):
        self.path_template = path_template
        self.handler = handler
        self.sig = inspect.signature(handler)
        # Use signature annotations directly instead of get_type_hints()
        # to avoid NameError with locally-defined classes
        self.hints = {
            name: p.annotation
            for name, p in self.sig.parameters.items()
            if p.annotation is not inspect.Parameter.empty
        }

        # TODO: Extract path parameter names from template like "/users/{user_id}"
        # Use re.findall(r"\{(\w+)\}", path_template) to find all {param} names
        self.path_param_names: set[str] = set()

        # TODO: Build regex to extract path param values from actual paths
        # Replace each {param} with (?P<param>[^/]+) and compile
        # e.g., "/users/{user_id}" -> "^/users/(?P<user_id>[^/]+)$"
        self.path_regex = re.compile(f"^{path_template}$")

    def extract_path_params(self, actual_path: str) -> dict[str, str]:
        """Extract path parameter values from an actual request path."""
        match = self.path_regex.match(actual_path)
        if not match:
            return {}
        return match.groupdict()

    def inject(self, request: Request) -> dict[str, Any]:
        """Build the kwargs dict to call the handler with.

        Inspects each parameter and determines its source.
        """
        kwargs: dict[str, Any] = {}
        path_params = self.extract_path_params(request.path)
        query_params = request.query_params

        for name, param in self.sig.parameters.items():
            annotation = self.hints.get(name, param.annotation)

            # TODO: 1. Request object itself
            # If annotation is Request or name == "request", pass the request
            # kwargs[name] = request; continue

            # TODO: 2. Depends() -- call the dependency function
            # If param.default is a Depends instance:
            #   dep_func = param.default.dependency
            #   dep_sig = inspect.signature(dep_func)
            #   Build dep_kwargs: for each dep param, if it's Request, pass request
            #   kwargs[name] = dep_func(**dep_kwargs); continue

            # TODO: 3. Body model -- annotation is a BaseModel subclass
            # If annotation is a type and subclass of BaseModel:
            #   kwargs[name] = annotation(**request.json_body); continue

            # TODO: 4. Path parameter
            # If name is in self.path_param_names:
            #   raw_value = path_params.get(name, "")
            #   kwargs[name] = self._coerce(raw_value, annotation); continue

            # TODO: 5. Query parameter
            # If name is in query_params:
            #   kwargs[name] = self._coerce(query_params[name], annotation); continue

            # TODO: 6. Use default value if available
            # If param.default is not inspect.Parameter.empty:
            #   kwargs[name] = param.default; continue

            raise ValueError(
                f"Cannot resolve parameter '{name}' for {self.handler.__name__}"
            )

        return kwargs

    def _coerce(self, value: str, annotation: Any) -> Any:
        """Coerce a string value to the annotated type."""
        # TODO: Convert string value to the annotation type
        # - str or empty annotation -> return as-is
        # - int -> int(value)
        # - float -> float(value)
        # - bool -> value.lower() in ("true", "1", "yes")
        return value

    def call(self, request: Request) -> Any:
        """Inject parameters and call the handler."""
        kwargs = self.inject(request)
        return self.handler(**kwargs)


# ===========================================================================
# SECTION 5: Mini App with Auto-Injection
# ===========================================================================

class IgniteApp:
    """Mini framework that uses ParameterInjector for auto-injection."""

    def __init__(self):
        self._routes: list[tuple[str, str, Callable, ParameterInjector]] = []

    def get(self, path: str):
        return self._register("GET", path)

    def post(self, path: str):
        return self._register("POST", path)

    def put(self, path: str):
        return self._register("PUT", path)

    def delete(self, path: str):
        return self._register("DELETE", path)

    def _register(self, method: str, path: str):
        def decorator(func: Callable) -> Callable:
            injector = ParameterInjector(path, func)
            self._routes.append((method, path, func, injector))
            return func
        return decorator

    def dispatch(self, request: Request) -> Response:
        """Find matching route and dispatch with auto-injection."""
        for method, path, handler, injector in self._routes:
            if method != request.method:
                continue
            path_params = injector.extract_path_params(request.path)
            if path_params is not None and injector.path_regex.match(request.path):
                try:
                    result = injector.call(request)
                    return Response(body=result, status_code=200)
                except ValueError as e:
                    return Response(body={"error": str(e)}, status_code=422)
        return Response(body={"error": "Not Found"}, status_code=404)


# ===========================================================================
# SECTION 6: Demos
# ===========================================================================

def demo_path_params():
    """Show path parameter injection."""
    print("--- Section 1: Path Parameter Injection ---")

    app = IgniteApp()

    @app.get("/users/{user_id}")
    def get_user(user_id: int) -> dict:
        return {"user_id": user_id, "name": f"User {user_id}"}

    resp = app.dispatch(Request("GET", "/users/42"))
    assert resp.body["user_id"] == 42
    assert isinstance(resp.body["user_id"], int)
    print(f"  GET /users/42 -> {resp.body}")

    @app.get("/items/{category}/{item_id}")
    def get_item(category: str, item_id: int) -> dict:
        return {"category": category, "item_id": item_id}

    resp2 = app.dispatch(Request("GET", "/items/electronics/7"))
    assert resp2.body == {"category": "electronics", "item_id": 7}
    print(f"  GET /items/electronics/7 -> {resp2.body}")

    print("  [PASS] Path parameter injection works")


def demo_query_params():
    """Show query parameter injection."""
    print("\n--- Section 2: Query Parameter Injection ---")

    app = IgniteApp()

    @app.get("/search")
    def search(q: str, limit: int = 10, offset: int = 0) -> dict:
        return {"query": q, "limit": limit, "offset": offset}

    resp = app.dispatch(Request("GET", "/search", query_string="q=python&limit=5"))
    assert resp.body == {"query": "python", "limit": 5, "offset": 0}
    print(f"  GET /search?q=python&limit=5 -> {resp.body}")

    resp2 = app.dispatch(Request("GET", "/search", query_string="q=rust"))
    assert resp2.body == {"query": "rust", "limit": 10, "offset": 0}
    print(f"  GET /search?q=rust -> {resp2.body}")

    print("  [PASS] Query parameter injection works")


def demo_body_injection():
    """Show request body injection via BaseModel annotation."""
    print("\n--- Section 3: Body Model Injection ---")

    class CreateUser(BaseModel):
        name: str
        email: str
        age: int = 0

    app = IgniteApp()

    @app.post("/users")
    def create_user(user: CreateUser) -> dict:
        return {"created": user.dict()}

    body = json.dumps({"name": "Alice", "email": "alice@example.com", "age": 30})
    resp = app.dispatch(Request("POST", "/users", body=body.encode()))
    assert resp.body["created"]["name"] == "Alice"
    assert resp.body["created"]["age"] == 30
    print(f"  POST /users -> {resp.body}")

    print("  [PASS] Body model injection works")


def demo_depends():
    """Show dependency injection via Depends()."""
    print("\n--- Section 4: Depends() Injection ---")

    # Simulate a database session dependency
    class FakeDB:
        def __init__(self):
            self.connected = True
        def query(self, table: str) -> list:
            return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    def get_db() -> FakeDB:
        return FakeDB()

    # Simulate an auth dependency that reads from request
    class CurrentUser:
        def __init__(self, user_id: int, role: str):
            self.user_id = user_id
            self.role = role

    def get_current_user(request: Request) -> CurrentUser:
        # In real code, this would parse a JWT token from headers
        token = request.headers.get("authorization", "")
        if token == "Bearer admin-token":
            return CurrentUser(user_id=1, role="admin")
        return CurrentUser(user_id=0, role="anonymous")

    app = IgniteApp()

    @app.get("/db-users")
    def list_users(db: FakeDB = Depends(get_db)) -> dict:
        users = db.query("users")
        return {"users": users}

    @app.get("/me")
    def get_me(user: CurrentUser = Depends(get_current_user)) -> dict:
        return {"user_id": user.user_id, "role": user.role}

    resp = app.dispatch(Request("GET", "/db-users"))
    assert resp.body["users"][0]["name"] == "Alice"
    print(f"  GET /db-users -> {resp.body}")

    resp2 = app.dispatch(Request(
        "GET", "/me",
        headers={"authorization": "Bearer admin-token"},
    ))
    assert resp2.body["role"] == "admin"
    print(f"  GET /me (admin) -> {resp2.body}")

    resp3 = app.dispatch(Request("GET", "/me"))
    assert resp3.body["role"] == "anonymous"
    print(f"  GET /me (no token) -> {resp3.body}")

    print("  [PASS] Depends() injection works")


def demo_mixed_params():
    """Show handlers with mixed parameter types."""
    print("\n--- Section 5: Mixed Parameter Types ---")

    class UpdateItem(BaseModel):
        name: str
        price: float

    class FakeDB:
        connected: bool = True

    def get_db() -> FakeDB:
        return FakeDB()

    app = IgniteApp()

    @app.put("/items/{item_id}")
    def update_item(
        item_id: int,
        item: UpdateItem,
        db: FakeDB = Depends(get_db),
    ) -> dict:
        return {
            "item_id": item_id,
            "updated": item.dict(),
            "db_connected": db.connected,
        }

    body = json.dumps({"name": "Widget", "price": 9.99})
    resp = app.dispatch(Request("PUT", "/items/5", body=body.encode()))
    assert resp.body["item_id"] == 5
    assert resp.body["updated"]["name"] == "Widget"
    assert resp.body["updated"]["price"] == 9.99
    assert resp.body["db_connected"] is True
    print(f"  PUT /items/5 -> {resp.body}")

    print("  [PASS] Mixed parameter types work")


def demo_request_passthrough():
    """Show that Request can also be injected directly."""
    print("\n--- Section 6: Request Passthrough ---")

    app = IgniteApp()

    @app.get("/raw")
    def raw_handler(request: Request, q: str = "default") -> dict:
        return {
            "method": request.method,
            "path": request.path,
            "query": q,
        }

    resp = app.dispatch(Request("GET", "/raw", query_string="q=hello"))
    assert resp.body["method"] == "GET"
    assert resp.body["path"] == "/raw"
    assert resp.body["query"] == "hello"
    print(f"  GET /raw?q=hello -> {resp.body}")

    print("  [PASS] Request passthrough works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    try:
        demo_path_params()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_query_params()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_body_injection()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_depends()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_mixed_params()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_request_passthrough()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print("\n--- Summary ---")
    print("Automatic parameter injection gives our Ignite framework:")
    print("  - Path params extracted from URL patterns via regex")
    print("  - Query params parsed from query string with type coercion")
    print("  - Body models parsed from JSON into BaseModel subclasses")
    print("  - Dependencies resolved via Depends() markers")
    print("  - Mixed parameter types in a single handler")
    print("  - Raw Request passthrough when needed")
    print("\nImplement the TODOs above to make all 6 sections pass!")
    print("Next up: Kata 51 -- type-driven validation!")


if __name__ == "__main__":
    main()
