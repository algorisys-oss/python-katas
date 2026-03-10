"""
Kata 51 -- Type-Driven Validation
Run: python playground/skeletons/51_type_driven_validation.py

Build a validation system that uses type annotations and descriptors to
validate request data automatically. Field descriptors with constraints
(min, max, pattern, etc.). Integrate with the parameter injection system.
Test with valid and invalid requests.

Completes within 5 seconds.
"""

import inspect
import json
import re
from typing import Any, Callable, get_type_hints
from urllib.parse import parse_qs


# ===========================================================================
# SECTION 1: Field Descriptor with Constraints
# ===========================================================================
# A Field() call defines validation constraints for a model attribute.

_MISSING = object()


class Field:
    """Descriptor that validates a model field against constraints.

    Usage:
        class User(ValidatedModel):
            name: str = Field(min_length=1, max_length=50)
            age: int = Field(ge=0, le=150)
            email: str = Field(pattern=r"^[^@]+@[^@]+\\.[^@]+$")
    """

    def __init__(
        self,
        *,
        default: Any = _MISSING,
        min_length: int | None = None,
        max_length: int | None = None,
        ge: int | float | None = None,      # greater than or equal
        le: int | float | None = None,       # less than or equal
        gt: int | float | None = None,       # greater than
        lt: int | float | None = None,       # less than
        pattern: str | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        description: str = "",
        examples: list[Any] | None = None,
    ):
        self.default = default
        self.min_length = min_length
        self.max_length = max_length
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt
        self.pattern = re.compile(pattern) if pattern else None
        self.pattern_str = pattern
        self.min_items = min_items
        self.max_items = max_items
        self.description = description
        self.examples = examples or []
        self._name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when the descriptor is assigned to a class attribute."""
        self._name = name

    def validate(self, value: Any) -> list[str]:
        """Validate a value and return a list of error messages."""
        errors: list[str] = []

        # TODO: String length checks
        # If value is a str:
        #   Check min_length: if len(value) < self.min_length, add error
        #   Check max_length: if len(value) > self.max_length, add error
        #   Check pattern: if self.pattern and not self.pattern.match(value), add error

        # TODO: Numeric range checks
        # If value is int or float:
        #   Check ge (>=): if value < self.ge, add error
        #   Check le (<=): if value > self.le, add error
        #   Check gt (>): if value <= self.gt, add error
        #   Check lt (<): if value >= self.lt, add error

        # TODO: Collection size checks
        # If value is list, tuple, or set:
        #   Check min_items: if len(value) < self.min_items, add error
        #   Check max_items: if len(value) > self.max_items, add error

        return errors

    def to_schema(self) -> dict[str, Any]:
        """Generate JSON Schema fragment for this field."""
        schema: dict[str, Any] = {}
        if self.description:
            schema["description"] = self.description
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
        if self.pattern_str:
            schema["pattern"] = self.pattern_str
        if self.min_items is not None:
            schema["minItems"] = self.min_items
        if self.max_items is not None:
            schema["maxItems"] = self.max_items
        if self.examples:
            schema["examples"] = self.examples
        return schema

    def __repr__(self) -> str:
        parts = [f"name={self._name!r}"]
        if self.ge is not None: parts.append(f"ge={self.ge}")
        if self.le is not None: parts.append(f"le={self.le}")
        if self.min_length is not None: parts.append(f"min_length={self.min_length}")
        if self.max_length is not None: parts.append(f"max_length={self.max_length}")
        if self.pattern_str: parts.append(f"pattern={self.pattern_str!r}")
        return f"Field({', '.join(parts)})"


# ===========================================================================
# SECTION 2: Validated Model
# ===========================================================================

class ValidationError(Exception):
    """Raised when model validation fails."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"{len(errors)} validation error(s)")

    def to_response(self) -> dict[str, Any]:
        return {
            "error": {
                "status_code": 422,
                "detail": "Validation Error",
                "errors": self.errors,
            }
        }


PYTHON_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
}


class ValidatedModel:
    """Base class for validated request/response models.

    Fields can be plain annotations or Field() descriptors with constraints.
    Validation runs automatically on __init__.
    """

    def __init__(self, **kwargs: Any):
        hints = get_type_hints(type(self))
        errors: list[dict[str, str]] = []

        for field_name, field_type in hints.items():
            if field_name.startswith("_"):
                continue

            # Get the Field descriptor if any
            field_desc = None
            for cls in type(self).__mro__:
                if field_name in cls.__dict__:
                    val = cls.__dict__[field_name]
                    if isinstance(val, Field):
                        field_desc = val
                    break

            # TODO: Get the value from kwargs, field default, or class attribute
            # 1. If field_name is in kwargs, use that value
            # 2. Else if field_desc exists and field_desc.default is not _MISSING,
            #    use field_desc.default
            # 3. Else if class has a non-Field attribute with this name, use it
            # 4. Else: append a "field is required" error and continue
            value = kwargs.get(field_name)
            if value is None and field_name not in kwargs:
                errors.append({
                    "field": field_name,
                    "message": "field is required",
                    "type": "missing",
                })
                continue

            # TODO: Type check -- try to coerce value to field_type
            # if not isinstance(value, field_type):
            #     try: value = field_type(value)
            #     except: append type_error and continue

            # TODO: Field constraint validation
            # if field_desc:
            #     field_errors = field_desc.validate(value)
            #     for msg in field_errors:
            #         errors.append({"field": field_name, "message": msg, ...})

            setattr(self, field_name, value)

        if errors:
            raise ValidationError(errors)

    def dict(self) -> "dict[str, Any]":
        hints = get_type_hints(type(self))
        return {f: getattr(self, f) for f in hints if not f.startswith("_")}

    @classmethod
    def schema(cls) -> "dict[str, Any]":
        """Generate a JSON Schema for this model."""
        hints = get_type_hints(cls)
        properties: "dict[str, Any]" = {}
        required: "list[str]" = []

        for field_name, field_type in hints.items():
            if field_name.startswith("_"):
                continue

            prop: "dict[str, Any]" = {
                "type": PYTHON_TYPE_MAP.get(field_type, "string"),
            }

            # Merge Field constraints if present
            for klass in cls.__mro__:
                if field_name in klass.__dict__:
                    val = klass.__dict__[field_name]
                    if isinstance(val, Field):
                        prop.update(val.to_schema())
                        if val.default is _MISSING:
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

    def __repr__(self) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in self.dict().items())
        return f"{type(self).__name__}({fields})"


# ===========================================================================
# SECTION 3: Query Parameter Validation
# ===========================================================================

class Query:
    """Marker for validated query parameters."""

    def __init__(
        self,
        default: Any = None,
        *,
        ge: int | float | None = None,
        le: int | float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        description: str = "",
    ):
        self.default = default
        self.field = Field(
            ge=ge, le=le,
            min_length=min_length, max_length=max_length,
            pattern=pattern, description=description,
        )

    def validate(self, name: str, value: Any) -> list[str]:
        self.field._name = name
        return self.field.validate(value)


# ===========================================================================
# SECTION 4: Validated Parameter Injector
# ===========================================================================

class Request:
    """Simulated HTTP request."""

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        body: bytes = b"",
        query_string: str = "",
    ):
        self.method = method.upper()
        self.path = path
        self.body = body
        self.query_string = query_string

    @property
    def json_body(self) -> dict[str, Any]:
        if not self.body:
            return {}
        return json.loads(self.body)

    @property
    def query_params(self) -> dict[str, str]:
        parsed = parse_qs(self.query_string)
        return {k: v[0] for k, v in parsed.items()}


class ValidatedInjector:
    """Parameter injector that validates inputs using Field constraints."""

    def __init__(self, path_template: str, handler: Callable):
        self.path_template = path_template
        self.handler = handler
        self.sig = inspect.signature(handler)
        self.hints = {
            name: p.annotation for name, p in self.sig.parameters.items()
            if p.annotation is not inspect.Parameter.empty
        }
        self.path_param_names = set(re.findall(r"\{(\w+)\}", path_template))
        pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path_template)
        self.path_regex = re.compile(f"^{pattern}$")

    def extract_path_params(self, actual_path: str) -> dict[str, str] | None:
        match = self.path_regex.match(actual_path)
        return match.groupdict() if match else None

    def call(self, request: Request) -> Any:
        kwargs: dict[str, Any] = {}
        errors: list[dict[str, str]] = []
        path_params = self.extract_path_params(request.path) or {}
        query_params = request.query_params

        for name, param in self.sig.parameters.items():
            annotation = self.hints.get(name, param.annotation)

            # Request passthrough
            if annotation is Request or name == "request":
                kwargs[name] = request
                continue

            # Body model (ValidatedModel subclass)
            if isinstance(annotation, type) and issubclass(annotation, ValidatedModel):
                try:
                    kwargs[name] = annotation(**request.json_body)
                except ValidationError as ve:
                    errors.extend(ve.errors)
                continue

            # Path param
            if name in self.path_param_names:
                raw = path_params.get(name, "")
                try:
                    kwargs[name] = self._coerce(raw, annotation)
                except (ValueError, TypeError) as e:
                    errors.append({
                        "field": name,
                        "message": f"invalid path parameter: {e}",
                        "type": "type_error",
                    })
                continue

            # Query param with optional Query() validation
            query_marker = None
            if isinstance(param.default, Query):
                query_marker = param.default

            if name in query_params:
                raw_val = query_params[name]
                try:
                    coerced = self._coerce(raw_val, annotation)
                except (ValueError, TypeError) as e:
                    errors.append({
                        "field": name,
                        "message": f"invalid query parameter: {e}",
                        "type": "type_error",
                    })
                    continue

                # Validate with Query() constraints
                if query_marker:
                    field_errors = query_marker.validate(name, coerced)
                    for msg in field_errors:
                        errors.append({
                            "field": name, "message": msg, "type": "value_error",
                        })
                kwargs[name] = coerced
                continue

            # Default value
            if query_marker and query_marker.default is not None:
                kwargs[name] = query_marker.default
                continue
            if param.default is not inspect.Parameter.empty and not isinstance(
                param.default, Query
            ):
                kwargs[name] = param.default
                continue

            errors.append({
                "field": name, "message": "parameter is required", "type": "missing",
            })

        if errors:
            raise ValidationError(errors)

        return self.handler(**kwargs)

    def _coerce(self, value: str, annotation: Any) -> Any:
        if annotation is inspect.Parameter.empty or annotation is str:
            return value
        if annotation is int:
            return int(value)
        if annotation is float:
            return float(value)
        if annotation is bool:
            return value.lower() in ("true", "1", "yes")
        return value


# ===========================================================================
# SECTION 5: Mini App
# ===========================================================================

class Response:
    def __init__(self, body: Any = None, status_code: int = 200):
        self.body = body
        self.status_code = status_code


class IgniteApp:
    def __init__(self):
        self._routes: list[tuple[str, str, ValidatedInjector]] = []

    def get(self, path: str):
        return self._register("GET", path)

    def post(self, path: str):
        return self._register("POST", path)

    def put(self, path: str):
        return self._register("PUT", path)

    def _register(self, method: str, path: str):
        def decorator(func: Callable) -> Callable:
            injector = ValidatedInjector(path, func)
            self._routes.append((method, path, injector))
            return func
        return decorator

    def dispatch(self, request: Request) -> Response:
        for method, path, injector in self._routes:
            if method != request.method:
                continue
            if injector.extract_path_params(request.path) is not None:
                try:
                    result = injector.call(request)
                    return Response(body=result, status_code=200)
                except ValidationError as ve:
                    return Response(body=ve.to_response(), status_code=422)
        return Response(body={"error": "Not Found"}, status_code=404)


# ===========================================================================
# SECTION 6: Demos
# ===========================================================================

def demo_field_validation():
    """Show Field descriptor validation."""
    print("--- Section 1: Field Descriptor Validation ---")

    class User(ValidatedModel):
        name: str = Field(min_length=1, max_length=50)
        age: int = Field(ge=0, le=150)
        email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")

    # Valid user
    user = User(name="Alice", age=30, email="alice@example.com")
    print(f"  Valid: {user}")
    assert user.name == "Alice"
    assert user.age == 30

    # Invalid: name too short
    try:
        User(name="", age=30, email="alice@example.com")
        assert False, "Should have raised"
    except ValidationError as e:
        print(f"  Empty name -> {e.errors[0]['message']}")
        assert "min" in e.errors[0]["message"].lower()

    # Invalid: age out of range
    try:
        User(name="Bob", age=-1, email="bob@example.com")
        assert False, "Should have raised"
    except ValidationError as e:
        print(f"  Negative age -> {e.errors[0]['message']}")
        assert "-1" in e.errors[0]["message"]

    # Invalid: bad email
    try:
        User(name="Charlie", age=25, email="not-an-email")
        assert False, "Should have raised"
    except ValidationError as e:
        print(f"  Bad email -> {e.errors[0]['message']}")
        assert "pattern" in e.errors[0]["message"].lower()

    print("  [PASS] Field validation works")


def demo_multiple_errors():
    """Show collecting multiple validation errors."""
    print("\n--- Section 2: Multiple Validation Errors ---")

    class Product(ValidatedModel):
        name: str = Field(min_length=1)
        price: float = Field(gt=0)
        quantity: int = Field(ge=0)

    try:
        Product(name="", price=-5.0, quantity=-1)
        assert False, "Should have raised"
    except ValidationError as e:
        assert len(e.errors) == 3
        for err in e.errors:
            print(f"  Error: {err['field']} -> {err['message']}")
        print(f"  Total errors: {len(e.errors)}")

    print("  [PASS] Multiple error collection works")


def demo_schema_generation():
    """Show JSON Schema generation from models."""
    print("\n--- Section 3: JSON Schema Generation ---")

    class CreateUser(ValidatedModel):
        name: str = Field(min_length=1, max_length=100, description="User's full name")
        age: int = Field(ge=0, le=150, description="User's age")
        email: str = Field(
            pattern=r"^[^@]+@[^@]+\.[^@]+$",
            description="Email address",
        )

    schema = CreateUser.schema()
    print(f"  Schema title: {schema['title']}")
    print(f"  Properties: {list(schema['properties'].keys())}")
    print(f"  Required: {schema['required']}")

    assert schema["title"] == "CreateUser"
    assert "name" in schema["properties"]
    assert schema["properties"]["name"]["minLength"] == 1
    assert schema["properties"]["age"]["minimum"] == 0
    assert "pattern" in schema["properties"]["email"]

    print(f"  name schema: {schema['properties']['name']}")
    print(f"  age schema: {schema['properties']['age']}")

    print("  [PASS] Schema generation works")


def demo_query_validation():
    """Show query parameter validation."""
    print("\n--- Section 4: Query Parameter Validation ---")

    app = IgniteApp()

    @app.get("/search")
    def search(
        q: str = Query(min_length=1, max_length=100),
        limit: int = Query(10, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ) -> dict:
        return {"q": q, "limit": limit, "offset": offset}

    # Valid
    resp = app.dispatch(Request("GET", "/search", query_string="q=python&limit=20"))
    assert resp.status_code == 200
    assert resp.body["q"] == "python"
    print(f"  Valid: {resp.body}")

    # Invalid: limit too high
    resp2 = app.dispatch(Request("GET", "/search", query_string="q=test&limit=500"))
    assert resp2.status_code == 422
    print(f"  limit=500 -> {resp2.body['error']['errors'][0]['message']}")

    # Invalid: empty query
    resp3 = app.dispatch(Request("GET", "/search", query_string="q="))
    assert resp3.status_code == 422
    print(f"  q='' -> {resp3.body['error']['errors'][0]['message']}")

    print("  [PASS] Query parameter validation works")


def demo_integrated_validation():
    """Show full integration: body model + path params + query validation."""
    print("\n--- Section 5: Integrated Validation ---")

    class UpdateUser(ValidatedModel):
        name: str = Field(min_length=1, max_length=50)
        email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")

    app = IgniteApp()

    @app.put("/users/{user_id}")
    def update_user(user_id: int, user: UpdateUser) -> dict:
        return {"user_id": user_id, "updated": user.dict()}

    # Valid request
    body = json.dumps({"name": "Alice", "email": "alice@test.com"})
    resp = app.dispatch(Request("PUT", "/users/1", body=body.encode()))
    assert resp.status_code == 200
    assert resp.body["user_id"] == 1
    print(f"  Valid: {resp.body}")

    # Invalid body
    bad_body = json.dumps({"name": "", "email": "bad"})
    resp2 = app.dispatch(Request("PUT", "/users/1", body=bad_body.encode()))
    assert resp2.status_code == 422
    print(f"  Invalid body -> {len(resp2.body['error']['errors'])} errors:")
    for err in resp2.body["error"]["errors"]:
        print(f"    {err['field']}: {err['message']}")

    print("  [PASS] Integrated validation works")


def demo_list_validation():
    """Show list/collection field validation."""
    print("\n--- Section 6: Collection Validation ---")

    class TaggedItem(ValidatedModel):
        name: str = Field(min_length=1)
        tags: list = Field(min_items=1, max_items=5)

    # Valid
    item = TaggedItem(name="Widget", tags=["sale", "new"])
    assert item.tags == ["sale", "new"]
    print(f"  Valid: {item}")

    # Too many tags
    try:
        TaggedItem(name="Widget", tags=["a", "b", "c", "d", "e", "f"])
        assert False, "Should have raised"
    except ValidationError as e:
        print(f"  6 tags -> {e.errors[0]['message']}")
        assert "max" in e.errors[0]["message"].lower()

    # Empty tags
    try:
        TaggedItem(name="Widget", tags=[])
        assert False, "Should have raised"
    except ValidationError as e:
        print(f"  0 tags -> {e.errors[0]['message']}")
        assert "min" in e.errors[0]["message"].lower()

    print("  [PASS] Collection validation works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    try:
        demo_field_validation()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_multiple_errors()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_schema_generation()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_query_validation()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_integrated_validation()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_list_validation()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print("\n--- Summary ---")
    print("Type-driven validation gives our Ignite framework:")
    print("  - Field() descriptors with min/max, pattern, range constraints")
    print("  - ValidatedModel base class with automatic validation")
    print("  - Multiple error collection (not fail-fast)")
    print("  - JSON Schema generation from model definitions")
    print("  - Query() parameter validation markers")
    print("  - Integrated body + path + query validation")
    print("  - Collection size validation (min_items, max_items)")
    print("\nImplement the TODOs above to make all 6 sections pass!")
    print("Next up: Kata 52 -- OpenAPI schema generation!")


if __name__ == "__main__":
    main()
