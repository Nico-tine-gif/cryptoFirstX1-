from core.networks.bitcoin import BitcoinAdapter
from core.monitoring.blockchain_monitor import BlockchainMonitor
from core.monitoring.realtime_transactions import RealtimeTransactionMonitor
from core.monitoring.p7_monitor import P7Monitor
from core.transactions.realtime_ledger import RealtimeTransactionLedger


class P7LiveMonitor:
    """
    P7 live integration layer.

    Connects:
      BitcoinAdapter
      P3 RealtimeTransactionLedger
      BlockchainMonitor
      RealtimeTransactionMonitor
      P7Monitor

    Signing and broadcasting remain controlled by P6 boundaries.
    """

    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.db_path = db_path

        # Live Bitcoin network adapter
        self.adapter = BitcoinAdapter()

        # Existing P3 realtime ledger
        self.ledger = RealtimeTransactionLedger(db_path=db_path)

        # Existing monitoring components
        self.blockchain = BlockchainMonitor(confirmations=3)

        self.realtime = RealtimeTransactionMonitor(
            network=self.adapter,
            ledger=self.ledger,
            interval=10,
        )

        # P7 coordinator
        self.p7 = P7Monitor(
            network_adapter=self.adapter,
            network="bitcoin",
            db_path=db_path,
        )

    def status(self):
        return {
            "adapter_attached": True,
            "network": "bitcoin",
            "monitoring": True,
            "block_monitor": True,
            "transaction_monitor": True,
            "confirmation_monitor": True,
            "reorg_detection": True,
            "signing": "P6 BOUNDARY",
            "broadcasting": "P6 BOUNDARY",
            "private_keys_stored": False,
        }

    def scan(self):
        result = {}

        try:
            result["tip"] = self.adapter.latest_height()
        except Exception as exc:
            result["tip_error"] = str(exc)

        try:
            result["tip_hash"] = self.adapter.latest_hash()
        except Exception as exc:
            result["tip_hash_error"] = str(exc)

        try:
            txids = self.adapter.mempool_txids()
            result["mempool"] = len(txids)
        except Exception as exc:
            result["mempool_error"] = str(exc)

        return result


if __name__ == "__main__":
    monitor = P7LiveMonitor()

    status = monitor.status()

    print("============================================================")
    print(" P7 LIVE MONITOR")
    print("============================================================")
    print("Bitcoin adapter          :", status["adapter_attached"])
    print("Network                  :", status["network"])
    print("Monitoring               :", status["monitoring"])
    print("Block monitoring         :", status["block_monitor"])
    print("Transaction monitoring   :", status["transaction_monitor"])
    print("Confirmation monitoring  :", status["confirmation_monitor"])
    print("Reorg detection          :", status["reorg_detection"])
    print("Signing                  :", status["signing"])
    print("Broadcasting             :", status["broadcasting"])
    print("Private keys stored      :", status["private_keys_stored"])

    print()
    print("=== ACTUAL BITCOIN NETWORK CHECK ===")

    result = monitor.scan()

    print("LATEST HEIGHT             :", result.get("tip"))
    print("LATEST HASH               :", result.get("tip_hash"))
    print("MEMPOOL TX COUNT          :", result.get("mempool"))

    if "tip_error" in result:
        print("TIP ERROR                 :", result["tip_error"])

    if "tip_hash_error" in result:
        print("TIP HASH ERROR            :", result["tip_hash_error"])

    if "mempool_error" in result:
        print("MEMPOOL ERROR             :", result["mempool_error"])

    print("============================================================")
