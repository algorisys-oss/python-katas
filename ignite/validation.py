"""Ignite Validation — BaseModel with type annotation validation."""

from __future__ import annotations

import json
import typing
from typing import Any, get_type_hints


class ValidationError(Exception):
    """Raised when input data fails validation."""

    def __init__(self, errors: list[dict[str, str]]) -> None:
        self.errors = errors
        super().__init__(f"{len(errors)} validation error(s)")

    def __str__(self) -> str:
        lines = [f"{len(self.errors)} validation error(s):"]
        for err in self.errors:
            lines.append(f"  - {err['field']}: {err['message']}")
        return "\n".join(lines)

    def to_response(self) -> dict[str, Any]:
        """Convert to a structured JSON response body."""
        return {
            "error": {
                "status_code": 422,
                "detail": "Validation Error",
                "type": "Unprocessable Entity",
                "errors": [
                    {
                        "loc": ["body", err.get("field", "unknown")],
                        "msg": err.get("message", "invalid value"),
                        "type": err.get("type", "value_error"),
                    }
                    for err in self.errors
                ],
            }
        }


class FieldInfo:
    """Metadata for a single model field."""

    def __init__(
        self,
        default: Any = ...,
        description: str = "",
        min_length: int | None = None,
        max_length: int | None = None,
        ge: int | float | None = None,
        le: int | float | None = None,
    ) -> None:
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
    """Check if a type annotation is Optional[X] and extract X."""
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    if origin is typing.Union and type(None) in args:
        real_types = [a for a in args if a is not type(None)]
        if len(real_types) == 1:
            return True, real_types[0]
    return False, annotation


def _coerce_value(value: Any, target_type: type, field_name: str) -> Any:
    """Attempt to coerce a value to the target type."""
    if value is None:
        return None

    origin = typing.get_origin(target_type)

    # Already the right type (only check for non-generic types)
    if (
        origin is None
        and isinstance(target_type, type)
        and isinstance(value, target_type)
    ):
        return value

    # Nested model: if target is a BaseModel subclass, validate recursively
    if isinstance(target_type, type) and issubclass(target_type, BaseModel):
        if isinstance(value, dict):
            return target_type(**value)
        raise ValidationError([{
            "field": field_name,
            "message": f"expected object, got {type(value).__name__}",
        }])

    # List type: list[X]
    if origin is list:
        args = typing.get_args(target_type)
        item_type = args[0] if args else str
        if not isinstance(value, list):
            raise ValidationError([{
                "field": field_name,
                "message": f"expected list, got {type(value).__name__}",
            }])
        return [
            _coerce_value(item, item_type, f"{field_name}[{i}]")
            for i, item in enumerate(value)
        ]

    # Primitive coercion
    try:
        if target_type is bool and isinstance(value, str):
            if value.lower() in ("true", "1", "yes"):
                return True
            if value.lower() in ("false", "0", "no"):
                return False
            raise ValueError(f"cannot convert '{value}' to bool")
        return target_type(value)
    except (ValueError, TypeError) as e:
        raise ValidationError([{
            "field": field_name,
            "message": (
                f"cannot coerce {type(value).__name__} to "
                f"{target_type.__name__}: {e}"
            ),
        }])


class BaseModel:
    """A Pydantic-style base model with validation from type annotations.

    Subclasses declare fields as class-level annotations:

        class User(BaseModel):
            name: str
            age: int
            email: Optional[str] = None
    """

    def __init__(self, **data: Any) -> None:
        errors: list[dict[str, str]] = []
        hints = get_type_hints(type(self))

        for field_name, annotation in hints.items():
            field_info = self._get_field_info(field_name)
            is_optional, inner_type = _is_optional(annotation)

            if field_name in data:
                raw_value = data[field_name]
            elif field_info is not None and not field_info.is_required:
                object.__setattr__(self, field_name, field_info.default)
                continue
            elif is_optional:
                object.__setattr__(self, field_name, None)
                continue
            elif hasattr(type(self), field_name):
                object.__setattr__(
                    self, field_name, getattr(type(self), field_name)
                )
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

            # Coerce to target type
            try:
                coerced = _coerce_value(raw_value, inner_type, field_name)
            except ValidationError as ve:
                errors.extend(ve.errors)
                continue

            # Run constraints from FieldInfo
            if field_info is not None:
                constraint_errors = self._check_constraints(
                    field_name, coerced, field_info
                )
                if constraint_errors:
                    errors.extend(constraint_errors)
                    continue

            object.__setattr__(self, field_name, coerced)

        # Check for unknown fields
        known = set(hints.keys())
        for key in data:
            if key not in known:
                errors.append({
                    "field": key,
                    "message": "unknown field",
                })

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
        errors: list[dict[str, str]] = []
        if info.min_length is not None and hasattr(value, "__len__"):
            if len(value) < info.min_length:
                errors.append({
                    "field": field_name,
                    "message": (
                        f"length {len(value)} < min_length {info.min_length}"
                    ),
                })
        if info.max_length is not None and hasattr(value, "__len__"):
            if len(value) > info.max_length:
                errors.append({
                    "field": field_name,
                    "message": (
                        f"length {len(value)} > max_length {info.max_length}"
                    ),
                })
        if info.ge is not None and isinstance(value, (int, float)):
            if value < info.ge:
                errors.append({
                    "field": field_name,
                    "message": f"value {value} < minimum {info.ge}",
                })
        if info.le is not None and isinstance(value, (int, float)):
            if value > info.le:
                errors.append({
                    "field": field_name,
                    "message": f"value {value} > maximum {info.le}",
                })
        return errors

    def model_dump(self) -> dict[str, Any]:
        """Convert the model instance to a dictionary."""
        hints = get_type_hints(type(self))
        result: dict[str, Any] = {}
        for field_name in hints:
            value = getattr(self, field_name)
            if isinstance(value, BaseModel):
                value = value.model_dump()
            elif isinstance(value, list):
                value = [
                    item.model_dump() if isinstance(item, BaseModel) else item
                    for item in value
                ]
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
