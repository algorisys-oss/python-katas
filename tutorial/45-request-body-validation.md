# Kata 45 -- Request Body & Validation

[prev: 44-dependency-injection](./44-dependency-injection.md) | [next: 46-query-parameters](./46-query-parameters.md)

---

## What We're Building

A **Pydantic-style validation system** using Python type annotations. This is how our Ignite framework validates incoming request data -- JSON bodies are parsed, coerced to the right types, and checked against constraints before the route handler ever sees them.

We'll build four key components:
1. **BaseModel** -- a class that validates `__init__` kwargs against type hints
2. **Type coercion** -- automatic conversion (str to int, dict to nested model)
3. **Field constraints** -- min/max length, ge/le for numeric bounds
4. **Request integration** -- parsing JSON bodies and validating against models

This is the same pattern used by FastAPI + Pydantic, but we build it from scratch to understand every piece.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `get_type_hints()` | Extracts resolved type annotations from a class | Runtime type introspection |
| `typing.get_origin()` | Gets the base of a generic (`list[str]` -> `list`) | Detecting parameterized types |
| `typing.get_args()` | Gets type parameters (`list[str]` -> `(str,)`) | Extracting inner types |
| `Optional[T]` | `Union[T, None]` -- field can be T or None | Nullable fields |
| Type coercion | Converting `"42"` (str) to `42` (int) at runtime | Handling form/query data |
| `FieldInfo` | Metadata class holding constraints for a field | Validation rules |
| `object.__setattr__` | Set attribute bypassing descriptors/`__setattr__` | Controlled attribute setting |
| Nested validation | Recursively validating dicts as nested models | Complex data structures |

## The Code

### 1. The ValidationError

Every validation failure produces structured, field-level error messages:

```python
class ValidationError(Exception):
    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors  # [{"field": "age", "message": "value < 0"}]
        super().__init__(f"{len(errors)} validation error(s)")
```

### 2. FieldInfo and Constraints

`Field()` creates metadata that attaches constraints to model fields:

```python
class FieldInfo:
    def __init__(self, default=..., min_length=None, max_length=None,
                 ge=None, le=None):
        self.default = default  # Ellipsis means required
        self.min_length = min_length
        self.max_length = max_length
        self.ge = ge  # greater-than-or-equal
        self.le = le  # less-than-or-equal

class CreateUser(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    bio: Optional[str] = None
```

### 3. Detecting Optional Types

`Optional[str]` is actually `Union[str, None]`. We detect this at runtime:

```python
def _is_optional(annotation):
    origin = typing.get_origin(annotation)  # Union
    args = typing.get_args(annotation)      # (str, NoneType)
    if origin is typing.Union and type(None) in args:
        real_types = [a for a in args if a is not type(None)]
        return True, real_types[0]  # True, str
    return False, annotation
```

### 4. Type Coercion

Query strings and form data arrive as strings. We coerce them:

```python
def _coerce_value(value, target_type, field_name):
    if isinstance(value, target_type):
        return value  # Already correct

    # Nested model: dict -> Model(**dict)
    if issubclass(target_type, BaseModel) and isinstance(value, dict):
        return target_type(**value)

    # list[X]: coerce each element
    if typing.get_origin(target_type) is list:
        item_type = typing.get_args(target_type)[0]
        return [_coerce_value(item, item_type, ...) for item in value]

    # Primitive: str -> int, str -> float, etc.
    return target_type(value)  # int("42") -> 42
```

### 5. The BaseModel.__init__

The heart of validation -- iterate type hints, resolve values, coerce, validate:

```python
class BaseModel:
    def __init__(self, **data):
        errors = []
        hints = get_type_hints(type(self))

        for field_name, annotation in hints.items():
            is_optional, inner_type = _is_optional(annotation)

            # Resolve value: from data, default, or error
            if field_name in data:
                raw_value = data[field_name]
            elif has_default:
                self.field = default; continue
            else:
                errors.append({"field": field_name, "message": "required"})
                continue

            # Coerce and validate
            coerced = _coerce_value(raw_value, inner_type, field_name)
            constraint_errors = check_constraints(coerced, field_info)
            self.field = coerced

        if errors:
            raise ValidationError(errors)
```

### 6. Request Integration

The framework automatically validates request bodies:

```python
def validate_body(request, model_class):
    data = request.json()          # Parse JSON bytes -> dict
    return model_class(**data)     # Validate against model

# In a route handler:
@app.post("/users")
def create_user(request, body: CreateUser):
    # body is already validated!
    print(body.name, body.age)
```

## Playground

```bash
python playground/45_request_body_validation.py
```

Expected output:

```
--- Section 1: Basic Model Validation ---
  Created user: CreateUser(name='Alice', email='alice@example.com', age=30, bio=None, address=None, tags=[])
  user.name = 'Alice'
  user.age = 30
  user.bio = None (optional, defaults to None)
  user.tags = [] (defaults to [])
  model_dump() = {'name': 'Alice', 'email': 'alice@example.com', 'age': 30, 'bio': None, 'address': None, 'tags': []}
  [PASS] Basic validation works

--- Section 2: Type Coercion ---
  age='25' (str) -> age=25 (int)
  price='9.99' (str) -> price=9.99 (float)
  quantity='10' (str) -> quantity=10 (int)
  [PASS] Type coercion works

--- Section 3: Validation Errors ---
  age=-5: value -5 < minimum 0
  name(101 chars): length 101 > max_length 100
  age='not-a-number': cannot coerce str to int: ...
  unknown field 'foo': unknown field
  [PASS] Validation errors reported correctly

--- Section 4: Nested Models ---
  User with address: Charlie
  address.city = 'Springfield'
  address.country = 'US' (default)
  address in dump = {'street': '123 Main St', 'city': 'Springfield', 'zip_code': '62701', 'country': 'US'}
  Missing nested fields: 2 error(s)
  [PASS] Nested model validation works

--- Section 5: Request Body Integration ---
  Parsed request body -> Diana, tags=['admin', 'user']
  Invalid JSON: Invalid JSON: ...
  Empty body: Invalid JSON: Request body is empty
  [PASS] Request body integration works

--- Section 6: JSON Serialization ---
  model_json() = {"name": "Laptop", "price": 999.99, ...}
  Round-trip: Product(name='Laptop', price=999.99, ...)
  [PASS] JSON serialization works

All 6 sections passed. Request body & validation mastered!
```

## How It Works

### Validation Pipeline

```
JSON bytes                    Type Hints              Validated Model
----------                    ----------              ---------------
b'{"name": "Alice",    -->   get_type_hints()    -->  CreateUser(
   "age": "25"}'             name: str                  name="Alice",
                             age: int                   age=25  <-- coerced
                             bio: Optional[str]         bio=None  <-- default
                                                      )
```

### Resolution Order for Each Field

```
1. Is field_name in data?
   YES -> coerce value to annotated type
   NO  -> continue...

2. Does field have a default?
   YES -> use default value
   NO  -> continue...

3. Is field Optional[T]?
   YES -> set to None
   NO  -> ERROR: "field is required"

After coercion:
4. Run constraint checks (min_length, ge, le, etc.)
5. Check for unknown fields in data
6. If any errors: raise ValidationError
```

### Type Coercion Strategy

| Source | Target | Method |
|---|---|---|
| `str` | `int` | `int("42")` -> `42` |
| `str` | `float` | `float("3.14")` -> `3.14` |
| `str` | `bool` | `"true"/"1"/"yes"` -> `True` |
| `dict` | `BaseModel` | `Address(**dict)` (recursive) |
| `list[dict]` | `list[Model]` | coerce each element |

## Exercises

1. **Add regex validation** -- extend `FieldInfo` with a `pattern: str` parameter that validates string fields against a regex (e.g., email format). Use `re.match()` in `_check_constraints()`.

2. **Implement `model_update()`** -- a method that takes partial data (like a PATCH request) and returns a new model instance with only the provided fields updated, keeping other fields from the original.

3. **Add custom validators** -- implement a `@validator("field_name")` decorator that registers a custom validation function. The function receives the value and returns the validated value or raises an error.

4. **Support Union types** -- extend `_coerce_value()` to handle `Union[int, str]` (try each type in order until one succeeds).

5. **Implement `model_schema()`** -- a class method that returns a JSON Schema dict describing the model (field names, types, required/optional, constraints). This is what OpenAPI/Swagger uses.

## What's Next

With request body validation in place, our Ignite framework can now safely parse and validate incoming JSON data. In [Kata 46: Query Parameters](./46-query-parameters.md), we'll build the other half of input handling -- extracting typed parameters from URL query strings using function signature inspection.

---

[prev: 44-dependency-injection](./44-dependency-injection.md) | [next: 46-query-parameters](./46-query-parameters.md)
