# Kata 51 -- Type-Driven Validation

[prev: 50-parameter-injection](./50-parameter-injection.md) | [next: 52-openapi-schema](./52-openapi-schema.md)

---

## What We're Building

A **validation system** that uses type annotations and descriptors to validate request data automatically. Define constraints once on your model and get validation everywhere:

```python
class CreateUser(ValidatedModel):
    name: str = Field(min_length=1, max_length=50)
    age: int = Field(ge=0, le=150)
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")

user = CreateUser(name="Alice", age=30, email="alice@example.com")  # OK
user = CreateUser(name="", age=-1, email="bad")  # ValidationError with 3 errors
```

The system collects all validation errors (not fail-fast), generates JSON Schema from model definitions, and integrates with the parameter injection system from Kata 50.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `Field()` descriptor | Defines constraints (min, max, pattern) on a field | Model field validation |
| `__set_name__` | Descriptor protocol hook -- Python tells the field its name | Auto-configuring descriptors |
| `ValidatedModel` | Base class that validates on `__init__` | Request/response models |
| Error collection | Gather all errors, not just the first | User-friendly error responses |
| JSON Schema | Generate `{"type": "object", "properties": ...}` from models | OpenAPI integration |
| `Query()` marker | Validated query parameters with constraints | Search, pagination |
| Type coercion | Auto-convert `"42"` to `int` before validation | String-sourced data |

## The Code

### 1. Field Descriptor

```python
class Field:
    def __init__(self, *, default=_MISSING,
                 min_length=None, max_length=None,
                 ge=None, le=None, gt=None, lt=None,
                 pattern=None, min_items=None, max_items=None):
        ...

    def __set_name__(self, owner, name):
        self._name = name  # Python tells us the field name

    def validate(self, value):
        errors = []
        if isinstance(value, str):
            if self.min_length and len(value) < self.min_length:
                errors.append(f"{self._name}: length < minimum")
        if isinstance(value, (int, float)):
            if self.ge is not None and value < self.ge:
                errors.append(f"{self._name}: {value} < minimum {self.ge}")
        return errors
```

### 2. ValidatedModel

```python
class ValidatedModel:
    def __init__(self, **kwargs):
        hints = get_type_hints(type(self))
        errors = []

        for field_name, field_type in hints.items():
            # 1. Get value from kwargs or field default
            # 2. Type check/coerce
            # 3. Run Field.validate() if descriptor exists
            # 4. Collect errors

        if errors:
            raise ValidationError(errors)
```

### 3. JSON Schema Generation

```python
@classmethod
def schema(cls):
    return {
        "type": "object",
        "title": cls.__name__,
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 50},
            "age": {"type": "integer", "minimum": 0, "maximum": 150},
        },
        "required": ["name", "age", "email"],
    }
```

### 4. Query Validation

```python
@app.get("/search")
def search(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=100),
):
    return {"q": q, "limit": limit}
```

## Playground

```bash
python playground/51_type_driven_validation.py
```

Expected output:

```
--- Section 1: Field Descriptor Validation ---
  Valid: User(name='Alice', age=30, email='alice@example.com')
  Empty name -> name: length 0 < minimum 1
  Negative age -> age: -1 < minimum 0
  Bad email -> email: value does not match pattern ...
  [PASS] Field validation works

--- Section 2: Multiple Validation Errors ---
  Error: name -> name: length 0 < minimum 1
  Error: price -> price: -5.0 must be > 0
  Error: quantity -> quantity: -1 < minimum 0
  Total errors: 3
  [PASS] Multiple error collection works

--- Section 3: JSON Schema Generation ---
  Schema title: CreateUser
  Properties: ['name', 'age', 'email']
  Required: ['name', 'age', 'email']
  [PASS] Schema generation works

--- Section 4: Query Parameter Validation ---
  Valid: {'q': 'python', 'limit': 20, 'offset': 0}
  limit=500 -> limit: 500 > maximum 100
  q='' -> parameter is required
  [PASS] Query parameter validation works

--- Section 5: Integrated Validation ---
  Valid: {'user_id': 1, 'updated': {'name': 'Alice', 'email': 'alice@test.com'}}
  Invalid body -> 2 errors
  [PASS] Integrated validation works

--- Section 6: Collection Validation ---
  Valid: TaggedItem(name='Widget', tags=['sale', 'new'])
  6 tags -> tags: 6 items > maximum 5
  0 tags -> tags: 0 items < minimum 1
  [PASS] Collection validation works

All 6 sections passed. Type-driven validation mastered!
```

## How It Works

### Validation Flow

```
CreateUser(name="", age=-1, email="bad")
    |
    v
__init__ loops over type hints:
    |
    +-- name: str, Field(min_length=1)
    |   value="" -> len(0) < 1 -> ERROR
    |
    +-- age: int, Field(ge=0)
    |   value=-1 -> -1 < 0 -> ERROR
    |
    +-- email: str, Field(pattern=...)
    |   value="bad" -> no match -> ERROR
    |
    v
3 errors collected -> raise ValidationError([...])
```

### Field Constraint Types

| Constraint | Applies To | Meaning |
|---|---|---|
| `min_length` | `str` | Minimum string length |
| `max_length` | `str` | Maximum string length |
| `pattern` | `str` | Regex that must match |
| `ge` | `int`, `float` | Greater than or equal |
| `le` | `int`, `float` | Less than or equal |
| `gt` | `int`, `float` | Strictly greater than |
| `lt` | `int`, `float` | Strictly less than |
| `min_items` | `list`, `tuple`, `set` | Minimum collection size |
| `max_items` | `list`, `tuple`, `set` | Maximum collection size |

### Schema Mapping

```
Field(ge=0, le=150)  ->  {"minimum": 0, "maximum": 150}
Field(min_length=1)  ->  {"minLength": 1}
Field(pattern="...")  ->  {"pattern": "..."}
```

## Exercises

1. **Nested model validation** -- support fields annotated with another `ValidatedModel` subclass so you can validate nested objects.

2. **Enum validation** -- if a field is annotated with an `Enum` type, validate that the value is one of the enum members. Generate `{"enum": [...]}` in the schema.

3. **Custom validators** -- add a `validator` parameter to `Field()` that accepts a callable: `Field(validator=lambda v: v.startswith("https://"))`.

4. **Unique items** -- add a `unique_items=True` constraint for list fields that checks for duplicates.

5. **Dependent field validation** -- implement model-level validation where one field's constraints depend on another (e.g., `end_date` must be after `start_date`).

## What's Next

With validated models that generate JSON Schema, we have everything needed for automatic API documentation. In [Kata 52: OpenAPI Schema Generation](./52-openapi-schema.md), we'll build a complete OpenAPI 3.0 spec generator that extracts path params, query params, request body, and response schemas from handler signatures.

---

[prev: 50-parameter-injection](./50-parameter-injection.md) | [next: 52-openapi-schema](./52-openapi-schema.md)
