"""
Kata 79 -- Multipart Form Parsing
Run: python playground/skeletons/79_multipart_form_parsing.py

Parse multipart/form-data from scratch using only the stdlib: boundary
extraction, part splitting, Content-Disposition header parsing, and
separating text fields from file uploads.  Simulates ASGI body reading.

Completes within 5 seconds.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ===========================================================================
# SECTION 1: Boundary Extraction
# ===========================================================================
# The Content-Type header carries the boundary string that separates parts.
# Example Content-Type: 'multipart/form-data; boundary=----FormBoundaryXyz'

def extract_boundary(content_type: str) -> str:
    """Extract the boundary parameter from a Content-Type header value.

    Args:
        content_type: e.g. 'multipart/form-data; boundary=----FormBoundaryXyz'

    Returns:
        The boundary string without surrounding whitespace.

    Raises:
        ValueError: if no boundary parameter is found.
    """
    # TODO: Use re.search() to find the pattern: boundary=<value>
    # The value ends at whitespace or semicolon.
    # Pattern hint: r"boundary=([^\s;]+)"
    # If no match, raise ValueError("No boundary found in Content-Type: ...")
    # Return match.group(1)
    pass


# ===========================================================================
# SECTION 2: Multipart Body Builder
# ===========================================================================
# Builds a standards-compliant multipart body for testing and demonstration.
# You do NOT need to modify this section -- it is provided for you.

def build_multipart_body(
    fields: dict[str, str],
    files: dict[str, tuple[str, str, bytes]],
    boundary: str,
) -> bytes:
    """Construct a multipart/form-data body manually.

    Args:
        fields: {name: text_value}
        files:  {name: (filename, content_type, data_bytes)}
        boundary: the boundary string (without leading --)

    Returns:
        The complete multipart body as bytes, including the final boundary.
    """
    CRLF = b"\r\n"
    parts: list[bytes] = []

    for name, value in fields.items():
        part = (
            f'Content-Disposition: form-data; name="{name}"'.encode() + CRLF +
            CRLF +
            value.encode()
        )
        parts.append(part)

    for name, (filename, content_type, data) in files.items():
        part = (
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode() + CRLF +
            f"Content-Type: {content_type}".encode() + CRLF +
            CRLF +
            data
        )
        parts.append(part)

    # Prepend CRLF so that splitting on b"\r\n--boundary" yields an empty
    # preamble at index 0, making every subsequent index a real part.
    body = CRLF + b"--" + boundary.encode()
    for part in parts:
        body += CRLF + part + CRLF + b"--" + boundary.encode()
    body += b"--" + CRLF

    return body


# ===========================================================================
# SECTION 3: Raw Part Splitting
# ===========================================================================

def split_parts(body: bytes, boundary: str) -> list[bytes]:
    """Split a multipart body into raw part chunks.

    Each chunk contains the raw header block + body for one form field.
    The preamble (before the first boundary) and the epilogue are discarded.

    The delimiter between parts is: \\r\\n--{boundary}
    Splitting on this gives:
        index 0: preamble (discard)
        index 1..N-1: actual parts
        last element that starts with '--': the final boundary (stop)

    Args:
        body: the complete multipart body as bytes
        boundary: the boundary string (without leading --)

    Returns:
        List of raw part bytes, one per form field/file.
    """
    # TODO: Build the delimiter: b"\r\n--" + boundary.encode()
    # TODO: Split body on the delimiter -> raw_chunks
    # TODO: Iterate raw_chunks[1:] (skip preamble at index 0)
    #   - If chunk starts with b"--", break (final boundary)
    #   - If chunk starts with b"\r\n", strip those 2 bytes
    #   - Append to parts list
    # TODO: Return parts
    pass


# ===========================================================================
# SECTION 4: Header and Content-Disposition Parsing
# ===========================================================================

def parse_headers(header_block: str) -> dict[str, str]:
    """Parse a CRLF-delimited block of HTTP headers into a dict.

    Header names are lowercased for case-insensitive lookup.

    Args:
        header_block: raw header text separated by \\r\\n

    Returns:
        {'content-disposition': 'form-data; name="x"', ...}
    """
    # TODO: Split header_block on "\r\n" to get lines
    # TODO: For each line that contains ": ", split on ": " (maxsplit=1)
    # TODO: Store headers[name.lower()] = value
    # TODO: Return the headers dict
    pass


def parse_content_disposition(header_value: str) -> dict[str, str]:
    """Extract named parameters from a Content-Disposition header value.

    Only extracts quoted parameters: key="value"

    Args:
        header_value: e.g. 'form-data; name="avatar"; filename="photo.png"'

    Returns:
        {'name': 'avatar', 'filename': 'photo.png'}
    """
    # TODO: Use re.finditer() with pattern r'(\w+)="([^"]*)"'
    # TODO: For each match, store params[match.group(1)] = match.group(2)
    # HINT: match.group(1) is the key, match.group(2) is the value
    # TODO: Return params
    pass


# ===========================================================================
# SECTION 5: MultipartParser -- Full Parser
# ===========================================================================

@dataclass
class FormField:
    """A parsed text form field."""
    name: str
    value: str


@dataclass
class FormFile:
    """A parsed file upload."""
    name: str
    filename: str
    content_type: str
    data: bytes

    @property
    def size(self) -> int:
        return len(self.data)


class MultipartParser:
    """Parses a multipart/form-data body into fields and file uploads.

    Usage:
        parser = MultipartParser(body_bytes, boundary_string)
        fields, files = parser.get_fields_and_files()
    """

    def __init__(self, body: bytes, boundary: str):
        self.body = body
        self.boundary = boundary

    def parse(self) -> list[dict[str, Any]]:
        """Parse the body into a list of raw parts.

        Each part dict has:
            headers: dict[str, str]  -- lowercased header names
            body:    bytes           -- raw part body (text or binary)

        Steps:
            1. Call split_parts(self.body, self.boundary)
            2. For each raw part, split on b"\\r\\n\\r\\n" (max 1 split)
               to separate the header block from the body
            3. Strip trailing b"\\r\\n" from the body if present
            4. Decode the header block and call parse_headers()
            5. Append {"headers": ..., "body": ...} to results
        """
        # TODO: Call split_parts() to get raw parts
        # TODO: For each raw part:
        #   - Skip if b"\r\n\r\n" not in raw (malformed)
        #   - Split on b"\r\n\r\n" with maxsplit=1 -> header_block, body
        #   - Strip trailing b"\r\n" from body
        #   - Decode header_block with .decode("utf-8", errors="replace")
        #   - Call parse_headers() on the decoded block
        #   - Append {"headers": headers, "body": body}
        # TODO: Return the list
        pass

    def get_fields_and_files(
        self,
    ) -> tuple[dict[str, str], dict[str, FormFile | list[FormFile]]]:
        """Classify parsed parts into text fields and file uploads.

        Returns:
            fields: {name: text_value}
            files:  {name: FormFile} or {name: [FormFile, ...]} for multiples

        Steps for each part:
            1. Get content-disposition from headers
            2. Call parse_content_disposition() to get params
            3. Extract name and filename from params
            4. If filename is not None -> file upload, else -> text field
            5. For files: handle duplicates (same name) by collecting into a list
        """
        fields: dict[str, str] = {}
        files: dict[str, FormFile | list[FormFile]] = {}

        for part in self.parse():
            disposition = part["headers"].get("content-disposition", "")
            params = parse_content_disposition(disposition)
            name = params.get("name", "")
            filename = params.get("filename")

            if filename is not None:
                # TODO: Create a FormFile dataclass instance with:
                #   name, filename, content_type (from headers, default "application/octet-stream"),
                #   data=part["body"]
                # TODO: If files[name] does not exist yet, set files[name] = form_file
                # TODO: If files[name] is already a list, append form_file
                # TODO: If files[name] is a single FormFile, convert to list: [existing, form_file]
                pass
            else:
                # TODO: Decode part["body"] as utf-8 and store in fields[name]
                pass

        return fields, files


# ===========================================================================
# SECTION 6: ASGI Body Reader (simulated)
# ===========================================================================

async def read_body_from_receive(receive) -> bytes:
    """Collect the complete HTTP request body from an ASGI receive channel.

    The ASGI spec delivers the body in chunks via "http.request" events.
    Each event has:
        body:      bytes  -- the chunk (may be empty)
        more_body: bool   -- True if more chunks are coming

    Args:
        receive: async callable that returns the next ASGI event dict

    Returns:
        The complete body as a single bytes object.
    """
    # TODO: Create a list to collect chunks
    # TODO: Set more_body = True
    # TODO: While more_body is True:
    #   - message = await receive()
    #   - Append message.get("body", b"") to chunks
    #   - more_body = message.get("more_body", False)
    # TODO: Return b"".join(chunks)
    pass


def make_asgi_receiver(body: bytes, chunk_size: int = 128):
    """Create a simulated ASGI receive() callable that returns body in chunks.

    Used in tests and demos to avoid needing a real HTTP server.
    You do NOT need to modify this function.
    """
    chunks = [body[i : i + chunk_size] for i in range(0, len(body), chunk_size)]
    if not chunks:
        chunks = [b""]

    async def receive():
        if not chunks:
            return {"type": "http.request", "body": b"", "more_body": False}
        chunk = chunks.pop(0)
        return {
            "type": "http.request",
            "body": chunk,
            "more_body": bool(chunks),
        }

    return receive, len([body[i : i + chunk_size] for i in range(0, len(body), chunk_size)])


# ===========================================================================
# SECTION 7: Demos
# ===========================================================================

def demo_boundary_extraction():
    print("--- Section 1: Boundary Extraction ---")

    try:
        content_type = "multipart/form-data; boundary=----FormBoundary7MA4YWxkTrZu0gW"
        boundary = extract_boundary(content_type)
        print(f"  Content-Type: {content_type}")
        print(f"  Boundary: {boundary}")
        assert boundary == "----FormBoundary7MA4YWxkTrZu0gW"

        ct2 = "multipart/form-data; boundary=simple123"
        assert extract_boundary(ct2) == "simple123"

        try:
            extract_boundary("text/plain")
            assert False, "Should have raised"
        except ValueError as e:
            assert "No boundary" in str(e)

        print("  [PASS] Boundary extraction works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_body_construction():
    print("\n--- Section 2: Multipart Body Construction ---")

    try:
        boundary = "TestBoundaryABC"
        fields = {"username": "alice", "bio": "Python developer"}
        files = {
            "avatar": ("photo.png", "image/png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 60),
        }

        body = build_multipart_body(fields, files, boundary)
        assert isinstance(body, bytes)
        assert b"--TestBoundaryABC" in body
        assert b'name="username"' in body
        assert b"alice" in body
        assert b'filename="photo.png"' in body
        assert b"image/png" in body

        print(f"  Built multipart body: {len(body)} bytes")
        part_count = body.count(b"\r\nContent-Disposition")
        print(f"  Parts in body: {part_count} (username, bio, avatar)")
        assert part_count == 3

        print("  [PASS] Body construction works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_raw_splitting():
    print("\n--- Section 3: Raw Part Splitting ---")

    try:
        boundary = "SplitBoundary"
        fields = {"f1": "value1", "f2": "value2"}
        files = {"doc": ("report.pdf", "application/pdf", b"%PDF-1.4 fake content")}
        body = build_multipart_body(fields, files, boundary)

        raw_parts = split_parts(body, boundary)
        print(f"  Found {len(raw_parts)} raw parts")
        assert len(raw_parts) == 3

        for i, raw in enumerate(raw_parts):
            assert b"Content-Disposition" in raw
            header_block = raw.split(b"\r\n\r\n")[0].decode()
            header_names = [line.split(":")[0].lower()
                            for line in header_block.split("\r\n") if ":" in line]
            print(f"  Part {i} headers: {', '.join(header_names)}")

        print("  [PASS] Part splitting works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_content_disposition_parsing():
    print("\n--- Section 4: Content-Disposition Parsing ---")

    try:
        cases = [
            ('form-data; name="username"',
             {"name": "username"}),
            ('form-data; name="avatar"; filename="photo.png"',
             {"name": "avatar", "filename": "photo.png"}),
            ('form-data; name="file"; filename="résumé.pdf"',
             {"name": "file", "filename": "résumé.pdf"}),
            ('form-data; name="empty"; filename=""',
             {"name": "empty", "filename": ""}),
        ]

        for header_value, expected in cases:
            result = parse_content_disposition(header_value)
            for key, val in expected.items():
                assert result.get(key) == val, f"Expected {key}={val!r}, got {result.get(key)!r}"
            display = f"'{header_value}'"
            if len(display) > 52:
                display = display[:50] + "...'"
            print(f"  {display:<55} -> {result}")

        print("  [PASS] Content-Disposition parsing works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_full_parse():
    print("\n--- Section 5: Full Parse (Fields + Files) ---")

    try:
        boundary = "FullParseBoundary"
        png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        fields = {
            "username": "alice",
            "bio": "Python developer and open-source contributor",
        }
        files = {
            "avatar": ("photo.png", "image/png", png_header + b"\x00" * 52),
        }

        body = build_multipart_body(fields, files, boundary)
        parser = MultipartParser(body, boundary)
        parsed_fields, parsed_files = parser.get_fields_and_files()

        print("  Text fields:")
        assert parsed_fields.get("username") == "alice"
        assert parsed_fields.get("bio") == "Python developer and open-source contributor"
        for name, value in parsed_fields.items():
            print(f"    {name:<8} = {value}")

        print("  File uploads:")
        assert "avatar" in parsed_files
        avatar = parsed_files["avatar"]
        assert isinstance(avatar, FormFile)
        assert avatar.filename == "photo.png"
        assert avatar.content_type == "image/png"
        assert avatar.size == len(png_header) + 52
        print(f"    {avatar.name}: {avatar.filename} ({avatar.content_type}), {avatar.size} bytes")

        print("  [PASS] Full parse works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_multiple_files():
    print("\n--- Section 6: Multiple Files ---")

    try:
        boundary = "MultiFileBoundary"
        CRLF = b"\r\n"

        # Start with CRLF so that split_parts() sees an empty preamble at index 0.
        body = CRLF + b"--" + boundary.encode()
        body += CRLF + b'Content-Disposition: form-data; name="photo"; filename="sunset.jpg"' + CRLF
        body += b"Content-Type: image/jpeg" + CRLF + CRLF
        body += b"JPEG data #1" + CRLF
        body += b"--" + boundary.encode()
        body += CRLF + b'Content-Disposition: form-data; name="photo"; filename="profile.jpg"' + CRLF
        body += b"Content-Type: image/jpeg" + CRLF + CRLF
        body += b"JPEG data #2  " + CRLF
        body += b"--" + boundary.encode() + b"--" + CRLF

        parser = MultipartParser(body, boundary)
        parsed_fields, parsed_files = parser.get_fields_and_files()

        photo = parsed_files.get("photo")
        assert photo is not None, "Expected 'photo' in files"
        assert isinstance(photo, list), f"Expected list, got {type(photo)}"
        assert len(photo) == 2
        print(f"  Uploaded {len(photo)} files under field 'photo':")
        for i, f in enumerate(photo):
            print(f"    photo[{i}]: {f.filename} ({f.content_type}), {f.size} bytes")

        assert photo[0].filename == "sunset.jpg"
        assert photo[1].filename == "profile.jpg"
        print("  [PASS] Multiple files work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_asgi_body_reader():
    import asyncio

    print("\n--- Section 7: ASGI Body Reader (simulated) ---")

    try:
        boundary = "ASGIBoundary"
        fields = {"username": "bob"}
        files = {"data": ("data.csv", "text/csv", b"id,name\r\n1,Bob\r\n2,Alice\r\n")}
        body = build_multipart_body(fields, files, boundary)

        chunk_size = len(body) // 3 or 1
        receive, original_chunk_count = make_asgi_receiver(body, chunk_size=chunk_size)

        async def run():
            collected = await read_body_from_receive(receive)
            return collected

        collected = asyncio.run(run())
        assert collected == body
        print(f"  Received {original_chunk_count} chunks totaling {len(collected)} bytes")

        parser = MultipartParser(collected, boundary)
        parsed_fields, parsed_files = parser.get_fields_and_files()
        assert parsed_fields.get("username") == "bob"
        assert "data" in parsed_files
        csv_file = parsed_files["data"]
        assert isinstance(csv_file, FormFile)
        assert csv_file.filename == "data.csv"
        print(f"  Parsed from simulated ASGI: username={parsed_fields['username']}, "
              f"file={csv_file.filename}")

        print("  [PASS] ASGI body reader works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_boundary_extraction()
    demo_body_construction()
    demo_raw_splitting()
    demo_content_disposition_parsing()
    demo_full_parse()
    demo_multiple_files()
    demo_asgi_body_reader()

    print("\n--- Summary ---")
    print("The Multipart Form Parser covers:")
    print("  - Boundary extraction from Content-Type header")
    print("  - Building standards-compliant multipart bodies for testing")
    print("  - Splitting body on \\r\\n--boundary delimiters")
    print("  - Parsing per-part headers (Content-Disposition, Content-Type)")
    print("  - Separating text fields from file uploads")
    print("  - Collecting multiple files under the same field name")
    print("  - Reading chunked ASGI body with receive()")
    print("\nAll 7 sections attempted. Multipart parser skeleton ready!")


if __name__ == "__main__":
    main()
