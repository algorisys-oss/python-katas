# Kata 80 -- File Upload Handling

[prev: 78-realtime-chat](./78-realtime-chat.md) | next: none

---

## What We're Building

A **file upload pipeline** -- the machinery that sits between a raw HTTP multipart request and a safely-stored file on disk. Real frameworks (FastAPI, Starlette, Django) each have their own upload abstractions, but they all solve the same five problems:

1. **Buffering** -- hold the incoming bytes somewhere without blowing up RAM
2. **Validation** -- reject oversized, wrong-type, or dangerously-named files before they touch disk
3. **Sanitization** -- turn attacker-controlled filenames into safe paths
4. **Streaming** -- read large files in chunks instead of all at once
5. **Persistence** -- write the final bytes to a known, safe location

By building these pieces from scratch you will understand exactly what `UploadFile` does in FastAPI and why each design decision was made.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `UploadFile` class | Wraps a temp file with metadata | Any upload abstraction |
| `SpooledTemporaryFile` | In-memory up to limit, then disk | Memory-efficient upload buffering |
| Size validation | Reject files over a threshold | Prevent disk exhaustion |
| MIME type validation | Allow only specific content types | Images, docs, CSV-only endpoints |
| Filename sanitization | Strip path components and bad chars | Prevent path traversal |
| Streaming reads | Iterate in fixed-size chunks | Large file processing |
| Safe save-to-disk | Write to a controlled directory | Persisting uploaded files |
| Multiple file handling | Process a list of `UploadFile` objects | Multi-file form fields |
| Multipart simulation | Build/parse raw multipart data | Testing without an HTTP server |

---

## The UploadFile Class

### Why a Wrapper?

When a browser submits a `<form enctype="multipart/form-data">`, the web server receives a stream of bytes that looks like this:

```
--boundary\r\n
Content-Disposition: form-data; name="file"; filename="photo.jpg"\r\n
Content-Type: image/jpeg\r\n
\r\n
<binary jpeg data>\r\n
--boundary--\r\n
```

The framework parses this stream and hands your handler a file-like object plus metadata. `UploadFile` bundles both together:

```python
@dataclass
class UploadFile:
    filename: str            # original filename from the browser
    content_type: str        # MIME type from Content-Type header
    file: SpooledTemporaryFile  # file-like object with the bytes

    async def read(self, size: int = -1) -> bytes: ...
    async def seek(self, offset: int) -> None: ...
    async def close(self) -> None: ...
```

FastAPI's `UploadFile` is defined in Starlette and looks almost exactly like this. The async wrappers exist because Starlette runs on an async event loop -- in our synchronous implementation we drop the `async/await`.

### SpooledTemporaryFile

`SpooledTemporaryFile` is in the standard library (`tempfile` module). It behaves exactly like a regular file object but:

- Starts as an **in-memory `BytesIO`** buffer
- Automatically **rolls over to a real temp file on disk** once the data exceeds `max_size` bytes
- Is **automatically deleted** when closed

```python
import tempfile

# Spooled: stays in memory for files under 1 MB, spills to disk otherwise
spool = tempfile.SpooledTemporaryFile(max_size=1 * 1024 * 1024)
spool.write(b"hello world")
spool.seek(0)
print(spool.read())   # b'hello world'
spool.close()         # temp file deleted
```

This is ideal for upload handling: small files (thumbnails, config snippets) never hit disk; large files (video, zip) are handled transparently.

### Building UploadFile

```python
import tempfile
from dataclasses import dataclass, field

MAX_SPOOL_SIZE = 1 * 1024 * 1024  # 1 MB in memory, then disk

@dataclass
class UploadFile:
    filename: str
    content_type: str
    _file: tempfile.SpooledTemporaryFile = field(repr=False)

    @classmethod
    def from_bytes(cls, filename: str, content_type: str,
                   data: bytes) -> "UploadFile":
        """Create an UploadFile from raw bytes (useful for testing)."""
        spool = tempfile.SpooledTemporaryFile(max_size=MAX_SPOOL_SIZE)
        spool.write(data)
        spool.seek(0)
        return cls(filename=filename, content_type=content_type, _file=spool)

    def read(self, size: int = -1) -> bytes:
        return self._file.read(size)

    def seek(self, offset: int) -> None:
        self._file.seek(offset)

    def close(self) -> None:
        self._file.close()

    @property
    def size(self) -> int:
        """Return the total size of the uploaded content."""
        current = self._file.tell()
        self._file.seek(0, 2)   # seek to end
        end = self._file.tell()
        self._file.seek(current) # restore position
        return end
```

---

## File Validation

Validation should happen **before** any bytes reach permanent storage. Three checks matter most.

### 1. Size Limits

```python
class FileSizeTooLargeError(Exception):
    pass

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_size(upload: UploadFile, limit: int = MAX_UPLOAD_SIZE) -> None:
    if upload.size > limit:
        mb = upload.size / (1024 * 1024)
        raise FileSizeTooLargeError(
            f"File '{upload.filename}' is {mb:.1f} MB, "
            f"exceeds {limit // (1024*1024)} MB limit"
        )
```

### 2. Allowed MIME Types

Never trust the `Content-Type` header alone -- a browser or attacker can set it to anything. For strict security you would also read the first few bytes and check magic numbers. For most production uses, MIME validation plus content-sniffing together are sufficient.

```python
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "text/plain", "text/csv"}

class InvalidContentTypeError(Exception):
    pass

def validate_content_type(upload: UploadFile,
                           allowed: set[str]) -> None:
    if upload.content_type not in allowed:
        raise InvalidContentTypeError(
            f"Content type '{upload.content_type}' is not allowed. "
            f"Allowed: {sorted(allowed)}"
        )
```

### 3. Filename Sanitization

This is the most security-critical step. User-controlled filenames can contain:

- Path traversal: `../../etc/passwd`
- Absolute paths: `/etc/shadow`
- Unicode tricks: `file\x00.exe` (null byte)
- Windows reserved names: `CON`, `PRN`, `AUX`, `NUL`
- Double extensions: `image.php.jpg`

```python
import re
import os

WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

def sanitize_filename(filename: str) -> str:
    # 1. Extract just the basename -- no path components
    filename = os.path.basename(filename)

    # 2. Replace null bytes and control characters
    filename = filename.replace("\x00", "")
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)

    # 3. Keep only safe characters: alphanumerics, dots, hyphens, underscores
    filename = re.sub(r"[^\w.\-]", "_", filename)

    # 4. Collapse multiple dots (no hidden extension tricks like .php.jpg)
    filename = re.sub(r"\.{2,}", ".", filename)

    # 5. Strip leading dots and dashes (hidden files on Unix)
    filename = filename.lstrip(".-")

    # 6. Fallback for empty result
    if not filename:
        filename = "upload"

    # 7. Check Windows reserved names (case-insensitive, ignore extension)
    stem = filename.rsplit(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED:
        filename = f"file_{filename}"

    return filename
```

---

## Streaming Reads for Large Uploads

Never do `content = upload.read()` for large files -- this loads everything into RAM. Instead, process in chunks:

```python
CHUNK_SIZE = 64 * 1024  # 64 KB

def iter_chunks(upload: UploadFile, chunk_size: int = CHUNK_SIZE):
    """Generator that yields chunks from the upload."""
    upload.seek(0)
    while True:
        chunk = upload.read(chunk_size)
        if not chunk:
            break
        yield chunk

# Count bytes without loading everything at once
def count_bytes(upload: UploadFile) -> int:
    total = 0
    for chunk in iter_chunks(upload):
        total += len(chunk)
    return total
```

You can compose this with any sink -- a hash function, a compression stream, a database BLOB writer:

```python
import hashlib

def sha256_of_upload(upload: UploadFile) -> str:
    h = hashlib.sha256()
    for chunk in iter_chunks(upload):
        h.update(chunk)
    return h.hexdigest()
```

---

## Saving Uploaded Files to Disk Safely

The key rule: **always join the sanitized filename to a fixed base directory and verify the result stays inside that directory**:

```python
from pathlib import Path

def save_upload(upload: UploadFile, dest_dir: Path,
                chunk_size: int = CHUNK_SIZE) -> Path:
    """
    Save an UploadFile to dest_dir.

    Returns the absolute path of the saved file.
    Raises ValueError if the resolved path escapes dest_dir.
    """
    safe_name = sanitize_filename(upload.filename)
    dest_path = (dest_dir / safe_name).resolve()

    # Path traversal guard: the resolved path must start with dest_dir
    if not str(dest_path).startswith(str(dest_dir.resolve())):
        raise ValueError(
            f"Resolved path '{dest_path}' escapes upload directory"
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    upload.seek(0)

    with open(dest_path, "wb") as f:
        for chunk in iter_chunks(upload, chunk_size):
            f.write(chunk)

    return dest_path
```

Notice: even after `sanitize_filename`, we still resolve and check the path. Defence in depth -- if sanitization has a bug, the path check catches it.

### Handling Duplicate Filenames

```python
def unique_path(dest_dir: Path, filename: str) -> Path:
    """Return a path that does not already exist, appending _1, _2, etc."""
    path = dest_dir / filename
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    for i in range(1, 10_000):
        candidate = dest_dir / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not find unique filename after 10000 attempts")
```

---

## Multiple File Uploads

HTML forms can submit many files under the same field name:

```html
<input type="file" name="photos" multiple>
```

Handle them as a list:

```python
def handle_multiple_uploads(
    uploads: list[UploadFile],
    dest_dir: Path,
    allowed_types: set[str],
    max_size: int = MAX_UPLOAD_SIZE,
) -> list[dict]:
    results = []
    for upload in uploads:
        try:
            validate_size(upload, max_size)
            validate_content_type(upload, allowed_types)
            saved = save_upload(upload, dest_dir)
            results.append({"filename": upload.filename, "saved_as": str(saved),
                            "size": upload.size, "ok": True})
        except (FileSizeTooLargeError, InvalidContentTypeError) as exc:
            results.append({"filename": upload.filename, "error": str(exc),
                            "ok": False})
        finally:
            upload.close()
    return results
```

---

## How FastAPI / Starlette Handle File Uploads

For reference -- you won't use these directly in the kata, but understanding the framework layer helps.

### FastAPI route

```python
from fastapi import FastAPI, UploadFile, File, HTTPException

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # file is already an UploadFile instance
    content = await file.read()
    await file.seek(0)

    if file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(400, "Only JPEG and PNG allowed")

    dest = Path("/tmp/uploads") / sanitize_filename(file.filename)
    with open(dest, "wb") as f:
        async for chunk in file:        # UploadFile is async-iterable
            f.write(chunk)

    return {"saved": str(dest), "size": len(content)}

@app.post("/upload-many")
async def upload_many(files: list[UploadFile] = File(...)):
    return [{"filename": f.filename} for f in files]
```

FastAPI's `UploadFile` wraps a `SpooledTemporaryFile` internally, exactly as in our implementation. The default spool size in Starlette is 1 MB.

### The multipart/form-data format

When the browser posts a file, it encodes it as multipart:

```
POST /upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitBoundaryXYZ

------WebKitBoundaryXYZ
Content-Disposition: form-data; name="file"; filename="photo.jpg"
Content-Type: image/jpeg

<binary bytes of the jpeg>
------WebKitBoundaryXYZ--
```

The `boundary` string is chosen by the browser to not appear in the file data. The framework's multipart parser reads this stream and creates `UploadFile` objects for each part.

---

## Security Checklist

| Threat | Mitigation |
|---|---|
| **Path traversal** (`../../etc/passwd`) | `os.path.basename` + resolved path check |
| **Null byte injection** (`file\x00.exe`) | Strip `\x00` and control chars in sanitizer |
| **Content-type spoofing** | Validate MIME type; optionally check magic bytes |
| **Zip bomb / archive bombs** | Enforce size limit on raw bytes *before* decompression |
| **Disk exhaustion** | Per-file and per-request size limits |
| **Double extension** (`.php.jpg`) | Collapse multiple dots; check final extension |
| **Windows reserved names** | `CON`, `NUL`, etc. cause errors on Windows hosts |
| **Symlink attacks** | Write to a dedicated temp dir; do not follow symlinks |
| **Overwrite existing files** | Use `unique_path()` or store with UUIDs |
| **Serving uploaded files** | Never serve from the upload dir without content-type enforcement |

### Magic Byte Verification

For images, the first few bytes identify the format regardless of the `Content-Type` header:

```python
MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",   # followed by 4 size bytes then "WEBP"
}

def sniff_content_type(data: bytes) -> str | None:
    for magic, mime in MAGIC_BYTES.items():
        if data.startswith(magic):
            return mime
    return None
```

Use this to double-check the declared `content_type`:

```python
upload.seek(0)
header = upload.read(16)
upload.seek(0)

sniffed = sniff_content_type(header)
if sniffed and sniffed != upload.content_type:
    raise InvalidContentTypeError(
        f"Declared '{upload.content_type}' but file looks like '{sniffed}'"
    )
```

---

## Summary

| Component | Stdlib tool | Responsibility |
|---|---|---|
| `UploadFile` | `tempfile.SpooledTemporaryFile` | Buffer bytes + carry metadata |
| Size validation | `file.seek(0, 2)` / `tell()` | Enforce per-file byte limit |
| Type validation | String set membership | Allow only declared MIME types |
| Magic byte sniff | Slice first 16 bytes | Catch content-type spoofing |
| Filename sanitize | `os.path.basename`, `re.sub` | Prevent path traversal, bad chars |
| Streaming read | Generator + `file.read(chunk)` | Process large files without RAM spike |
| Save to disk | `pathlib.Path` + resolved check | Write safely within upload directory |
| Multiple files | `list[UploadFile]` + loop | Handle multi-file form fields |

The pipeline order matters: **sanitize filename → validate size → validate type → stream to disk**. Reject early, before bytes touch permanent storage.

## Exercises

1. **Add magic byte verification** -- extend `validate_content_type()` to also read the first 16 bytes and call `sniff_content_type()`. Raise `InvalidContentTypeError` if the sniffed type doesn't match the declared type.

2. **Add a UUID rename option** -- modify `save_upload()` to accept a `rename_to_uuid=False` parameter. When `True`, ignore the original filename and save as `<uuid4><ext>` to prevent collisions and hide the original name.

3. **Add per-request total size limit** -- write a `validate_total_size(uploads, limit)` function that raises an error if the combined size of all uploads in a list exceeds the limit.

4. **Stream directly to disk** -- modify `save_upload()` to accept an open file object instead of a path, so callers can pass a `SpooledTemporaryFile` or any writable stream.

5. **Add a multipart integration** -- wire `UploadFile` to the `MultipartParser` from Kata 79: write a function that takes a raw multipart body and boundary and returns a list of `UploadFile` objects.

## What's Next

You've built a complete file upload pipeline -- the same machinery that FastAPI's `UploadFile`, Django's `InMemoryUploadedFile`, and Starlette's upload handling use internally. The key insight is that uploads are just bytes: buffer them safely, validate before persisting, and always sanitize filenames before they touch the filesystem.

This completes the Ignite framework tutorial series. From raw sockets (Kata 36) through ASGI (Kata 37), routing, middleware, templating, sessions, WebSockets, and now file uploads -- you have built a production-grade web framework from scratch.

---

[prev: 78-realtime-chat](./78-realtime-chat.md) | next: none
