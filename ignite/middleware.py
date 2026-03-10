"""Ignite Middleware — composable ASGI middleware layers."""

from __future__ import annotations

from typing import Any, Callable


# Type aliases for ASGI
Scope = dict[str, Any]
Receive = Callable[..., Any]
Send = Callable[..., Any]
ASGIApp = Callable[..., Any]


class Middleware:
    """Base ASGI middleware class.

    The onion model: each middleware wraps the next app. A request passes
    through middlewares outside-in, and the response passes back inside-out.

        Request -->  [CORS]  -->  [Timing]  -->  [Logging]  -->  App
        Response <-- [CORS]  <--  [Timing]  <--  [Logging]  <--  App

    Each middleware can:
    - Inspect/modify the request before calling the inner app
    - Inspect/modify the response after the inner app returns
    - Short-circuit by not calling the inner app at all

    Subclass and override __call__ to add behavior.
    """

    def __init__(self, app: ASGIApp, **kwargs: Any) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Default: pass through to the inner app."""
        await self.app(scope, receive, send)


class MiddlewareStack:
    """Composes multiple middlewares around an app.

    Middlewares are applied in order: the first added is the outermost.
    This creates the onion-layer pattern.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._middleware_classes: list[tuple[type, dict[str, Any]]] = []

    def add(
        self, middleware_cls: type, **kwargs: Any
    ) -> "MiddlewareStack":
        """Add a middleware class (with optional kwargs) to the stack."""
        self._middleware_classes.append((middleware_cls, kwargs))
        return self

    def build(self) -> ASGIApp:
        """Build the composed app by wrapping middlewares outside-in.

        If we add [A, B, C], the call order is: A -> B -> C -> app.
        So we wrap in reverse: app = C(app), app = B(app), app = A(app).
        """
        app = self.app
        for cls, kwargs in reversed(self._middleware_classes):
            app = cls(app, **kwargs)
        return app
