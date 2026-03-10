"""
Kata 53 -- Swagger UI Integration
Run: python playground/53_swagger_ui.py

Build endpoints that serve Swagger UI and ReDoc HTML pages pointing to
the OpenAPI schema. Generate HTML templates that load Swagger UI / ReDoc
from CDN and feed them the schema URL. Test by verifying the HTML output
contains correct schema references.

Completes within 5 seconds.
"""

import inspect
import json
import re
from typing import Any, Callable, get_type_hints


# ===========================================================================
# SECTION 1: Minimal Framework Pieces (from prior katas)
# ===========================================================================

PYTHON_TYPE_MAP = {
    str: "string", int: "integer", float: "number",
    bool: "boolean", list: "array", dict: "object",
}


class Field:
    """Field with constraints for schema generation."""
    def __init__(self, *, default: Any = None, required: bool = True,
                 min_length: int | None = None, max_length: int | None = None,
                 ge: int | float | None = None, le: int | float | None = None,
                 description: str = "", example: Any = None):
        self.default = default
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.ge = ge
        self.le = le
        self.description = description
        self.example = example
        self._name = ""

    def __set_name__(self, owner, name):
        self._name = name

    def to_schema(self) -> dict[str, Any]:
        s: dict[str, Any] = {}
        if self.description: s["description"] = self.description
        if self.min_length is not None: s["minLength"] = self.min_length
        if self.max_length is not None: s["maxLength"] = self.max_length
        if self.ge is not None: s["minimum"] = self.ge
        if self.le is not None: s["maximum"] = self.le
        return s


class BaseModel:
    """Simple model base class."""
    def __init__(self, **kwargs):
        for name in get_type_hints(type(self)):
            if not name.startswith("_"):
                setattr(self, name, kwargs.get(name))

    @classmethod
    def schema(cls) -> dict[str, Any]:
        hints = get_type_hints(cls)
        props, req = {}, []
        for name, tp in hints.items():
            if name.startswith("_"): continue
            prop = {"type": PYTHON_TYPE_MAP.get(tp, "string")}
            for klass in cls.__mro__:
                if name in klass.__dict__ and isinstance(klass.__dict__[name], Field):
                    prop.update(klass.__dict__[name].to_schema())
                    if klass.__dict__[name].required: req.append(name)
                    break
            else:
                req.append(name)
            props[name] = prop
        return {"type": "object", "title": cls.__name__,
                "properties": props, "required": req}


class RouteInfo:
    """Route metadata."""
    def __init__(self, path, method, handler, *, tags=None, summary=None,
                 description=None, response_model=None, status_code=200,
                 deprecated=False):
        self.path = path
        self.method = method.upper()
        self.handler = handler
        self.tags = tags or []
        self.summary = summary or handler.__name__.replace("_", " ").title()
        self.description = description or handler.__doc__ or ""
        self.response_model = response_model
        self.status_code = status_code
        self.deprecated = deprecated


# ===========================================================================
# SECTION 2: Swagger UI HTML Template
# ===========================================================================

def generate_swagger_html(
    openapi_url: str = "/openapi.json",
    title: str = "Ignite API - Swagger UI",
) -> str:
    """Generate an HTML page that loads Swagger UI from CDN.

    The generated page:
    1. Loads Swagger UI CSS and JS from unpkg CDN
    2. Initializes SwaggerUIBundle with the OpenAPI schema URL
    3. Renders the interactive API documentation
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
        html {{ box-sizing: border-box; overflow-y: scroll; }}
        *, *::before, *::after {{ box-sizing: inherit; }}
        body {{ margin: 0; background: #fafafa; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                url: "{openapi_url}",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout",
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true
            }});
        }};
    </script>
</body>
</html>"""


# ===========================================================================
# SECTION 3: ReDoc HTML Template
# ===========================================================================

def generate_redoc_html(
    openapi_url: str = "/openapi.json",
    title: str = "Ignite API - ReDoc",
) -> str:
    """Generate an HTML page that loads ReDoc from CDN.

    ReDoc provides a clean, three-panel documentation layout:
    - Left panel: navigation menu
    - Center panel: endpoint documentation
    - Right panel: request/response examples
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 0; }}
    </style>
</head>
<body>
    <redoc spec-url="{openapi_url}"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""


# ===========================================================================
# SECTION 4: Simulated ASGI Response
# ===========================================================================

class ASGIResponse:
    """Captures ASGI send() calls for testing."""

    def __init__(self):
        self.status: int = 200
        self.headers: dict[str, str] = {}
        self.body: bytes = b""

    async def send(self, message: dict[str, Any]) -> None:
        if message["type"] == "http.response.start":
            self.status = message["status"]
            self.headers = {
                k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in message.get("headers", [])
            }
        elif message["type"] == "http.response.body":
            self.body += message.get("body", b"")

    @property
    def text(self) -> str:
        return self.body.decode()


# ===========================================================================
# SECTION 5: IgniteApp with Docs Routes
# ===========================================================================

class OpenAPIGenerator:
    """Simplified OpenAPI generator."""

    def __init__(self, title, version, description=""):
        self.title = title
        self.version = version
        self.description = description

    def generate(self, routes: list[RouteInfo]) -> dict[str, Any]:
        schemas: dict[str, Any] = {}
        paths: dict[str, Any] = {}
        for route in routes:
            if route.path not in paths:
                paths[route.path] = {}
            op: dict[str, Any] = {
                "summary": route.summary,
                "operationId": route.handler.__name__,
            }
            if route.tags: op["tags"] = route.tags
            if route.description: op["description"] = route.description

            # Extract params from signature
            sig = inspect.signature(route.handler)
            hints = {
                n: p.annotation for n, p in sig.parameters.items()
                if p.annotation is not inspect.Parameter.empty
            }
            path_params = set(re.findall(r"\{(\w+)\}", route.path))
            params = []
            for name, param in sig.parameters.items():
                ann = hints.get(name, param.annotation)
                if name == "request": continue
                if isinstance(ann, type) and issubclass(ann, BaseModel):
                    model_name = ann.__name__
                    schemas[model_name] = ann.schema()
                    op["requestBody"] = {
                        "required": True,
                        "content": {"application/json": {
                            "schema": {"$ref": f"#/components/schemas/{model_name}"}
                        }}
                    }
                    continue
                if name in path_params:
                    params.append({"name": name, "in": "path", "required": True,
                                   "schema": {"type": PYTHON_TYPE_MAP.get(ann, "string")}})
                else:
                    params.append({"name": name, "in": "query",
                                   "required": param.default is inspect.Parameter.empty,
                                   "schema": {"type": PYTHON_TYPE_MAP.get(ann, "string")}})
            if params: op["parameters"] = params

            # Response
            resp: dict[str, Any] = {"description": "Successful response"}
            if route.response_model and issubclass(route.response_model, BaseModel):
                mn = route.response_model.__name__
                schemas[mn] = route.response_model.schema()
                resp["content"] = {"application/json": {
                    "schema": {"$ref": f"#/components/schemas/{mn}"}
                }}
            op["responses"] = {str(route.status_code): resp}
            paths[route.path][route.method.lower()] = op

        spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {"title": self.title, "version": self.version},
            "paths": paths,
        }
        if self.description: spec["info"]["description"] = self.description
        if schemas: spec["components"] = {"schemas": schemas}
        return spec


class IgniteApp:
    """Mini framework with Swagger UI and ReDoc integration."""

    def __init__(
        self,
        title: str = "Ignite API",
        version: str = "1.0.0",
        description: str = "",
        docs_url: str = "/docs",
        redoc_url: str = "/redoc",
        openapi_url: str = "/openapi.json",
    ):
        self.title = title
        self.version = version
        self.description = description
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.openapi_url = openapi_url
        self._routes: list[RouteInfo] = []
        self._docs_routes_installed = False

    def get(self, path: str, **kwargs):
        return self._register("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self._register("POST", path, status_code=201, **kwargs)

    def _register(self, method: str, path: str, **kwargs):
        def decorator(func: Callable) -> Callable:
            route = RouteInfo(path, method, func, **kwargs)
            self._routes.append(route)
            return func
        return decorator

    def _install_docs_routes(self) -> None:
        """Install the /docs, /redoc, and /openapi.json routes."""
        if self._docs_routes_installed:
            return
        self._docs_routes_installed = True

    def openapi(self) -> dict[str, Any]:
        """Generate the OpenAPI spec (excludes docs routes)."""
        gen = OpenAPIGenerator(self.title, self.version, self.description)
        return gen.generate(self._routes)

    def _handle_docs_request(self, path: str) -> tuple[int, str, str] | None:
        """Handle built-in documentation routes.

        Returns (status_code, content_type, body) or None if not a docs route.
        """
        if path == self.openapi_url:
            return (
                200,
                "application/json",
                json.dumps(self.openapi(), indent=2),
            )
        elif path == self.docs_url:
            return (
                200,
                "text/html; charset=utf-8",
                generate_swagger_html(
                    openapi_url=self.openapi_url,
                    title=f"{self.title} - Swagger UI",
                ),
            )
        elif path == self.redoc_url:
            return (
                200,
                "text/html; charset=utf-8",
                generate_redoc_html(
                    openapi_url=self.openapi_url,
                    title=f"{self.title} - ReDoc",
                ),
            )
        return None

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        """ASGI application interface."""
        if scope["type"] != "http":
            return

        path = scope.get("path", "/")
        method = scope.get("method", "GET")

        # Check docs routes first
        docs_result = self._handle_docs_request(path)
        if docs_result:
            status, content_type, body = docs_result
            await send({
                "type": "http.response.start",
                "status": status,
                "headers": [
                    [b"content-type", content_type.encode()],
                ],
            })
            await send({
                "type": "http.response.body",
                "body": body.encode(),
            })
            return

        # Dispatch to user routes
        for route in self._routes:
            if route.method == method and route.path == path:
                result = route.handler(None)  # simplified
                body_bytes = json.dumps(result).encode()
                await send({
                    "type": "http.response.start",
                    "status": route.status_code,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": body_bytes,
                })
                return

        # 404
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": json.dumps({"error": "Not Found"}).encode(),
        })


# ===========================================================================
# SECTION 6: Demos
# ===========================================================================

import asyncio


async def simulate_request(
    app: IgniteApp, method: str, path: str
) -> ASGIResponse:
    """Helper to simulate an ASGI request and capture the response."""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
    }
    response = ASGIResponse()

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    await app(scope, receive, response.send)
    return response


def demo_swagger_html():
    """Show Swagger UI HTML generation."""
    print("--- Section 1: Swagger UI HTML ---")

    html = generate_swagger_html(
        openapi_url="/openapi.json",
        title="My API - Swagger UI",
    )

    # Verify key elements
    assert "swagger-ui" in html
    assert "swagger-ui-bundle.js" in html
    assert "swagger-ui-standalone-preset.js" in html
    assert "/openapi.json" in html
    assert "My API - Swagger UI" in html
    assert "SwaggerUIBundle" in html
    print(f"  HTML length: {len(html)} characters")
    print(f"  Contains swagger-ui div: True")
    print(f"  Contains CDN script: True")
    print(f"  Contains schema URL: True")
    print(f"  Contains title: True")

    print("  [PASS] Swagger UI HTML generation works")


def demo_redoc_html():
    """Show ReDoc HTML generation."""
    print("\n--- Section 2: ReDoc HTML ---")

    html = generate_redoc_html(
        openapi_url="/openapi.json",
        title="My API - ReDoc",
    )

    assert "redoc" in html.lower()
    assert "spec-url" in html
    assert "/openapi.json" in html
    assert "My API - ReDoc" in html
    assert "redoc.standalone.js" in html
    print(f"  HTML length: {len(html)} characters")
    print(f"  Contains redoc element: True")
    print(f"  Contains spec-url: True")
    print(f"  Contains CDN script: True")

    print("  [PASS] ReDoc HTML generation works")


def demo_custom_urls():
    """Show customizing docs URLs."""
    print("\n--- Section 3: Custom URLs ---")

    html1 = generate_swagger_html(openapi_url="/api/v2/schema")
    assert "/api/v2/schema" in html1
    print(f"  Custom schema URL: /api/v2/schema -> found in HTML")

    html2 = generate_redoc_html(openapi_url="/api/v2/schema")
    assert "/api/v2/schema" in html2
    print(f"  Custom ReDoc schema URL: /api/v2/schema -> found in HTML")

    print("  [PASS] Custom URLs work")


def demo_app_docs_routes():
    """Show docs routes integrated into the app."""
    print("\n--- Section 4: App Docs Routes ---")

    class CreateUser(BaseModel):
        name: str = Field(min_length=1, description="User name")
        email: str = Field(description="Email address")

    app = IgniteApp(
        title="User API",
        version="1.0.0",
        description="User management service",
    )

    @app.get("/users", tags=["users"], summary="List users")
    def list_users(request):
        return {"users": []}

    @app.post("/users", tags=["users"], summary="Create user")
    def create_user(user: CreateUser):
        return {"created": True}

    # Test /openapi.json endpoint
    resp = asyncio.run(simulate_request(app, "GET", "/openapi.json"))
    assert resp.status == 200
    assert "application/json" in resp.headers.get("content-type", "")
    spec = json.loads(resp.text)
    assert spec["info"]["title"] == "User API"
    assert "/users" in spec["paths"]
    print(f"  GET /openapi.json -> {resp.status}, title={spec['info']['title']}")

    # Test /docs endpoint
    resp2 = asyncio.run(simulate_request(app, "GET", "/docs"))
    assert resp2.status == 200
    assert "text/html" in resp2.headers.get("content-type", "")
    assert "swagger-ui" in resp2.text
    assert "/openapi.json" in resp2.text
    print(f"  GET /docs -> {resp2.status}, has swagger-ui: True")

    # Test /redoc endpoint
    resp3 = asyncio.run(simulate_request(app, "GET", "/redoc"))
    assert resp3.status == 200
    assert "text/html" in resp3.headers.get("content-type", "")
    assert "redoc" in resp3.text.lower()
    assert "/openapi.json" in resp3.text
    print(f"  GET /redoc -> {resp3.status}, has redoc: True")

    print("  [PASS] App docs routes work")


def demo_custom_docs_config():
    """Show customizing docs URL paths."""
    print("\n--- Section 5: Custom Docs Configuration ---")

    app = IgniteApp(
        title="Custom API",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/schema.json",
    )

    @app.get("/health")
    def health(request):
        return {"status": "ok"}

    # Schema at custom URL
    resp = asyncio.run(simulate_request(app, "GET", "/api/schema.json"))
    assert resp.status == 200
    spec = json.loads(resp.text)
    assert spec["info"]["title"] == "Custom API"
    print(f"  GET /api/schema.json -> {resp.status}")

    # Swagger at custom URL
    resp2 = asyncio.run(simulate_request(app, "GET", "/api/docs"))
    assert resp2.status == 200
    assert "/api/schema.json" in resp2.text  # Points to custom schema URL
    print(f"  GET /api/docs -> {resp2.status}, schema URL = /api/schema.json")

    # ReDoc at custom URL
    resp3 = asyncio.run(simulate_request(app, "GET", "/api/redoc"))
    assert resp3.status == 200
    assert "/api/schema.json" in resp3.text
    print(f"  GET /api/redoc -> {resp3.status}, schema URL = /api/schema.json")

    # Old URLs should 404
    resp4 = asyncio.run(simulate_request(app, "GET", "/docs"))
    assert resp4.status == 404
    print(f"  GET /docs -> {resp4.status} (not found, moved to /api/docs)")

    print("  [PASS] Custom docs configuration works")


def demo_html_structure():
    """Show detailed HTML structure validation."""
    print("\n--- Section 6: HTML Structure ---")

    # Swagger UI structure
    swagger = generate_swagger_html("/schema.json", "Test Swagger")
    assert "<!DOCTYPE html>" in swagger
    assert '<div id="swagger-ui"></div>' in swagger
    assert "SwaggerUIBundle" in swagger
    assert "StandaloneLayout" in swagger
    assert "deepLinking: true" in swagger
    print("  Swagger UI structure valid:")
    print("    - DOCTYPE, div#swagger-ui, SwaggerUIBundle config")
    print("    - StandaloneLayout, deepLinking enabled")

    # ReDoc structure
    redoc = generate_redoc_html("/schema.json", "Test ReDoc")
    assert "<!DOCTYPE html>" in redoc
    assert '<redoc spec-url="/schema.json"></redoc>' in redoc
    assert "redoc.standalone.js" in redoc
    print("  ReDoc structure valid:")
    print("    - DOCTYPE, <redoc> element with spec-url, standalone JS")

    # Both use the same schema URL
    for html in (swagger, redoc):
        assert "/schema.json" in html
    print("  Both reference same schema URL: /schema.json")

    print("  [PASS] HTML structure validation works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_swagger_html()
    demo_redoc_html()
    demo_custom_urls()
    demo_app_docs_routes()
    demo_custom_docs_config()
    demo_html_structure()

    print("\n--- Summary ---")
    print("Swagger UI integration gives our Ignite framework:")
    print("  - Swagger UI HTML generation with CDN loading")
    print("  - ReDoc HTML generation with CDN loading")
    print("  - Customizable docs, redoc, and openapi URLs")
    print("  - /openapi.json endpoint serving the full spec")
    print("  - /docs endpoint serving interactive Swagger UI")
    print("  - /redoc endpoint serving clean ReDoc documentation")
    print("  - Proper HTML structure with responsive layout")
    print("\nAll 6 sections passed. Swagger UI integration mastered!")
    print("Next up: Kata 54 -- SQLite integration!")


if __name__ == "__main__":
    main()
