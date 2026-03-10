# Kata 46 -- Query Parameter Parsing

[prev: 45-request-body-validation](./45-request-body-validation.md) | [next: 47-response-models](./47-response-models.md)

---

## What We're Building

An **automatic query parameter extraction system** that inspects function signatures and type hints to parse, coerce, and bind query string values to route handler parameters. This is how frameworks like FastAPI turn `?page=3&limit=50` into typed Python arguments.

We'll build four components:
1. **Query string parser** -- parse raw `key=value&key=value` strings
2. **Type coercion** -- convert string values to int, float, bool, and list types
3. **Signature inspector** -- read function parameters, types, and defaults
4. **Route integration** -- automatically bind query params to handler calls

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `urllib.parse.parse_qs()` | Parses query strings into `{key: [values]}` | Raw query string handling |
| `inspect.signature()` | Reads a function's parameters and defaults | Auto-binding arguments |
| `get_type_hints()` | Resolves type annotations at runtime | Type-driven coercion |
| `Parameter.empty` | Sentinel for "no default value" | Detecting required params |
| `list[T]` parameters | Repeated keys like `?tag=a&tag=b` | Multi-value query params |
| `Optional[T]` | Nullable parameter (defaults to None) | Optional query params |
| Type coercion | `"42"` -> `42`, `"true"` -> `True` | Query strings are always strings |

## The Code

### 1. Query String Basics

Query strings are always strings. `parse_qs` returns lists because keys can repeat:

```python
from urllib.parse import parse_qs

parsed = parse_qs("name=Alice&age=30&tag=a&tag=b")
# {'name': ['Alice'], 'age': ['30'], 'tag': ['a', 'b']}
#                                          ^^ repeated key
```

### 2. Type Coercion from Strings

Everything in a query string is a string. We coerce based on annotations:

```python
def _coerce_single(value: str, target_type: type) -> Any:
    if target_type is str:   return value
    if target_type is int:   return int(value)      # "42" -> 42
    if target_type is float: return float(value)    # "3.14" -> 3.14
    if target_type is bool:                          # "true" -> True
        return value.lower() in ("true", "1", "yes", "on")
```

### 3. Detecting List Types

`list[str]` means "collect all values for this key":

```python
def _is_list_type(annotation):
    origin = typing.get_origin(annotation)  # list
    if origin is list:
        args = typing.get_args(annotation)  # (str,)
        return True, args[0] if args else str
    return False, annotation
```

### 4. Signature-Based Extraction

The magic: inspect the handler's signature to know what params to extract:

```python
def extract_query_params(func, query_string, skip_params={"request"}):
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    raw_params = parse_qs(query_string)
    result = {}

    for param_name, param in sig.parameters.items():
        if param_name in skip_params:
            continue

        annotation = hints.get(param_name, str)
        has_default = param.default is not inspect.Parameter.empty

        if param_name in raw_params:
            result[param_name] = coerce(raw_params[param_name], annotation)
        elif has_default:
            result[param_name] = param.default
        else:
            raise Error(f"{param_name}: required but not provided")

    return result
```

### 5. Route Integration

```python
def list_articles(
    request: Request,
    page: int = 1,           # /articles?page=3
    per_page: int = 10,      # /articles?per_page=25
    author: Optional[str] = None,  # /articles?author=alice
    tags: list[str] = [],    # /articles?tags=python&tags=web
) -> dict:
    ...

# The framework auto-extracts:
# GET /articles?page=2&author=alice&tags=python&tags=web
# -> page=2, per_page=10, author="alice", tags=["python", "web"]
```

## Playground

```python
python playground/46_query_parameters.py
```

Expected output:

```
--- Section 1: Basic Query String Parsing ---
  Query: 'name=Alice&age=30&active=true'
  Parsed: {'name': ['Alice'], 'age': ['30'], 'active': ['true']}
  Query: 'tag=python&tag=web&tag=api'
  Parsed: {'tag': ['python', 'web', 'api']}
  Query: 'q=hello+world&empty=&encoded=%2Fpath'
  Parsed: {'q': ['hello world'], 'empty': [''], 'encoded': ['/path']}
  [PASS] Basic parsing works

--- Section 2: Type Coercion ---
  '42' -> int: 42 (type=int)
  '3.14' -> float: 3.14 (type=float)
  'true' -> bool: True
  'false' -> bool: False
  '1' -> bool: True
  '0' -> bool: False
  'yes' -> bool: True
  'abc' -> int: cannot convert 'abc' to int
  [PASS] Type coercion works

--- Section 3: Signature-Based Extraction ---
  Query: 'q=python+tutorial&page=3&limit=50'
  Extracted: {'q': 'python tutorial', 'page': 3, 'limit': 50, 'sort': 'relevance', 'active': None}
  Query: 'q=web&active=true'
  active = True (coerced from 'true')
  [PASS] Signature extraction works

--- Section 4: List Parameters ---
  category = ['electronics', 'computers']
  min_price = 99.99
  tags = ['sale', 'new']
  ids (list[int]) = [1, 2, 3]
  [PASS] List parameters work

--- Section 5: Error Handling ---
  Missing required: Query parameter '__multiple__': ...required but not provided
  Invalid type: Query parameter '__multiple__': ...cannot convert 'abc' to int
  [PASS] Error handling works

--- Section 6: Route Integration ---
  GET /articles?page=2&per_page=25&author=alice&tags=python&tags=web
  Result: {'page': 2, 'per_page': 25, 'author': 'alice', 'tags': ['python', 'web']}
  GET /articles (no query params)
  Result: {'page': 1, 'per_page': 10, 'author': None, 'tags': []}
  [PASS] Route integration works

All 6 sections passed. Query parameter parsing mastered!
```

## How It Works

### Query Parameter Resolution

```
URL: /search?q=python&page=3&tags=web&tags=api
              |        |       |
              v        v       v
Query String: "q=python&page=3&tags=web&tags=api"
              |
              v (parse_qs)
Raw Params:   {"q": ["python"], "page": ["3"], "tags": ["web", "api"]}
              |
              v (inspect signature)
Handler:      def search(request, q: str, page: int = 1, tags: list[str] = [])
              |
              v (coerce + bind)
Call:         search(request, q="python", page=3, tags=["web", "api"])
```

### Scalar vs List Parameter Rules

```
Annotation    Query String        Result
----------    ------------        ------
q: str        ?q=hello            "hello"
page: int     ?page=3             3
active: bool  ?active=true        True
tags: list[str]  ?tags=a&tags=b   ["a", "b"]
ids: list[int]   ?ids=1&ids=2     [1, 2]
```

### Default Value Resolution

```
1. param_name in query string?
   YES -> coerce to annotated type

2. param has default in signature?
   YES -> use default (page: int = 1)

3. param is Optional[T]?
   YES -> use None

4. ELSE -> ERROR: required parameter missing
```

## Exercises

1. **Add enum support** -- extend coercion to handle `Enum` types. If a parameter is annotated as `SortOrder` (an Enum), validate that the string value matches one of the enum members.

2. **Implement query param aliases** -- add support for mapping query string keys to different parameter names (e.g., query param `per_page` maps to handler param `limit`).

3. **Add validation constraints** -- support min/max values for numeric query params using a `Query()` descriptor similar to `Field()` from kata 45.

4. **Support nested query params** -- parse dot-notation like `?filter.status=active&filter.type=blog` into nested dicts.

5. **Build a query string builder** -- the reverse: given typed parameters, construct a valid query string with proper URL encoding.

## What's Next

We can now parse both request bodies (kata 45) and query parameters. In [Kata 47: Response Models](./47-response-models.md), we'll build the output side -- response models that control exactly what data gets serialized and sent back to the client, with field filtering, aliases, and nested serialization.

---

[prev: 45-request-body-validation](./45-request-body-validation.md) | [next: 47-response-models](./47-response-models.md)
