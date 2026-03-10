"""
Kata 58 -- WebSocket Protocol
Run: python playground/58_websocket_protocol.py

Implement the WebSocket protocol at the byte level: HTTP upgrade handshake
(Sec-WebSocket-Accept from key+GUID with SHA-1+base64), frame parsing
(FIN bit, opcodes, masking, payload length encodings), and frame encoding.

Completes within 5 seconds.
"""

from __future__ import annotations

import base64
import hashlib
import struct
from typing import Any


# ===========================================================================
# SECTION 1: WebSocket Upgrade Handshake
# ===========================================================================
# The WebSocket handshake begins with an HTTP/1.1 Upgrade request. The server
# proves it understands WebSocket by computing Sec-WebSocket-Accept from the
# client's Sec-WebSocket-Key concatenated with the magic GUID, then SHA-1
# hashed and base64-encoded.

# This is the magic GUID defined in RFC 6455 section 4.2.2
WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-5AB5DC29E950"


def compute_accept_key(client_key: str) -> str:
    """Compute the Sec-WebSocket-Accept value from the client's key.

    Steps:
    1. Concatenate client_key + WEBSOCKET_GUID
    2. SHA-1 hash the result
    3. Base64-encode the hash
    """
    combined = client_key + WEBSOCKET_GUID
    sha1_hash = hashlib.sha1(combined.encode("ascii")).digest()
    return base64.b64encode(sha1_hash).decode("ascii")


def build_upgrade_response(client_key: str) -> str:
    """Build the HTTP 101 Switching Protocols response."""
    accept_key = compute_accept_key(client_key)
    return (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_key}\r\n"
        "\r\n"
    )


def parse_upgrade_request(raw_request: str) -> dict[str, str]:
    """Parse an HTTP upgrade request into headers dict."""
    lines = raw_request.strip().split("\r\n")
    request_line = lines[0]
    headers: dict[str, str] = {}

    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    method, path, version = request_line.split(" ", 2)
    headers["_method"] = method
    headers["_path"] = path
    headers["_version"] = version

    return headers


def validate_upgrade_request(headers: dict[str, str]) -> bool:
    """Check if a parsed request is a valid WebSocket upgrade."""
    return (
        headers.get("upgrade", "").lower() == "websocket"
        and "upgrade" in headers.get("connection", "").lower()
        and "sec-websocket-key" in headers
        and headers.get("sec-websocket-version") == "13"
    )


# ===========================================================================
# SECTION 2: WebSocket Frame Structure
# ===========================================================================
# A WebSocket frame has a compact binary header:
#
#  0               1               2               3
#  0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
# +-+-+-+-+-------+-+-------------+-------------------------------+
# |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
# |I|S|S|S|  (4)  |A|     (7)     |            (16/64)            |
# |N|V|V|V|       |S|             |   (if payload len==126/127)   |
# | |1|2|3|       |K|             |                               |
# +-+-+-+-+-------+-+-------------+-------------------------------+
# |                Masking-key (0 or 4 bytes)                     |
# +-------------------------------+-------------------------------+
# |                        Payload Data                           |
# +---------------------------------------------------------------+

# Opcode constants
class Opcode:
    """WebSocket frame opcodes (RFC 6455 section 5.2)."""
    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA

    _NAMES = {
        0x0: "CONTINUATION",
        0x1: "TEXT",
        0x2: "BINARY",
        0x8: "CLOSE",
        0x9: "PING",
        0xA: "PONG",
    }

    @classmethod
    def name(cls, opcode: int) -> str:
        return cls._NAMES.get(opcode, f"UNKNOWN(0x{opcode:X})")


class WebSocketFrame:
    """Represents a parsed WebSocket frame."""

    def __init__(
        self,
        fin: bool,
        opcode: int,
        payload: bytes,
        masked: bool = False,
        mask_key: bytes | None = None,
    ):
        self.fin = fin
        self.opcode = opcode
        self.payload = payload
        self.masked = masked
        self.mask_key = mask_key

    @property
    def is_text(self) -> bool:
        return self.opcode == Opcode.TEXT

    @property
    def is_binary(self) -> bool:
        return self.opcode == Opcode.BINARY

    @property
    def is_close(self) -> bool:
        return self.opcode == Opcode.CLOSE

    @property
    def is_ping(self) -> bool:
        return self.opcode == Opcode.PING

    @property
    def is_pong(self) -> bool:
        return self.opcode == Opcode.PONG

    @property
    def is_control(self) -> bool:
        """Control frames have opcodes >= 0x8."""
        return self.opcode >= 0x8

    @property
    def text(self) -> str:
        """Decode payload as UTF-8 text."""
        return self.payload.decode("utf-8")

    def __repr__(self) -> str:
        payload_preview = self.payload[:20]
        return (
            f"WebSocketFrame(fin={self.fin}, opcode={Opcode.name(self.opcode)}, "
            f"len={len(self.payload)}, masked={self.masked}, "
            f"payload={payload_preview!r})"
        )


# ===========================================================================
# SECTION 3: Frame Masking / Unmasking
# ===========================================================================
# Client-to-server frames MUST be masked. The masking algorithm is a simple
# XOR with a 4-byte key, applied byte-by-byte.

def apply_mask(data: bytes, mask_key: bytes) -> bytes:
    """Apply (or remove) WebSocket masking.

    masking is symmetric: apply_mask(apply_mask(data, key), key) == data

    Algorithm: each byte i of data is XOR'd with mask_key[i % 4].
    """
    return bytes(b ^ mask_key[i % 4] for i, b in enumerate(data))


# ===========================================================================
# SECTION 4: Frame Decoder
# ===========================================================================
# Parse raw bytes into a WebSocketFrame.

def decode_frame(data: bytes) -> tuple[WebSocketFrame, int]:
    """Decode a WebSocket frame from raw bytes.

    Returns (frame, bytes_consumed) so the caller knows where the next
    frame starts in the buffer.

    Raises ValueError if not enough data is available.
    """
    if len(data) < 2:
        raise ValueError("Need at least 2 bytes for frame header")

    # Byte 0: FIN bit (bit 7) and opcode (bits 0-3)
    byte0 = data[0]
    fin = bool(byte0 & 0x80)          # bit 7
    opcode = byte0 & 0x0F             # bits 0-3

    # Byte 1: MASK bit (bit 7) and payload length (bits 0-6)
    byte1 = data[1]
    masked = bool(byte1 & 0x80)       # bit 7
    payload_length = byte1 & 0x7F     # bits 0-6

    offset = 2

    # Extended payload length
    if payload_length == 126:
        # Next 2 bytes are the actual length (16-bit unsigned big-endian)
        if len(data) < offset + 2:
            raise ValueError("Need 2 more bytes for 16-bit length")
        payload_length = struct.unpack("!H", data[offset:offset + 2])[0]
        offset += 2
    elif payload_length == 127:
        # Next 8 bytes are the actual length (64-bit unsigned big-endian)
        if len(data) < offset + 8:
            raise ValueError("Need 8 more bytes for 64-bit length")
        payload_length = struct.unpack("!Q", data[offset:offset + 8])[0]
        offset += 8

    # Masking key (4 bytes, only if masked)
    mask_key = None
    if masked:
        if len(data) < offset + 4:
            raise ValueError("Need 4 bytes for masking key")
        mask_key = data[offset:offset + 4]
        offset += 4

    # Payload data
    if len(data) < offset + payload_length:
        raise ValueError(
            f"Need {payload_length} bytes for payload, "
            f"have {len(data) - offset}"
        )
    payload = data[offset:offset + payload_length]

    # Unmask if necessary
    if masked and mask_key:
        payload = apply_mask(payload, mask_key)

    frame = WebSocketFrame(
        fin=fin,
        opcode=opcode,
        payload=payload,
        masked=masked,
        mask_key=mask_key,
    )

    bytes_consumed = offset + payload_length
    return frame, bytes_consumed


# ===========================================================================
# SECTION 5: Frame Encoder
# ===========================================================================
# Build raw bytes from frame parameters.

def encode_frame(
    payload: bytes,
    opcode: int = Opcode.TEXT,
    fin: bool = True,
    masked: bool = False,
    mask_key: bytes | None = None,
) -> bytes:
    """Encode a WebSocket frame to raw bytes.

    Args:
        payload: The data to send
        opcode: Frame type (TEXT, BINARY, CLOSE, PING, PONG)
        fin: True if this is the final fragment
        masked: Whether to mask the payload (client->server must mask)
        mask_key: 4-byte masking key (required if masked=True)
    """
    frame = bytearray()

    # Byte 0: FIN + opcode
    byte0 = opcode
    if fin:
        byte0 |= 0x80
    frame.append(byte0)

    # Byte 1: MASK + payload length
    length = len(payload)
    if masked:
        mask_bit = 0x80
    else:
        mask_bit = 0x00

    if length < 126:
        frame.append(mask_bit | length)
    elif length < 65536:
        frame.append(mask_bit | 126)
        frame.extend(struct.pack("!H", length))
    else:
        frame.append(mask_bit | 127)
        frame.extend(struct.pack("!Q", length))

    # Masking key
    if masked:
        if mask_key is None:
            raise ValueError("mask_key required when masked=True")
        if len(mask_key) != 4:
            raise ValueError("mask_key must be exactly 4 bytes")
        frame.extend(mask_key)
        payload = apply_mask(payload, mask_key)

    # Payload
    frame.extend(payload)

    return bytes(frame)


# ===========================================================================
# SECTION 6: Demos
# ===========================================================================

def demo_upgrade_handshake():
    """Demonstrate the WebSocket upgrade handshake."""
    print("--- Section 1: Upgrade Handshake ---")

    # Example from RFC 6455 section 4.2.2
    client_key = "dGhlIHNhbXBsZSBub25jZQ=="
    accept = compute_accept_key(client_key)
    print(f"  Client key: {client_key}")
    print(f"  Accept key: {accept}")
    # Verify the computation: SHA1(key + GUID) -> base64
    assert accept == "tXq1gVv/tWydLUgLipuUy9hajPw=", f"Got {accept}"

    # Parse an upgrade request
    raw_request = (
        "GET /ws HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {client_key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )
    headers = parse_upgrade_request(raw_request)
    assert validate_upgrade_request(headers)
    print("  Upgrade request is valid")

    # Build response
    response = build_upgrade_response(client_key)
    assert "101 Switching Protocols" in response
    assert accept in response
    print("  Response: HTTP/1.1 101 Switching Protocols")
    print(f"  Sec-WebSocket-Accept: {accept}")

    print("  [PASS] Upgrade handshake works")


def demo_frame_structure():
    """Show WebSocket frame opcodes and properties."""
    print("\n--- Section 2: Frame Structure ---")

    # Text frame
    text_frame = WebSocketFrame(fin=True, opcode=Opcode.TEXT,
                                payload=b"Hello")
    print(f"  Text frame: {text_frame}")
    assert text_frame.is_text
    assert text_frame.text == "Hello"
    assert text_frame.fin
    assert not text_frame.is_control

    # Binary frame
    bin_frame = WebSocketFrame(fin=True, opcode=Opcode.BINARY,
                               payload=b"\x00\x01\x02")
    assert bin_frame.is_binary
    assert not bin_frame.is_control

    # Control frames
    close_frame = WebSocketFrame(fin=True, opcode=Opcode.CLOSE, payload=b"")
    ping_frame = WebSocketFrame(fin=True, opcode=Opcode.PING, payload=b"")
    pong_frame = WebSocketFrame(fin=True, opcode=Opcode.PONG, payload=b"")
    assert close_frame.is_close and close_frame.is_control
    assert ping_frame.is_ping and ping_frame.is_control
    assert pong_frame.is_pong and pong_frame.is_control
    print("  Opcodes: TEXT=0x1, BINARY=0x2, CLOSE=0x8, PING=0x9, PONG=0xA")

    print("  [PASS] Frame structure works")


def demo_masking():
    """Demonstrate the masking/unmasking algorithm."""
    print("\n--- Section 3: Masking ---")

    original = b"Hello"
    mask_key = b"\x37\xfa\x21\x3d"

    # Mask the data
    masked = apply_mask(original, mask_key)
    print(f"  Original: {original!r}")
    print(f"  Mask key: {mask_key.hex()}")
    print(f"  Masked:   {masked.hex()}")
    assert masked != original

    # Unmask (same operation, XOR is symmetric)
    unmasked = apply_mask(masked, mask_key)
    print(f"  Unmasked: {unmasked!r}")
    assert unmasked == original

    # Known test vector from RFC 6455
    # "Hello" masked with key 0x37fa213d should produce specific bytes
    expected_masked = bytes([
        0x48 ^ 0x37,  # H ^ 37 = 7f
        0x65 ^ 0xfa,  # e ^ fa = 9f
        0x6c ^ 0x21,  # l ^ 21 = 4d
        0x6c ^ 0x3d,  # l ^ 3d = 51
        0x6f ^ 0x37,  # o ^ 37 = 58
    ])
    assert masked == expected_masked, f"Expected {expected_masked.hex()}, got {masked.hex()}"
    print("  Verified against known test vector")

    print("  [PASS] Masking works")


def demo_frame_encoding():
    """Demonstrate encoding WebSocket frames to bytes."""
    print("\n--- Section 4: Frame Encoding ---")

    # Simple unmasked text frame
    raw = encode_frame(b"Hello", opcode=Opcode.TEXT)
    print(f"  Encoded 'Hello' (unmasked): {raw.hex()}")
    # Byte 0: 0x81 (FIN=1, opcode=1)
    # Byte 1: 0x05 (MASK=0, length=5)
    assert raw[0] == 0x81  # FIN + TEXT
    assert raw[1] == 0x05  # length 5, no mask
    assert raw[2:] == b"Hello"

    # Masked text frame
    mask_key = b"\x37\xfa\x21\x3d"
    raw_masked = encode_frame(b"Hello", opcode=Opcode.TEXT,
                               masked=True, mask_key=mask_key)
    print(f"  Encoded 'Hello' (masked):   {raw_masked.hex()}")
    assert raw_masked[0] == 0x81
    assert raw_masked[1] == 0x85  # 0x80 (mask) | 5

    # 16-bit length (126-65535)
    medium_payload = b"X" * 300
    raw_medium = encode_frame(medium_payload, opcode=Opcode.BINARY)
    assert raw_medium[1] == 126  # length marker
    decoded_len = struct.unpack("!H", raw_medium[2:4])[0]
    assert decoded_len == 300
    print(f"  300-byte payload: length marker=126, extended={decoded_len}")

    # Close frame with status code
    close_payload = struct.pack("!H", 1000) + b"Normal closure"
    raw_close = encode_frame(close_payload, opcode=Opcode.CLOSE)
    assert raw_close[0] == 0x88  # FIN + CLOSE
    print(f"  Close frame: opcode=0x8, status=1000")

    # Ping frame
    raw_ping = encode_frame(b"ping-data", opcode=Opcode.PING)
    assert raw_ping[0] == 0x89  # FIN + PING
    print(f"  Ping frame: opcode=0x9")

    print("  [PASS] Frame encoding works")


def demo_frame_decoding():
    """Demonstrate decoding WebSocket frames from bytes."""
    print("\n--- Section 5: Frame Decoding ---")

    # Decode an unmasked text frame
    raw = bytes([0x81, 0x05]) + b"Hello"
    frame, consumed = decode_frame(raw)
    print(f"  Decoded: {frame}")
    assert frame.fin is True
    assert frame.opcode == Opcode.TEXT
    assert frame.payload == b"Hello"
    assert frame.masked is False
    assert consumed == 7

    # Decode a masked frame
    mask_key = b"\x37\xfa\x21\x3d"
    masked_payload = apply_mask(b"Hello", mask_key)
    raw_masked = bytes([0x81, 0x85]) + mask_key + masked_payload
    frame2, consumed2 = decode_frame(raw_masked)
    print(f"  Decoded masked: {frame2}")
    assert frame2.payload == b"Hello"  # automatically unmasked
    assert frame2.masked is True
    assert consumed2 == 11  # 2 header + 4 mask + 5 payload

    # Decode a 16-bit length frame
    payload = b"A" * 200
    raw_medium = bytes([0x82, 126]) + struct.pack("!H", 200) + payload
    frame3, consumed3 = decode_frame(raw_medium)
    print(f"  Decoded 200-byte binary: len={len(frame3.payload)}")
    assert frame3.opcode == Opcode.BINARY
    assert len(frame3.payload) == 200

    # Round-trip: encode then decode
    original = b"Round trip test!"
    encoded = encode_frame(original, opcode=Opcode.TEXT)
    decoded, _ = decode_frame(encoded)
    assert decoded.payload == original
    assert decoded.text == "Round trip test!"
    print(f"  Round-trip: '{decoded.text}' matches original")

    # Round-trip with masking
    mask_key = b"\xAB\xCD\xEF\x01"
    encoded_masked = encode_frame(original, opcode=Opcode.TEXT,
                                   masked=True, mask_key=mask_key)
    decoded_masked, _ = decode_frame(encoded_masked)
    assert decoded_masked.payload == original
    print(f"  Masked round-trip: '{decoded_masked.text}' matches original")

    print("  [PASS] Frame decoding works")


def demo_multiple_frames():
    """Demonstrate decoding multiple frames from a buffer."""
    print("\n--- Section 6: Multiple Frames in Buffer ---")

    # Build a buffer with 3 frames concatenated
    frame1 = encode_frame(b"First", opcode=Opcode.TEXT)
    frame2 = encode_frame(b"Second", opcode=Opcode.TEXT)
    frame3 = encode_frame(b"", opcode=Opcode.CLOSE)

    buffer = frame1 + frame2 + frame3

    # Decode all frames
    frames = []
    offset = 0
    while offset < len(buffer):
        frame, consumed = decode_frame(buffer[offset:])
        frames.append(frame)
        offset += consumed

    print(f"  Buffer: {len(buffer)} bytes, {len(frames)} frames")
    assert len(frames) == 3
    assert frames[0].text == "First"
    assert frames[1].text == "Second"
    assert frames[2].is_close
    print(f"  Frame 1: '{frames[0].text}' (TEXT)")
    print(f"  Frame 2: '{frames[1].text}' (TEXT)")
    print(f"  Frame 3: CLOSE")

    # Non-final fragments (FIN=False)
    frag1 = encode_frame(b"Hel", opcode=Opcode.TEXT, fin=False)
    frag2 = encode_frame(b"lo", opcode=Opcode.CONTINUATION, fin=True)

    f1, _ = decode_frame(frag1)
    f2, _ = decode_frame(frag2)
    assert f1.fin is False
    assert f1.opcode == Opcode.TEXT
    assert f2.fin is True
    assert f2.opcode == Opcode.CONTINUATION
    reassembled = f1.payload + f2.payload
    assert reassembled == b"Hello"
    print(f"  Fragmented: '{reassembled.decode()}' (2 fragments)")

    print("  [PASS] Multiple frames work")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_upgrade_handshake()
    demo_frame_structure()
    demo_masking()
    demo_frame_encoding()
    demo_frame_decoding()
    demo_multiple_frames()

    print("\n--- Summary ---")
    print("WebSocket protocol implementation covers:")
    print("  - HTTP upgrade handshake with Sec-WebSocket-Accept")
    print("  - Frame structure: FIN, opcode, mask, payload length")
    print("  - Opcodes: TEXT, BINARY, CLOSE, PING, PONG, CONTINUATION")
    print("  - Masking with XOR (client-to-server requirement)")
    print("  - 7-bit, 16-bit, and 64-bit payload length encodings")
    print("  - Frame encoder and decoder with round-trip verification")
    print("  - Multi-frame buffer parsing and fragmentation")
    print("\nAll 6 sections passed. WebSocket protocol mastered!")
    print("Next up: Kata 59 -- ASGI WebSocket!")


if __name__ == "__main__":
    main()
