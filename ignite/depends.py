"""Ignite Depends — dependency injection system."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable


class Depends:
    """Marker class for declaring dependencies.

    Usage in a route handler:
        def get_users(db: Database = Depends(get_database)):
            ...

    The DI system sees Depends(get_database) as the default value,
    calls get_database() to resolve it, and injects the result.
    """

    def __init__(
        self, dependency: Callable, *, use_cache: bool = True
    ) -> None:
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        name = getattr(self.dependency, "__name__", str(self.dependency))
        return f"Depends({name}, cache={self.use_cache})"


class DependencyResolver:
    """Resolves dependencies by inspecting function signatures.

    Features:
    - Recursive resolution (A depends on B depends on C)
    - Per-request caching (same dependency called once per request)
    - Override support (for testing)
    - Async dependency support
    """

    def __init__(self) -> None:
        self._overrides: dict[Callable, Callable] = {}

    def override(self, original: Callable, replacement: Callable) -> None:
        """Override a dependency for testing."""
        self._overrides[original] = replacement

    def clear_overrides(self) -> None:
        """Remove all dependency overrides."""
        self._overrides.clear()

    async def resolve(
        self,
        func: Callable,
        cache: dict[Callable, Any] | None = None,
        **extra_kwargs: Any,
    ) -> Any:
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
                actual_dep = self._overrides.get(
                    dep.dependency, dep.dependency
                )

                # Check cache first
                if dep.use_cache and actual_dep in cache:
                    resolved_kwargs[name] = cache[actual_dep]
                    continue

                # Recursively resolve the dependency's own dependencies
                result = await self.resolve(actual_dep, cache=cache)

                # Cache the result if caching is enabled
                if dep.use_cache:
                    cache[actual_dep] = result

                resolved_kwargs[name] = result

            # If no default or not a Depends, skip (will use function default)

        result = func(**resolved_kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return result
