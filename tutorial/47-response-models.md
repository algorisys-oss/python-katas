# Kata 47 -- Response Models

[prev: 46-query-parameters](./46-query-parameters.md) | [next: 48-error-handling](./48-error-handling.md)

---

## What We're Building

A **response model serialization system** for the Ignite framework. While kata 45 handled input validation, response models control the *output* -- what fields are included in API responses, how they're named, and how complex types get serialized to JSON.

We'll build five components:
1. **ResponseModel** -- base class with configurable serialization
2. **Field filtering** -- include/exclude fields, skip None values
3. **Field aliases** -- map internal names to API names (e.g., `created_at` -> `createdAt`)
4. **Nested serialization** -- recursively serialize model trees
5. **JSONResponse** -- HTTP response wrapper with status codes and headers

This is how FastAPI controls API output -- you define a response model and the framework ensures only the right data reaches the client.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Response models | Control which fields appear in API output | Every API endpoint |
| `model_dump()` | Serialize a model to a dict with filtering options | Building JSON responses |
| Field exclusion | Remove sensitive fields (password, internal IDs) | Security/privacy |
| Field aliases | Rename fields for the API (`snake_case` -> `camelCase`) | JavaScript client compatibility |
| `exclude_none` | Skip fields with `None` values | Sparse responses |
| `from_object()` | Map arbitrary objects to response models | DB model -> API response |
| Custom encoders | Serialize complex types (datetime, Decimal) | Non-JSON-native types |
| Nested models | Recursively serialize model trees | Related data (user -> posts) |

## The Code

### 1. The ResponseModel Base

Unlike `BaseModel` (input), `ResponseModel` focuses on output control:

```python
class ResponseModel:
    class Config:
        exclude_fields: set[str] = set()       # Always hidden
        include_fields: set[str] | None = None  # None = all
        field_aliases: dict[str, str] = {}      # internal -> api
        json_encoders: dict[type, Any] = {}     # type -> serializer

    def model_dump(self, *, include=None, exclude=None,
                   by_alias=False, exclude_none=False) -> dict:
        ...
```

### 2. Field Filtering

```python
class UserResponse(ResponseModel):
    id: int
    name: str
    email: str
    password_hash: str  # NEVER expose this

    class Config:
        exclude_fields = {"password_hash", "internal_id"}

user.model_dump()
# {"id": 1, "name": "Alice", "email": "alice@test.com"}
# password_hash is excluded!

# Runtime overrides:
user.model_dump(include={"id", "name"})   # Only these fields
user.model_dump(exclude={"email"})         # Also exclude email
user.model_dump(exclude_none=True)         # Skip None fields
```

### 3. Field Aliases

```python
class UserResponse(ResponseModel):
    created_at: datetime

    class Config:
        field_aliases = {"created_at": "createdAt"}

user.model_dump(by_alias=True)
# {"createdAt": "2024-01-15T10:30:00+00:00"}  # camelCase!
```

### 4. Custom Type Encoders

```python
class Config:
    json_encoders = {
        datetime: lambda dt: dt.isoformat(),
        Decimal: lambda d: float(d),
    }
```

### 5. From Object Mapping

Safely convert database models to API responses:

```python
class DBUser:  # From your ORM
    id = 7
    name = "Eve"
    password_hash = "secret123"  # Dangerous!

response = UserResponse.from_object(db_user)
response.model_dump()
# {"id": 7, "name": "Eve"} -- password_hash excluded by Config
```

## Playground

```python
python playground/47_response_models.py
```

Expected output:

```
--- Section 1: Basic Response Model ---
  UserResponse: {'created_at': '2024-01-15T10:30:00+00:00', 'name': 'Alice', ...}
  [PASS] Basic response model works

--- Section 2: Field Inclusion/Exclusion ---
  Exclude email+bio: {'created_at': None, 'name': 'Bob', 'id': 1}
  Include id+name only: {'id': 1, 'name': 'Bob'}
  Exclude None: {'name': 'Bob', 'id': 1, 'email': 'bob@test.com'}
  [PASS] Field inclusion/exclusion works

--- Section 3: Field Aliases ---
  Without aliases: keys = ['created_at', 'name', 'bio', 'id', 'email']
  With aliases: keys = ['createdAt', 'name', 'bio', 'user_id', 'email']
  [PASS] Field aliases work

--- Section 4: Nested Models ---
  Post with nested author:
    title = 'Understanding Python Type Hints'
    author = {'created_at': None, 'name': 'Diana', ...}
    tags = ['python', 'typing']
  [PASS] Nested model serialization works

--- Section 5: From Object Mapping ---
  DBUser -> UserResponse: {'name': 'Eve', 'bio': 'Security researcher', ...}
  [PASS] From-object mapping works

--- Section 6: Paginated Response ---
  Paginated: total=50, page=1
  Items: 3 users
  has_next=True, has_prev=False
  [PASS] Paginated response works

--- Section 7: JSONResponse Integration ---
  Status: 200
  Content-Type: application/json
  Body: {'name': 'Frank', ...}
  [PASS] JSONResponse integration works

All 7 sections passed. Response models mastered!
```

## How It Works

### Serialization Pipeline

```
Model Instance              Config                    Output Dict
--------------              ------                    -----------
UserResponse(               exclude: {password}  -->  {
  id=1,                     aliases: {id: userId}       "userId": 1,
  name="Alice",             encoders: {datetime: ...}   "name": "Alice",
  password="hash",          exclude_none: True          "createdAt": "2024-..."
  created_at=datetime(...),                           }
  bio=None,                 ^^ bio=None excluded
)
```

### model_dump() Resolution

```
For each field in type hints:
  1. Apply include filter (if specified)
  2. Apply exclude filter (Config + parameter)
  3. Skip None values (if exclude_none=True)
  4. Apply custom encoder (datetime -> isoformat)
  5. Recurse for nested ResponseModel instances
  6. Apply alias for output key name (if by_alias=True)
```

### Input vs Output Models

```
Request (Input)                    Response (Output)
---------------                    ----------------
BaseModel (kata 45)                ResponseModel (this kata)
Validates incoming data            Controls outgoing data
Raises on invalid input            Filters/transforms output
Type coercion (str -> int)         Type encoding (datetime -> str)
Required/optional fields           Include/exclude fields
Constraint checking                Alias mapping
```

## Exercises

1. **Add `computed_field`** -- implement a decorator that adds computed fields to the output. For example, `full_name` computed from `first_name` + `last_name`, included in `model_dump()` but not stored as an attribute.

2. **Implement response model inheritance** -- ensure that `UserDetailResponse(UserResponse)` correctly inherits Config settings and merges them (child exclude_fields adds to parent's).

3. **Add `model_dump_json()` with indent** -- extend `model_json()` to accept formatting options (indent, sort_keys) for pretty-printed API responses.

4. **Build a generic `ListResponse[T]`** -- a generic paginated response that takes a model type parameter: `ListResponse[UserResponse]` automatically serializes items using the specified model.

5. **Add field-level serializers** -- allow per-field custom serialization (e.g., `price` always rounds to 2 decimal places) using a `@serializer("price")` decorator.

## What's Next

We now have complete input (kata 45-46) and output (this kata) handling. In [Kata 48: Error Handling](./48-error-handling.md), we'll build the error handling system -- `HTTPException`, exception handler registries, and structured error responses that catch and format any exception that occurs during request processing.

---

[prev: 46-query-parameters](./46-query-parameters.md) | [next: 48-error-handling](./48-error-handling.md)
