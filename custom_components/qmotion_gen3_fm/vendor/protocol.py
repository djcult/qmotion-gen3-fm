"""QSync Gen 3 FM wire encoding.

Grounded in QSyncAMFM v1.1.3 decompilation and real gateway captures.
Wire framing: one-byte type, one-byte payload length, payload bytes.
"""
from dataclasses import dataclass

SYNC = bytes.fromhex("16 00")
PORT = 9760

class ProtocolError(ValueError):
    """Invalid or truncated QSync protocol data."""

@dataclass(frozen=True)
class Frame:
    kind: int
    payload: bytes

def decode_frames(data: bytes) -> list[Frame]:
    frames = []
    offset = 0
    while offset < len(data):
        if offset + 2 > len(data):
            raise ProtocolError("Incomplete frame header")
        kind, size = data[offset], data[offset + 1]
        end = offset + 2 + size
        if end > len(data):
            raise ProtocolError("Truncated frame payload")
        frames.append(Frame(kind, data[offset + 2:end]))
        offset = end
    return frames

def move(channel: int, position: int) -> bytes:
    if not 0 <= channel <= 255 or not 0 <= position <= 100:
        raise ValueError("channel must be 0..255 and position must be 0..100")
    return bytes((0x38, 0x02, channel, position))

def prepare_pairing(channel: int) -> bytes:
    if not 0 <= channel <= 255:
        raise ValueError("channel must be 0..255")
    return bytes((0x38, 0x02, channel, 0xFA))

def complete_pairing(channel: int, page: bytes) -> bytes:
    if not 0 <= channel <= 255 or len(page) != 2:
        raise ValueError("channel must be 0..255 and page must be 2 bytes")
    return bytes((0x34, 0x03, page[1], page[0], channel))

# Documented in app source but intentionally not exposed as CLI operations
# until behaviour has been verified against a disposable test group.
def delete_group_packet(page: bytes) -> bytes:
    if len(page) != 2:
        raise ValueError("page must be 2 bytes")
    return bytes((0x32, 0x02, page[1], page[0]))
