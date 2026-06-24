# Kata 44 -- Dependency Injection System

[prev: 43-middleware-pipeline](./43-middleware-pipeline.md) | [next: 45-request-body-validation](./45-request-body-validation.md)

---

## What We're Building

A **FastAPI-style dependency injection system** for the Ignite framework -- declare what your handler needs via `Depends()`, and the framework resolves, caches, and injects those dependencies automatically.

We'll build seven components:
1. **Depends marker** -- a sentinel default value that declares a dependency
2. **Dependency resolver** -- inspects function signatures and resolves dependencies
3. **Dependency chains** -- recursive resolution (A depends on B depends on C)
4. **Per-request caching** -- same dependency resolved once per request, even if needed by multiple parameters
5. **Overrides** -- swap real dependencies for mocks during testing
6. **Practical API example** -- settings, database, user auth as a dependency chain
7. **Dependency graph visualization** -- inspect and print the dependency tree

The key insight: Python's `inspect.signature()` lets you read a function's parameters and their default values. If a default is a `Depends(...)` instance, the DI system knows to resolve it.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `Depends()` marker | Declares a parameter as a dependency | Route handlers needing shared services |
| `inspect.signature()` | Read parameter names, types, and defaults | Automatic dependency detection |
| Recursive resolution | Resolve a dependency's own dependencies | Chains like handler -> repo -> db -> config |
| Per-request cache | Avoid calling the same dependency twice in one request | Database connections, auth tokens |
| Dependency overrides | Replace real deps with mocks | Testing without real databases |
| Dependency graph | Visualize the resolution tree | Debugging complex dependency chains |

## The Code

### 1. The Depends Marker

`Depends` is just a class used as a default parameter value. Python lets you put any object as a default:

```python
class Depends:
    def __init__(self, dependency: Callable, *, use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache

# Usage -- Depends(get_db) becomes the default value for 'db':
def list_users(db: dict = Depends(get_db)):
    ...
```

When the resolver inspects the signature, it sees that `db`'s default is a `Depends` instance and knows to call `get_db()` to provide the value.

### 2. Signature Inspection

The resolver uses `inspect.signature()` to find which parameters need resolution:

```python
import inspect

sig = inspect.signature(list_users)
for name, param in sig.parameters.items():
    if isinstance(param.default, Depends):
        # This parameter needs dependency injection
        dep_func = param.default.dependency
        result = dep_func()  # resolve it
```

### 3. Recursive Resolution

Dependencies can have their own dependencies. The resolver calls itself recursively:

```python
def resolve(self, func, cache=None, **extra_kwargs):
    cache = cache or {}
    kwargs = {}

    for name, param in inspect.signature(func).parameters.items():
        if name in extra_kwargs:
            kwargs[name] = extra_kwargs[name]  # path params, etc.
        elif isinstance(param.default, Depends):
            dep = param.default
            actual = self._overrides.get(dep.dependency, dep.dependency)

            if dep.use_cache and actual in cache:
                kwargs[name] = cache[actual]
            else:
                result = self.resolve(actual, cache=cache)  # recursive!
                if dep.use_cache:
                    cache[actual] = result
                kwargs[name] = result

    return func(**kwargs)
```

### 4. Per-Request Caching

Without caching, a shared dependency called by two different paths would execute twice:

```python
def get_db(): ...  # expensive connection

def service_a(db=Depends(get_db)): ...
def service_b(db=Depends(get_db)): ...

def handler(a=Depends(service_a), b=Depends(service_b)):
    # Without cache: get_db() called TWICE
    # With cache:    get_db() called ONCE, result shared
    ...
```

The cache is a simple dict `{dependency_func: result}` that lives for one request.

### 5. Overrides for Testing

Swap any dependency without changing handler code:

```python
resolver = DependencyResolver()

# In tests:
resolver.override(get_real_database, get_mock_database)
result = resolver.resolve(my_handler)  # uses mock DB

# Cleanup:
resolver.clear_overrides()
```

## Playground

```bash
python playground/44_dependency_injection.py
```

Expected output:

```
--- Section 1: The Depends Marker ---
  Param 'db' depends on get_database()
  Param 'user' depends on get_current_user()
  [VALID] Depends markers detected in signature

--- Section 2: Basic Dependency Resolution ---
  Handler with config: debug=True
  User #42 (debug=True)
  [VALID] Basic dependency resolution works

--- Section 3: Dependency Chains ---
  Chain result: Users from users via postgresql://localhost/mydb
  Dependency chain:
    list_users
      -> get_user_repo
           -> get_database
                -> get_settings
  [VALID] Dependency chains resolve recursively

--- Section 4: Per-Request Caching ---
  Result: ServiceA using resource #1 | ServiceB using resource #1
  get_expensive_resource called 1 time(s)
  No-cache result: X#1 | Y#2
  get_cheap_resource called 2 time(s)
  [VALID] Caching prevents redundant dependency calls

--- Section 5: Dependency Overrides (Testing) ---
  Production: {'name': 'Alice', 'db': 'PostgreSQL'}
  Test (overridden): {'name': 'Alice', 'db': 'MockDB'}
  After clear: {'name': 'Alice', 'db': 'PostgreSQL'}
  [VALID] Dependency overrides work for testing

--- Section 6: Practical Example -- Mini API ---
  list_items -> 200: Items for Alice from sqlite:///app.db
  get_item(42) -> 200: Item #42 for Alice
  list_items (mocked) -> 200: Items for TestBot from mock://test
  [VALID] Practical API with DI works end-to-end

--- Section 7: Visualizing the Dependency Graph ---
  Dependency graph for list_items:
  list_items
    -> get_current_user
      -> get_db
        -> get_settings
    -> get_db
      -> (cached)
  [VALID] Dependency graph visualization works

--- Summary ---
Dependency injection decouples components and simplifies testing:
  - Depends(func) marks a parameter as a dependency
  - The resolver inspects signatures and calls dependencies
  - Chains resolve recursively (A -> B -> C)
  - Per-request caching avoids redundant calls
  - Overrides swap real deps for mocks in tests

All 7 sections passed. Dependency injection mastered!
Next up: Kata 45 -- Request Body Validation
```

## How It Works

### Resolution Flow

```
Handler: list_items(user=Depends(get_current_user), db=Depends(get_db))

resolve(list_items)
  |
  +-- param 'user': Depends(get_current_user)
  |     |
  |     +-- resolve(get_current_user)
  |           |
  |           +-- param 'db': Depends(get_db)
  |                 |
  |                 +-- resolve(get_db)
  |                       |
  |                       +-- param 'settings': Depends(get_settings)
  |                             |
  |                             +-- resolve(get_settings)
  |                                   return {"db_url": "...", ...}
  |                             cache[get_settings] = result
  |                       return {"engine": "...", "connected": True}
  |                 cache[get_db] = result
  |           return {"id": 1, "name": "Alice", ...}
  |     cache[get_current_user] = result
  |
  +-- param 'db': Depends(get_db)
  |     cache HIT -> reuse cached result
  |
  +-- call list_items(user=..., db=...)
```

### Caching Prevents Diamond Dependencies

```
Without cache:              With cache:
    handler                     handler
    /     \                     /     \
  svc_a  svc_b               svc_a  svc_b
    |      |                    |      |
  get_db  get_db              get_db  (cached)
    |      |                    |
  2 calls!                   1 call
```

### Override Mechanism

```
Production:                  Testing:
  handler                      handler
    |                            |
  get_real_db  <-- original    get_mock_db  <-- override
    |                            |
  PostgreSQL                   In-memory dict
```

## Exercises

1. **Async dependency resolution** -- extend the resolver to handle `async def` dependencies. Use `inspect.iscoroutinefunction()` to detect them and `await` the result. This is essential for real async frameworks.

2. **Circular dependency detection** -- add detection for circular dependencies (A depends on B depends on A). Track the resolution stack and raise a clear error message showing the cycle.

3. **Scoped dependencies** -- implement `Depends(get_db, scope="app")` where `scope="app"` means the dependency is resolved once for the entire app lifetime (singleton), not per-request. Add a separate app-level cache.

4. **Dependency with cleanup** -- support generator dependencies that yield a value and run cleanup code after the request. For example, a database connection that auto-commits or rolls back:

   *Excerpt — core logic only (some details elided); not a standalone runnable snippet.*

   ```python
   def get_db_session():
       session = create_session()
       try:
           yield session
           session.commit()
       except:
           session.rollback()
   ```

5. **Type-based resolution** -- instead of explicit `Depends(func)`, resolve dependencies by type annotation alone. If a parameter is annotated as `db: Database` and a `Database` provider is registered, inject it automatically (like Angular's DI).

## What's Next

With dependency injection wired up, our handlers can cleanly receive databases, auth, config, and any other service. In [Kata 45: Request Body Validation](./45-request-body-validation.md), we build a validation system that parses and validates JSON request bodies, combining path parameters with body data for complete request handling.

---

[prev: 43-middleware-pipeline](./43-middleware-pipeline.md) | [next: 45-request-body-validation](./45-request-body-validation.md)
