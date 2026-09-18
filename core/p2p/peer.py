from dataclasses import dataclass


@dataclass
class Peer:
    peer_id: str
    address: str
    port: int
    network: str
    status: str = "UNKNOWN"
    last_seen: int | None = None
