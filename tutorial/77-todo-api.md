# Kata 77 -- Todo API (Capstone 1)

[prev: 76-testing-utilities](./76-testing-utilities.md) | [next: 78-realtime-chat](./78-realtime-chat.md)

---

## What We're Building

A **complete Todo REST API** -- our first capstone project that brings together every Ignite feature we've built across the previous katas. This is a real-world-style CRUD application with:

- **Route decorators** (`@app.get`, `@app.post`, `@app.put`, `@app.delete`)
- **Path parameters** (`/todos/{id}`)
- **Query parameters** (`?done=true&limit=10&offset=0`)
- **Request body validation** (title required, non-empty)
- **SQLite repository** (persistent storage with CRUD operations)
- **Error handling** (404, 422 with structured error responses)
- **Middleware** (request logging, CORS)
- **Dependency injection** (repository injected into handlers)
- **Health checks** (`/health` endpoint)
- **TestClient** (comprehensive testing without a real server)

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| App factory | `create_app()` function that wires everything | Configurable app creation |
| Repository pattern | Database operations behind a clean interface | Decoupling data access |
| CRUD endpoints | Create, Read, Update, Delete operations | Standard REST APIs |
| Path param matching | `/todos/{id}` extracts the ID | Resource-specific routes |
| Query filtering | `?done=true` filters results | List endpoints |
| Pagination | `?limit=10&offset=20` | Large result sets |
| Full workflow test | End-to-end test of the complete API | Integration testing |

## The Code

### 1. App Factory

```python
def create_app(db_path=":memory:"):
    app = IgniteApp()

    repo = TodoRepository(db_path)
    app.dependency("todo_repo", lambda: repo)

    app.add_middleware(logging_middleware)
    app.add_middleware(cors_middleware)

    app.health_check("database", lambda: {"status": "healthy"})

    register_todo_routes(app)
    return app
```

### 2. Todo Repository

```python
class TodoRepository:
    def list_all(self, *, done=None, limit=100, offset=0):
        query = "SELECT * FROM todos"
        if done is not None:
            query += " WHERE done = ?"
        query += " ORDER BY id LIMIT ? OFFSET ?"
        ...

    def create(self, title, description=""):
        cursor = self.conn.execute(
            "INSERT INTO todos (title, description) VALUES (?, ?)", ...)
        return self.get_by_id(cursor.lastrowid)

    def update(self, todo_id, **fields): ...
    def delete(self, todo_id): ...
```

### 3. Route Handlers

```python
@app.post("/todos")
def create_todo(request):
    body = request.body or {}
    if "title" not in body or not body["title"].strip():
        raise HTTPException(422, "title is required")
    repo = app.resolve("todo_repo")
    todo = repo.create(body["title"], body.get("description", ""))
    return Response(status_code=201, body=todo)

@app.get("/todos/{id}")
def get_todo(request):
    todo_id = int(request.path_params["id"])
    todo = repo.get_by_id(todo_id)
    if todo is None:
        raise HTTPException(404, f"Todo {todo_id} not found")
    return Response(status_code=200, body=todo)
```

## Playground

```bash
python playground/77_todo_api.py
```

Expected output:

```
--- Section 1: Create Todos ---
  POST /todos -> 201: {'id': 1, 'title': 'Buy groceries', ...}
  Missing title -> 422: title is required and cannot be empty
  Empty title -> 422
  [PASS] Create todos works

--- Section 2: List Todos ---
  All todos: 3 items
  Done todos: 1 items
  Pending todos: 2 items
  Page 1 (limit=2): 2 items
  [PASS] List todos works

--- Section 3-8: Get, Update, Delete, Middleware, Health, Workflow ---
  [PASS] All sections pass

All 8 sections passed. Todo API capstone complete!
```

## How It Works

### API Endpoints

```
GET    /todos          List all todos (with filtering/pagination)
POST   /todos          Create a new todo
GET    /todos/{id}     Get a specific todo
PUT    /todos/{id}     Update a todo
DELETE /todos/{id}     Delete a todo
GET    /health         Health check
```

### Request Flow

```
Client Request
     |
     v
Logging Middleware  -> logs "POST /todos"
     |
     v
CORS Middleware     -> handles OPTIONS preflight
     |
     v
Route Matching      -> matches /todos/{id} pattern
     |                 extracts path_params: {id: "42"}
     v
Route Handler       -> resolves todo_repo dependency
     |                 validates request body
     |                 calls repository method
     v
Response            -> 200/201/204 with JSON body
                       or 404/422 error response
```

### Full Workflow

```
1. GET /todos           -> [] (empty)
2. POST /todos x3       -> create 3 todos
3. GET /todos           -> [{...}, {...}, {...}]
4. GET /todos/1         -> {id: 1, title: "Learn Python"}
5. PUT /todos/1 {done}  -> {done: true}
6. GET /todos?done=true -> [{id: 1, ...}]
7. DELETE /todos/3      -> 204
8. GET /health          -> {status: "healthy"}
```

## Exercises

1. **Add search** -- implement `GET /todos?search=python` that searches in both title and description using SQL LIKE.

2. **Add sorting** -- support `?sort=created_at&order=desc` query parameters.

3. **Add tags** -- create a `tags` table with a many-to-many relationship. Support `POST /todos` with `tags: ["work", "urgent"]` and `GET /todos?tag=work`.

4. **Add authentication** -- require an API key in the `Authorization` header. Different keys have different permissions (read-only vs read-write).

5. **Add batch operations** -- implement `POST /todos/batch` to create multiple todos at once, and `DELETE /todos/batch` to delete multiple by IDs.

## What's Next

With the Todo API capstone complete, you've seen how all the Ignite framework pieces fit together in a real application. In [Kata 78: Real-Time Chat](./78-realtime-chat.md), our final capstone, we'll combine HTTP routes with WebSocket communication to build a real-time chat system with rooms, presence, and message history.

---

[prev: 76-testing-utilities](./76-testing-utilities.md) | [next: 78-realtime-chat](./78-realtime-chat.md)
