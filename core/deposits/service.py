from core.deposits.reconciler import DepositReconciler
from core.deposits.store import DepositStore


class DepositService:

    def __init__(self, network, required_confirmations=3):
        self.network = network
        self.store = DepositStore()

        self.reconciler = DepositReconciler(
            network=network,
            store=self.store,
            required_confirmations=required_confirmations,
        )

    def watch(self, address, label=""):
        self.store.watch_address(
            address=address,
            network=self.network.name,
            label=label,
        )

    def unwatch(self, address):
        self.store.unwatch_address(address)

    def scan(self):
        return self.reconciler.scan_all()

    def reconcile(self):
        return self.reconciler.reconcile()

    def status(self):
        return {
            "network": self.network.name,
            "provider": self.network.adapter.provider(),
            "watched_addresses": len(
                self.store.watched_addresses()
            ),
            "deposit_counts": self.store.counts(),
            "recent_deposits": self.store.all(20),
        }
