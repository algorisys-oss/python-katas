# Run: uvicorn demo_app:app --port 8000
#
# Demo application showcasing the Ignite framework.
# Demonstrates routes with path params, JSON responses, HTML responses,
# error handling, middleware, models, authentication, and health checks.

from __future__ import annotations

from ignite import Ignite, JSONResponse, HTMLResponse, Depends, HTTPException, BaseModel
from ignite.auth import create_token, verify_token, AuthMiddleware
from ignite.cors import CORSMiddleware
from ignite.health import HealthCheckRegistry, HealthStatus, CheckResult
from ignite.database import Database, Query
from ignite.templating import TemplateEngine

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = Ignite()

# -- CORS middleware (allow all origins for the demo) -----------------------
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# -- Secrets ----------------------------------------------------------------
JWT_SECRET = "demo-secret-do-not-use-in-production"

# -- Template engine --------------------------------------------------------
templates = TemplateEngine()

# -- In-memory database -----------------------------------------------------
db = Database(":memory:")
with db.get_cursor() as cur:
    cur.execute("""
        CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0
        )
    """)
    cur.execute("INSERT INTO items (name, price) VALUES ('Widget', 9.99)")
    cur.execute("INSERT INTO items (name, price) VALUES ('Gadget', 24.50)")
    cur.execute("INSERT INTO items (name, price) VALUES ('Doohickey', 4.75)")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ItemModel(BaseModel):
    name: str
    price: float = 0.0


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

health = HealthCheckRegistry()


def _db_health() -> CheckResult:
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT 1")
        return CheckResult(name="database", status=HealthStatus.HEALTHY)
    except Exception as exc:
        return CheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            details={"error": str(exc)},
        )


health.register("database", _db_health, liveness=True, readiness=True)


# Register health endpoints via the framework router if available,
# otherwise define them manually below.
@app.get("/health")
async def health_endpoint():
    report = health.run_all()
    return JSONResponse(report.to_dict(), status_code=report.http_status_code)


@app.get("/health/live")
async def health_live():
    report = health.run_liveness()
    return JSONResponse(report.to_dict(), status_code=report.http_status_code)


@app.get("/health/ready")
async def health_ready():
    report = health.run_readiness()
    return JSONResponse(report.to_dict(), status_code=report.http_status_code)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def home():
    """Serve a simple HTML landing page."""
    html = templates.render(
        """<!DOCTYPE html>
<html>
<head><title>Ignite Demo</title></head>
<body>
  <h1>Welcome to Ignite!</h1>
  <p>A lightweight Python ASGI framework.</p>
  <h2>Available endpoints</h2>
  <ul>
    <li><code>GET /</code> -- this page</li>
    <li><code>GET /api/hello/{name}</code> -- greeting</li>
    <li><code>GET /api/items</code> -- list items</li>
    <li><code>POST /api/items</code> -- create item (JSON body)</li>
    <li><code>GET /api/items/{id}</code> -- get item by id</li>
    <li><code>POST /auth/login</code> -- obtain JWT</li>
    <li><code>GET /auth/me</code> -- current user (requires Bearer token)</li>
    <li><code>GET /health</code> -- health check</li>
  </ul>
</body>
</html>"""
    )
    return HTMLResponse(html)


@app.get("/api/hello/{name}")
async def hello(name: str):
    """Greet a user by name (path parameter)."""
    return {"message": f"Hello, {name}!"}


# -- Items CRUD (backed by SQLite) -----------------------------------------

@app.get("/api/items")
async def list_items():
    """List all items from the database."""
    rows = Query("items").select("id", "name", "price").execute(db)
    return {"items": rows}


@app.get("/api/items/{item_id}")
async def get_item(item_id: str):
    """Get a single item by id."""
    rows = Query("items").where("id", int(item_id)).execute(db)
    if not rows:
        raise HTTPException(status_code=404, detail="Item not found")
    return rows[0]


@app.post("/api/items")
async def create_item(body: dict):
    """Create a new item. Expects JSON: {"name": "...", "price": 1.23}."""
    name = body.get("name")
    price = body.get("price", 0.0)
    if not name:
        raise HTTPException(status_code=422, detail="name is required")
    result = Query("items").insert(name=name, price=float(price)).execute(db)
    new_id = result[0]["lastrowid"]
    return JSONResponse(
        {"id": new_id, "name": name, "price": price},
        status_code=201,
    )


# -- Authentication --------------------------------------------------------

@app.post("/auth/login")
async def login(body: dict):
    """Authenticate and return a JWT.

    For the demo, any username/password combination is accepted.
    """
    username = body.get("username", "")
    if not username:
        raise HTTPException(status_code=422, detail="username is required")

    token = create_token(
        {"sub": username, "username": username, "role": "user"},
        JWT_SECRET,
        expires_in=3600,
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me")
async def me(request):
    """Return the currently authenticated user.

    Requires an ``Authorization: Bearer <token>`` header.
    """
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    payload = verify_token(auth[7:], JWT_SECRET)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "username": payload.get("username"),
        "role": payload.get("role"),
    }


# -- Error demonstration ---------------------------------------------------

@app.get("/error")
async def trigger_error():
    """Deliberately raise an error to show framework error handling."""
    raise HTTPException(status_code=500, detail="Something went wrong!")


# ---------------------------------------------------------------------------
# Entry point (for ``python demo_app.py`` convenience)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Start with:  uvicorn demo_app:app --port 8000")
    print("Or:          python -m uvicorn demo_app:app --port 8000")
