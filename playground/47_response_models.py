"""
Kata 47 -- Response Models
Run: python playground/47_response_models.py

Build response model serialization for the Ignite framework. Define output
models that control what fields are included in the response. Support field
inclusion/exclusion, nested model serialization, and converting model
instances to JSON-safe dicts.

Completes within 5 seconds.
"""

from __future__ import annotations

import json
import typing
from datetime import datetime, timezone
from typing import Any, Optional, get_type_hints


# ===========================================================================
# SECTION 1: ResponseModel Base Class
# ===========================================================================
# Unlike request validation (kata 45) which validates INPUT, response models
# control OUTPUT -- what data gets serialized and sent back to the client.

class ResponseModel:
    """Base class for response models that control output serialization.

    Key differences from request BaseModel:
    - No validation on construction (data is already trusted)
    - Focus on serialization: which fields to include/exclude
    - Support for field aliases (internal name vs API name)
    - Custom serializers for complex types (datetime, etc.)
    """

    # Override in subclasses to exclude fields from output
    class Config:
        exclude_fields: set[str] = set()
        include_fields: set[str] | None = None  # None = include all
        field_aliases: dict[str, str] = {}  # internal_name -> api_name
        json_encoders: dict[type, Any] = {}  # type -> encoder function

    def __init__(self, **data: Any):
        hints = get_type_hints(type(self))
        for field_name in hints:
            if field_name in data:
                object.__setattr__(self, field_name, data[field_name])
            elif hasattr(type(self), field_name):
                object.__setattr__(self, field_name, getattr(type(self), field_name))
            else:
                object.__setattr__(self, field_name, None)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResponseModel":
        """Create an instance from a dictionary."""
        return cls(**data)

    @classmethod
    def from_object(cls, obj: Any) -> "ResponseModel":
        """Create an instance from any object with matching attributes."""
        hints = get_type_hints(cls)
        data = {}
        for field_name in hints:
            if hasattr(obj, field_name):
                data[field_name] = getattr(obj, field_name)
        return cls(**data)

    def model_dump(
        self,
        *,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        by_alias: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        """Serialize the model to a dictionary.

        Args:
            include: Only include these fields (overrides Config)
            exclude: Exclude these fields (merged with Config)
            by_alias: Use field aliases from Config
            exclude_none: Skip fields with None values
        """
        hints = get_type_hints(type(self))
        config = self._get_config()

        # Determine which fields to include
        fields = set(hints.keys())

        if include is not None:
            fields &= include
        elif config.get("include_fields") is not None:
            fields &= config["include_fields"]

        # Remove excluded fields
        excluded = config.get("exclude_fields", set())
        if exclude is not None:
            excluded = excluded | exclude
        fields -= excluded

        result: dict[str, Any] = {}
        aliases = config.get("field_aliases", {})
        encoders = config.get("json_encoders", {})

        for field_name in fields:
            value = getattr(self, field_name, None)

            if exclude_none and value is None:
                continue

            # Apply custom encoder if exists
            value = self._encode_value(value, encoders)

            # Determine output key name
            key = aliases.get(field_name, field_name) if by_alias else field_name

            result[key] = value

        return result

    def model_json(self, **kwargs: Any) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.model_dump(**kwargs), default=str)

    @classmethod
    def _get_config(cls) -> dict[str, Any]:
        """Extract Config class settings as a dict."""
        config_cls = getattr(cls, "Config", None)
        if config_cls is None:
            return {}
        return {
            "exclude_fields": getattr(config_cls, "exclude_fields", set()),
            "include_fields": getattr(config_cls, "include_fields", None),
            "field_aliases": getattr(config_cls, "field_aliases", {}),
            "json_encoders": getattr(config_cls, "json_encoders", {}),
        }

    @classmethod
    def _encode_value(cls, value: Any, encoders: dict[type, Any]) -> Any:
        """Recursively encode a value for JSON serialization."""
        # Check custom encoders first
        for enc_type, encoder in encoders.items():
            if isinstance(value, enc_type):
                return encoder(value)

        # Nested ResponseModel
        if isinstance(value, ResponseModel):
            return value.model_dump()

        # List of ResponseModels
        if isinstance(value, list):
            return [
                cls._encode_value(item, encoders) for item in value
            ]

        # Dict values
        if isinstance(value, dict):
            return {
                k: cls._encode_value(v, encoders) for k, v in value.items()
            }

        # datetime default encoding
        if isinstance(value, datetime):
            return value.isoformat()

        return value

    def __repr__(self) -> str:
        hints = get_type_hints(type(self))
        fields = ", ".join(
            f"{k}={getattr(self, k)!r}" for k in hints
        )
        return f"{type(self).__name__}({fields})"


# ===========================================================================
# SECTION 2: Define Response Models
# ===========================================================================

class UserResponse(ResponseModel):
    """Public user response -- hides password and internal fields."""
    id: int
    name: str
    email: str
    bio: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        exclude_fields = {"password_hash", "internal_id"}
        field_aliases = {"id": "user_id", "created_at": "createdAt"}
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class UserDetailResponse(UserResponse):
    """Extended user response with additional fields."""
    posts_count: int = 0
    followers_count: int = 0
    is_verified: bool = False


class PostResponse(ResponseModel):
    """Blog post response model."""
    id: int
    title: str
    content: str
    author: Optional[UserResponse] = None
    tags: list[str] = []
    published_at: Optional[datetime] = None

    class Config:
        field_aliases = {"published_at": "publishedAt"}
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class PaginatedResponse(ResponseModel):
    """Generic paginated response wrapper."""
    items: list[Any] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    has_next: bool = False
    has_prev: bool = False


# ===========================================================================
# SECTION 3: Response Builder
# ===========================================================================
# Utility to build HTTP responses with proper content-type and status.

class JSONResponse:
    """A JSON HTTP response with status code and headers."""

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.headers = headers or {}
        self.headers.setdefault("content-type", "application/json")

        # Serialize content
        if isinstance(content, ResponseModel):
            self.body = content.model_dump()
        elif isinstance(content, dict):
            self.body = content
        elif isinstance(content, list):
            self.body = [
                item.model_dump() if isinstance(item, ResponseModel) else item
                for item in content
            ]
        else:
            self.body = content

    def to_bytes(self) -> bytes:
        return json.dumps(self.body, default=str).encode("utf-8")

    def __repr__(self) -> str:
        return (
            f"JSONResponse(status={self.status_code}, "
            f"body={json.dumps(self.body, default=str)[:80]}...)"
        )


def respond(
    model_class: type[ResponseModel],
    data: Any,
    status_code: int = 200,
    **dump_kwargs: Any,
) -> JSONResponse:
    """Create a JSONResponse from data using a response model.

    This is the function the Ignite framework calls to serialize
    route handler return values.
    """
    if isinstance(data, dict):
        instance = model_class.from_dict(data)
    elif isinstance(data, model_class):
        instance = data
    else:
        instance = model_class.from_object(data)

    return JSONResponse(
        content=instance.model_dump(**dump_kwargs),
        status_code=status_code,
    )


# ===========================================================================
# SECTION 4: Demos
# ===========================================================================

def demo_basic_response():
    """Show basic response model serialization."""
    print("--- Section 1: Basic Response Model ---")

    user = UserResponse(
        id=1, name="Alice", email="alice@example.com",
        bio="Python developer",
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    )
    dumped = user.model_dump()
    print(f"  UserResponse: {dumped}")
    assert dumped["id"] == 1
    assert dumped["name"] == "Alice"
    assert "password_hash" not in dumped  # excluded by Config
    assert isinstance(dumped["created_at"], str)  # datetime -> ISO string

    print("  [PASS] Basic response model works")


def demo_field_exclusion():
    """Show field inclusion and exclusion."""
    print("\n--- Section 2: Field Inclusion/Exclusion ---")

    user = UserResponse(id=1, name="Bob", email="bob@test.com")

    # Exclude email for a public listing
    public = user.model_dump(exclude={"email", "bio"})
    print(f"  Exclude email+bio: {public}")
    assert "email" not in public
    assert "bio" not in public
    assert "name" in public

    # Include only specific fields
    minimal = user.model_dump(include={"id", "name"})
    print(f"  Include id+name only: {minimal}")
    assert set(minimal.keys()) == {"id", "name"}

    # Exclude None values
    sparse = user.model_dump(exclude_none=True)
    print(f"  Exclude None: {sparse}")
    assert "bio" not in sparse  # bio is None
    assert "name" in sparse

    print("  [PASS] Field inclusion/exclusion works")


def demo_aliases():
    """Show field aliasing (camelCase output)."""
    print("\n--- Section 3: Field Aliases ---")

    user = UserResponse(
        id=42, name="Charlie", email="charlie@test.com",
        created_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    # Without aliases
    normal = user.model_dump()
    print(f"  Without aliases: keys = {list(normal.keys())}")
    assert "created_at" in normal

    # With aliases (camelCase for JavaScript clients)
    aliased = user.model_dump(by_alias=True)
    print(f"  With aliases: keys = {list(aliased.keys())}")
    assert "createdAt" in aliased
    assert "user_id" in aliased
    assert "created_at" not in aliased

    print("  [PASS] Field aliases work")


def demo_nested_models():
    """Show nested model serialization."""
    print("\n--- Section 4: Nested Models ---")

    author = UserResponse(id=1, name="Diana", email="diana@test.com")
    post = PostResponse(
        id=101,
        title="Understanding Python Type Hints",
        content="Type hints are a powerful feature...",
        author=author,
        tags=["python", "typing"],
        published_at=datetime(2024, 3, 15, 9, 0, 0, tzinfo=timezone.utc),
    )

    dumped = post.model_dump()
    print(f"  Post with nested author:")
    print(f"    title = {dumped['title']!r}")
    print(f"    author = {dumped['author']}")
    print(f"    tags = {dumped['tags']}")

    # Nested author is also serialized as a dict
    assert isinstance(dumped["author"], dict)
    assert dumped["author"]["name"] == "Diana"
    assert isinstance(dumped["published_at"], str)

    print("  [PASS] Nested model serialization works")


def demo_from_object():
    """Show creating response models from arbitrary objects."""
    print("\n--- Section 5: From Object Mapping ---")

    # Simulate a database model (plain class with attributes)
    class DBUser:
        def __init__(self):
            self.id = 7
            self.name = "Eve"
            self.email = "eve@test.com"
            self.password_hash = "hashed_secret_123"
            self.internal_id = "uuid-abc-123"
            self.bio = "Security researcher"

    db_user = DBUser()
    response = UserResponse.from_object(db_user)
    dumped = response.model_dump()
    print(f"  DBUser -> UserResponse: {dumped}")
    assert dumped["name"] == "Eve"
    assert "password_hash" not in dumped  # excluded!
    assert "internal_id" not in dumped  # excluded!

    print("  [PASS] From-object mapping works")


def demo_paginated_response():
    """Show paginated response with a list of models."""
    print("\n--- Section 6: Paginated Response ---")

    users = [
        UserResponse(id=i, name=f"User{i}", email=f"user{i}@test.com")
        for i in range(1, 4)
    ]

    paginated = PaginatedResponse(
        items=users,
        total=50,
        page=1,
        per_page=3,
        has_next=True,
        has_prev=False,
    )

    dumped = paginated.model_dump()
    print(f"  Paginated: total={dumped['total']}, page={dumped['page']}")
    print(f"  Items: {len(dumped['items'])} users")
    print(f"  has_next={dumped['has_next']}, has_prev={dumped['has_prev']}")

    assert len(dumped["items"]) == 3
    assert dumped["items"][0]["name"] == "User1"
    assert dumped["total"] == 50
    assert dumped["has_next"] is True

    print("  [PASS] Paginated response works")


def demo_json_response():
    """Show JSONResponse integration."""
    print("\n--- Section 7: JSONResponse Integration ---")

    user = UserResponse(id=1, name="Frank", email="frank@test.com")
    response = respond(UserResponse, user, status_code=200)
    print(f"  Status: {response.status_code}")
    print(f"  Content-Type: {response.headers['content-type']}")
    print(f"  Body: {response.body}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.body["name"] == "Frank"

    # From dict
    data = {"id": 2, "name": "Grace", "email": "grace@test.com"}
    response2 = respond(UserResponse, data, status_code=201)
    print(f"  From dict: {response2.body}")
    assert response2.status_code == 201
    assert response2.body["name"] == "Grace"

    # Bytes output (what gets sent over the wire)
    wire_bytes = response2.to_bytes()
    print(f"  Wire bytes: {wire_bytes[:60]}...")
    assert isinstance(wire_bytes, bytes)
    assert json.loads(wire_bytes)["name"] == "Grace"

    print("  [PASS] JSONResponse integration works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_basic_response()
    demo_field_exclusion()
    demo_aliases()
    demo_nested_models()
    demo_from_object()
    demo_paginated_response()
    demo_json_response()

    print("\n--- Summary ---")
    print("Response models give our Ignite framework:")
    print("  - Controlled output serialization (include/exclude fields)")
    print("  - Field aliases for camelCase API output")
    print("  - Nested model serialization (recursive)")
    print("  - Custom type encoders (datetime -> ISO string)")
    print("  - from_object() to map DB models -> API responses safely")
    print("  - exclude_none for sparse responses")
    print("  - JSONResponse with status codes and headers")
    print("\nAll 7 sections passed. Response models mastered!")
    print("Next up: Kata 48 -- error handling & exception handlers!")


if __name__ == "__main__":
    main()
