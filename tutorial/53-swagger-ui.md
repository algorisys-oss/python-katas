# Kata 53 -- Swagger UI Integration

[prev: 52-openapi-schema](./52-openapi-schema.md) | [next: 54-sqlite-integration](./54-sqlite-integration.md)

---

## What We're Building

**Interactive API documentation** served directly from our framework. We build three built-in endpoints:

- **`/openapi.json`** -- serves the OpenAPI spec as JSON
- **`/docs`** -- serves Swagger UI (interactive API explorer)
- **`/redoc`** -- serves ReDoc (clean three-panel documentation)

```python
app = IgniteApp(
    title="User API",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc
    openapi_url="/openapi.json",  # Schema endpoint
)
```

Both Swagger UI and ReDoc are loaded from CDN -- we only generate the HTML wrapper that points to our schema URL. Since we cannot serve real pages in a subprocess, we test by verifying the HTML output contains correct schema references.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Swagger UI | Interactive API explorer with "Try it out" | Developer testing |
| ReDoc | Clean three-panel documentation | Public API docs |
| HTML generation | Build HTML pages with f-strings | Serving static pages |
| CDN loading | Load JS/CSS from unpkg/redoc CDN | Zero local dependencies |
| Schema URL | Point docs to `/openapi.json` | Connecting docs to spec |
| Custom URLs | Configure `/api/docs` instead of `/docs` | URL namespacing |
| ASGI routing | Intercept docs paths before user routes | Built-in endpoints |

## The Code

### 1. Swagger UI HTML Template

```python
def generate_swagger_html(openapi_url="/openapi.json", title="API - Swagger UI"):
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
        SwaggerUIBundle({{
            url: "{openapi_url}",
            dom_id: '#swagger-ui',
            layout: "StandaloneLayout",
            deepLinking: true,
        }});
    </script>
</body>
</html>"""
```

Key details:
- Use `{{` and `}}` to escape braces inside the f-string (JavaScript needs literal braces)
- The `url` property tells Swagger UI where to fetch the OpenAPI spec
- CDN URLs point to versioned packages for stability

### 2. ReDoc HTML Template

```python
def generate_redoc_html(openapi_url="/openapi.json", title="API - ReDoc"):
    return f"""<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
    <redoc spec-url="{openapi_url}"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""
```

ReDoc uses a custom `<redoc>` element with a `spec-url` attribute -- much simpler than Swagger UI.

### 3. Docs Route Handler

```python
def _handle_docs_request(self, path):
    if path == self.openapi_url:
        return (200, "application/json", json.dumps(self.openapi()))
    elif path == self.docs_url:
        return (200, "text/html; charset=utf-8",
                generate_swagger_html(openapi_url=self.openapi_url))
    elif path == self.redoc_url:
        return (200, "text/html; charset=utf-8",
                generate_redoc_html(openapi_url=self.openapi_url))
    return None  # Not a docs route
```

### 4. ASGI Integration

```python
async def __call__(self, scope, receive, send):
    path = scope.get("path", "/")

    # Check docs routes FIRST (before user routes)
    docs_result = self._handle_docs_request(path)
    if docs_result:
        status, content_type, body = docs_result
        await send({"type": "http.response.start", "status": status, ...})
        await send({"type": "http.response.body", "body": body.encode()})
        return

    # Then dispatch to user routes...
```

## Playground

```bash
python playground/53_swagger_ui.py
```

Expected output:

```
--- Section 1: Swagger UI HTML ---
  HTML length: 1201 characters
  Contains swagger-ui div: True
  Contains CDN script: True
  Contains schema URL: True
  [PASS] Swagger UI HTML generation works

--- Section 2: ReDoc HTML ---
  HTML length: 523 characters
  Contains redoc element: True
  Contains spec-url: True
  Contains CDN script: True
  [PASS] ReDoc HTML generation works

--- Section 3: Custom URLs ---
  Custom schema URL: /api/v2/schema -> found in HTML
  [PASS] Custom URLs work

--- Section 4: App Docs Routes ---
  GET /openapi.json -> 200, title=User API
  GET /docs -> 200, has swagger-ui: True
  GET /redoc -> 200, has redoc: True
  [PASS] App docs routes work

--- Section 5: Custom Docs Configuration ---
  GET /api/schema.json -> 200
  GET /api/docs -> 200, schema URL = /api/schema.json
  GET /api/redoc -> 200, schema URL = /api/schema.json
  GET /docs -> 404 (not found, moved to /api/docs)
  [PASS] Custom docs configuration works

--- Section 6: HTML Structure ---
  Swagger UI structure valid
  ReDoc structure valid
  Both reference same schema URL: /schema.json
  [PASS] HTML structure validation works

All 6 sections passed. Swagger UI integration mastered!
```

## How It Works

### Request Flow

```
Browser: GET /docs
    |
    v
ASGI __call__ receives scope
    |
    v
_handle_docs_request("/docs")
    |
    v
Match self.docs_url -> generate Swagger HTML
    |
    v
HTML sent to browser
    |
    v
Browser loads swagger-ui from CDN
    |
    v
Swagger UI fetches /openapi.json
    |
    v
_handle_docs_request("/openapi.json")
    |
    v
Generate OpenAPI spec from routes -> JSON response
    |
    v
Swagger UI renders interactive docs
```

### Swagger UI vs ReDoc

| Feature | Swagger UI | ReDoc |
|---|---|---|
| Interactive "Try it out" | Yes | No |
| Three-panel layout | No | Yes |
| Code samples | Basic | Rich |
| Bundle size | ~1.5 MB | ~800 KB |
| Best for | Development/testing | Public documentation |

### CDN Resources

| Resource | CDN URL |
|---|---|
| Swagger UI CSS | `https://unpkg.com/swagger-ui-dist@5/swagger-ui.css` |
| Swagger UI JS | `https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js` |
| Swagger Presets | `https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js` |
| ReDoc JS | `https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js` |

## Exercises

1. **Disable docs in production** -- add `docs_url=None` support that disables the `/docs` endpoint entirely. Useful for production deployments.

2. **Custom CSS** -- add a `swagger_css_url` parameter to inject custom CSS into the Swagger UI page for branding.

3. **OAuth2 redirect** -- add a `/docs/oauth2-redirect` endpoint that Swagger UI needs for OAuth2 "Authorize" flow testing.

4. **Embed schema inline** -- instead of fetching `/openapi.json` separately, embed the spec as a `<script>` tag in the HTML to eliminate the extra request.

5. **Dark mode** -- add a `theme` parameter that switches between light and dark themes for both Swagger UI and ReDoc.

## What's Next

Our Ignite framework now has a complete developer experience: route decorators, parameter injection, validation, OpenAPI schema, and interactive documentation. In [Kata 54: SQLite Integration](./54-sqlite-integration.md), we'll add database support so our API can persist and query data.

---

[prev: 52-openapi-schema](./52-openapi-schema.md) | [next: 54-sqlite-integration](./54-sqlite-integration.md)
