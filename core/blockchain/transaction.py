from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class BlockchainTransaction:
    txid: str
    block_height: Optional[int] = None
    block_hash: Optional[str] = None
    confirmed: bool = False
    confirmations: int = 0
    raw: dict[str, Any] = field(default_factory=dict)

    def as_dict(self):
        return {
            "txid": self.txid,
            "block_height": self.block_height,
            "block_hash": self.block_hash,
            "confirmed": self.confirmed,
            "confirmations": self.confirmations,
        }
