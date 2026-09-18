import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.wallet.utxo import UTXO
from core.wallet.wallet import Wallet
from core.wallet.manager import WalletManager


wallet = Wallet()

wallet.add_address(
    "bc1qexample",
    label="test"
)

wallet.add_utxo(
    UTXO(
        txid="tx001",
        vout=0,
        value_sats=100_000_000,
        address="bc1qexample",
        confirmed=True,
        block_height=100,
    )
)

wallet.add_utxo(
    UTXO(
        txid="tx002",
        vout=1,
        value_sats=50_000_000,
        address="bc1qexample",
        confirmed=False,
    )
)

balance = wallet.balance()

assert balance.confirmed_sats == 100_000_000
assert balance.unconfirmed_sats == 50_000_000
assert balance.total_sats == 150_000_000

assert len(wallet.list_addresses()) == 1
assert len(wallet.list_utxos()) == 2

wallet.remove_utxo("tx002", 1)

assert len(wallet.list_utxos()) == 1
assert wallet.balance().total_sats == 100_000_000

manager = WalletManager()

created = manager.create("main")

assert manager.get("main") is created
assert manager.names() == ["main"]

print("P2 WALLET TEST: PASS")
