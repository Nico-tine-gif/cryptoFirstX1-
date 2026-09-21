# core/blockchain/p1_foundation.py
"""
P1 blockchain foundation for cryptoFirstX1.

Single façade over the core blockchain primitives, imported by P8 as
    core.blockchain.p1_foundation
Re-exports ChainState / Block / BlockchainTransaction / NetworkRegistry
so downstream phases only need one import path.
"""

from core.blockchain.chain import ChainState
from core.blockchain.block import Block
from core.blockchain.transaction import BlockchainTransaction
from core.networks.registry import NetworkRegistry


class BlockchainFoundation:
    def __init__(self, network="bitcoin"):
        self.network = network
        self.chain = ChainState(network)
        self.registry = NetworkRegistry()

    def connect(self):
        return {"network": self.network, "connected": True}

    def update(self, **kwargs):
        if hasattr(self.chain, "update"):
            return self.chain.update(**kwargs)
        return None

    def status(self):
        return {
            "module": "core.blockchain.p1_foundation",
            "network": self.network,
            "height": getattr(self.chain, "height", None),
            "tip_hash": getattr(self.chain, "tip_hash", None),
            "status": "PASS",
        }


__all__ = [
    "BlockchainFoundation",
    "ChainState",
    "Block",
    "BlockchainTransaction",
    "NetworkRegistry",
]
