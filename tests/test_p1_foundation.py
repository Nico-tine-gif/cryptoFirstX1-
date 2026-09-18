import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.blockchain.chain import ChainState
from core.blockchain.block import Block
from core.blockchain.transaction import BlockchainTransaction
from core.networks.registry import NetworkRegistry


state = ChainState("bitcoin")
state.update(
    height=100,
    tip_hash="abc",
    timestamp=123,
    provider="test",
)

assert state.height == 100
assert state.tip_hash == "abc"
assert state.provider == "test"

block = Block(
    height=100,
    block_hash="abc",
)

assert block.as_dict()["height"] == 100

tx = BlockchainTransaction(
    txid="tx123",
    block_height=100,
    confirmations=3,
    confirmed=True,
)

assert tx.confirmed
assert tx.confirmations == 3

registry = NetworkRegistry()

class Dummy:
    pass

registry.register("TEST", Dummy())

assert "test" in registry.names()
assert registry.get("test")

print("P1 FOUNDATION TEST: PASS")
