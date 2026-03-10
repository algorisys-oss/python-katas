"""
Kata 52 -- OpenAPI Schema Generation
Run: python playground/52_openapi_schema.py

Build automatic OpenAPI 3.0 schema generation from registered routes.
Extract path params, query params, request body schema, and response
schema from handler signatures and annotations. Generate the full
OpenAPI JSON document.

Completes within 5 seconds.
"""

import inspect
import json
import re
from typing import Any, Callable, get_type_hints


# ===========================================================================
# SECTION 1: Model & Field Definitions (from kata 51)
# ===========================================================================

PYTHON_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


class Field:
    """Field descriptor with constraints for schema generation."""

    def __init__(
        self,
        *,
        default: Any = None,
        required: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
        ge: int | float | None = None,
        le: int | float | None = None,
        gt: int | float | None = None,
        lt: int | float | None = None,
        pattern: str | None = None,
        description: str = "",
        example: Any = None,
    ):
        self.default = default
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt
        self.pattern = pattern
        self.description = description
        self.example = example
        self._name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    def to_schema(self) -> dict[str, Any]:
        schema: dict[str, Any] = {}
        if self.description:
            schema["description"] = self.description
        if self.example is not None:
            schema["example"] = self.example
        if self.min_length is not None:
            schema["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
        if self.ge is not None:
            schema["minimum"] = self.ge
        if self.le is not None:
            schema["maximum"] = self.le
        if self.gt is not None:
            schema["exclusiveMinimum"] = self.gt
        if self.lt is not None:
            schema["exclusiveMaximum"] = self.lt
        if self.pattern:
            schema["pattern"] = self.pattern
        return schema


class BaseModel:
    """Model base class for request/response schemas."""

    def __init__(self, **kwargs: Any):
        hints = get_type_hints(type(self))
        for name, tp in hints.items():
            if name.startswith("_"):
                continue
            setattr(self, name, kwargs.get(name))

    def dict(self) -> "dict[str, Any]":
        hints = get_type_hints(type(self))
        return {f: getattr(self, f) for f in hints if not f.startswith("_")}

    @classmethod
    def schema(cls) -> "dict[str, Any]":
        """Generate JSON Schema for this model."""
        hints = get_type_hints(cls)
        properties: "dict[str, Any]" = {}
        required: "list[str]" = []

        for field_name, field_type in hints.items():
            if field_name.startswith("_"):
                continue
            prop: "dict[str, Any]" = {
                "type": PYTHON_TYPE_MAP.get(field_type, "string"),
            }
            # Check for Field descriptor
            for klass in cls.__mro__:
                if field_name in klass.__dict__:
                    val = klass.__dict__[field_name]
                    if isinstance(val, Field):
                        prop.update(val.to_schema())
                        if val.required:
                            required.append(field_name)
                        break
            else:
                required.append(field_name)
            properties[field_name] = prop

        return {
            "type": "object",
            "title": cls.__name__,
            "properties": properties,
            "required": required,
        }


# ===========================================================================
# SECTION 2: Route Metadata
# ===========================================================================

class RouteInfo:
    """Stores route metadata for OpenAPI generation."""

    def __init__(
        self,
        path: str,
        method: str,
        handler: Callable,
        *,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_model: type | None = None,
        status_code: int = 200,
        deprecated: bool = False,
    ):
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
# SECTION 3: OpenAPI Schema Generator
# ===========================================================================

class Depends:
    """Dependency injection marker (excluded from OpenAPI params)."""
    def __init__(self, func: Callable):
        self.dependency = func


class Query:
    """Query parameter marker with constraints."""
    def __init__(
        self,
        default: Any = None,
        *,
        ge: int | float | None = None,
        le: int | float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        description: str = "",
        example: Any = None,
    ):
        self.default = default
        self.field = Field(
            ge=ge, le=le,
            min_length=min_length, max_length=max_length,
            description=description, example=example,
        )
        self.description = description
        self.example = example


class OpenAPIGenerator:
    """Generates an OpenAPI 3.0 specification from registered routes.

    Inspects each route's handler signature to extract:
    - Path parameters from {param} placeholders
    - Query parameters from simple-type params
    - Request body from BaseModel-annotated params
    - Response schema from response_model
    """

    def __init__(
        self,
        title: str = "Ignite API",
        version: str = "1.0.0",
        description: str = "",
    ):
        self.title = title
        self.version = version
        self.description = description

    def generate(self, routes: list[RouteInfo]) -> dict[str, Any]:
        """Generate the complete OpenAPI 3.0 document."""
        schemas: dict[str, Any] = {}
        paths: dict[str, Any] = {}

        for route in routes:
            # Convert {param} to OpenAPI style (already correct format)
            openapi_path = route.path

            if openapi_path not in paths:
                paths[openapi_path] = {}

            operation = self._build_operation(route, schemas)
            paths[openapi_path][route.method.lower()] = operation

        spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {
                "title": self.title,
                "version": self.version,
            },
            "paths": paths,
        }

        if self.description:
            spec["info"]["description"] = self.description

        if schemas:
            spec["components"] = {"schemas": schemas}

        return spec

    def _build_operation(
        self,
        route: RouteInfo,
        schemas: dict[str, Any],
    ) -> dict[str, Any]:
        """Build an OpenAPI operation object for a single route."""
        operation: dict[str, Any] = {
            "summary": route.summary,
            "operationId": route.handler.__name__,
        }

        if route.description:
            operation["description"] = route.description
        if route.tags:
            operation["tags"] = route.tags
        if route.deprecated:
            operation["deprecated"] = True

        # Analyze handler signature for parameters and body
        params, body_schema = self._extract_params(route, schemas)

        if params:
            operation["parameters"] = params

        if body_schema:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": body_schema,
                    }
                },
            }

        # Response schema
        operation["responses"] = self._build_responses(route, schemas)

        return operation

    def _extract_params(
        self,
        route: RouteInfo,
        schemas: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Extract parameters and body schema from handler signature."""
        sig = inspect.signature(route.handler)
        # Use signature annotations directly to avoid issues with
        # locally-defined classes and get_type_hints()
        hints = {
            n: p.annotation
            for n, p in sig.parameters.items()
            if p.annotation is not inspect.Parameter.empty
        }
        path_param_names = set(re.findall(r"\{(\w+)\}", route.path))

        params: list[dict[str, Any]] = []
        body_schema: dict[str, Any] | None = None

        for name, param in sig.parameters.items():
            annotation = hints.get(name, param.annotation)

            # Skip Request and Depends parameters
            if name == "request" or (
                hasattr(annotation, "__name__") and annotation.__name__ == "Request"
            ):
                continue
            if isinstance(param.default, Depends):
                continue

            # Body model
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                model_schema = annotation.schema()
                model_name = annotation.__name__
                schemas[model_name] = model_schema
                body_schema = {"$ref": f"#/components/schemas/{model_name}"}
                continue

            # Path parameter
            if name in path_param_names:
                p: dict[str, Any] = {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {
                        "type": PYTHON_TYPE_MAP.get(annotation, "string"),
                    },
                }
                params.append(p)
                continue

            # Query parameter
            query_schema: dict[str, Any] = {
                "type": PYTHON_TYPE_MAP.get(annotation, "string"),
            }
            required = param.default is inspect.Parameter.empty

            if isinstance(param.default, Query):
                query_marker = param.default
                query_schema.update(query_marker.field.to_schema())
                if query_marker.description:
                    pass  # already in schema via to_schema
                required = query_marker.default is None

            q: dict[str, Any] = {
                "name": name,
                "in": "query",
                "required": required,
                "schema": query_schema,
            }

            if isinstance(param.default, Query) and param.default.description:
                q["description"] = param.default.description

            params.append(q)

        return params, body_schema

    def _build_responses(
        self,
        route: RouteInfo,
        schemas: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the responses section for an operation."""
        status = str(route.status_code)
        response: dict[str, Any] = {
            "description": "Successful response",
        }

        if route.response_model and issubclass(route.response_model, BaseModel):
            model_schema = route.response_model.schema()
            model_name = route.response_model.__name__
            schemas[model_name] = model_schema
            response["content"] = {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{model_name}"},
                }
            }

        responses: dict[str, Any] = {status: response}

        # Add standard error responses
        if route.method in ("POST", "PUT", "PATCH"):
            responses["422"] = {
                "description": "Validation Error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {
                                    "type": "object",
                                    "properties": {
                                        "status_code": {"type": "integer"},
                                        "detail": {"type": "string"},
                                        "errors": {"type": "array"},
                                    },
                                }
                            },
                        }
                    }
                },
            }

        return responses


# ===========================================================================
# SECTION 4: IgniteApp with OpenAPI
# ===========================================================================

class IgniteApp:
    """Mini framework with integrated OpenAPI generation."""

    def __init__(
        self,
        title: str = "Ignite API",
        version: str = "1.0.0",
        description: str = "",
    ):
        self.title = title
        self.version = version
        self.description = description
        self._routes: list[RouteInfo] = []

    def get(self, path: str, **kwargs):
        return self._register("GET", path, status_code=kwargs.pop("status_code", 200), **kwargs)

    def post(self, path: str, **kwargs):
        return self._register("POST", path, status_code=kwargs.pop("status_code", 201), **kwargs)

    def put(self, path: str, **kwargs):
        return self._register("PUT", path, status_code=kwargs.pop("status_code", 200), **kwargs)

    def delete(self, path: str, **kwargs):
        return self._register("DELETE", path, status_code=kwargs.pop("status_code", 204), **kwargs)

    def _register(self, method: str, path: str, **kwargs):
        def decorator(func: Callable) -> Callable:
            route = RouteInfo(path, method, func, **kwargs)
            self._routes.append(route)
            return func
        return decorator

    def openapi(self) -> dict[str, Any]:
        """Generate the OpenAPI spec for all registered routes."""
        generator = OpenAPIGenerator(
            title=self.title,
            version=self.version,
            description=self.description,
        )
        return generator.generate(self._routes)

    def openapi_json(self, indent: int = 2) -> str:
        """Return the OpenAPI spec as formatted JSON."""
        return json.dumps(self.openapi(), indent=indent)


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_basic_schema():
    """Show basic OpenAPI schema generation."""
    print("--- Section 1: Basic OpenAPI Schema ---")

    app = IgniteApp(title="Pet Store API", version="0.1.0")

    @app.get("/pets", tags=["pets"], summary="List all pets")
    def list_pets() -> dict:
        """Returns a list of all pets in the store."""
        return {"pets": []}

    @app.get("/pets/{pet_id}", tags=["pets"], summary="Get a pet")
    def get_pet(pet_id: int) -> dict:
        return {"id": pet_id}

    spec = app.openapi()

    assert spec["openapi"] == "3.0.3"
    assert spec["info"]["title"] == "Pet Store API"
    assert spec["info"]["version"] == "0.1.0"
    assert "/pets" in spec["paths"]
    assert "/pets/{pet_id}" in spec["paths"]
    print(f"  OpenAPI version: {spec['openapi']}")
    print(f"  Title: {spec['info']['title']}")
    print(f"  Paths: {list(spec['paths'].keys())}")

    # Check path parameter
    pet_get = spec["paths"]["/pets/{pet_id}"]["get"]
    assert pet_get["parameters"][0]["name"] == "pet_id"
    assert pet_get["parameters"][0]["in"] == "path"
    assert pet_get["parameters"][0]["required"] is True
    print(f"  Path param: {pet_get['parameters'][0]}")

    print("  [PASS] Basic OpenAPI schema works")


def demo_query_params():
    """Show query parameter extraction."""
    print("\n--- Section 2: Query Parameters ---")

    app = IgniteApp(title="Search API", version="1.0.0")

    @app.get("/search", tags=["search"])
    def search(
        q: str,
        limit: int = Query(10, ge=1, le=100, description="Max results"),
        offset: int = Query(0, ge=0, description="Skip items"),
    ) -> dict:
        return {}

    spec = app.openapi()
    search_op = spec["paths"]["/search"]["get"]
    params = search_op["parameters"]

    assert len(params) == 3
    print(f"  Parameters ({len(params)}):")
    for p in params:
        print(f"    {p['name']}: in={p['in']}, required={p['required']}, "
              f"schema={p['schema']}")

    # q is required (no default)
    q_param = next(p for p in params if p["name"] == "q")
    assert q_param["required"] is True

    # limit has constraints
    limit_param = next(p for p in params if p["name"] == "limit")
    assert limit_param["schema"]["minimum"] == 1
    assert limit_param["schema"]["maximum"] == 100

    print("  [PASS] Query parameters work")


def demo_request_body():
    """Show request body schema extraction."""
    print("\n--- Section 3: Request Body Schema ---")

    class CreatePet(BaseModel):
        name: str = Field(min_length=1, max_length=50, description="Pet name")
        species: str = Field(description="Animal species")
        age: int = Field(ge=0, description="Age in years")

    app = IgniteApp(title="Pet API", version="1.0.0")

    @app.post("/pets", tags=["pets"], summary="Create a pet")
    def create_pet(pet: CreatePet) -> dict:
        return pet.dict()

    spec = app.openapi()
    create_op = spec["paths"]["/pets"]["post"]

    # Request body references the schema
    assert "requestBody" in create_op
    body_schema = create_op["requestBody"]["content"]["application/json"]["schema"]
    assert "$ref" in body_schema
    assert body_schema["$ref"] == "#/components/schemas/CreatePet"
    print(f"  Body schema ref: {body_schema['$ref']}")

    # Schema is in components
    assert "CreatePet" in spec["components"]["schemas"]
    model_schema = spec["components"]["schemas"]["CreatePet"]
    assert model_schema["title"] == "CreatePet"
    assert "name" in model_schema["properties"]
    assert model_schema["properties"]["name"]["minLength"] == 1
    print(f"  Model schema: {json.dumps(model_schema, indent=2)[:200]}...")

    print("  [PASS] Request body schema works")


def demo_response_model():
    """Show response model schema generation."""
    print("\n--- Section 4: Response Model ---")

    class PetResponse(BaseModel):
        id: int = Field(description="Pet ID")
        name: str = Field(description="Pet name")
        species: str = Field(description="Species")

    app = IgniteApp(title="Pet API", version="1.0.0")

    @app.get("/pets/{pet_id}", tags=["pets"], response_model=PetResponse)
    def get_pet(pet_id: int) -> dict:
        return {}

    spec = app.openapi()
    get_op = spec["paths"]["/pets/{pet_id}"]["get"]

    # Response references the schema
    resp_200 = get_op["responses"]["200"]
    resp_schema = resp_200["content"]["application/json"]["schema"]
    assert resp_schema["$ref"] == "#/components/schemas/PetResponse"
    print(f"  Response schema ref: {resp_schema['$ref']}")

    # Schema is in components
    assert "PetResponse" in spec["components"]["schemas"]
    print(f"  PetResponse fields: {list(spec['components']['schemas']['PetResponse']['properties'].keys())}")

    print("  [PASS] Response model works")


def demo_full_api():
    """Show a complete API with multiple endpoints."""
    print("\n--- Section 5: Full API Spec ---")

    class CreateUser(BaseModel):
        name: str = Field(min_length=1, max_length=100)
        email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")

    class UserResponse(BaseModel):
        id: int = Field(description="User ID")
        name: str = Field(description="Full name")
        email: str = Field(description="Email address")

    app = IgniteApp(
        title="User Management API",
        version="2.0.0",
        description="A comprehensive user management API",
    )

    @app.get("/users", tags=["users"], summary="List users")
    def list_users(
        limit: int = Query(10, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ) -> dict:
        """Return a paginated list of users."""
        return {}

    @app.post("/users", tags=["users"], summary="Create user",
              response_model=UserResponse)
    def create_user(user: CreateUser) -> dict:
        """Create a new user account."""
        return {}

    @app.get("/users/{user_id}", tags=["users"], summary="Get user",
             response_model=UserResponse)
    def get_user(user_id: int) -> dict:
        """Get a single user by ID."""
        return {}

    @app.put("/users/{user_id}", tags=["users"], summary="Update user")
    def update_user(user_id: int, user: CreateUser) -> dict:
        """Update an existing user."""
        return {}

    @app.delete("/users/{user_id}", tags=["users"], summary="Delete user")
    def delete_user(user_id: int) -> dict:
        """Remove a user from the system."""
        return {}

    spec = app.openapi()

    # Verify structure
    assert len(spec["paths"]) == 2  # /users and /users/{user_id}
    assert spec["info"]["description"] == "A comprehensive user management API"

    # Count operations
    op_count = sum(
        len(methods) for methods in spec["paths"].values()
    )
    assert op_count == 5
    print(f"  Paths: {list(spec['paths'].keys())}")
    print(f"  Total operations: {op_count}")
    print(f"  Schemas: {list(spec.get('components', {}).get('schemas', {}).keys())}")

    # Print condensed JSON
    spec_json = json.dumps(spec, indent=2)
    print(f"  Spec size: {len(spec_json)} characters")

    print("  [PASS] Full API spec works")


def demo_validation_errors_schema():
    """Show that POST/PUT routes include 422 error responses."""
    print("\n--- Section 6: Validation Error Responses ---")

    class Item(BaseModel):
        name: str = Field(min_length=1)

    app = IgniteApp(title="Test API", version="1.0.0")

    @app.get("/items")
    def list_items() -> dict:
        return {}

    @app.post("/items")
    def create_item(item: Item) -> dict:
        return {}

    spec = app.openapi()

    # GET should not have 422
    get_responses = spec["paths"]["/items"]["get"]["responses"]
    assert "422" not in get_responses
    print("  GET /items: no 422 response (correct)")

    # POST should have 422
    post_responses = spec["paths"]["/items"]["post"]["responses"]
    assert "422" in post_responses
    assert post_responses["422"]["description"] == "Validation Error"
    print("  POST /items: has 422 response (correct)")
    print(f"  422 schema: {json.dumps(post_responses['422'], indent=2)[:150]}...")

    print("  [PASS] Validation error responses work")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_basic_schema()
    demo_query_params()
    demo_request_body()
    demo_response_model()
    demo_full_api()
    demo_validation_errors_schema()

    print("\n--- Summary ---")
    print("OpenAPI schema generation gives our Ignite framework:")
    print("  - Automatic OpenAPI 3.0.3 spec generation")
    print("  - Path parameter extraction from route templates")
    print("  - Query parameter detection with constraints")
    print("  - Request body schemas from BaseModel annotations")
    print("  - Response model schemas with $ref references")
    print("  - Shared component schemas (no duplication)")
    print("  - Automatic 422 error responses for write operations")
    print("\nAll 6 sections passed. OpenAPI schema generation mastered!")
    print("Next up: Kata 53 -- Swagger UI integration!")


if __name__ == "__main__":
    main()
