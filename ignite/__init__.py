"""Ignite — a minimal ASGI web framework for learning.

Usage:
    from ignite import Ignite, Request, Response, JSONResponse, HTMLResponse
    from ignite import Depends, HTTPException, BaseModel

    app = Ignite()

    @app.get("/")
    async def index():
        return {"message": "Hello, Ignite!"}

    # Run with: uvicorn myapp:app --reload
"""

from .app import Ignite
from .depends import Depends, DependencyResolver
from .exceptions import (
    BadRequest,
    ExceptionHandlerRegistry,
    Forbidden,
    HTTPException,
    NotFound,
    Unauthorized,
)
from .middleware import Middleware, MiddlewareStack
from .params import ParameterInjector
from .request import Request
from .response import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from .routing import Route, Router
from .validation import BaseModel, Field, ValidationError

__all__ = [
    # App
    "Ignite",
    # Request / Response
    "Request",
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "PlainTextResponse",
    "RedirectResponse",
    "StreamingResponse",
    # Routing
    "Router",
    "Route",
    # Middleware
    "Middleware",
    "MiddlewareStack",
    # Dependency Injection
    "Depends",
    "DependencyResolver",
    # Exceptions
    "HTTPException",
    "NotFound",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "ExceptionHandlerRegistry",
    # Validation
    "BaseModel",
    "Field",
    "ValidationError",
    # Params
    "ParameterInjector",
]
