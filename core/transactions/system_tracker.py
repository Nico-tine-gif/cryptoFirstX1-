from core.monitoring.realtime_transactions import RealtimeTransactionMonitor
from core.transactions.realtime_ledger import RealtimeTransactionLedger


class SystemTransactionTracker:

    def __init__(self, network):
        self.network = network
        self.ledger = RealtimeTransactionLedger()
        self.monitor = RealtimeTransactionMonitor(
            network=network,
            ledger=self.ledger,
        )

    def scan(self):
        return self.monitor.cycle()

    def status(self):
        return {
            "network": self.network.name,
            "provider": self.network.adapter.provider(),
            "last_height": self.monitor.last_height,
            "counts": self.ledger.counts(),
            "recent": self.ledger.recent(20),
        }
