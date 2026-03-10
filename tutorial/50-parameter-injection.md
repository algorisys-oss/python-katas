# Kata 50 -- Automatic Parameter Injection

[prev: 49-route-decorators](./49-route-decorators.md) | [next: 51-type-driven-validation](./51-type-driven-validation.md)

---

## What We're Building

**Automatic parameter injection** that inspects handler function signatures and fills in arguments from the right source. This is the magic behind FastAPI's declarative handler style:

```python
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Database = Depends(get_db)):
    return db.find(user_id)

@app.post("/users")
def create_user(user: CreateUser, limit: int = 10):
    ...
```

The injector examines each parameter's name, type annotation, and default value to determine where the value comes from: URL path, query string, request body, or dependency function.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `inspect.signature()` | Reads a function's parameter names, annotations, defaults | Automatic injection |
| Path parameters | Extract `{user_id}` from URL using regex | REST resource IDs |
| Query parameters | Parse `?q=python&limit=10` from query string | Filtering, pagination |
| Body model | Parse JSON body into a `BaseModel` subclass | Creating/updating resources |
| `Depends()` marker | Signal that a parameter comes from a dependency function | Database sessions, auth |
| Type coercion | Convert string `"42"` to `int` based on annotation | All parameter sources |
| Named groups regex | `(?P<user_id>[^/]+)` captures path segments | URL pattern matching |

## The Code

### 1. The ParameterInjector

```python
class ParameterInjector:
    def __init__(self, path_template, handler):
        self.handler = handler
        self.sig = inspect.signature(handler)
        self.hints = {
            name: p.annotation
            for name, p in self.sig.parameters.items()
            if p.annotation is not inspect.Parameter.empty
        }
        # "/users/{user_id}" -> {"user_id"}
        self.path_param_names = set(re.findall(r"\{(\w+)\}", path_template))
        # Build regex: "/users/(?P<user_id>[^/]+)"
        pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path_template)
        self.path_regex = re.compile(f"^{pattern}$")
```

### 2. The Injection Logic

For each parameter in the handler signature, check sources in priority order:

```python
def inject(self, request):
    kwargs = {}
    for name, param in self.sig.parameters.items():
        annotation = self.hints.get(name, param.annotation)

        # 1. Request itself
        if annotation is Request or name == "request":
            kwargs[name] = request

        # 2. Depends() -- call the dependency
        elif isinstance(param.default, Depends):
            kwargs[name] = param.default.dependency()

        # 3. BaseModel -- parse from JSON body
        elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
            kwargs[name] = annotation(**request.json_body)

        # 4. Path parameter -- from URL regex match
        elif name in self.path_param_names:
            kwargs[name] = self._coerce(path_params[name], annotation)

        # 5. Query parameter -- from query string
        elif name in query_params:
            kwargs[name] = self._coerce(query_params[name], annotation)

        # 6. Default value
        elif param.default is not inspect.Parameter.empty:
            kwargs[name] = param.default
```

### 3. Type Coercion

String values from URLs and query strings are coerced to the annotated type:

```python
def _coerce(self, value, annotation):
    if annotation is int:   return int(value)
    if annotation is float: return float(value)
    if annotation is bool:  return value.lower() in ("true", "1", "yes")
    return value  # str or unknown
```

### 4. Depends() Pattern

```python
class Depends:
    def __init__(self, dependency):
        self.dependency = dependency

# Usage:
def get_db(): return Database()

@app.get("/users")
def list_users(db: Database = Depends(get_db)):
    return db.query("users")
```

## Playground

```python
python playground/50_parameter_injection.py
```

Expected output:

```
--- Section 1: Path Parameter Injection ---
  GET /users/42 -> {'user_id': 42, 'name': 'User 42'}
  GET /items/electronics/7 -> {'category': 'electronics', 'item_id': 7}
  [PASS] Path parameter injection works

--- Section 2: Query Parameter Injection ---
  GET /search?q=python&limit=5 -> {'query': 'python', 'limit': 5, 'offset': 0}
  GET /search?q=rust -> {'query': 'rust', 'limit': 10, 'offset': 0}
  [PASS] Query parameter injection works

--- Section 3: Body Model Injection ---
  POST /users -> {'created': {'name': 'Alice', 'email': 'alice@example.com', 'age': 30}}
  [PASS] Body model injection works

--- Section 4: Depends() Injection ---
  GET /db-users -> {'users': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]}
  GET /me (admin) -> {'user_id': 1, 'role': 'admin'}
  GET /me (no token) -> {'user_id': 0, 'role': 'anonymous'}
  [PASS] Depends() injection works

--- Section 5: Mixed Parameter Types ---
  PUT /items/5 -> {'item_id': 5, 'updated': {'name': 'Widget', 'price': 9.99}, 'db_connected': True}
  [PASS] Mixed parameter types work

--- Section 6: Request Passthrough ---
  GET /raw?q=hello -> {'method': 'GET', 'path': '/raw', 'query': 'hello'}
  [PASS] Request passthrough works

All 6 sections passed. Parameter injection mastered!
```

## How It Works

### Parameter Source Resolution

```
Handler: def update_item(item_id: int, item: UpdateItem, db: DB = Depends(get_db))

Parameter      Annotation    Default       Source
---------      ----------    -------       ------
item_id        int           (none)        Path param (matches {item_id} in URL)
item           UpdateItem    (none)        Body model (subclass of BaseModel)
db             DB            Depends(...)  Dependency injection
```

### Path Template to Regex

```
Template:  /items/{category}/{item_id}
                     |            |
                     v            v
Regex:     /items/(?P<category>[^/]+)/(?P<item_id>[^/]+)

URL:       /items/electronics/7
Match:     category="electronics", item_id="7"
Coerce:    category="electronics", item_id=7 (int annotation)
```

### Depends() Execution Chain

```
Request arrives
    |
    v
Injector sees: db: DB = Depends(get_db)
    |
    v
Inspect get_db's signature
    |
    v
get_db needs request? -> inject Request
    |
    v
Call get_db(request=request) -> DB instance
    |
    v
Pass DB instance as 'db' to handler
```

## Exercises

1. **Nested dependencies** -- support `Depends()` where the dependency function itself has `Depends()` parameters. Build a dependency resolution graph.

2. **Dependency caching** -- if the same dependency function is used by multiple parameters (or nested deps), only call it once per request and reuse the result.

3. **Header injection** -- add a `Header()` marker so `def handler(auth: str = Header("Authorization"))` extracts from request headers.

4. **Cookie injection** -- similar to Header but for cookies: `session_id: str = Cookie("session_id")`.

5. **Background tasks** -- inject a `BackgroundTasks` object that collects functions to run after the response is sent.

## What's Next

Parameter injection gives us clean handler signatures, but we still trust the data blindly. In [Kata 51: Type-Driven Validation](./51-type-driven-validation.md), we'll build a validation system that uses type annotations and Field descriptors to automatically validate request data with constraints like min/max, patterns, and range checks.

---

[prev: 49-route-decorators](./49-route-decorators.md) | [next: 51-type-driven-validation](./51-type-driven-validation.md)
