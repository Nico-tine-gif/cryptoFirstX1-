from dataclasses import dataclass
from typing import Optional


@dataclass
class ChainState:
    network: str
    height: int = 0
    tip_hash: Optional[str] = None
    timestamp: Optional[int] = None
    provider: Optional[str] = None

    def update(self, height, tip_hash, timestamp=None, provider=None):
        self.height = int(height)
        self.tip_hash = tip_hash
        self.timestamp = timestamp
        self.provider = provider

    def as_dict(self):
        return {
            "network": self.network,
            "height": self.height,
            "tip_hash": self.tip_hash,
            "timestamp": self.timestamp,
            "provider": self.provider,
        }
