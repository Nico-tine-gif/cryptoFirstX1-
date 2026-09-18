from dataclasses import dataclass, field
from typing import Any


@dataclass
class Block:
    height: int
    block_hash: str
    previous_hash: str = ""
    timestamp: int = 0
    transaction_count: int = 0
    raw: dict[str, Any] = field(default_factory=dict)

    def as_dict(self):
        return {
            "height": self.height,
            "block_hash": self.block_hash,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transaction_count": self.transaction_count,
        }
