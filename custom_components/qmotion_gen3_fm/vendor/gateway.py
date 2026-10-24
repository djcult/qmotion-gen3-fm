"""Synchronous gateway client; no third-party dependencies."""
from dataclasses import dataclass
import socket
import time
from .protocol import PORT, SYNC, decode_frames, move, prepare_pairing, complete_pairing, ProtocolError

@dataclass(frozen=True)
class Group:
    name: str
    channel: int
    page: bytes
    raw: bytes

    @classmethod
    def from_record(cls, record: bytes) -> "Group":
        if len(record) != 60:
            raise ProtocolError(f"FM group record must be 60 bytes, got {len(record)}")
        return cls(
            name=record[32:48].split(b"\0", 1)[0].decode("utf-8", "replace"),
            channel=record[8],
            page=record[22:24],
            raw=record,
        )

class Gateway:
    def __init__(self, host: str, port: int = PORT, timeout: float = 5):
        self.host, self.port, self.timeout = host, port, timeout

    def exchange(self, packet: bytes, read_timeout: float = 1.0) -> bytes:
        """Send one request, accumulate any response; missing ACK is not proof of failure."""
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(0.2)
            sock.sendall(packet)
            result = bytearray()
            deadline = time.monotonic() + read_timeout
            while time.monotonic() < deadline:
                try:
                    chunk = sock.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                result.extend(chunk)
            return bytes(result)

    def list_groups(self) -> list[Group]:
        response = self.exchange(SYNC, read_timeout=2.5)
        if not response:
            raise ProtocolError("No sync response from gateway")
        frames = decode_frames(response)
        if not frames or frames[0].kind != 0x16 or len(frames[0].payload) != 6:
            raise ProtocolError("Unexpected gateway sync prelude")
        expected = frames[0].payload[-1]
        records = [f for f in frames[1:] if f.kind == 0x16 and len(f.payload) == 60]
        if len(records) != expected:
            raise ProtocolError(f"Gateway advertises {expected} groups, received {len(records)}")
        return [Group.from_record(f.payload) for f in records]

    def set_position(self, channel: int, position: int) -> bytes:
        return self.exchange(move(channel, position))

    def prepare_pairing(self, channel: int) -> bytes:
        return self.exchange(prepare_pairing(channel))

    def complete_pairing(self, group: Group) -> bytes:
        return self.exchange(complete_pairing(group.channel, group.page))
