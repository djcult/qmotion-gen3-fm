"""Unverified FM gateway administration packet builders.

Derived from QSyncAMFM 1.1.3. Never mutate a production gateway without
reviewing the dry-run bytes and independently confirming the target.
"""
from datetime import datetime, timezone

def parse_mac(value: str) -> bytes:
    raw = bytes.fromhex(value.replace(":", "").replace("-", ""))
    if len(raw) != 6:
        raise ValueError("Gateway MAC must consist of exactly six bytes")
    return raw

def next_channel(used: set[int]) -> int:
    for channel in range(9, 255):
        if channel % 8 and channel not in used:
            return channel
    raise ValueError("No free FM channel")

def create_group_packet(name: str, mac: bytes, channel: int, now: int | None = None) -> bytes:
    encoded = name.encode("utf-8")
    if not encoded or len(encoded) > 16 or b"\0" in encoded:
        raise ValueError("Group name must contain 1..16 UTF-8 bytes and no NUL")
    if len(mac) != 6:
        raise ValueError("Gateway MAC must have six bytes")
    if not 9 <= channel <= 254 or channel % 8 == 0:
        raise ValueError("Invalid FM channel")
    timestamp = int(datetime.now(timezone.utc).timestamp()) if now is None else now
    if not 0 <= timestamp <= 0xFFFFFFFF:
        raise ValueError("Timestamp out of range")
    raw = bytearray(60)
    raw[0] = 3  # FM group OID
    raw[8] = channel
    raw[9:15] = mac
    raw[15:19] = timestamp.to_bytes(4, "big")
    raw[21] = 1  # shade type used by the original app
    raw[24:32] = bytes.fromhex("19 7f 32 7f 4b 7f 00 7f")
    raw[32:32 + len(encoded)] = encoded
    # update-group: command 0x37, length 61, header 0x01, 60-byte record
    return bytes.fromhex("37 3d 01") + bytes(raw)

def delete_group_packet(page: bytes) -> bytes:
    if len(page) != 2 or page == b"\0\0":
        raise ValueError("Valid two-byte allocated page address required")
    return bytes((0x32, 0x02, page[1], page[0]))

ERASE_PACKET = bytes.fromhex("02 00")
