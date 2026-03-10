"""Ignite Params — automatic parameter injection for route handlers."""

from __future__ import annotations

import asyncio
import inspect
import re
from typing import Any, Callable, get_type_hints
from urllib.parse import parse_qs

from .depends import Depends
from .request import Request
from .validation import BaseModel


class ParameterInjector:
    """Inspects handler signatures and injects parameters automatically.

    Parameter sources (in priority order):
    1. Request — if annotated as Request, pass the raw request object
    2. Depends — default value is Depends(func) -> call the dependency
    3. Body model — annotation is a BaseModel subclass -> parse from JSON
    4. Path params — name matches a {param} in the route path
    5. Query params — remaining simple-type params come from query string
    6. Default value — use the parameter's default if nothing else matches
    """

    def __init__(self, path_template: str, handler: Callable) -> None:
        self.path_template = path_template
        self.handler = handler
        self.sig = inspect.signature(handler)

        # Use signature annotations directly to avoid NameError with
        # locally-defined classes
        self.hints: dict[str, Any] = {
            name: p.annotation
            for name, p in self.sig.parameters.items()
            if p.annotation is not inspect.Parameter.empty
        }

        # Extract path parameter names from template
        self.path_param_names = set(
            re.findall(r"\{(\w+)\}", path_template)
        )

        # Build regex to extract path param values
        pattern = re.sub(
            r"\{(\w+)(?::\w+)?\}", r"(?P<\1>[^/]+)", path_template
        )
        self.path_regex = re.compile(f"^{pattern}$")

    def extract_path_params(self, actual_path: str) -> dict[str, str] | None:
        """Extract path parameter values from an actual request path.

        Returns a dict of param names to string values, or None if no match.
        """
        match = self.path_regex.match(actual_path)
        if not match:
            return None
        return match.groupdict()

    async def inject(self, request: Request) -> dict[str, Any]:
        """Build the kwargs dict to call the handler with."""
        kwargs: dict[str, Any] = {}
        path_params_raw = self.extract_path_params(request.path) or {}
        query_params = self._parse_query_params(request)

        for name, param in self.sig.parameters.items():
            annotation = self.hints.get(name, param.annotation)

            # 1. Request object itself
            if annotation is Request or name == "request":
                kwargs[name] = request
                continue

            # 2. Depends() — call the dependency function
            if isinstance(param.default, Depends):
                dep_func = param.default.dependency
                dep_sig = inspect.signature(dep_func)
                dep_kwargs: dict[str, Any] = {}
                for dep_name, dep_param in dep_sig.parameters.items():
                    dep_ann = dep_param.annotation
                    if dep_ann is Request or dep_name == "request":
                        dep_kwargs[dep_name] = request
                result = dep_func(**dep_kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                kwargs[name] = result
                continue

            # 3. Body model — annotation is a BaseModel subclass
            if (
                isinstance(annotation, type)
                and issubclass(annotation, BaseModel)
            ):
                body_data = await request.json()
                kwargs[name] = annotation(**body_data)
                continue

            # 4. Path parameter
            if name in self.path_param_names and name in path_params_raw:
                raw_value = path_params_raw[name]
                kwargs[name] = self._coerce(raw_value, annotation)
                continue

            # 5. Query parameter
            if name in query_params:
                kwargs[name] = self._coerce(query_params[name], annotation)
                continue

            # 6. Use default value if available
            if param.default is not inspect.Parameter.empty:
                kwargs[name] = param.default
                continue

        return kwargs

    async def call(self, request: Request) -> Any:
        """Inject parameters and call the handler."""
        kwargs = await self.inject(request)
        result = self.handler(**kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return result

    @staticmethod
    def _parse_query_params(request: Request) -> dict[str, str]:
        """Parse query string into a single-value dict."""
        parsed = parse_qs(request.query_string)
        return {k: v[0] for k, v in parsed.items()}

    @staticmethod
    def _coerce(value: str, annotation: Any) -> Any:
        """Coerce a string value to the annotated type."""
        if annotation is inspect.Parameter.empty or annotation is str:
            return value
        if annotation is int:
            return int(value)
        if annotation is float:
            return float(value)
        if annotation is bool:
            return value.lower() in ("true", "1", "yes")
        return value
