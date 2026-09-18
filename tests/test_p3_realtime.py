import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.transactions.realtime_ledger import RealtimeTransactionLedger


with tempfile.TemporaryDirectory() as tmp:
    db = Path(tmp) / "test.db"

    ledger = RealtimeTransactionLedger(db)

    ledger.record(
        txid="tx-real-001",
        network="bitcoin",
        status="MEMPOOL",
        fee_sats=500,
        input_total_sats=10000,
        output_total_sats=9500,
        raw={"txid": "tx-real-001"},
    )

    item = ledger.get("tx-real-001")

    assert item is not None
    assert item["status"] == "MEMPOOL"
    assert item["fee_sats"] == 500

    ledger.record(
        txid="tx-real-001",
        network="bitcoin",
        status="CONFIRMED",
        block_height=123456,
        block_hash="000000abc",
        confirmations=3,
    )

    item = ledger.get("tx-real-001")

    assert item["status"] == "CONFIRMED"
    assert item["block_height"] == 123456
    assert item["confirmations"] == 3

    events = ledger.events("tx-real-001")

    assert len(events) >= 2

    counts = ledger.counts()

    assert counts["CONFIRMED"] == 1

print("P3 REALTIME LEDGER TEST: PASS")
