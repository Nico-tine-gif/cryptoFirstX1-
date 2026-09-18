import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.withdrawals.transaction_tracker import TransactionTracker


def test_transaction_tracking():
    tracker = TransactionTracker()

    txid = "p5-test-transaction"

    tracker.track(
        txid=txid,
        network="bitcoin",
        state="MEMPOOL",
    )

    item = tracker.get(txid)

    assert item is not None
    assert item["txid"] == txid
    assert item["state"] == "MEMPOOL"

    tracker.update_state(
        txid,
        "CONFIRMING",
        confirmations=1,
        block_height=1,
        block_hash="p5-test-block",
    )

    item = tracker.get(txid)

    assert item["state"] == "CONFIRMING"
    assert item["confirmations"] == 1

    print("TRANSACTION TRACKING: PASS")


if __name__ == "__main__":
    test_transaction_tracking()
    print("P5 TRANSACTION TRACKING TEST: PASS")
