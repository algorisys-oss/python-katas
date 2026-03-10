"""
Kata 80 -- File Upload Handling
Run: python playground/skeletons/80_file_upload_handling.py

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
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# ===========================================================================
# SECTION 1: UploadFile -- the core abstraction
# ===========================================================================

MAX_SPOOL_SIZE = 1 * 1024 * 1024  # 1 MB
CHUNK_SIZE = 64 * 1024             # 64 KB


@dataclass
class UploadFile:
    """
    Represents an uploaded file.

    Fields:
      filename     : original name declared by the client
      content_type : MIME type from the Content-Type header
      _file        : SpooledTemporaryFile holding the raw bytes
    """

    filename: str
    content_type: str
    _file: tempfile.SpooledTemporaryFile = field(repr=False)

    @classmethod
    def from_bytes(
        cls,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> "UploadFile":
        """Create an UploadFile from raw bytes (useful for testing)."""
        # TODO: Create a SpooledTemporaryFile with max_size=MAX_SPOOL_SIZE,
        # write `data` into it, seek back to 0, and return a new UploadFile.
        pass

    def read(self, size: int = -1) -> bytes:
        """Read up to `size` bytes (or all remaining if size == -1)."""
        # TODO: Delegate to self._file.read(size)
        pass

    def seek(self, offset: int, whence: int = 0) -> None:
        """Seek to position `offset`."""
        # TODO: Delegate to self._file.seek(offset, whence)
        pass

    def tell(self) -> int:
        """Return the current stream position."""
        return self._file.tell()

    def close(self) -> None:
        """Close and delete the underlying temporary file."""
        # TODO: Close self._file
        pass

    @property
    def size(self) -> int:
        """
        Total byte size of the uploaded content.

        Hint: save the current position, seek to the end (whence=2),
        record that position, then restore the original position.
        """
        # TODO: Compute and return total size without consuming the file
        pass

    def __repr__(self) -> str:
        return (
            f"UploadFile(filename={self.filename!r}, "
            f"content_type={self.content_type!r}, "
            f"size={self.size})"
        )


# ===========================================================================
# SECTION 2: Validation
# ===========================================================================

class UploadError(Exception):
    """Base class for upload validation errors."""


class FileSizeTooLargeError(UploadError):
    """Raised when the uploaded file exceeds the size limit."""


class InvalidContentTypeError(UploadError):
    """Raised when the content-type is not in the allowed set."""


class UnsafeFilenameError(UploadError):
    """Raised when the filename cannot be safely sanitized."""


MAX_UPLOAD_SIZE = 10 * 1024 * 1024
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

    The cursor position must be preserved after this call.
    """
    # TODO:
    # 1. Get upload.size
    # 2. If size > limit, raise FileSizeTooLargeError with a descriptive message
    #    (include the file size in MB and the limit in MB)
    pass


def validate_content_type(
    upload: UploadFile,
    allowed: set[str],
) -> None:
    """
    Raise InvalidContentTypeError if upload.content_type is not in `allowed`.
    """
    # TODO:
    # Check upload.content_type against the allowed set.
    # Raise InvalidContentTypeError with a message listing the allowed types.
    pass


def sanitize_filename(filename: str) -> str:
    """
    Return a safe version of `filename` suitable for use as a path component.

    Steps to implement:
      1. os.path.basename() -- strip directory components
      2. Remove null bytes (\\x00) and control characters (\\x00-\\x1f, \\x7f)
      3. re.sub to replace [^\\w.\\-] with underscores
      4. Collapse consecutive dots with re.sub
      5. lstrip(".-") -- no hidden files
      6. Fall back to "upload" if empty
      7. Check _WINDOWS_RESERVED: prefix with "file_" if matched
    """
    # TODO: Implement all seven sanitization steps described above.
    # Hint: use os.path.basename, str.replace, re.sub, str.lstrip, str.upper,
    # str.rsplit to get the stem for the Windows reserved name check.
    pass


# ===========================================================================
# SECTION 3: Magic-byte content-type sniffing
# ===========================================================================

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

    Check each entry in _MAGIC_SIGNATURES (data.startswith(magic)).
    Also handle WebP: first 4 bytes == b"RIFF" and bytes 8-12 == b"WEBP".
    Return None if no signature matches.
    """
    # TODO: Iterate _MAGIC_SIGNATURES and check data.startswith(magic).
    # Add a special case for WebP (RIFF....WEBP format).
    pass


def validate_magic_bytes(upload: UploadFile, allowed: set[str]) -> None:
    """
    Read the first 16 bytes and check the sniffed type is in `allowed`.

    Always restore the cursor to position 0 after checking.
    If sniff_content_type returns None, skip the check (cannot determine).
    """
    # TODO:
    # 1. seek(0), read(16), seek(0)
    # 2. sniff_content_type(header)
    # 3. If sniffed is not None and not in allowed, raise InvalidContentTypeError
    pass


# ===========================================================================
# SECTION 4: Streaming reads
# ===========================================================================

def iter_chunks(
    upload: UploadFile,
    chunk_size: int = CHUNK_SIZE,
) -> Iterator[bytes]:
    """
    Yield `chunk_size`-byte chunks from the upload.

    Always start from the beginning (seek to 0 first).
    Stop when read() returns an empty bytes object.
    """
    # TODO:
    # seek(0)
    # loop: chunk = upload.read(chunk_size); if not chunk: break; yield chunk
    pass


def count_bytes_streaming(upload: UploadFile) -> int:
    """Count the total bytes by streaming through iter_chunks."""
    # TODO: Sum len(chunk) for each chunk from iter_chunks(upload)
    pass


def sha256_of_upload(upload: UploadFile) -> str:
    """Compute the SHA-256 hex digest of the upload by streaming."""
    # TODO:
    # Create hashlib.sha256() object.
    # Feed each chunk from iter_chunks(upload) into h.update(chunk).
    # Return h.hexdigest().
    pass


# ===========================================================================
# SECTION 5: Saving to disk safely
# ===========================================================================

def unique_dest_path(dest_dir: Path, filename: str) -> Path:
    """
    Return a Path inside dest_dir that does not yet exist.

    If dest_dir/filename already exists, try stem_1.suffix, stem_2.suffix, etc.
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

    Steps:
      1. sanitize_filename(upload.filename)
      2. Resolve dest_dir and create it (mkdir parents=True, exist_ok=True)
      3. Compute dest_path (use unique_dest_path unless allow_overwrite)
      4. Path-traversal guard: verify dest_path starts with resolved dest_dir
      5. seek(0), open dest_path for binary write, stream chunks into it
      6. Return dest_path

    Raise ValueError if the resolved path escapes dest_dir.
    """
    # TODO: Implement all six steps above.
    # Key: use dest_dir.resolve() and check str(dest_path).startswith(...)
    pass


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
    Validate and save each UploadFile in the batch.

    For each upload:
      - validate_size
      - validate_content_type
      - validate_magic_bytes
      - sha256_of_upload
      - save_upload
      - Append UploadResult(ok=True, ...)
    On UploadError:
      - Append UploadResult(ok=False, error=str(exc))
    Always call upload.close() in a finally block.
    """
    # TODO: Implement the loop described above.
    results: list[UploadResult] = []
    # ... your code here ...
    return results


# ===========================================================================
# SECTION 7: Multipart simulation
# ===========================================================================
# You do NOT need to modify this section -- it is provided so the demo runs.

def _make_multipart_body(
    parts: list[dict],
    boundary: bytes = b"----KataBoundary001",
) -> tuple[bytes, bytes]:
    """Build a multipart/form-data body from a list of part dicts."""
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


def _parse_multipart(body: bytes, boundary: bytes) -> list[UploadFile]:
    """Parse a multipart/form-data body into UploadFile objects."""
    delimiter = b"--" + boundary
    parts_raw = body.split(delimiter)
    uploads: list[UploadFile] = []

    for part in parts_raw:
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue
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

        filename = "upload"
        for token in disp.split(";"):
            token = token.strip()
            if token.startswith("filename="):
                filename = token[len("filename="):].strip().strip('"')

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
    print("--- Section 1: UploadFile Class ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_size_validation():
    print("\n--- Section 2: Size Validation ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_content_type_validation():
    print("\n--- Section 3: Content-Type Validation ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_filename_sanitization():
    print("\n--- Section 4: Filename Sanitization ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_magic_byte_sniffing():
    print("\n--- Section 5: Magic Byte Sniffing ---")

    try:
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

        fake = UploadFile.from_bytes("not_a_jpeg.png", "image/png", jpeg_magic)
        sniffed = sniff_content_type(fake.read(16))
        fake.seek(0)
        print(f"  PNG claim but JPEG bytes -> sniffed: {sniffed!r}")
        assert sniffed == "image/jpeg"
        fake.close()

        print("  [PASS] Magic byte sniffing works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_streaming_reads():
    print("\n--- Section 6: Streaming Reads ---")

    try:
        payload = bytes(range(256)) * 1200
        upload = UploadFile.from_bytes("big_file.bin", "application/octet-stream", payload)

        upload.seek(0)
        chunk_count = sum(1 for _ in iter_chunks(upload, chunk_size=64 * 1024))
        print(f"  File size    : {len(payload)} bytes")
        print(f"  Chunk size   : 64 KB, chunk count: {chunk_count}")
        assert chunk_count == 5

        counted = count_bytes_streaming(upload)
        assert counted == len(payload)
        print(f"  Streaming count: {counted} bytes (matches)")

        digest_stream = sha256_of_upload(upload)
        digest_direct = hashlib.sha256(payload).hexdigest()
        assert digest_stream == digest_direct
        print(f"  SHA-256 (streaming): {digest_stream[:16]}...  matches direct hash")

        upload.close()
        print("  [PASS] Streaming reads work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_save_to_disk(tmp_dir: Path):
    print("\n--- Section 7: Save to Disk ---")

    try:
        upload_dir = tmp_dir / "uploads"

        data = b"Image data " * 200
        upload = UploadFile.from_bytes("my photo.jpg", "image/jpeg", data)
        saved = save_upload(upload, upload_dir)
        assert saved.exists()
        assert saved.read_bytes() == data
        print(f"  Saved 'my photo.jpg' -> {saved.name}  ({saved.stat().st_size} bytes)")
        upload.close()

        evil_data = b"evil content"
        evil_upload = UploadFile.from_bytes("../../evil.txt", "text/plain", evil_data)
        saved_evil = save_upload(evil_upload, upload_dir)
        assert str(saved_evil).startswith(str(upload_dir.resolve()))
        assert saved_evil.name == "evil.txt"
        print(f"  Path traversal attempt '../../evil.txt' -> {saved_evil.name}  (safe)")
        evil_upload.close()

        dup_data = b"second copy"
        dup1 = UploadFile.from_bytes("my_photo.jpg", "image/jpeg", data)
        dup2 = UploadFile.from_bytes("my_photo.jpg", "image/jpeg", dup_data)
        saved_dup1 = save_upload(dup1, upload_dir)
        saved_dup2 = save_upload(dup2, upload_dir)
        assert saved_dup1 != saved_dup2
        print(f"  Duplicate 'my_photo.jpg' -> {saved_dup1.name} / {saved_dup2.name}")
        dup1.close()
        dup2.close()

        files = sorted(upload_dir.iterdir())
        print(f"  Upload dir contains {len(files)} files:")
        for f in files:
            print(f"    {f.name}  ({f.stat().st_size} bytes)")

        print("  [PASS] Save to disk works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_multiple_uploads(tmp_dir: Path):
    print("\n--- Section 8: Multiple File Uploads ---")

    try:
        batch_dir = tmp_dir / "batch"

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

        assert ok_count == 3
        assert fail_count == 2
        print("  [PASS] Multiple file uploads work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_multipart_pipeline(tmp_dir: Path):
    print("\n--- Section 9: Full Multipart Pipeline ---")

    try:
        pipeline_dir = tmp_dir / "pipeline"

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
                "filename": "../../thumb.png",
                "content_type": "image/png",
                "data": png_data,
            },
        ]

        body, boundary = _make_multipart_body(parts)
        print(f"  Multipart body: {len(body)} bytes, boundary={boundary.decode()}")

        uploads = _parse_multipart(body, boundary)
        print(f"  Parsed {len(uploads)} upload(s):")
        for u in uploads:
            print(f"    {u!r}")

        assert len(uploads) == 2
        assert uploads[0].size == len(jpeg_data)
        assert uploads[1].size == len(png_data)

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
                assert ".." not in saved_name
            else:
                print(f"    [FAIL] '{r.original_filename}': {r.error}")

        ok = [r for r in results if r.ok]
        assert len(ok) == 2
        assert "vacation_photo.jpg" in [Path(r.saved_path).name for r in ok]
        assert "thumb.png" in [Path(r.saved_path).name for r in ok]

        print("  [PASS] Full multipart pipeline works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


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
    print(f"\nAll 9 sections attempted in {elapsed:.2f}s. File upload handling complete!")


if __name__ == "__main__":
    main()
