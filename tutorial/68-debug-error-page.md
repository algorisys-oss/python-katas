# Kata 68 -- Debug Error Page

[prev: 67-hot-reload](./67-hot-reload.md) | [next: 69-structured-logging](./69-structured-logging.md)

---

## What We're Building

A **rich debug error page** for our Ignite framework. When an exception occurs during development, instead of a plain traceback, we generate an HTML page showing:

1. **Exception type and message** -- prominently displayed at the top
2. **Stack frames with source code** -- each frame shows the surrounding code, with the error line highlighted
3. **Local variables** -- every variable in scope at each frame
4. **Request context** -- HTTP method, path, headers, query params

This is what Django's debug page and Werkzeug's debugger do. We build it from scratch using Python's `traceback`, `linecache`, and `sys.exc_info()`.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `sys.exc_info()` | Get current exception info tuple | Capturing exception details |
| `tb.tb_frame` | Access frame from traceback | Walking the call stack |
| `frame.f_locals` | Local variables in a frame | Inspecting variable state |
| `linecache.getline()` | Read source lines by number | Showing code context |
| `html.escape()` | Prevent XSS in HTML output | Rendering user data in HTML |
| `traceback.format_exception()` | Format exception as text | Plain text fallback |

## The Code

### 1. Frame Extraction

Walk the traceback chain and extract detailed info from each frame:

```python
def extract_frames(exc_info):
    _, _, tb = exc_info
    frames = []

    current_tb = tb
    while current_tb is not None:
        frame = current_tb.tb_frame
        lineno = current_tb.tb_lineno
        filename = frame.f_code.co_filename
        function = frame.f_code.co_name

        # Get source code context
        start_line = max(1, lineno - 5)
        code_lines = []
        for i in range(lineno - 5, lineno + 6):
            line = linecache.getline(filename, i)
            if line:
                code_lines.append(line.rstrip())

        # Get local variables (skip dunders, truncate long reprs)
        locals_dict = {}
        for key, value in frame.f_locals.items():
            if not (key.startswith("__") and key.endswith("__")):
                repr_val = repr(value)[:200]
                locals_dict[key] = repr_val

        frames.append(FrameInfo(filename, lineno, function,
                                code_lines, start_line, locals_dict))
        current_tb = current_tb.tb_next

    return frames
```

### 2. Request Context

```python
class RequestContext:
    def __init__(self, method="GET", path="/", headers=None,
                 query_params=None, body=None, client_ip="127.0.0.1"):
        self.method = method
        self.path = path
        self.headers = headers or {}
        # ...

    def to_dict(self):
        result = {"Method": self.method, "Path": self.path}
        if self.headers:
            result["Headers"] = self.headers
        return result
```

### 3. HTML Error Page

```python
class DebugErrorPage:
    def generate(self, exc_info, request=None):
        exc_type, exc_value, _ = exc_info
        frames = extract_frames(exc_info)

        parts = [self._html_header(exc_type, exc_value)]
        if request:
            parts.append(self._request_section(request))
        for i, frame in enumerate(reversed(frames)):
            parts.append(self._frame_section(frame, i))
        parts.append(self._plain_traceback(...))
        parts.append("</body></html>")
        return "\n".join(parts)
```

### 4. Debug Middleware

```python
class DebugMiddleware:
    def __init__(self, debug=True):
        self.debug = debug

    def handle_error(self, exc_info, request=None):
        if self.debug:
            html = DebugErrorPage().generate(exc_info, request)
            return {"content_type": "text/html", "body": html, "status_code": 500}
        else:
            return {"content_type": "application/json",
                    "body": '{"error": "Internal Server Error"}',
                    "status_code": 500}
```

## Playground

```bash
python playground/68_debug_error_page.py
```

Expected output:

```
--- Section 1: Frame Extraction ---
  Extracted 4 frames:
    FrameInfo(68_debug_error_page.py:... in demo_frame_extraction)
    FrameInfo(68_debug_error_page.py:... in outer_function)
    FrameInfo(68_debug_error_page.py:... in middle_function)
    FrameInfo(68_debug_error_page.py:... in inner_function)
  [PASS] Frame extraction works

--- Section 2: Request Context ---
  Request context:
    Method: POST
    Path: /api/users
    ...
  [PASS] Request context works

--- Section 3: HTML Error Page ---
  Generated HTML error page:
    Size: ... bytes
    Contains exception type: KeyError
    Contains request info: GET /api/users/99
    Contains local variables: yes
    Contains source code: yes
  [PASS] HTML error page generation works

--- Section 4: Debug Middleware ---
  Debug mode: content_type=text/html, status=500
  Production mode: content_type=application/json, status=500
  [PASS] Debug middleware works
```

## How It Works

### Exception Info Pipeline

```
Exception raised
     |
     v
sys.exc_info() -> (type, value, traceback)
     |
     v
Walk traceback chain:
  tb -> tb.tb_next -> tb.tb_next -> None
     |
     v
For each frame:
  +-- filename, lineno, function name
  +-- source code (via linecache)
  +-- local variables (via frame.f_locals)
     |
     v
Render to HTML:
  +-- Error header (type + message)
  +-- Request info table
  +-- Stack frames (innermost first)
  |     +-- Code block with error line highlighted
  |     +-- Local variables table
  +-- Plain text traceback (for copy-paste)
```

### Security: Debug vs Production

```
               Debug Mode (development)         Production Mode
              +-------------------------+   +--------------------+
Exception --> | Full HTML error page    |   | Generic JSON error |
              | - Source code           |   | {"error": "500"}   |
              | - Local variables       |   | No internal details|
              | - Request details       |   |                    |
              +-------------------------+   +--------------------+

NEVER expose debug pages in production -- they reveal:
  - Source code
  - Database credentials in variables
  - File system paths
  - Internal architecture
```

## Exercises

1. **Add syntax highlighting** -- use simple regex-based highlighting for Python keywords (`def`, `class`, `if`, etc.), strings, and comments in the code context.

2. **Add interactive variable expansion** -- for complex variables (dicts, lists), add a click-to-expand feature using JavaScript to show nested values.

3. **Add request/response timeline** -- show how much time was spent in each frame, using timestamps from a profiling wrapper.

4. **Add a REPL console** -- like Werkzeug's debugger, embed a JavaScript console that can evaluate Python expressions in the error frame's context.

5. **Add error grouping** -- track similar errors across requests and show a count of how many times each unique error has occurred.

## What's Next

With rich debug pages, developers can quickly pinpoint bugs during development. In [Kata 69: Structured Logging](./69-structured-logging.md), we'll build JSON-based structured logging with request IDs via `contextvars` -- essential for debugging in production where debug pages aren't available.

---

[prev: 67-hot-reload](./67-hot-reload.md) | [next: 69-structured-logging](./69-structured-logging.md)
