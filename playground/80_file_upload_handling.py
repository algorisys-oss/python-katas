"""
Kata 80 -- File Upload Handling
Run: python playground/80_file_upload_handling.py

Build the full file upload pipeline: UploadFile abstraction backed by
SpooledTemporaryFile, file validation (size limits, MIME types, filename
sanitization), streaming reads, safe save-to-disk, multiple file handling,
and a simulated multipart pipeline -- all without any HTTP server.

Completes within 5 seconds.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import struct
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# ===========================================================================
# SECTION 1: UploadFile -- the core abstraction
# ===========================================================================
# Wraps a SpooledTemporaryFile with the metadata a web framework exposes:
# original filename and declared content-type.

MAX_SPOOL_SIZE = 1 * 1024 * 1024  # stay in RAM up to 1 MB, then spill to disk
CHUNK_SIZE = 64 * 1024             # 64 KB streaming chunk


@dataclass
class UploadFile:
    """
    Represents an uploaded file.

    Mirrors the interface of FastAPI/Starlette's UploadFile:
      - filename     : original name as declared by the client
      - content_type : MIME type from the Content-Type header
      - _file        : SpooledTemporaryFile holding the raw bytes
    """

    filename: str
    content_type: str
    _file: tempfile.SpooledTemporaryFile = field(repr=False)

    # ------------------------------------------------------------------
    # Factory

    @classmethod
    def from_bytes(
        cls,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> "UploadFile":
        """
        Create an UploadFile from raw bytes.

        Useful for testing and for simulating parsed multipart parts.
        """
        spool: tempfile.SpooledTemporaryFile = tempfile.SpooledTemporaryFile(
            max_size=MAX_SPOOL_SIZE
        )
        spool.write(data)
        spool.seek(0)
        return cls(filename=filename, content_type=content_type, _file=spool)

    # ------------------------------------------------------------------
    # File-like interface

    def read(self, size: int = -1) -> bytes:
        """Read up to `size` bytes (or all remaining if size == -1)."""
        return self._file.read(size)

    def seek(self, offset: int, whence: int = 0) -> None:
        """Seek to position `offset`."""
        self._file.seek(offset, whence)

    def tell(self) -> int:
        """Return the current stream position."""
        return self._file.tell()

    def close(self) -> None:
        """Close and delete the underlying temporary file."""
        self._file.close()

    # ------------------------------------------------------------------
    # Convenience

    @property
    def size(self) -> int:
        """Total byte size of the uploaded content."""
        current = self._file.tell()
        self._file.seek(0, 2)       # seek to end
        end = self._file.tell()
        self._file.seek(current)    # restore
        return end

    def __repr__(self) -> str:
        return (
            f"UploadFile(filename={self.filename!r}, "
            f"content_type={self.content_type!r}, "
            f"size={self.size})"
        )


# ===========================================================================
# SECTION 2: Validation
# ===========================================================================
# Three independent checks: size, MIME type, filename safety.
# All raise descriptive exceptions so callers can return useful error messages.

class UploadError(Exception):
    """Base class for upload validation errors."""


class FileSizeTooLargeError(UploadError):
    """Raised when the uploaded file exceeds the size limit."""


class InvalidContentTypeError(UploadError):
    """Raised when the content-type is not in the allowed set."""


class UnsafeFilenameError(UploadError):
    """Raised when the filename cannot be safely sanitized."""


# Default limits used by the demo
MAX_UPLOAD_SIZE = 10 * 1024 * 1024          # 10 MB
ALLOWED_IMAGE_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}
ALLOWED_DOCUMENT_TYPES: set[str] = {
    "application/pdf",
    "text/plain",
    "text/csv",
}

# Windows reserved device names -- writing to these causes errors on Windows
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5",
    "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
    "LPT6", "LPT7", "LPT8", "LPT9",
}


def validate_size(upload: UploadFile, limit: int = MAX_UPLOAD_SIZE) -> None:
    """
    Raise FileSizeTooLargeError if the upload exceeds `limit` bytes.

    Checks the size without consuming the file -- the cursor position
    is preserved so callers can still read afterwards.
    """
    size = upload.size
    if size > limit:
        mb = size / (1024 * 1024)
        raise FileSizeTooLargeError(
            f"File '{upload.filename}' is {mb:.2f} MB, "
            f"limit is {limit // (1024 * 1024)} MB"
        )


def validate_content_type(
    upload: UploadFile,
    allowed: set[str],
) -> None:
    """
    Raise InvalidContentTypeError if the declared content-type is not allowed.

    Note: this trusts the declared MIME type. For stronger security, combine
    with sniff_content_type() to verify against magic bytes.
    """
    if upload.content_type not in allowed:
        raise InvalidContentTypeError(
            f"Content-Type '{upload.content_type}' is not allowed. "
            f"Allowed types: {sorted(allowed)}"
        )


def sanitize_filename(filename: str) -> str:
    """
    Return a safe version of `filename` suitable for use as a filesystem path.

    Steps:
      1. Strip directory components (path traversal).
      2. Remove null bytes and ASCII control characters.
      3. Replace characters outside [a-zA-Z0-9._-] with underscores.
      4. Collapse consecutive dots (blocks double-extension tricks).
      5. Strip leading dots and dashes (hidden files on Unix).
      6. Fall back to "upload" if nothing remains.
      7. Prefix Windows reserved names.
    """
    # 1. basename only -- kills ../../etc/passwd style attacks
    filename = os.path.basename(filename)

    # 2. Remove null bytes and control characters (0x00-0x1f, 0x7f)
    filename = filename.replace("\x00", "")
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)

    # 3. Allow only safe characters
    filename = re.sub(r"[^\w.\-]", "_", filename)

    # 4. Collapse multiple consecutive dots
    filename = re.sub(r"\.{2,}", ".", filename)

    # 5. Strip leading dots and dashes
    filename = filename.lstrip(".-")

    # 6. Fallback
    if not filename:
        filename = "upload"

    # 7. Windows reserved names (check stem only, case-insensitive)
    stem = filename.rsplit(".", 1)[0].upper()
    if stem in _WINDOWS_RESERVED:
        filename = f"file_{filename}"

    return filename


# ===========================================================================
# SECTION 3: Magic-byte content-type sniffing
# ===========================================================================
# Read the first few bytes of the file and compare against known signatures.
# This catches cases where a client lies about the content-type.

_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"%PDF-", "application/pdf"),
    (b"PK\x03\x04", "application/zip"),
]


def sniff_content_type(data: bytes) -> str | None:
    """
    Return the MIME type inferred from the first bytes of `data`, or None.

    Only recognises a small set of common formats. For production use a
    library like `python-magic` (wraps libmagic).
    """
    for magic, mime in _MAGIC_SIGNATURES:
        if data.startswith(magic):
            return mime
    # WebP: "RIFF????WEBP"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_magic_bytes(upload: UploadFile, allowed: set[str]) -> None:
    """
    Read the first 16 bytes and check that the sniffed type is in `allowed`.

    Leaves the cursor at position 0 after checking.
    """
    upload.seek(0)
    header = upload.read(16)
    upload.seek(0)

    sniffed = sniff_content_type(header)
    if sniffed is None:
        return  # cannot determine -- trust content_type header

    if sniffed not in allowed:
        raise InvalidContentTypeError(
            f"File content looks like '{sniffed}', "
            f"which is not in allowed types: {sorted(allowed)}"
        )

    if sniffed != upload.content_type:
        # Mismatch: declared type differs from actual content
        # We still allow it if sniffed type is allowed (above already checked)
        pass  # could raise here for stricter enforcement


# ===========================================================================
# SECTION 4: Streaming reads
# ===========================================================================
# Iterating in fixed-size chunks avoids loading the entire file into RAM.

def iter_chunks(
    upload: UploadFile,
    chunk_size: int = CHUNK_SIZE,
) -> Iterator[bytes]:
    """
    Yield chunks of `chunk_size` bytes from the upload.

    Always starts from the beginning of the file (seeks to 0 first).
    """
    upload.seek(0)
    while True:
        chunk = upload.read(chunk_size)
        if not chunk:
            break
        yield chunk


def count_bytes_streaming(upload: UploadFile) -> int:
    """Count the total bytes without loading the file into a single buffer."""
    total = 0
    for chunk in iter_chunks(upload):
        total += len(chunk)
    return total


def sha256_of_upload(upload: UploadFile) -> str:
    """Compute the SHA-256 hex digest of the upload by streaming."""
    h = hashlib.sha256()
    for chunk in iter_chunks(upload):
        h.update(chunk)
    return h.hexdigest()


# ===========================================================================
# SECTION 5: Saving to disk safely
# ===========================================================================

def unique_dest_path(dest_dir: Path, filename: str) -> Path:
    """
    Return a Path inside dest_dir that does not yet exist.

    If dest_dir/filename already exists, appends _1, _2, ... to the stem.
    """
    path = dest_dir / filename
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for i in range(1, 10_001):
        candidate = dest_dir / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not find a unique filename after 10 000 attempts")


def save_upload(
    upload: UploadFile,
    dest_dir: Path,
    chunk_size: int = CHUNK_SIZE,
    allow_overwrite: bool = False,
) -> Path:
    """
    Write the upload to dest_dir using the sanitized filename.

    Security guarantees:
      - Filename is sanitized before use.
      - The resolved destination path is checked to remain inside dest_dir.
      - Writes in chunks to avoid large in-memory copies.

    Returns the absolute path of the written file.
    Raises ValueError if the resolved path would escape dest_dir.
    """
    safe_name = sanitize_filename(upload.filename)
    dest_dir_resolved = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    if allow_overwrite:
        dest_path = dest_dir_resolved / safe_name
    else:
        dest_path = unique_dest_path(dest_dir_resolved, safe_name)

    # Path-traversal guard (defence in depth -- sanitize_filename should have
    # already stripped path separators, but we verify after resolve())
    if not str(dest_path).startswith(str(dest_dir_resolved) + os.sep) and \
       dest_path != dest_dir_resolved:
        raise ValueError(
            f"Resolved path '{dest_path}' escapes upload directory "
            f"'{dest_dir_resolved}'"
        )

    upload.seek(0)
    with open(dest_path, "wb") as fout:
        for chunk in iter_chunks(upload, chunk_size):
            fout.write(chunk)

    return dest_path


# ===========================================================================
# SECTION 6: Multiple file handling
# ===========================================================================

@dataclass
class UploadResult:
    """Outcome of processing one file in a multi-upload batch."""
    original_filename: str
    ok: bool
    saved_path: str | None = None
    size: int | None = None
    sha256: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def process_uploads(
    uploads: list[UploadFile],
    dest_dir: Path,
    allowed_types: set[str],
    max_size: int = MAX_UPLOAD_SIZE,
) -> list[UploadResult]:
    """
    Validate and save each upload in a batch.

    Failures are captured per-file so one bad file does not block the rest.
    """
    results: list[UploadResult] = []

    for upload in uploads:
        try:
            validate_size(upload, max_size)
            validate_content_type(upload, allowed_types)
            validate_magic_bytes(upload, allowed_types)

            digest = sha256_of_upload(upload)
            saved = save_upload(upload, dest_dir)

            results.append(UploadResult(
                original_filename=upload.filename,
                ok=True,
                saved_path=str(saved),
                size=upload.size,
                sha256=digest,
            ))
        except UploadError as exc:
            results.append(UploadResult(
                original_filename=upload.filename,
                ok=False,
                error=str(exc),
            ))
        finally:
            upload.close()

    return results


# ===========================================================================
# SECTION 7: Multipart simulation
# ===========================================================================
# Real upload handling requires a multipart parser. We build a minimal one
# so the demo can construct realistic UploadFile objects without HTTP.

def _make_multipart_body(
    parts: list[dict],
    boundary: bytes = b"----KataBoundary001",
) -> tuple[bytes, bytes]:
    """
    Build a multipart/form-data body from a list of parts.

    Each part dict:
      name         : form field name
      filename     : original filename
      content_type : MIME type string
      data         : raw bytes

    Returns (body_bytes, boundary).
    """
    buf = io.BytesIO()
    crlf = b"\r\n"

    for part in parts:
        buf.write(b"--" + boundary + crlf)
        disposition = (
            f'Content-Disposition: form-data; name="{part["name"]}"; '
            f'filename="{part["filename"]}"'
        ).encode()
        buf.write(disposition + crlf)
        buf.write(f'Content-Type: {part["content_type"]}'.encode() + crlf)
        buf.write(crlf)
        buf.write(part["data"])
        buf.write(crlf)

    buf.write(b"--" + boundary + b"--" + crlf)
    return buf.getvalue(), boundary


def _parse_multipart(
    body: bytes,
    boundary: bytes,
) -> list[UploadFile]:
    """
    Parse a multipart/form-data body into a list of UploadFile objects.

    This is a minimal parser for demo purposes. Production parsers handle
    streaming bodies, quoted strings, and character encoding edge cases.
    """
    delimiter = b"--" + boundary
    parts_raw = body.split(delimiter)
    uploads: list[UploadFile] = []

    for part in parts_raw:
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue

        # Split headers from body at the blank line
        if b"\r\n\r\n" not in part:
            continue
        headers_raw, _, part_data = part.partition(b"\r\n\r\n")

        headers: dict[str, str] = {}
        for line in headers_raw.split(b"\r\n"):
            if b":" in line:
                key, _, val = line.partition(b":")
                headers[key.strip().lower().decode()] = val.strip().decode()

        disp = headers.get("content-disposition", "")
        content_type = headers.get("content-type", "application/octet-stream")

        # Extract filename from Content-Disposition
        filename = "upload"
        for token in disp.split(";"):
            token = token.strip()
            if token.startswith("filename="):
                filename = token[len("filename="):].strip().strip('"')

        # Strip trailing CRLF that was added before the boundary
        if part_data.endswith(b"\r\n"):
            part_data = part_data[:-2]

        uploads.append(
            UploadFile.from_bytes(
                filename=filename,
                content_type=content_type,
                data=part_data,
            )
        )

    return uploads


# ===========================================================================
# SECTION 8: Demos
# ===========================================================================

def demo_upload_file_class():
    """Show UploadFile creation, read, seek, size, and close."""
    print("--- Section 1: UploadFile Class ---")

    data = b"Hello, file upload world! " * 100
    upload = UploadFile.from_bytes(
        filename="greetings.txt",
        content_type="text/plain",
        data=data,
    )

    assert upload.filename == "greetings.txt"
    assert upload.content_type == "text/plain"
    assert upload.size == len(data)
    print(f"  filename     : {upload.filename}")
    print(f"  content_type : {upload.content_type}")
    print(f"  size         : {upload.size} bytes")

    first_10 = upload.read(10)
    assert first_10 == b"Hello, fil"
    print(f"  first 10 B   : {first_10}")

    upload.seek(0)
    all_data = upload.read()
    assert all_data == data
    print(f"  full read OK : {len(all_data)} bytes")

    upload.close()
    print("  [PASS] UploadFile class works")


def demo_size_validation():
    """Show size limit enforcement."""
    print("\n--- Section 2: Size Validation ---")

    small = UploadFile.from_bytes("tiny.txt", "text/plain", b"x" * 100)
    validate_size(small, limit=1024)
    print(f"  100 B file passes 1 KB limit: OK")
    small.close()

    big = UploadFile.from_bytes("huge.bin", "application/octet-stream",
                                b"x" * (2 * 1024 * 1024))
    try:
        validate_size(big, limit=1024 * 1024)
        print("  ERROR: should have raised")
    except FileSizeTooLargeError as exc:
        print(f"  2 MB file rejected (1 MB limit): {exc}")
    big.close()

    print("  [PASS] Size validation works")


def demo_content_type_validation():
    """Show MIME type enforcement."""
    print("\n--- Section 3: Content-Type Validation ---")

    jpeg = UploadFile.from_bytes("photo.jpg", "image/jpeg", b"\xff\xd8\xff" + b"x" * 50)
    validate_content_type(jpeg, ALLOWED_IMAGE_TYPES)
    print("  image/jpeg accepted: OK")
    jpeg.close()

    exe = UploadFile.from_bytes("virus.exe", "application/x-msdownload", b"MZ" + b"\x00" * 50)
    try:
        validate_content_type(exe, ALLOWED_IMAGE_TYPES)
        print("  ERROR: should have raised")
    except InvalidContentTypeError as exc:
        print(f"  .exe rejected: {exc}")
    exe.close()

    print("  [PASS] Content-type validation works")


def demo_filename_sanitization():
    """Show filename sanitization handles attacks."""
    print("\n--- Section 4: Filename Sanitization ---")

    cases = [
        ("../../etc/passwd",         "passwd"),
        ("/absolute/path/file.txt",  "file.txt"),
        ("normal_file.jpg",          "normal_file.jpg"),
        ("file\x00.exe",             "file.exe"),
        ("file with spaces.txt",     "file_with_spaces.txt"),
        ("..hidden",                 "hidden"),
        ("image...php.jpg",          "image.php.jpg"),
        ("CON.txt",                  "file_CON.txt"),
        ("NUL",                      "file_NUL"),
        ("",                         "upload"),
        ("....",                     "upload"),
    ]

    all_ok = True
    for raw, expected in cases:
        result = sanitize_filename(raw)
        status = "OK" if result == expected else f"FAIL (got {result!r})"
        print(f"  {raw!r:35s} -> {result!r:25s} {status}")
        if result != expected:
            all_ok = False

    assert all_ok, "One or more sanitization cases failed"
    print("  [PASS] Filename sanitization works")


def demo_magic_byte_sniffing():
    """Show content-type sniffing from file bytes."""
    print("\n--- Section 5: Magic Byte Sniffing ---")

    jpeg_magic = b"\xff\xd8\xff\xe0" + b"\x00" * 50
    png_magic  = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    pdf_magic  = b"%PDF-1.4\n" + b"\x00" * 50
    webp_magic = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 20
    text_data  = b"Hello world\n" + b"\x00" * 50

    cases = [
        (jpeg_magic, "image/jpeg"),
        (png_magic,  "image/png"),
        (pdf_magic,  "application/pdf"),
        (webp_magic, "image/webp"),
        (text_data,  None),
    ]

    for data, expected in cases:
        result = sniff_content_type(data)
        status = "OK" if result == expected else f"FAIL (got {result!r})"
        print(f"  sniff {expected!r:20s}: {result!r:20s} {status}")
        assert result == expected

    # A declared type mismatch is detected
    fake = UploadFile.from_bytes("not_a_jpeg.png", "image/png", jpeg_magic)
    sniffed = sniff_content_type(fake.read(16))
    fake.seek(0)
    print(f"  PNG claim but JPEG bytes -> sniffed: {sniffed!r}")
    assert sniffed == "image/jpeg"
    fake.close()

    print("  [PASS] Magic byte sniffing works")


def demo_streaming_reads():
    """Show chunk iteration, byte counting, and SHA-256 computation."""
    print("\n--- Section 6: Streaming Reads ---")

    # Create a 300 KB file (larger than a single 64 KB chunk)
    payload = bytes(range(256)) * 1200  # 307 200 bytes
    upload = UploadFile.from_bytes("big_file.bin", "application/octet-stream", payload)

    # Count chunks
    upload.seek(0)
    chunk_count = sum(1 for _ in iter_chunks(upload, chunk_size=64 * 1024))
    print(f"  File size    : {len(payload)} bytes")
    print(f"  Chunk size   : 64 KB, chunk count: {chunk_count}")
    assert chunk_count == 5  # ceil(307200 / 65536) = 5

    # Streaming byte count equals actual size
    counted = count_bytes_streaming(upload)
    assert counted == len(payload)
    print(f"  Streaming count: {counted} bytes (matches)")

    # SHA-256 via streaming equals hashlib on full bytes
    digest_stream = sha256_of_upload(upload)
    digest_direct = hashlib.sha256(payload).hexdigest()
    assert digest_stream == digest_direct
    print(f"  SHA-256 (streaming): {digest_stream[:16]}...  matches direct hash")

    upload.close()
    print("  [PASS] Streaming reads work")


def demo_save_to_disk(tmp_dir: Path):
    """Show safe file saving with sanitized paths."""
    print("\n--- Section 7: Save to Disk ---")

    upload_dir = tmp_dir / "uploads"

    # Normal save
    data = b"Image data " * 200
    upload = UploadFile.from_bytes("my photo.jpg", "image/jpeg", data)
    saved = save_upload(upload, upload_dir)
    assert saved.exists()
    assert saved.read_bytes() == data
    print(f"  Saved 'my photo.jpg' -> {saved.name}  ({saved.stat().st_size} bytes)")
    upload.close()

    # Path traversal attempt -- save_upload should neutralise it
    evil_data = b"evil content"
    evil_upload = UploadFile.from_bytes("../../evil.txt", "text/plain", evil_data)
    saved_evil = save_upload(evil_upload, upload_dir)
    # File must be inside upload_dir
    assert str(saved_evil).startswith(str(upload_dir.resolve()))
    assert saved_evil.name == "evil.txt"   # basename only
    print(f"  Path traversal attempt '../../evil.txt' -> {saved_evil.name}  (safe)")
    evil_upload.close()

    # Duplicate filename gets a unique suffix
    dup_data = b"second copy"
    dup1 = UploadFile.from_bytes("my_photo.jpg", "image/jpeg", data)
    dup2 = UploadFile.from_bytes("my_photo.jpg", "image/jpeg", dup_data)
    saved_dup1 = save_upload(dup1, upload_dir)
    saved_dup2 = save_upload(dup2, upload_dir)
    assert saved_dup1 != saved_dup2
    print(f"  Duplicate 'my_photo.jpg' -> {saved_dup1.name} / {saved_dup2.name}")
    dup1.close()
    dup2.close()

    # List what was saved
    files = sorted(upload_dir.iterdir())
    print(f"  Upload dir contains {len(files)} files:")
    for f in files:
        print(f"    {f.name}  ({f.stat().st_size} bytes)")

    print("  [PASS] Save to disk works")


def demo_multiple_uploads(tmp_dir: Path):
    """Show batch upload processing with mixed valid/invalid files."""
    print("\n--- Section 8: Multiple File Uploads ---")

    batch_dir = tmp_dir / "batch"

    # Build a batch of five uploads: three valid images, one too large, one wrong type
    jpeg_header = b"\xff\xd8\xff\xe0" + b"\x00" * 12
    png_header  = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8

    uploads = [
        UploadFile.from_bytes("avatar.jpg",  "image/jpeg", jpeg_header + b"J" * 4096),
        UploadFile.from_bytes("banner.png",  "image/png",  png_header  + b"P" * 8192),
        UploadFile.from_bytes("icon.gif",    "image/gif",  b"GIF89a"   + b"G" * 512),
        UploadFile.from_bytes("too_big.jpg", "image/jpeg", b"x" * (11 * 1024 * 1024)),
        UploadFile.from_bytes("doc.pdf",     "application/pdf", b"%PDF-1.4\n"),
    ]

    results = process_uploads(
        uploads,
        dest_dir=batch_dir,
        allowed_types=ALLOWED_IMAGE_TYPES,
        max_size=10 * 1024 * 1024,
    )

    ok_count = sum(1 for r in results if r.ok)
    fail_count = sum(1 for r in results if not r.ok)
    print(f"  Processed {len(results)} files: {ok_count} OK, {fail_count} failed")

    for r in results:
        if r.ok:
            saved_name = Path(r.saved_path).name
            print(f"    [OK]   {r.original_filename:20s} -> {saved_name}  "
                  f"({r.size} B, sha256={r.sha256[:12]}...)")
        else:
            print(f"    [FAIL] {r.original_filename:20s} -> {r.error}")

    assert ok_count == 3   # avatar.jpg, banner.png, icon.gif
    assert fail_count == 2  # too_big.jpg (size), doc.pdf (content-type)
    print("  [PASS] Multiple file uploads work")


def demo_multipart_pipeline(tmp_dir: Path):
    """Show the full upload pipeline: build multipart -> parse -> validate -> save."""
    print("\n--- Section 9: Full Multipart Pipeline ---")

    pipeline_dir = tmp_dir / "pipeline"

    # --- Step 1: client constructs multipart body ---
    jpeg_data = b"\xff\xd8\xff\xe0" + b"\x00" * 12 + b"R" * 2048
    png_data  = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8  + b"P" * 4096

    parts = [
        {
            "name": "photo",
            "filename": "vacation photo.jpg",
            "content_type": "image/jpeg",
            "data": jpeg_data,
        },
        {
            "name": "thumbnail",
            "filename": "../../thumb.png",   # attacker tries path traversal
            "content_type": "image/png",
            "data": png_data,
        },
    ]

    body, boundary = _make_multipart_body(parts)
    print(f"  Multipart body: {len(body)} bytes, boundary={boundary.decode()}")

    # --- Step 2: server receives and parses ---
    uploads = _parse_multipart(body, boundary)
    print(f"  Parsed {len(uploads)} upload(s):")
    for u in uploads:
        print(f"    {u!r}")

    assert len(uploads) == 2
    assert uploads[0].filename == "vacation photo.jpg"
    assert uploads[1].filename == "../../thumb.png"
    assert uploads[0].size == len(jpeg_data)
    assert uploads[1].size == len(png_data)

    # --- Step 3: validate and save ---
    results = process_uploads(
        uploads,
        dest_dir=pipeline_dir,
        allowed_types=ALLOWED_IMAGE_TYPES,
        max_size=MAX_UPLOAD_SIZE,
    )

    print(f"  Pipeline results:")
    for r in results:
        if r.ok:
            saved_name = Path(r.saved_path).name
            print(f"    [OK]   original='{r.original_filename}' -> saved='{saved_name}'")
            # Path traversal attempt must be neutralised
            assert ".." not in saved_name
        else:
            print(f"    [FAIL] '{r.original_filename}': {r.error}")

    ok = [r for r in results if r.ok]
    assert len(ok) == 2
    # Filename with space was sanitized
    assert "vacation_photo.jpg" in [Path(r.saved_path).name for r in ok]
    # Path traversal attempt was neutralised
    assert "thumb.png" in [Path(r.saved_path).name for r in ok]

    print("  [PASS] Full multipart pipeline works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    import time
    start = time.monotonic()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        demo_upload_file_class()
        demo_size_validation()
        demo_content_type_validation()
        demo_filename_sanitization()
        demo_magic_byte_sniffing()
        demo_streaming_reads()
        demo_save_to_disk(tmp_dir)
        demo_multiple_uploads(tmp_dir)
        demo_multipart_pipeline(tmp_dir)

    elapsed = time.monotonic() - start

    print("\n--- Summary ---")
    print("File upload handling components:")
    print("  - UploadFile: wraps SpooledTemporaryFile with filename + content_type")
    print("  - validate_size: reject files over the byte limit")
    print("  - validate_content_type: allow only declared MIME types")
    print("  - sniff_content_type: detect type from magic bytes")
    print("  - sanitize_filename: strip path traversal, bad chars, reserved names")
    print("  - iter_chunks: stream large files in 64 KB pieces")
    print("  - sha256_of_upload: hash without loading full file into RAM")
    print("  - save_upload: write to disk with resolved path guard")
    print("  - process_uploads: batch validation + save with per-file error capture")
    print("  - multipart simulation: build + parse raw multipart bodies")
    print(f"\nAll 9 sections passed in {elapsed:.2f}s. File upload handling complete!")


if __name__ == "__main__":
    main()
