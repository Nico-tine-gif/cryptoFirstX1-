from dataclasses import dataclass, field
from typing import Optional


DEPOSIT_STATES = {
    "DETECTED",
    "MEMPOOL",
    "CONFIRMING",
    "CONFIRMED",
    "RECONCILED",
    "ORPHANED",
    "REJECTED",
}


@dataclass
class Deposit:
    deposit_id: str
    txid: str
    vout: int
    address: str
    value_sats: int
    network: str = "bitcoin"
    state: str = "DETECTED"
    block_height: Optional[int] = None
    block_hash: Optional[str] = None
    confirmations: int = 0
    required_confirmations: int = 3
    first_seen: int = 0
    last_seen: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.state = self.state.upper()

        if self.state not in DEPOSIT_STATES:
            raise ValueError(f"INVALID_DEPOSIT_STATE:{self.state}")

        self.value_sats = int(self.value_sats)
        self.vout = int(self.vout)
        self.confirmations = int(self.confirmations)
        self.required_confirmations = int(self.required_confirmations)

    @property
    def confirmed(self):
        return self.confirmations >= self.required_confirmations

    def update_confirmations(self, confirmations):
        self.confirmations = max(0, int(confirmations))

        if self.confirmations <= 0:
            self.state = "MEMPOOL"
        elif self.confirmations < self.required_confirmations:
            self.state = "CONFIRMING"
        else:
            self.state = "CONFIRMED"

    def as_dict(self):
        return {
            "deposit_id": self.deposit_id,
            "txid": self.txid,
            "vout": self.vout,
            "address": self.address,
            "value_sats": self.value_sats,
            "network": self.network,
            "state": self.state,
            "block_height": self.block_height,
            "block_hash": self.block_hash,
            "confirmations": self.confirmations,
            "required_confirmations": self.required_confirmations,
            "confirmed": self.confirmed,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "metadata": self.metadata,
        }
