# Kata 58 -- WebSocket Protocol

[prev: 57-query-builder](./57-query-builder.md) | [next: 59-asgi-websocket](./59-asgi-websocket.md)

---

## What We're Building

A **byte-level WebSocket protocol implementation**. WebSocket is the standard for full-duplex communication over a single TCP connection. We build three layers:

1. **Upgrade handshake** -- the HTTP request/response that switches from HTTP to WebSocket, including the `Sec-WebSocket-Accept` computation (SHA-1 + base64)
2. **Frame parser** -- decode the compact binary frame format with FIN bit, opcodes, masking, and variable-length payload encoding
3. **Frame encoder** -- build WebSocket frames from scratch, with support for masking

This is what every WebSocket library (websockets, wsproto, autobahn) does internally -- but we implement it from first principles.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Upgrade handshake | Switches HTTP to WebSocket | Connection establishment |
| `Sec-WebSocket-Accept` | SHA-1 + base64 proof of protocol support | Handshake validation |
| Frame structure | FIN, opcode, mask, length, payload | Every WebSocket message |
| Opcodes | TEXT (0x1), BINARY (0x2), CLOSE (0x8), PING (0x9), PONG (0xA) | Message type identification |
| Masking | XOR with 4-byte key (client-to-server requirement) | Security against proxy attacks |
| Payload length encoding | 7-bit, 16-bit, or 64-bit | Variable-size messages |
| Frame fragmentation | FIN=0 for continuation frames | Large message streaming |

## The Code

### 1. The Upgrade Handshake

WebSocket begins with an HTTP request containing `Upgrade: websocket`. The server proves it speaks WebSocket by computing `Sec-WebSocket-Accept`:

```python
WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-5AB5DC29E950"

def compute_accept_key(client_key: str) -> str:
    combined = client_key + WEBSOCKET_GUID
    sha1_hash = hashlib.sha1(combined.encode("ascii")).digest()
    return base64.b64encode(sha1_hash).decode("ascii")
```

The magic GUID is defined in RFC 6455 -- every WebSocket implementation uses the same constant.

### 2. Frame Structure

The binary frame format is compact and elegant:

```
 Byte 0: [FIN:1][RSV:3][OPCODE:4]
 Byte 1: [MASK:1][PAYLOAD_LEN:7]
 Bytes 2-3 or 2-9: Extended length (if needed)
 Bytes N-N+3: Masking key (if MASK=1)
 Remaining: Payload data
```

### 3. Masking Algorithm

Client-to-server frames must be masked. The algorithm is simple XOR:

```python
def apply_mask(data: bytes, mask_key: bytes) -> bytes:
    return bytes(b ^ mask_key[i % 4] for i, b in enumerate(data))
```

Masking is symmetric -- applying it twice returns the original data.

### 4. Frame Encoding

```python
def encode_frame(payload, opcode=0x1, fin=True, masked=False, mask_key=None):
    frame = bytearray()

    # Byte 0: FIN + opcode
    byte0 = opcode | (0x80 if fin else 0)
    frame.append(byte0)

    # Byte 1: MASK + length
    length = len(payload)
    mask_bit = 0x80 if masked else 0x00

    if length < 126:
        frame.append(mask_bit | length)
    elif length < 65536:
        frame.append(mask_bit | 126)
        frame.extend(struct.pack("!H", length))
    else:
        frame.append(mask_bit | 127)
        frame.extend(struct.pack("!Q", length))
```

### 5. Frame Decoding

```python
def decode_frame(data):
    fin = bool(data[0] & 0x80)
    opcode = data[0] & 0x0F
    masked = bool(data[1] & 0x80)
    payload_length = data[1] & 0x7F

    offset = 2
    if payload_length == 126:
        payload_length = struct.unpack("!H", data[offset:offset+2])[0]
        offset += 2
    elif payload_length == 127:
        payload_length = struct.unpack("!Q", data[offset:offset+8])[0]
        offset += 8
```

## Playground

```
python playground/58_websocket_protocol.py
```

Expected output:

```
--- Section 1: Upgrade Handshake ---
  Client key: dGhlIHNhbXBsZSBub25jZQ==
  Accept key: tXq1gVv/tWydLUgLipuUy9hajPw=
  Upgrade request is valid
  Response: HTTP/1.1 101 Switching Protocols
  Sec-WebSocket-Accept: tXq1gVv/tWydLUgLipuUy9hajPw=
  [PASS] Upgrade handshake works

--- Section 2: Frame Structure ---
  Text frame: WebSocketFrame(fin=True, opcode=TEXT, len=5, ...)
  Opcodes: TEXT=0x1, BINARY=0x2, CLOSE=0x8, PING=0x9, PONG=0xA
  [PASS] Frame structure works

--- Section 3: Masking ---
  Original: b'Hello'
  Mask key: 37fa213d
  Masked:   7f9f4d5158
  Unmasked: b'Hello'
  Verified against known test vector
  [PASS] Masking works

--- Section 4: Frame Encoding ---
  Encoded 'Hello' (unmasked): 810548656c6c6f
  [PASS] Frame encoding works

--- Section 5: Frame Decoding ---
  Decoded: WebSocketFrame(fin=True, opcode=TEXT, len=5, ...)
  Round-trip: 'Round trip test!' matches original
  [PASS] Frame decoding works

--- Section 6: Multiple Frames in Buffer ---
  Buffer: 17 bytes, 3 frames
  Fragmented: 'Hello' (2 fragments)
  [PASS] Multiple frames work

All 6 sections passed. WebSocket protocol mastered!
```

## How It Works

### The Handshake Flow

```
Client                           Server
  |                                |
  |  GET /ws HTTP/1.1              |
  |  Upgrade: websocket            |
  |  Connection: Upgrade           |
  |  Sec-WebSocket-Key: xxx        |
  |  Sec-WebSocket-Version: 13     |
  |  ------------------------------>
  |                                |
  |  HTTP/1.1 101 Switching        |
  |  Upgrade: websocket            |
  |  Connection: Upgrade           |
  |  Sec-WebSocket-Accept: yyy     |
  |  <------------------------------
  |                                |
  |  <<<< WebSocket frames >>>>   |
  |  <---------------------------->
```

### Frame Byte Layout

```
Example: Unmasked text frame "Hello" (5 bytes)

Byte 0: 0x81 = 10000001
         ^         ^^^^ opcode=1 (TEXT)
         FIN=1

Byte 1: 0x05 = 00000101
         ^       ^^^^^^^ length=5
         MASK=0

Bytes 2-6: H e l l o  (payload)
```

### Payload Length Encoding

| Length Value | Encoding | Range |
|---|---|---|
| 0-125 | 7-bit inline | Short messages |
| 126 | Next 2 bytes (uint16 BE) | Up to 65,535 bytes |
| 127 | Next 8 bytes (uint64 BE) | Up to 2^63 bytes |

## Exercises

1. **Add close code parsing** -- when decoding a CLOSE frame, the first 2 bytes of the payload are a 16-bit status code (1000=normal, 1001=going away, etc.). Parse and expose it as `frame.close_code`.

2. **Implement fragmentation reassembly** -- build a `FrameAssembler` that collects continuation frames (FIN=0) and reassembles them into a complete message when the final frame (FIN=1) arrives.

3. **Add per-message deflate** -- implement the `permessage-deflate` extension (RFC 7692) by compressing/decompressing payloads with `zlib`.

4. **Build a frame validator** -- validate that control frames (CLOSE, PING, PONG) have payload <= 125 bytes and FIN=1 (RFC requirement). Reject invalid frames.

5. **Implement auto-pong** -- build a frame processor that automatically responds to PING frames with a matching PONG frame (same payload).

## What's Next

Now that we understand the WebSocket wire protocol, in [Kata 59: ASGI WebSocket](./59-asgi-websocket.md) we'll build the ASGI layer on top -- the `scope`, `receive`, and `send` interface that ASGI frameworks use to handle WebSocket connections without touching raw bytes.

---

[prev: 57-query-builder](./57-query-builder.md) | [next: 59-asgi-websocket](./59-asgi-websocket.md)
