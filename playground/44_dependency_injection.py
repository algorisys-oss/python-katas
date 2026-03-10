"""
Kata 44 -- Dependency Injection System
Run: python playground/44_dependency_injection.py

Build a FastAPI-style dependency injection system with Depends().
Resolve dependencies by inspecting function signatures, support
dependency chains, per-request caching, and overrides for testing.

Completes within 5 seconds.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, get_type_hints


# ===========================================================================
# SECTION 1: The Depends Marker
# ===========================================================================

class Depends:
    """Marker class for declaring dependencies.

    Usage in a route handler:
        def get_users(db: Database = Depends(get_database)):
            ...

    The DI system sees Depends(get_database) as the default value,
    calls get_database() to resolve it, and injects the result.
    """

    def __init__(self, dependency: Callable, *, use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        name = getattr(self.dependency, "__name__", str(self.dependency))
        return f"Depends({name}, cache={self.use_cache})"


def demo_depends_marker():
    """Show how Depends works as a marker in function signatures."""

    def get_database():
        return {"type": "PostgreSQL", "host": "localhost"}

    def get_current_user():
        return {"id": 1, "name": "Alice"}

    # A handler that declares dependencies via Depends()
    def list_items(
        db: dict = Depends(get_database),
        user: dict = Depends(get_current_user),
    ):
        return f"Items for {user['name']} from {db['type']}"

    # Inspect the signature to find Depends markers
    sig = inspect.signature(list_items)
    for name, param in sig.parameters.items():
        if isinstance(param.default, Depends):
            dep_name = param.default.dependency.__name__
            print(f"  Param '{name}' depends on {dep_name}()")
        else:
            print(f"  Param '{name}' has no dependency")

    # Verify we found the right dependencies
    deps_found = {
        name: param.default.dependency.__name__
        for name, param in sig.parameters.items()
        if isinstance(param.default, Depends)
    }
    assert deps_found == {"db": "get_database", "user": "get_current_user"}
    print(f"  [VALID] Depends markers detected in signature")


# ===========================================================================
# SECTION 2: Dependency Resolver
# ===========================================================================

class DependencyResolver:
    """Resolves dependencies by inspecting function signatures.

    Features:
    - Recursive resolution (A depends on B depends on C)
    - Per-request caching (same dependency called once per request)
    - Override support (for testing)
    """

    def __init__(self):
        self._overrides: dict[Callable, Callable] = {}

    def override(self, original: Callable, replacement: Callable) -> None:
        """Override a dependency for testing."""
        self._overrides[original] = replacement

    def clear_overrides(self) -> None:
        """Remove all dependency overrides."""
        self._overrides.clear()

    def resolve(self, func: Callable,
                cache: dict[Callable, Any] | None = None,
                **extra_kwargs: Any) -> Any:
        """Resolve all dependencies for a function and call it.

        Args:
            func: The function to resolve and call.
            cache: Per-request cache dict. Dependencies with use_cache=True
                   are resolved once and reused.
            **extra_kwargs: Additional keyword arguments to pass directly
                           (e.g., path parameters from the router).
        """
        if cache is None:
            cache = {}

        sig = inspect.signature(func)
        resolved_kwargs: dict[str, Any] = {}

        for name, param in sig.parameters.items():
            # If the caller provided this kwarg directly, use it
            if name in extra_kwargs:
                resolved_kwargs[name] = extra_kwargs[name]
                continue

            # If the parameter has a Depends default, resolve it
            if isinstance(param.default, Depends):
                dep = param.default
                actual_dep = self._overrides.get(dep.dependency, dep.dependency)

                # Check cache first
                if dep.use_cache and actual_dep in cache:
                    resolved_kwargs[name] = cache[actual_dep]
                    continue

                # Recursively resolve the dependency's own dependencies
                result = self.resolve(actual_dep, cache=cache)

                # Cache the result if caching is enabled
                if dep.use_cache:
                    cache[actual_dep] = result

                resolved_kwargs[name] = result
            # If no default or not a Depends, skip (will use function default)

        return func(**resolved_kwargs)


def demo_basic_resolution():
    """Demonstrate basic dependency resolution."""
    resolver = DependencyResolver()

    # Simple dependency -- no sub-dependencies
    def get_config():
        return {"debug": True, "version": "1.0"}

    def get_handler(config: dict = Depends(get_config)):
        return f"Handler with config: debug={config['debug']}"

    result = resolver.resolve(get_handler)
    print(f"  {result}")
    assert "debug=True" in result

    # Dependency with extra kwargs (like path params from router)
    def get_user(user_id: int, config: dict = Depends(get_config)):
        return f"User #{user_id} (debug={config['debug']})"

    result2 = resolver.resolve(get_user, user_id=42)
    print(f"  {result2}")
    assert "User #42" in result2
    assert "debug=True" in result2

    print(f"  [VALID] Basic dependency resolution works")


# ===========================================================================
# SECTION 3: Dependency Chains
# ===========================================================================

def demo_dependency_chains():
    """Demonstrate chained dependencies: A -> B -> C."""
    resolver = DependencyResolver()

    # Level 0: no dependencies
    def get_settings():
        return {"db_url": "postgresql://localhost/mydb", "pool_size": 5}

    # Level 1: depends on settings
    def get_database(settings: dict = Depends(get_settings)):
        return {
            "url": settings["db_url"],
            "pool_size": settings["pool_size"],
            "connected": True,
        }

    # Level 2: depends on database
    def get_user_repo(db: dict = Depends(get_database)):
        return {"db": db, "table": "users"}

    # Level 3: depends on user_repo (handler)
    def list_users(repo: dict = Depends(get_user_repo)):
        return f"Users from {repo['table']} via {repo['db']['url']}"

    result = resolver.resolve(list_users)
    print(f"  Chain result: {result}")
    assert "users" in result
    assert "postgresql://localhost/mydb" in result

    # Show the dependency graph
    print(f"  Dependency chain:")
    print(f"    list_users")
    print(f"      -> get_user_repo")
    print(f"           -> get_database")
    print(f"                -> get_settings")

    print(f"  [VALID] Dependency chains resolve recursively")


# ===========================================================================
# SECTION 4: Per-Request Caching
# ===========================================================================

def demo_caching():
    """Show that dependencies are cached per-request."""
    resolver = DependencyResolver()
    call_count = 0

    def get_expensive_resource():
        nonlocal call_count
        call_count += 1
        return {"resource_id": call_count}

    # Two dependencies that both depend on the same expensive resource
    def get_service_a(res: dict = Depends(get_expensive_resource)):
        return f"ServiceA using resource #{res['resource_id']}"

    def get_service_b(res: dict = Depends(get_expensive_resource)):
        return f"ServiceB using resource #{res['resource_id']}"

    # Handler depends on both services
    def handler(
        svc_a: str = Depends(get_service_a),
        svc_b: str = Depends(get_service_b),
    ):
        return f"{svc_a} | {svc_b}"

    call_count = 0
    result = resolver.resolve(handler)
    print(f"  Result: {result}")
    print(f"  get_expensive_resource called {call_count} time(s)")

    # With caching, get_expensive_resource should be called only ONCE
    assert call_count == 1, f"Expected 1 call, got {call_count}"
    # Both services should reference the same resource
    assert "resource #1" in result.lower()

    # Without caching (use_cache=False)
    def get_cheap_resource():
        nonlocal call_count
        call_count += 1
        return {"resource_id": call_count}

    def svc_x(res: dict = Depends(get_cheap_resource, use_cache=False)):
        return f"X#{res['resource_id']}"

    def svc_y(res: dict = Depends(get_cheap_resource, use_cache=False)):
        return f"Y#{res['resource_id']}"

    def handler2(x: str = Depends(svc_x), y: str = Depends(svc_y)):
        return f"{x} | {y}"

    call_count = 0
    result2 = resolver.resolve(handler2)
    print(f"  No-cache result: {result2}")
    print(f"  get_cheap_resource called {call_count} time(s)")
    # Without caching, it should be called twice (once per service)
    assert call_count == 2, f"Expected 2 calls, got {call_count}"

    print(f"  [VALID] Caching prevents redundant dependency calls")


# ===========================================================================
# SECTION 5: Dependency Overrides (Testing)
# ===========================================================================

def demo_overrides():
    """Demonstrate overriding dependencies for testing."""
    resolver = DependencyResolver()

    # Production dependencies
    def get_real_database():
        return {"type": "PostgreSQL", "host": "prod-server"}

    def get_user(db: dict = Depends(get_real_database)):
        return {"name": "Alice", "db": db["type"]}

    # Without override: uses real database
    result1 = resolver.resolve(get_user)
    print(f"  Production: {result1}")
    assert result1["db"] == "PostgreSQL"

    # Override for testing
    def get_mock_database():
        return {"type": "MockDB", "host": "localhost"}

    resolver.override(get_real_database, get_mock_database)

    result2 = resolver.resolve(get_user)
    print(f"  Test (overridden): {result2}")
    assert result2["db"] == "MockDB"

    # Clear overrides
    resolver.clear_overrides()
    result3 = resolver.resolve(get_user)
    print(f"  After clear: {result3}")
    assert result3["db"] == "PostgreSQL"

    print(f"  [VALID] Dependency overrides work for testing")


# ===========================================================================
# SECTION 6: Practical Example -- Mini API
# ===========================================================================

@dataclass
class Request:
    """Minimal request object."""
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    path_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """Minimal response object."""
    status: int = 200
    body: Any = ""


# Simulated "services"
def get_settings():
    """Application settings (could come from env vars)."""
    return {"db_url": "sqlite:///app.db", "secret_key": "s3cret"}


def get_db(settings: dict = Depends(get_settings)):
    """Database connection (depends on settings)."""
    return {"engine": settings["db_url"], "connected": True}


def get_current_user(db: dict = Depends(get_db)):
    """Get the current authenticated user (depends on database)."""
    # In reality, would check token, query DB, etc.
    if not db["connected"]:
        return None
    return {"id": 1, "name": "Alice", "role": "admin"}


def demo_practical_api():
    """Simulate a mini API using the DI system."""
    resolver = DependencyResolver()

    # Define route handlers with Depends
    def list_items(
        user: dict = Depends(get_current_user),
        db: dict = Depends(get_db),
    ):
        if user is None:
            return Response(status=401, body="Unauthorized")
        return Response(
            body=f"Items for {user['name']} from {db['engine']}"
        )

    def get_item(
        item_id: int,
        user: dict = Depends(get_current_user),
    ):
        return Response(body=f"Item #{item_id} for {user['name']}")

    # Resolve and call handlers
    resp1 = resolver.resolve(list_items)
    print(f"  list_items -> {resp1.status}: {resp1.body}")
    assert resp1.status == 200
    assert "Alice" in resp1.body

    resp2 = resolver.resolve(get_item, item_id=42)
    print(f"  get_item(42) -> {resp2.status}: {resp2.body}")
    assert "Item #42" in resp2.body

    # Override for testing
    def mock_db(settings: dict = Depends(get_settings)):
        return {"engine": "mock://test", "connected": True}

    def mock_user(db: dict = Depends(get_db)):
        return {"id": 99, "name": "TestBot", "role": "tester"}

    resolver.override(get_db, mock_db)
    resolver.override(get_current_user, mock_user)

    resp3 = resolver.resolve(list_items)
    print(f"  list_items (mocked) -> {resp3.status}: {resp3.body}")
    assert "TestBot" in resp3.body
    assert "mock://test" in resp3.body

    resolver.clear_overrides()
    print(f"  [VALID] Practical API with DI works end-to-end")


# ===========================================================================
# SECTION 7: Visualizing the Dependency Graph
# ===========================================================================

def get_dependency_graph(func: Callable,
                         visited: set | None = None) -> dict:
    """Build a tree of dependencies for visualization."""
    if visited is None:
        visited = set()

    name = getattr(func, "__name__", str(func))
    if func in visited:
        return {"name": name, "deps": ["(cached)"]}
    visited.add(func)

    deps = []
    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        if isinstance(param.default, Depends):
            sub_graph = get_dependency_graph(
                param.default.dependency, visited
            )
            deps.append(sub_graph)

    return {"name": name, "deps": deps}


def print_graph(graph: dict, indent: int = 0) -> None:
    """Pretty-print a dependency graph."""
    prefix = "  " * indent
    connector = "-> " if indent > 0 else ""
    print(f"  {prefix}{connector}{graph['name']}")
    for dep in graph["deps"]:
        if isinstance(dep, str):
            print(f"  {prefix}  -> {dep}")
        else:
            print_graph(dep, indent + 1)


def demo_dependency_graph():
    """Visualize the dependency tree."""
    def list_items(
        user: dict = Depends(get_current_user),
        db: dict = Depends(get_db),
    ):
        pass

    graph = get_dependency_graph(list_items)
    print(f"  Dependency graph for list_items:")
    print_graph(graph)

    # Verify graph structure
    assert graph["name"] == "list_items"
    assert len(graph["deps"]) == 2
    assert graph["deps"][0]["name"] == "get_current_user"

    print(f"  [VALID] Dependency graph visualization works")


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("--- Section 1: The Depends Marker ---")
    demo_depends_marker()
    print()

    print("--- Section 2: Basic Dependency Resolution ---")
    demo_basic_resolution()
    print()

    print("--- Section 3: Dependency Chains ---")
    demo_dependency_chains()
    print()

    print("--- Section 4: Per-Request Caching ---")
    demo_caching()
    print()

    print("--- Section 5: Dependency Overrides (Testing) ---")
    demo_overrides()
    print()

    print("--- Section 6: Practical Example -- Mini API ---")
    demo_practical_api()
    print()

    print("--- Section 7: Visualizing the Dependency Graph ---")
    demo_dependency_graph()
    print()

    print("--- Summary ---")
    print("Dependency injection decouples components and simplifies testing:")
    print("  - Depends(func) marks a parameter as a dependency")
    print("  - The resolver inspects signatures and calls dependencies")
    print("  - Chains resolve recursively (A -> B -> C)")
    print("  - Per-request caching avoids redundant calls")
    print("  - Overrides swap real deps for mocks in tests")
    print()
    print("All 7 sections passed. Dependency injection mastered!")
    print("Next up: Kata 45 -- Request Body Validation")


if __name__ == "__main__":
    main()
