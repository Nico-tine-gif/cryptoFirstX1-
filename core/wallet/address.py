from dataclasses import dataclass


@dataclass(frozen=True)
class WalletAddress:
    address: str
    network: str = "bitcoin"
    label: str = ""

    def as_dict(self):
        return {
            "address": self.address,
            "network": self.network,
            "label": self.label,
        }
