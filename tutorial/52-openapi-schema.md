# Kata 52 -- OpenAPI Schema Generation

[prev: 51-type-driven-validation](./51-type-driven-validation.md) | [next: 53-swagger-ui](./53-swagger-ui.md)

---

## What We're Building

**Automatic OpenAPI 3.0 schema generation** from registered routes. By inspecting handler signatures, we extract everything needed to produce a complete API specification:

```python
app = IgniteApp(title="Pet Store API", version="1.0.0")

@app.get("/pets/{pet_id}", tags=["pets"], response_model=PetResponse)
def get_pet(pet_id: int):
    ...

@app.post("/pets", tags=["pets"])
def create_pet(pet: CreatePet):
    ...

spec = app.openapi()  # Full OpenAPI 3.0.3 JSON document
```

The generator walks each route, inspects its handler's `inspect.signature()`, and classifies each parameter as a path param, query param, or request body. Models get extracted into `components/schemas` with `$ref` references.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| OpenAPI 3.0 | Standard API description format | API documentation |
| Path parameters | `{pet_id}` in URL -> `"in": "path"` param | Resource identifiers |
| Query parameters | Simple-type params -> `"in": "query"` | Filtering, pagination |
| Request body | BaseModel param -> `requestBody` with schema | Create/update endpoints |
| Response model | `response_model=` kwarg -> response schema | Documenting responses |
| `$ref` references | `"$ref": "#/components/schemas/Pet"` | Schema reuse |
| Schema generation | Python type -> JSON Schema type mapping | Model documentation |

## The Code

### 1. The OpenAPI Document Structure

```python
{
    "openapi": "3.0.3",
    "info": {"title": "Pet Store API", "version": "1.0.0"},
    "paths": {
        "/pets": {
            "get": {"summary": "List Pets", "parameters": [...]},
            "post": {"summary": "Create Pet", "requestBody": {...}},
        },
        "/pets/{pet_id}": {
            "get": {"summary": "Get Pet", "parameters": [...], "responses": {...}},
        },
    },
    "components": {
        "schemas": {
            "CreatePet": {"type": "object", "properties": {...}},
            "PetResponse": {"type": "object", "properties": {...}},
        }
    }
}
```

### 2. Parameter Classification

```python
def _extract_params(self, route, schemas):
    sig = inspect.signature(route.handler)
    path_param_names = set(re.findall(r"\{(\w+)\}", route.path))

    for name, param in sig.parameters.items():
        annotation = hints.get(name)

        if name == "request":    continue  # Skip
        if Depends default:      continue  # Not in OpenAPI

        if issubclass(annotation, BaseModel):
            # -> requestBody with $ref
            schemas[annotation.__name__] = annotation.schema()
            body_schema = {"$ref": f"#/components/schemas/{name}"}

        elif name in path_param_names:
            # -> {"name": name, "in": "path", "required": True, ...}

        else:
            # -> {"name": name, "in": "query", "required": no_default, ...}
```

### 3. Schema from Models

```python
class CreatePet(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="Pet name")
    species: str = Field(description="Animal species")
    age: int = Field(ge=0, description="Age in years")

# Generates:
{
    "type": "object",
    "title": "CreatePet",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 50,
                 "description": "Pet name"},
        "species": {"type": "string", "description": "Animal species"},
        "age": {"type": "integer", "minimum": 0, "description": "Age in years"},
    },
    "required": ["name", "species", "age"]
}
```

### 4. Response Model + Error Responses

```python
def _build_responses(self, route, schemas):
    responses = {
        str(route.status_code): {
            "description": "Successful response",
            "content": {"application/json": {
                "schema": {"$ref": "#/components/schemas/PetResponse"}
            }}
        }
    }
    # POST/PUT/PATCH also get 422 Validation Error
    if route.method in ("POST", "PUT", "PATCH"):
        responses["422"] = {"description": "Validation Error", ...}
```

## Playground

```bash
python playground/52_openapi_schema.py
```

Expected output:

```
--- Section 1: Basic OpenAPI Schema ---
  OpenAPI version: 3.0.3
  Title: Pet Store API
  Paths: ['/pets', '/pets/{pet_id}']
  Path param: {'name': 'pet_id', 'in': 'path', 'required': True, ...}
  [PASS] Basic OpenAPI schema works

--- Section 2: Query Parameters ---
  Parameters (3):
    q: in=query, required=True, schema={'type': 'string'}
    limit: in=query, required=False, schema={'type': 'integer', 'minimum': 1, 'maximum': 100}
    offset: in=query, required=False, schema={'type': 'integer', 'minimum': 0}
  [PASS] Query parameters work

--- Section 3: Request Body Schema ---
  Body schema ref: #/components/schemas/CreatePet
  Model schema: {"type": "object", "title": "CreatePet", ...}
  [PASS] Request body schema works

--- Section 4: Response Model ---
  Response schema ref: #/components/schemas/PetResponse
  PetResponse fields: ['id', 'name', 'species']
  [PASS] Response model works

--- Section 5: Full API Spec ---
  Paths: ['/users', '/users/{user_id}']
  Total operations: 5
  Schemas: ['CreateUser', 'UserResponse']
  [PASS] Full API spec works

--- Section 6: Validation Error Responses ---
  GET /items: no 422 response (correct)
  POST /items: has 422 response (correct)
  [PASS] Validation error responses work

All 6 sections passed. OpenAPI schema generation mastered!
```

## How It Works

### Type to JSON Schema Mapping

| Python Type | JSON Schema Type |
|---|---|
| `str` | `"string"` |
| `int` | `"integer"` |
| `float` | `"number"` |
| `bool` | `"boolean"` |
| `list` | `"array"` |
| `dict` | `"object"` |

### Schema Reference Flow

```
@app.post("/pets")
def create_pet(pet: CreatePet): ...
                 |
                 v
Inspect: annotation = CreatePet (BaseModel subclass)
                 |
                 v
Generate: schemas["CreatePet"] = CreatePet.schema()
                 |
                 v
Reference: requestBody.schema = {"$ref": "#/components/schemas/CreatePet"}
```

### Query Parameter with Constraints

```
def search(limit: int = Query(10, ge=1, le=100, description="Max results"))
    |
    v
{
    "name": "limit",
    "in": "query",
    "required": false,
    "schema": {"type": "integer", "minimum": 1, "maximum": 100},
    "description": "Max results"
}
```

## Exercises

1. **Array response models** -- support `response_model=list[Pet]` that generates `{"type": "array", "items": {"$ref": "..."}}`.

2. **Optional fields** -- handle `Optional[str]` annotations to mark fields as not required and add `"nullable": true` to the schema.

3. **Tags metadata** -- add tag descriptions to the OpenAPI spec: `{"tags": [{"name": "pets", "description": "Pet operations"}]}`.

4. **Security schemes** -- generate `components/securitySchemes` for Bearer token auth and add `security` requirements to protected endpoints.

5. **Example values** -- use `Field(example=...)` to populate the `"example"` field in the schema, making the Swagger UI "Try it out" feature more useful.

## What's Next

We can now generate a complete OpenAPI spec, but humans need a visual way to explore it. In [Kata 53: Swagger UI Integration](./53-swagger-ui.md), we'll serve interactive Swagger UI and ReDoc documentation pages that load our schema and let developers explore the API in a browser.

---

[prev: 51-type-driven-validation](./51-type-driven-validation.md) | [next: 53-swagger-ui](./53-swagger-ui.md)
