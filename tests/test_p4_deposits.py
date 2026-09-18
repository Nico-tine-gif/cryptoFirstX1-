import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.deposits.model import Deposit
from core.deposits.store import DepositStore


with tempfile.TemporaryDirectory() as tmp:
    db = Path(tmp) / "p4.db"

    store = DepositStore(db)

    store.watch_address(
        "bc1qtest",
        network="bitcoin",
        label="test-wallet",
    )

    assert len(store.watched_addresses()) == 1

    deposit = Deposit(
        deposit_id="deposit-001",
        txid="tx-001",
        vout=0,
        address="bc1qtest",
        value_sats=100_000,
        state="MEMPOOL",
        confirmations=0,
        required_confirmations=3,
    )

    store.save(deposit)

    item = store.get("deposit-001")

    assert item is not None
    assert item["value_sats"] == 100_000
    assert item["state"] == "MEMPOOL"

    deposit.update_confirmations(1)
    store.save(deposit)

    assert store.get("deposit-001")["state"] == "CONFIRMING"

    deposit.update_confirmations(3)
    store.save(deposit)

    item = store.get("deposit-001")

    assert item["state"] == "CONFIRMED"
    assert item["confirmations"] == 3

    events = store.events("deposit-001")

    assert len(events) >= 3

print("P4 DEPOSIT TEST: PASS")
