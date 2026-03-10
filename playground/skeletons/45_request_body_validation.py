"""
Kata 45 -- Request Body & Validation
Run: python playground/skeletons/45_request_body_validation.py

Build a Pydantic-style validation system using Python type annotations.
Define a BaseModel-like class that validates data against type hints.
Support required/optional fields, type coercion, and nested models.
Integrate with Ignite's request body parsing.

Completes within 5 seconds.
"""

from __future__ import annotations

import json
import typing
from typing import Any, Optional, get_type_hints


# ===========================================================================
# SECTION 1: BaseModel Foundation
# ===========================================================================
# We build a Pydantic-style BaseModel from scratch. The key insight is that
# Python type annotations (via typing.get_type_hints) give us a schema
# we can validate data against at runtime.

class ValidationError(Exception):
    """Raised when input data fails validation."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"{len(errors)} validation error(s)")

    def __str__(self) -> str:
        lines = [f"{len(self.errors)} validation error(s):"]
        for err in self.errors:
            lines.append(f"  - {err['field']}: {err['message']}")
        return "\n".join(lines)


class FieldInfo:
    """Metadata for a single model field."""

    def __init__(
        self,
        default: Any = ...,  # Ellipsis means required
        description: str = "",
        min_length: int | None = None,
        max_length: int | None = None,
        ge: int | float | None = None,  # greater than or equal
        le: int | float | None = None,  # less than or equal
    ):
        self.default = default
        self.description = description
        self.min_length = min_length
        self.max_length = max_length
        self.ge = ge
        self.le = le

    @property
    def is_required(self) -> bool:
        return self.default is ...


def Field(
    default: Any = ...,
    description: str = "",
    min_length: int | None = None,
    max_length: int | None = None,
    ge: int | float | None = None,
    le: int | float | None = None,
) -> Any:
    """Factory for field metadata, like Pydantic's Field()."""
    return FieldInfo(
        default=default,
        description=description,
        min_length=min_length,
        max_length=max_length,
        ge=ge,
        le=le,
    )


def _is_optional(annotation: type) -> tuple[bool, type]:
    """Check if a type annotation is Optional[X] and extract X.

    Optional[X] is actually Union[X, None] under the hood.
    """
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    # TODO: Check if origin is typing.Union and type(None) is in args
    # TODO: If so, extract the non-None type from args
    # TODO: Return (True, inner_type) for Optional, (False, annotation) otherwise
    # HINT: real_types = [a for a in args if a is not type(None)]
    pass
    return False, annotation


def _coerce_value(value: Any, target_type: type, field_name: str) -> Any:
    """Attempt to coerce a value to the target type.

    Supports: int, float, str, bool, and nested BaseModel subclasses.
    """
    # None is valid for Optional fields (caller handles this)
    if value is None:
        return None

    # Check for parameterized generics (list[str], etc.) before isinstance
    origin = typing.get_origin(target_type)

    # Already the right type (only check for non-generic types)
    if origin is None and isinstance(target_type, type) and isinstance(value, target_type):
        return value

    # TODO: Handle nested models -- if target_type is a BaseModel subclass
    # and value is a dict, create an instance: target_type(**value)
    # HINT: isinstance(target_type, type) and issubclass(target_type, BaseModel)

    # TODO: Handle list types -- if origin is list, get the item type from
    # typing.get_args(target_type), then coerce each element
    # HINT: return [_coerce_value(item, item_type, f"{field_name}[{i}]") ...]

    # TODO: Handle primitive coercion (str -> int, str -> float, etc.)
    # Special case: bool from string ("true"/"false"/"1"/"0"/"yes"/"no")
    # HINT: try: return target_type(value) except (ValueError, TypeError): ...
    # For bool, check value.lower() against known true/false strings first.

    raise ValidationError([{
        "field": field_name,
        "message": f"cannot coerce {type(value).__name__} to "
                   f"{target_type.__name__}: unsupported",
    }])


class BaseModel:
    """A Pydantic-style base model with validation from type annotations.

    Subclasses declare fields as class-level annotations:

        class User(BaseModel):
            name: str
            age: int
            email: Optional[str] = None
    """

    def __init__(self, **data: Any):
        errors: list[dict[str, str]] = []
        hints = get_type_hints(type(self))

        for field_name, annotation in hints.items():
            # Get field info (FieldInfo or plain default)
            field_info = self._get_field_info(field_name)
            is_optional, inner_type = _is_optional(annotation)

            # TODO: Determine if we have a value for this field
            # Check in this order:
            # 1. field_name is in data -> use data[field_name]
            # 2. field_info exists and has a non-required default -> use default
            # 3. is_optional -> set to None
            # 4. class has a default attribute -> use it
            # 5. Otherwise -> append error "field is required"
            # HINT: Use object.__setattr__(self, field_name, value) to set attributes

            if field_name in data:
                raw_value = data[field_name]
            elif field_info is not None and not field_info.is_required:
                object.__setattr__(self, field_name, field_info.default)
                continue
            elif is_optional:
                object.__setattr__(self, field_name, None)
                continue
            elif hasattr(type(self), field_name):
                object.__setattr__(self, field_name, getattr(type(self), field_name))
                continue
            else:
                errors.append({
                    "field": field_name,
                    "message": "field is required",
                })
                continue

            # Handle None for optional fields
            if raw_value is None and is_optional:
                object.__setattr__(self, field_name, None)
                continue
            elif raw_value is None and not is_optional:
                errors.append({
                    "field": field_name,
                    "message": "value cannot be None for non-optional field",
                })
                continue

            # TODO: Coerce raw_value to inner_type using _coerce_value()
            # Wrap in try/except ValidationError to collect errors
            # HINT: coerced = _coerce_value(raw_value, inner_type, field_name)

            # TODO: If field_info exists, run constraint checks using
            # self._check_constraints(field_name, coerced, field_info)
            # If there are constraint errors, extend the errors list and continue

            # TODO: Set the attribute: object.__setattr__(self, field_name, coerced)
            pass

        # TODO: Check for unknown fields (keys in data not in hints)
        # Append error {"field": key, "message": "unknown field"} for each
        # HINT: known = set(hints.keys()); for key in data: if key not in known: ...

        if errors:
            raise ValidationError(errors)

    @classmethod
    def _get_field_info(cls, field_name: str) -> FieldInfo | None:
        """Get FieldInfo for a field, if it has one."""
        value = cls.__dict__.get(field_name)
        if isinstance(value, FieldInfo):
            return value
        if field_name in cls.__dict__:
            return FieldInfo(default=cls.__dict__[field_name])
        return None

    @staticmethod
    def _check_constraints(
        field_name: str, value: Any, info: FieldInfo
    ) -> list[dict[str, str]]:
        """Validate value against FieldInfo constraints."""
        errors = []

        # TODO: Check min_length constraint (if info.min_length is not None
        #       and value has __len__, check len(value) >= info.min_length)
        # HINT: Append {"field": field_name, "message": f"length ... < min_length ..."}

        # TODO: Check max_length constraint similarly

        # TODO: Check ge (greater-than-or-equal) constraint for int/float values
        # HINT: if info.ge is not None and isinstance(value, (int, float)):

        # TODO: Check le (less-than-or-equal) constraint similarly

        return errors

    def model_dump(self) -> dict[str, Any]:
        """Convert the model instance to a dictionary."""
        hints = get_type_hints(type(self))
        result = {}
        for field_name in hints:
            value = getattr(self, field_name)
            # TODO: If value is a BaseModel, recursively call model_dump()
            # TODO: If value is a list, model_dump() each BaseModel item
            # HINT: isinstance(value, BaseModel) -> value = value.model_dump()
            result[field_name] = value
        return result

    def model_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.model_dump())

    def __repr__(self) -> str:
        hints = get_type_hints(type(self))
        fields = ", ".join(
            f"{k}={getattr(self, k)!r}" for k in hints
        )
        return f"{type(self).__name__}({fields})"


# ===========================================================================
# SECTION 2: Define Models for Testing
# ===========================================================================

class Address(BaseModel):
    street: str
    city: str
    zip_code: str
    country: str = "US"


class CreateUser(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str
    age: int = Field(ge=0, le=150)
    bio: Optional[str] = None
    address: Optional[Address] = None
    tags: list[str] = Field(default=[])


class Product(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    quantity: int = Field(ge=0, default=0)
    description: Optional[str] = None


# ===========================================================================
# SECTION 3: Ignite Request Integration
# ===========================================================================

class Request:
    """Simulated HTTP request with body parsing."""

    def __init__(self, method: str, path: str, body: bytes = b"",
                 content_type: str = "application/json"):
        self.method = method
        self.path = path
        self._body = body
        self.content_type = content_type

    def json(self) -> dict[str, Any]:
        """Parse body as JSON."""
        if not self._body:
            raise ValueError("Request body is empty")
        return json.loads(self._body.decode("utf-8"))

    def body(self) -> bytes:
        return self._body


def validate_body(request: Request, model_class: type[BaseModel]) -> BaseModel:
    """Parse request body and validate against a model.

    This is what the Ignite framework would call automatically
    when a route handler has a parameter annotated with a BaseModel subclass.
    """
    # TODO: Parse the request body as JSON using request.json()
    # Catch ValueError and json.JSONDecodeError, wrapping them
    # as ValidationError with field "__body__" and message "Invalid JSON: ..."

    # TODO: Create and return model_class(**data) with the parsed data
    pass


# ===========================================================================
# SECTION 4: Demos
# ===========================================================================

def demo_basic_validation():
    """Show basic model validation with valid data."""
    print("--- Section 1: Basic Model Validation ---")

    user = CreateUser(
        name="Alice",
        email="alice@example.com",
        age=30,
    )
    print(f"  Created user: {user}")
    print(f"  user.name = {user.name!r}")
    print(f"  user.age = {user.age}")
    print(f"  user.bio = {user.bio!r} (optional, defaults to None)")
    print(f"  user.tags = {user.tags!r} (defaults to [])")

    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.age == 30
    assert user.bio is None
    assert user.tags == []

    dumped = user.model_dump()
    print(f"  model_dump() = {dumped}")
    assert dumped == {
        "name": "Alice", "email": "alice@example.com",
        "age": 30, "bio": None, "address": None, "tags": [],
    }

    print("  [PASS] Basic validation works")


def demo_type_coercion():
    """Show automatic type coercion (e.g., str -> int)."""
    print("\n--- Section 2: Type Coercion ---")

    user = CreateUser(name="Bob", email="bob@test.com", age="25")
    print(f"  age='25' (str) -> age={user.age} (int)")
    assert user.age == 25
    assert isinstance(user.age, int)

    product = Product(name="Widget", price="9.99")
    print(f"  price='9.99' (str) -> price={product.price} (float)")
    assert product.price == 9.99
    assert isinstance(product.price, float)

    product2 = Product(name="Gadget", price=5.0, quantity="10")
    print(f"  quantity='10' (str) -> quantity={product2.quantity} (int)")
    assert product2.quantity == 10

    print("  [PASS] Type coercion works")


def demo_validation_errors():
    """Show what happens with invalid data."""
    print("\n--- Section 3: Validation Errors ---")

    try:
        CreateUser(email="test@test.com", age=20)
    except ValidationError as e:
        print(f"  Missing 'name': {e.errors[0]['message']}")
        assert any(err["field"] == "name" for err in e.errors)

    try:
        CreateUser(name="Young", email="y@test.com", age=-5)
    except ValidationError as e:
        print(f"  age=-5: {e.errors[0]['message']}")
        assert any("minimum" in err["message"] for err in e.errors)

    try:
        CreateUser(name="A" * 101, email="long@test.com", age=25)
    except ValidationError as e:
        print(f"  name(101 chars): {e.errors[0]['message']}")
        assert any("max_length" in err["message"] for err in e.errors)

    try:
        CreateUser(name="Bad", email="b@test.com", age="not-a-number")
    except ValidationError as e:
        print(f"  age='not-a-number': {e.errors[0]['message']}")
        assert any("coerce" in err["message"] for err in e.errors)

    try:
        CreateUser(name="X", email="x@test.com", age=20, foo="bar")
    except ValidationError as e:
        print(f"  unknown field 'foo': {e.errors[0]['message']}")
        assert any(err["field"] == "foo" for err in e.errors)

    print("  [PASS] Validation errors reported correctly")


def demo_nested_models():
    """Show nested model validation."""
    print("\n--- Section 4: Nested Models ---")

    user = CreateUser(
        name="Charlie",
        email="charlie@test.com",
        age=35,
        address={
            "street": "123 Main St",
            "city": "Springfield",
            "zip_code": "62701",
        },
    )
    print(f"  User with address: {user.name}")
    print(f"  address.city = {user.address.city!r}")
    print(f"  address.country = {user.address.country!r} (default)")
    assert isinstance(user.address, Address)
    assert user.address.city == "Springfield"
    assert user.address.country == "US"

    dumped = user.model_dump()
    print(f"  address in dump = {dumped['address']}")
    assert dumped["address"]["city"] == "Springfield"

    try:
        CreateUser(
            name="Bad", email="b@test.com", age=20,
            address={"street": "X"},
        )
    except ValidationError as e:
        print(f"  Missing nested fields: {len(e.errors)} error(s)")
        assert len(e.errors) >= 2

    print("  [PASS] Nested model validation works")


def demo_request_integration():
    """Show how validation integrates with HTTP requests."""
    print("\n--- Section 5: Request Body Integration ---")

    body = json.dumps({
        "name": "Diana",
        "email": "diana@test.com",
        "age": 28,
        "tags": ["admin", "user"],
    }).encode()
    request = Request("POST", "/users", body)
    user = validate_body(request, CreateUser)
    print(f"  Parsed request body -> {user.name}, tags={user.tags}")
    assert user.name == "Diana"
    assert user.tags == ["admin", "user"]

    bad_request = Request("POST", "/users", b"not json")
    try:
        validate_body(bad_request, CreateUser)
    except ValidationError as e:
        print(f"  Invalid JSON: {e.errors[0]['message']}")
        assert "Invalid JSON" in e.errors[0]["message"]

    empty_request = Request("POST", "/users", b"")
    try:
        validate_body(empty_request, CreateUser)
    except ValidationError as e:
        print(f"  Empty body: {e.errors[0]['message']}")

    bad_data = json.dumps({"email": "test@test.com"}).encode()
    bad_data_request = Request("POST", "/users", bad_data)
    try:
        validate_body(bad_data_request, CreateUser)
    except ValidationError as e:
        print(f"  Missing fields: {len(e.errors)} error(s)")

    print("  [PASS] Request body integration works")


def demo_model_json():
    """Show JSON serialization."""
    print("\n--- Section 6: JSON Serialization ---")

    product = Product(name="Laptop", price=999.99, quantity=5,
                      description="A powerful laptop")
    json_str = product.model_json()
    print(f"  model_json() = {json_str}")

    data = json.loads(json_str)
    product2 = Product(**data)
    print(f"  Round-trip: {product2}")
    assert product2.name == product.name
    assert product2.price == product.price
    assert product2.quantity == product.quantity

    print("  [PASS] JSON serialization works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    try:
        demo_basic_validation()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_type_coercion()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_validation_errors()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_nested_models()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_request_integration()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_model_json()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print("\n--- Summary ---")
    print("Request body validation gives our Ignite framework:")
    print("  - BaseModel with type-annotation-driven validation")
    print("  - Automatic type coercion (str -> int, dict -> nested model)")
    print("  - Field constraints (min/max length, ge/le)")
    print("  - Required vs optional fields")
    print("  - Nested model support")
    print("  - JSON serialization / deserialization")
    print("  - Clean error reporting with field-level messages")
    print("\nAll 6 sections passed. Request body & validation mastered!")
    print("Next up: Kata 46 -- query parameter parsing!")


if __name__ == "__main__":
    main()
