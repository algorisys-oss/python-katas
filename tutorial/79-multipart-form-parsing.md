# Kata 79 -- Multipart Form Parsing

[prev: 78-realtime-chat](./78-realtime-chat.md) | next: none

---

## What We're Building

A **multipart/form-data parser from scratch** -- understanding how browsers upload files over HTTP at the byte level, and building a pure-stdlib Python parser that extracts text fields and file uploads from a raw multipart body.

This kata teaches you what frameworks like Starlette and Django do internally when your route handler receives an `UploadFile`. Instead of relying on a library, you build the protocol yourself.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `multipart/form-data` encoding | Encodes mixed text + binary data for upload | File upload forms |
| Boundary string | Delimiter that separates each form part | Parsing multipart bodies |
| Part headers | Per-part metadata: Content-Disposition, Content-Type | Identifying fields vs files |
| Content-Disposition parsing | Extracts `name` and `filename` from header value | Field and file naming |
| Boundary protocol | `--boundary`, `--boundary--` markers | Correct splitting |
| `re` for header parsing | Regex to extract quoted parameters | Robust header parsing |
| CRLF handling | HTTP requires `\r\n` line endings | Protocol compliance |
| ASGI body reading | Reading chunked body from `receive()` | Production integration |

## Why multipart/form-data Exists

HTML forms submit data in one of two encodings:

- **`application/x-www-form-urlencoded`** -- the default. All field names and values are URL-encoded (`name=Alice&age=30`). Works well for text, but terrible for binary data: a 1 MB image would triple in size and lose information.
- **`multipart/form-data`** -- required when a form includes `<input type="file">`. The body is split into *parts*, each with its own headers, separated by a boundary string. Binary data passes through unchanged.

The HTML that triggers multipart encoding:

```html
<form method="POST" action="/upload" enctype="multipart/form-data">
  <input type="text" name="username" />
  <input type="file" name="avatar" />
  <button>Upload</button>
</form>
```

Without `enctype="multipart/form-data"`, the browser would use URL encoding and the file content would be garbled.

## The Content-Type Header and Boundary

When the browser sends a multipart request, the `Content-Type` header carries the boundary string:

```
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryXyZ123
```

The boundary is a string that does **not** appear in any of the field values. Browsers generate it randomly to guarantee uniqueness. You extract it from the header before parsing the body.

```python
import re

content_type = "multipart/form-data; boundary=----WebKitFormBoundaryXyZ123"
match = re.search(r'boundary=([^\s;]+)', content_type)
boundary = match.group(1)  # '----WebKitFormBoundaryXyZ123'
```

## Anatomy of a Multipart Body

The body uses `\r\n` (CRLF) as the line ending, as required by HTTP. Each part follows this exact structure:

```
--{boundary}\r\n
{header-name}: {header-value}\r\n
{header-name}: {header-value}\r\n
\r\n
{body data}\r\n
--{boundary}\r\n
...more parts...
--{boundary}--\r\n
```

A concrete example with a text field and a file upload:

```
------WebKitFormBoundaryXyZ123\r\n
Content-Disposition: form-data; name="username"\r\n
\r\n
alice\r\n
------WebKitFormBoundaryXyZ123\r\n
Content-Disposition: form-data; name="avatar"; filename="photo.jpg"\r\n
Content-Type: image/jpeg\r\n
\r\n
<binary JPEG data>\r\n
------WebKitFormBoundaryXyZ123--\r\n
```

Key observations:
- Every part boundary is `--` + boundary string
- The final boundary has an extra `--` suffix: `--` + boundary string + `--`
- Headers and body are separated by a blank line (`\r\n\r\n`)
- The body can be text or raw binary bytes

## Content-Disposition Header Parsing

The `Content-Disposition` header identifies the form field and optional filename:

```
Content-Disposition: form-data; name="username"
Content-Disposition: form-data; name="avatar"; filename="photo.jpg"
```

Parsing it requires extracting quoted parameter values. The `name` is always present; `filename` is only present for file fields.

```python
import re

def parse_content_disposition(header_value: str) -> dict[str, str]:
    """Extract parameters from Content-Disposition header.

    Input:  'form-data; name="avatar"; filename="photo.jpg"'
    Output: {'name': 'avatar', 'filename': 'photo.jpg'}
    """
    params = {}
    # Match: key="value" or key=value
    for match in re.finditer(r'(\w+)="([^"]*)"', header_value):
        params[match.group(1)] = match.group(2)
    return params
```

## Building a Parser from Scratch

The full parsing algorithm:

1. Extract the boundary from the `Content-Type` header
2. Split the body on `\r\n--{boundary}` to get raw parts
3. Discard the preamble (before the first boundary) and epilogue (after `--`)
4. For each part, split on `\r\n\r\n` to separate headers from body
5. Parse each header line as `Name: Value`
6. Parse `Content-Disposition` to get `name` and optional `filename`
7. Classify the part as a text field or file upload

```python
class MultipartParser:
    def __init__(self, body: bytes, boundary: str):
        self.body = body
        self.boundary = boundary.encode()

    def parse(self) -> list[dict]:
        delimiter = b"\r\n--" + self.boundary
        # The body is prefixed with \r\n so index 0 is always an empty preamble
        raw_chunks = self.body.split(delimiter)
        parts = []

        for raw in raw_chunks[1:]:  # skip empty preamble at index 0
            if raw.startswith(b"--"):
                break  # final boundary suffix "--\r\n" -- stop
            # Strip the leading \r\n that follows each boundary line
            if raw.startswith(b"\r\n"):
                raw = raw[2:]
            # Split headers from body at the blank line
            if b"\r\n\r\n" not in raw:
                continue
            header_block, body = raw.split(b"\r\n\r\n", 1)
            # Strip trailing \r\n from body (belongs to the next boundary)
            if body.endswith(b"\r\n"):
                body = body[:-2]
            headers = {}
            for line in header_block.decode().split("\r\n"):
                if ": " in line:
                    k, v = line.split(": ", 1)
                    headers[k.lower()] = v
            parts.append({"headers": headers, "body": body})

        return parts
```

## Handling Text Fields vs File Fields

After parsing the raw parts, classify them:

```python
def classify_parts(parts: list[dict]) -> tuple[dict, dict]:
    """Separate text fields from file uploads.

    Returns:
        fields: {name: text_value}
        files:  {name: {"filename": str, "content_type": str, "data": bytes}}
    """
    fields = {}
    files = {}

    for part in parts:
        disposition = part["headers"].get("content-disposition", "")
        params = parse_content_disposition(disposition)
        name = params.get("name", "")
        filename = params.get("filename")

        if filename is not None:
            # File upload
            files[name] = {
                "filename": filename,
                "content_type": part["headers"].get("content-type", "application/octet-stream"),
                "data": part["body"],
            }
        else:
            # Text field
            fields[name] = part["body"].decode("utf-8")

    return fields, files
```

## Edge Cases

### Multiple Files with the Same Field Name

HTML allows `<input type="file" name="photos" multiple>`. When multiple files share the same field name, store them in a list:

```python
if filename is not None:
    files.setdefault(name, []).append({...})
```

### Empty Parts

A part with no body is valid. The split produces an empty bytes object after the blank line. Always guard with a length check before decoding.

### Large Files

In a real server you would not buffer the entire body in memory. Instead, stream the body in chunks, writing file data directly to disk. The algorithm stays the same -- you just process the boundary delimiter incrementally. Libraries like `python-multipart` use this approach.

### Boundary in Body Data

This cannot happen by design: the browser inspects the file data and picks a boundary string guaranteed not to appear in it. The RFC requires this.

### Missing CRLF

Some clients send `\n` instead of `\r\n`. A robust parser should accept both. You can normalize the body with `body.replace(b"\r\n", b"\n")` before splitting if you encounter such clients.

## Integration with ASGI

In an ASGI app, the request body arrives in chunks via the `receive()` callable. To collect the full body:

```python
async def read_body(receive) -> bytes:
    """Read the complete request body from ASGI receive channel."""
    chunks = []
    more_body = True
    while more_body:
        message = await receive()
        chunks.append(message.get("body", b""))
        more_body = message.get("more_body", False)
    return b"".join(chunks)

async def handle_upload(scope, receive, send):
    # 1. Read full body
    body = await read_body(receive)

    # 2. Extract boundary from Content-Type header
    headers = dict(scope["headers"])
    content_type = headers.get(b"content-type", b"").decode()
    match = re.search(r"boundary=([^\s;]+)", content_type)
    if not match:
        # Return 400 Bad Request
        ...
    boundary = match.group(1)

    # 3. Parse
    parser = MultipartParser(body, boundary)
    parts = parser.parse()
    fields, files = classify_parts(parts)

    # 4. Use the data
    username = fields.get("username", "")
    avatar = files.get("avatar")
    if avatar:
        # avatar["data"] contains raw bytes
        with open(f"/uploads/{avatar['filename']}", "wb") as f:
            f.write(avatar["data"])
```

## Complete Parser Code

```python
import re

def extract_boundary(content_type: str) -> str:
    match = re.search(r"boundary=([^\s;]+)", content_type)
    if not match:
        raise ValueError(f"No boundary in Content-Type: {content_type!r}")
    return match.group(1)

def parse_content_disposition(value: str) -> dict[str, str]:
    params = {}
    for m in re.finditer(r'(\w+)="([^"]*)"', value):
        params[m.group(1)] = m.group(2)
    return params

class MultipartParser:
    def __init__(self, body: bytes, boundary: str):
        self.body = body
        self.boundary = boundary

    def parse(self) -> list[dict]:
        delimiter = b"\r\n--" + self.boundary.encode()
        raw_chunks = self.body.split(delimiter)
        parts = []
        for raw in raw_chunks[1:]:  # index 0 is always empty preamble
            if raw.startswith(b"--"):
                break
            if raw.startswith(b"\r\n"):
                raw = raw[2:]
            if b"\r\n\r\n" not in raw:
                continue
            header_block, body = raw.split(b"\r\n\r\n", 1)
            if body.endswith(b"\r\n"):
                body = body[:-2]
            headers = {}
            for line in header_block.decode().split("\r\n"):
                if ": " in line:
                    k, v = line.split(": ", 1)
                    headers[k.lower()] = v
            parts.append({"headers": headers, "body": body})
        return parts

    def get_fields_and_files(self):
        fields, files = {}, {}
        for part in self.parse():
            disp = part["headers"].get("content-disposition", "")
            params = parse_content_disposition(disp)
            name = params.get("name", "")
            filename = params.get("filename")
            if filename is not None:
                files[name] = {
                    "filename": filename,
                    "content_type": part["headers"].get("content-type", "application/octet-stream"),
                    "data": part["body"],
                }
            else:
                fields[name] = part["body"].decode("utf-8")
        return fields, files
```

## Playground

```python
python playground/79_multipart_form_parsing.py
```

Expected output:

```
--- Section 1: Boundary Extraction ---
  Content-Type: multipart/form-data; boundary=----FormBoundary7MA4YWxkTrZu0gW
  Boundary: ----FormBoundary7MA4YWxkTrZu0gW
  [PASS] Boundary extraction works

--- Section 2: Multipart Body Construction ---
  Built multipart body: 368 bytes
  Parts in body: 3 (username, bio, avatar)
  [PASS] Body construction works

--- Section 3: Raw Part Splitting ---
  Found 3 raw parts
  Part 0 headers: content-disposition
  Part 1 headers: content-disposition
  Part 2 headers: content-disposition, content-type
  [PASS] Part splitting works

--- Section 4: Content-Disposition Parsing ---
  'form-data; name="username"'      -> {'name': 'username'}
  'form-data; name="avatar"; filename="photo.png"' -> {'name': 'avatar', 'filename': 'photo.png'}
  [PASS] Content-Disposition parsing works

--- Section 5: Full Parse (Fields + Files) ---
  Text fields:
    username = alice
    bio      = Python developer and open-source contributor
  File uploads:
    avatar: photo.png (image/png), 72 bytes
  [PASS] Full parse works

--- Section 6: Multiple Files ---
  Uploaded 2 files under field 'photo':
    photo[0]: sunset.jpg (image/jpeg), 12 bytes
    photo[1]: profile.jpg (image/jpeg), 14 bytes
  [PASS] Multiple files work

--- Section 7: ASGI Body Reader (simulated) ---
  Received 4 chunks totaling 227 bytes
  Parsed from simulated ASGI: username=bob, file=data.csv
  [PASS] ASGI body reader works

All 7 sections passed. Multipart parser complete!
```

## How It Works

### Body Structure Diagram

```
POST /upload HTTP/1.1
Content-Type: multipart/form-data; boundary=BOUNDARY
Content-Length: ...

--BOUNDARY\r\n                     <- part delimiter
Content-Disposition: form-data; name="username"\r\n
\r\n                               <- blank line separates headers from body
alice\r\n                          <- part body (text field)
--BOUNDARY\r\n                     <- next part
Content-Disposition: form-data; name="avatar"; filename="photo.png"\r\n
Content-Type: image/png\r\n
\r\n
<PNG binary data>\r\n              <- part body (file bytes)
--BOUNDARY--\r\n                   <- final boundary (note trailing --)
```

### Split Algorithm

The body is prefixed with `\r\n` so that splitting on `\r\n--BOUNDARY` always produces an empty string at index 0. This makes the algorithm uniform: every non-empty chunk from index 1 onward is a real part.

```
body = b"\r\n--BOUNDARY\r\n{part1}\r\n--BOUNDARY\r\n{part2}\r\n--BOUNDARY--\r\n"

body.split(b"\r\n--BOUNDARY")
  -> [b"",                          <- index 0: empty preamble -- discard
      b"\r\nheaders\r\n\r\nbody1", <- index 1: first part
      b"\r\nheaders\r\n\r\nbody2", <- index 2: second part
      b"--\r\n"]                   <- index N: starts with "--" -- stop
```

### Header vs Body Separation

Within each part, the first `\r\n\r\n` separates the header block from the body. This is the same convention as the HTTP request itself.

```
"Content-Disposition: form-data; name=\"username\"\r\n"
+
"\r\n"         <- blank line = end of headers
+
"alice"        <- body starts here
```

## Exercises

1. **Handle `\n`-only line endings** -- some clients send `\n` instead of `\r\n`. Modify `MultipartParser.parse()` to accept both by normalizing the body before splitting.

2. **Stream to disk** -- instead of collecting the full body in memory, write a `StreamingMultipartParser` that processes bytes in chunks of 64 KB, writing file parts directly to a `tempfile.NamedTemporaryFile`.

3. **Add content-length validation** -- after parsing, compare the total bytes in all parts against the `Content-Length` header. Raise an error if they don't match.

4. **Multiple files under one field name** -- extend `get_fields_and_files()` so that multiple file parts with the same `name` are collected into a list rather than overwriting each other.

5. **Integrate with Ignite** -- add a `multipart_form_data()` method to Ignite's `Request` class that parses the body on demand and caches the result, similar to how `json()` and `form()` work.

## What's Next

You've built a multipart parser from scratch -- the same core algorithm used by Django, Starlette, and every other Python web framework. The key insight is that `multipart/form-data` is just a text-framing protocol: boundaries delimit parts, each part has its own headers, and binary data passes through unchanged.

This completes the deep dive into HTTP at the byte level. From raw sockets (kata 36) to multipart bodies (kata 79), you now understand every layer of the HTTP stack.

---

[prev: 78-realtime-chat](./78-realtime-chat.md) | next: none
