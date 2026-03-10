"""Ignite App — the main ASGI application class."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from .depends import Depends, DependencyResolver
from .exceptions import ExceptionHandlerRegistry, HTTPException
from .middleware import ASGIApp, MiddlewareStack
from .params import ParameterInjector
from .request import Request
from .response import JSONResponse, PlainTextResponse, Response
from .routing import Router, compile_path
from .validation import BaseModel, ValidationError


class Ignite:
    """A minimal ASGI web framework.

    This is the main entry point of the Ignite framework. It:
    - Is an ASGI callable (implements __call__)
    - Handles lifespan events (startup/shutdown)
    - Routes HTTP requests to handler functions
    - Supports path parameters, query params, and body parsing
    - Provides dependency injection via Depends()
    - Catches exceptions and maps them to error responses
    - Supports middleware composition

    Usage with uvicorn:
        app = Ignite()

        @app.get("/")
        async def index():
            return {"message": "Hello, Ignite!"}

        # Terminal: uvicorn myapp:app --reload
    """

    def __init__(self, title: str = "Ignite API", version: str = "0.1.0") -> None:
        self.title = title
        self.version = version

        # Core components
        self.router = Router()
        self.dependency_resolver = DependencyResolver()
        self.exception_handlers = ExceptionHandlerRegistry()
        self._middleware_stack = MiddlewareStack(self._handle_request)

        # Lifespan event handlers
        self._on_startup: list[Callable] = []
        self._on_shutdown: list[Callable] = []

        # Shared application state (available during lifespan)
        self.state: dict[str, Any] = {}

        # Injectors keyed by handler function for param injection
        self._injectors: dict[Callable, ParameterInjector] = {}

        # Built ASGI app (with middleware). None until first request.
        self._app: ASGIApp | None = None

    # =========================================================================
    # ASGI Interface
    # =========================================================================

    async def __call__(
        self, scope: dict[str, Any], receive: Callable, send: Callable
    ) -> None:
        """ASGI entry point — called by the server for every connection."""
        scope_type = scope["type"]

        if scope_type == "lifespan":
            await self._handle_lifespan(scope, receive, send)
        elif scope_type == "http":
            # Build middleware-wrapped app on first request
            if self._app is None:
                self._app = self._middleware_stack.build()
            await self._app(scope, receive, send)
        # Ignore unknown scope types (websocket, etc.)

    # =========================================================================
    # Lifespan Handling
    # =========================================================================

    async def _handle_lifespan(
        self, scope: dict, receive: Callable, send: Callable
    ) -> None:
        """Handle ASGI lifespan events (startup/shutdown)."""
        while True:
            message = await receive()

            if message["type"] == "lifespan.startup":
                try:
                    for handler in self._on_startup:
                        result = handler(self.state)
                        if asyncio.iscoroutine(result):
                            await result
                    await send({"type": "lifespan.startup.complete"})
                except Exception as exc:
                    await send({
                        "type": "lifespan.startup.failed",
                        "message": str(exc),
                    })
                    return

            elif message["type"] == "lifespan.shutdown":
                try:
                    for handler in self._on_shutdown:
                        result = handler(self.state)
                        if asyncio.iscoroutine(result):
                            await result
                    await send({"type": "lifespan.shutdown.complete"})
                except Exception:
                    await send({"type": "lifespan.shutdown.complete"})
                return

    # =========================================================================
    # HTTP Request Handling (core ASGI app before middleware)
    # =========================================================================

    async def _handle_request(
        self, scope: dict[str, Any], receive: Callable, send: Callable
    ) -> None:
        """Handle an HTTP request: route, inject params, call handler."""
        request = Request(scope, receive)

        try:
            response = await self._dispatch(request)
        except Exception as exc:
            response = self.exception_handlers.handle(request, exc)

        await response(scope, receive, send)

    async def _dispatch(self, request: Request) -> Response:
        """Route the request and call the handler with injected params."""
        method = request.method
        path = request.path

        # Find matching route
        result = self.router.resolve(method, path)

        if result is None:
            # Check for 405
            routes_for_path = self.router._find_routes_for_path(path)
            if routes_for_path:
                allowed = sorted(set(r.method for r in routes_for_path))
                raise HTTPException(
                    405,
                    detail=f"{method} {path} not allowed. "
                           f"Allowed: {', '.join(allowed)}",
                    headers={"allow": ", ".join(allowed)},
                )
            raise HTTPException(404, detail=f"{path} not found")

        route, path_params = result
        request.path_params = path_params
        handler = route.handler

        # Use parameter injector if registered for this handler
        injector = self._injectors.get(handler)
        if injector is not None:
            handler_result = await injector.call(request)
        else:
            # Simple call: just pass request if handler accepts it
            handler_result = handler(request)
            if asyncio.iscoroutine(handler_result):
                handler_result = await handler_result

        # Convert handler return value to a Response
        return self._make_response(handler_result)

    @staticmethod
    def _make_response(result: Any) -> Response:
        """Convert a handler's return value into a proper Response."""
        if isinstance(result, Response):
            return result

        if isinstance(result, dict) or isinstance(result, list):
            return JSONResponse(content=result)

        if isinstance(result, BaseModel):
            return JSONResponse(content=result.model_dump())

        if isinstance(result, bytes):
            return Response(
                content=result, media_type="application/octet-stream"
            )

        # String or other -> plain text
        return PlainTextResponse(content=str(result))

    # =========================================================================
    # Route Decorators
    # =========================================================================

    def _route_decorator(
        self, path: str, method: str
    ) -> Callable:
        """Internal factory that builds the actual decorator."""
        def decorator(func: Callable) -> Callable:
            self.router.add_route(method, path, func)
            # Create a parameter injector for automatic param resolution
            self._injectors[func] = ParameterInjector(path, func)
            return func
        return decorator

    def get(self, path: str) -> Callable:
        """Register a GET route handler.

        Usage:
            @app.get("/users")
            async def list_users():
                return {"users": []}
        """
        return self._route_decorator(path, "GET")

    def post(self, path: str) -> Callable:
        """Register a POST route handler."""
        return self._route_decorator(path, "POST")

    def put(self, path: str) -> Callable:
        """Register a PUT route handler."""
        return self._route_decorator(path, "PUT")

    def delete(self, path: str) -> Callable:
        """Register a DELETE route handler."""
        return self._route_decorator(path, "DELETE")

    def patch(self, path: str) -> Callable:
        """Register a PATCH route handler."""
        return self._route_decorator(path, "PATCH")

    def route(
        self, path: str, methods: list[str] | None = None
    ) -> Callable:
        """Register a route for one or more HTTP methods.

        Usage:
            @app.route("/items", methods=["GET", "POST"])
            async def items(request: Request):
                ...
        """
        if methods is None:
            methods = ["GET"]

        def decorator(func: Callable) -> Callable:
            for method in methods:
                self.router.add_route(method, path, func)
            self._injectors[func] = ParameterInjector(path, func)
            return func
        return decorator

    # =========================================================================
    # Middleware Registration
    # =========================================================================

    def add_middleware(self, middleware_cls: type, **kwargs: Any) -> None:
        """Add a middleware class to the stack.

        Usage:
            app.add_middleware(CORSMiddleware, allow_origins=["*"])
        """
        self._middleware_stack.add(middleware_cls, **kwargs)
        # Reset built app so middleware is included on next request
        self._app = None

    # =========================================================================
    # Exception Handler Registration
    # =========================================================================

    def add_exception_handler(
        self, exc_class: type, handler: Callable
    ) -> None:
        """Register a custom exception handler.

        Usage:
            def handle_value_error(request, exc):
                return JSONResponse({"error": str(exc)}, status_code=400)

            app.add_exception_handler(ValueError, handle_value_error)
        """
        self.exception_handlers.add(exc_class, handler)

    # =========================================================================
    # Lifespan Event Registration
    # =========================================================================

    def on_startup(self, func: Callable) -> Callable:
        """Register a startup handler.

        Usage:
            @app.on_startup
            async def startup(state):
                state["db"] = await connect_db()
        """
        self._on_startup.append(func)
        return func

    def on_shutdown(self, func: Callable) -> Callable:
        """Register a shutdown handler.

        Usage:
            @app.on_shutdown
            async def shutdown(state):
                await state["db"].close()
        """
        self._on_shutdown.append(func)
        return func
