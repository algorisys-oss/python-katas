# Python Katas -- Build Plan

> Core Python mastery → Build a FastAPI-like framework from scratch, step by step.
> Reference: [node-byowf](~/lab/tutorial/node-byowf) (59 steps, "Blaze" -- Phoenix+LiveView clone for Node.js)

## Conventions

- Framework name: **Ignite** (Python edition)
- Each kata = 1 markdown tutorial in `tutorial/` with live runnable code
- Tutorial format: explanation + inline playground (runnable code blocks with expected output)
- Zero external dependencies for Module 1 (pure stdlib)
- Python 3.12+ (modern features: type hints, match statements, dataclasses, etc.)
- Each tutorial file: `NN-topic-name.md`

---

## Progress

### Module 1: Pythonic Foundations

- [x] 00 — Project Setup (venv, pyproject.toml, project structure, .gitignore)
- [x] 01 — Python Data Model (`__repr__`, `__str__`, `__eq__`, `__hash__`, `__len__`, `__getitem__`)
- [x] 02 — Iterators & Generators (`__iter__`, `__next__`, `yield`, generator expressions, `itertools`)
- [x] 03 — Decorators Deep Dive (function decorators, `@wraps`, decorator factories, stacking, class decorators)
- [x] 04 — Context Managers (`__enter__`/`__exit__`, `@contextmanager`, async context managers)
- [x] 05 — Comprehensions & Functional Style (list/dict/set comprehensions, `map`, `filter`, `reduce`, when to use what)
- [x] 06 — Type Hints & Protocols (`typing` module, generics, `Protocol`, `TypeVar`, `ParamSpec`, runtime vs static)
- [x] 07 — Dataclasses & Attrs (`@dataclass`, `field()`, `__post_init__`, frozen, slots, ordering)
- [x] 08 — Enums & Pattern Matching (`enum.Enum`, `StrEnum`, `match/case`, structural pattern matching)
- [x] 09 — Error Handling Done Right (custom exceptions, exception groups, `ExceptionGroup`, `except*`)
- [x] 10 — Closures, Scoping & First-Class Functions (LEGB rule, `nonlocal`, partial, higher-order functions)

**Milestone:** Fluent in idiomatic Python -- data model, generators, decorators, type system.

### Module 2: OOP & SOLID Principles

- [x] 11 — Classes & Inheritance (MRO, `super()`, mixins, `__init_subclass__`)
- [x] 12 — Properties & Descriptors (`@property`, `__get__`/`__set__`/`__set_name__`, computed attributes)
- [x] 13 — Metaclasses & `__init_subclass__` (class creation hooks, registry pattern, when to avoid metaclasses)
- [x] 14 — Abstract Base Classes (`abc.ABC`, `@abstractmethod`, virtual subclasses, `__subclasshook__`)
- [x] 15 — Single Responsibility Principle (SRP with real examples, refactoring a god class)
- [x] 16 — Open/Closed Principle (extending behavior without modification, strategy pattern)
- [x] 17 — Liskov Substitution Principle (behavioral subtyping, contract enforcement)
- [x] 18 — Interface Segregation Principle (Protocols over fat ABCs, role interfaces)
- [x] 19 — Dependency Inversion Principle (dependency injection, inversion of control)
- [x] 20 — Design Patterns in Python (factory, strategy, observer, singleton -- Pythonic implementations)

**Milestone:** SOLID principles applied in Python, using protocols and descriptors instead of Java-style patterns.

### Module 3: Concurrency & Parallelism

- [x] 21 — Threading Basics (`threading.Thread`, `Lock`, `RLock`, `Event`, `Condition`, daemon threads)
- [x] 22 — The GIL Explained (what it is, why it exists, what it blocks, CPU-bound vs I/O-bound, per-thread state)
- [x] 23 — Thread Synchronization (producer-consumer with `Queue`, `Semaphore`, `Barrier`, deadlock avoidance)
- [x] 24 — Multiprocessing (`Process`, `Pool`, `Queue`, `Pipe`, shared memory, `Value`/`Array`)
- [x] 25 — `concurrent.futures` (`ThreadPoolExecutor`, `ProcessPoolExecutor`, `as_completed`, `map`)
- [x] 26 — Async/Await Fundamentals (`asyncio`, event loop, coroutines, `async def`, `await`, `gather`)
- [x] 27 — Async I/O Patterns (`aiohttp`, `asyncio.Queue`, semaphore-limited concurrency, cancellation)
- [x] 28 — Async Iterators & Generators (`async for`, `async with`, `__aiter__`/`__anext__`, async comprehensions)
- [x] 29 — Subinterpreters (PEP 734, `interpreters` module, true parallelism without multiprocessing overhead)
- [x] 30 — Free-Threaded Python (PEP 703, no-GIL builds, `python3.13t`, thread safety implications)

**Milestone:** Deep understanding of Python concurrency -- GIL, threading, multiprocessing, async, and the future (no-GIL).

### Module 4: Advanced Language Features

- [x] 31 — `__slots__` & Memory Optimization (memory layout, `__slots__` vs `__dict__`, weakref compatibility)
- [x] 32 — Import System & Modules (`importlib`, relative imports, `__all__`, lazy imports, import hooks)
- [x] 33 — Logging & Debugging (`logging` module, handlers, formatters, filters, `breakpoint()`, `pdb`)
- [x] 34 — Testing with pytest (fixtures, parametrize, markers, mocking, `conftest.py`, test organization)
- [x] 35 — Packaging & Distribution (`pyproject.toml`, `setuptools`, `hatch`, entry points, publishing)

**Milestone:** Professional Python developer toolchain -- testing, packaging, debugging.

---

### Module 5: HTTP Foundations (Build Ignite Framework)

- [x] 36 — TCP Socket Server (`socket` module, raw TCP, parse HTTP request bytes, send HTTP response)
- [x] 37 — ASGI Primer (ASGI spec, scope/receive/send, lifespan events, why not WSGI)
- [x] 38 — ASGI App Skeleton (bare-bones ASGI app callable, uvicorn integration, "Hello, Ignite!")
- [x] 39 — Request Object (`Request` class wrapping ASGI scope/receive, headers, query params, body parsing)
- [x] 40 — Response Object (`Response`, `JSONResponse`, `HTMLResponse`, `RedirectResponse`, streaming)
- [x] 41 — Router (path registration, method dispatch, 404/405 handling)
- [x] 42 — Path Parameters (`/users/{user_id}` extraction, type coercion, regex patterns)
- [x] 43 — Middleware Pipeline (ASGI middleware pattern, composable wrappers, request/response hooks)
- [x] 44 — Dependency Injection System (FastAPI-style `Depends()`, resolution graph, caching, overrides)
- [x] 45 — Request Body & Validation (JSON body parsing, Pydantic-style validation, type coercion from annotations)
- [x] 46 — Query Parameter Parsing (type-annotated query params, defaults, lists, optional values)
- [x] 47 — Response Models (output serialization, field filtering, nested models)
- [x] 48 — Error Handling & Exception Handlers (HTTPException, custom handlers, validation error formatting)

**Milestone:** Complete HTTP framework with routing, middleware, DI, validation -- all on ASGI.

### Module 6: Decorator-Driven API Design

- [x] 49 — `@app.get()` / `@app.post()` Decorators (route decorators, method registration, OpenAPI metadata)
- [x] 50 — Automatic Parameter Injection (inspect function signatures, inject path/query/body/depends params)
- [x] 51 — Type-Driven Validation (use annotations + descriptors for automatic request validation)
- [x] 52 — OpenAPI Schema Generation (auto-generate `/docs` JSON schema from route metadata)
- [x] 53 — Swagger UI Integration (serve interactive API docs at `/docs`, ReDoc at `/redoc`)

**Milestone:** FastAPI-style decorator API with automatic docs generation.

### Module 7: Data Layer

- [x] 54 — SQLite Integration (`sqlite3` stdlib, connection management, parameterized queries)
- [x] 55 — Repository Pattern (data access abstraction, CRUD operations, async support)
- [x] 56 — Migrations (schema versioning, up/down migrations, migration runner CLI)
- [x] 57 — Query Builder (chainable `.where()`, `.order_by()`, `.limit()` → parameterized SQL)

**Milestone:** Clean data layer with migrations and query builder.

### Module 8: WebSocket Support

- [x] 58 — WebSocket Protocol (upgrade handshake, frame parsing, masking, opcodes)
- [x] 59 — ASGI WebSocket (WebSocket scope, accept/receive/send/close lifecycle)
- [x] 60 — WebSocket Routes & Handlers (`@app.websocket()`, connection manager, broadcast)
- [x] 61 — PubSub System (topic-based in-memory pub/sub, subscribe/publish/unsubscribe)

**Milestone:** Real-time WebSocket support with pub/sub broadcasting.

### Module 9: Security & Sessions

- [x] 62 — Cookie Handling (set/get/delete cookies, secure flags, SameSite)
- [x] 63 — Session Middleware (signed cookie sessions, `hmac`, session storage backends)
- [x] 64 — CORS Middleware (preflight handling, configurable origins/methods/headers)
- [x] 65 — CSRF Protection (token generation, form validation, double-submit pattern)
- [x] 66 — Authentication (JWT basics, `PyJWT`, protected routes, current user injection via Depends)

**Milestone:** Production security -- sessions, CORS, CSRF, auth.

### Module 10: Developer Experience

- [x] 67 — Hot Reload (file watcher, server restart on change, `watchfiles` integration)
- [x] 68 — Debug Error Page (rich traceback, local variables, request context)
- [x] 69 — Structured Logging (JSON logger, request ID via `contextvars`, timing middleware)
- [x] 70 — CLI Tool (`click` or `argparse` -- `ignite run`, `ignite routes`, `ignite migrate`)
- [x] 71 — Static Files (serve `static/` directory, MIME type detection, cache headers)
- [x] 72 — Template Rendering (Jinja2-style template engine, template inheritance, filters)

**Milestone:** Professional DX -- hot reload, error pages, CLI, templates.

### Module 11: Production

- [x] 73 — Health Check (`/health` endpoint, readiness/liveness probes)
- [x] 74 — Rate Limiting (sliding window per IP, `X-RateLimit-*` headers, 429)
- [x] 75 — Background Tasks (after-response tasks, `asyncio.create_task`, task queues)
- [x] 76 — Testing Utilities (test client, dependency overrides, fixture patterns)

**Milestone:** Production-ready framework with testing, rate limiting, background tasks.

### Module 12: Capstone

- [x] 77 — Todo API (full CRUD REST API using Ignite, demonstrating all framework features)
- [x] 78 — Real-Time Chat (WebSocket chat app with rooms, presence, message history)

**Milestone:** Complete framework demonstrated with real applications.

### Module 13: Advanced HTTP

- [x] 79 — Multipart Form Parsing (boundary protocol, Content-Disposition, from-scratch parser, text vs file fields)
- [x] 80 — File Upload Handling (UploadFile class, SpooledTemporaryFile, validation, streaming, safe save)

**Milestone:** Multipart parsing and file upload — essential for real-world APIs.

---

## Summary

| Module | Katas | Description |
|--------|-------|-------------|
| 1. Pythonic Foundations | 00–10 | Data model, generators, decorators, types |
| 2. OOP & SOLID | 11–20 | Classes, descriptors, metaclasses, SOLID principles |
| 3. Concurrency | 21–30 | Threading, GIL, multiprocessing, async, no-GIL |
| 4. Advanced Features | 31–35 | Memory, imports, testing, packaging |
| 5. HTTP Foundations | 36–48 | TCP, ASGI, routing, middleware, DI, validation |
| 6. Decorator API | 49–53 | FastAPI-style decorators, OpenAPI, Swagger |
| 7. Data Layer | 54–57 | SQLite, repository, migrations, query builder |
| 8. WebSocket | 58–61 | WS protocol, ASGI WS, pub/sub |
| 9. Security | 62–66 | Cookies, sessions, CORS, CSRF, auth |
| 10. DX | 67–72 | Hot reload, error pages, CLI, templates |
| 11. Production | 73–76 | Health, rate limiting, background tasks, testing |
| 12. Capstone | 77–78 | Todo API + real-time chat |
| 13. Advanced HTTP | 79–80 | Multipart parsing, file uploads |
| **Total** | **00–80** | **81 katas** |

---

## Dependency Strategy

| Dependency | Introduced at | Purpose | Why allowed |
|-----------|--------------|---------|-------------|
| — (none) | Katas 00–35 | Pure stdlib | Learn Python internals |
| `uvicorn` | Kata 38 | ASGI server | Standard ASGI server, like uvloop-powered |
| `pydantic` | Kata 45 | Validation reference | Study its approach, then build our own |
| `pytest` | Kata 34 | Testing | Standard Python test framework |
| `watchfiles` | Kata 67 | File watching | Rust-powered, fast |
| `PyJWT` | Kata 66 | JWT tokens | Standard JWT library |
| `click` | Kata 70 | CLI framework | Standard CLI library |
| `jinja2` | Kata 72 | Templates (reference) | Study, then build minimal engine |
