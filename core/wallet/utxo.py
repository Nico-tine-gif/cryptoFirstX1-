from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UTXO:
    txid: str
    vout: int
    value_sats: int
    address: Optional[str] = None
    confirmed: bool = False
    block_height: Optional[int] = None

    @property
    def outpoint(self):
        return f"{self.txid}:{self.vout}"

    def as_dict(self):
        return {
            "txid": self.txid,
            "vout": self.vout,
            "value_sats": self.value_sats,
            "address": self.address,
            "confirmed": self.confirmed,
            "block_height": self.block_height,
        }
