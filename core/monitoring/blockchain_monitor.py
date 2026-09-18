import time

from core.networks.bitcoin import BitcoinAdapter
from core.monitoring.block_tracker import BlockTracker
from core.monitoring.transaction_tracker import TransactionTracker
from core.monitoring.confirmation_tracker import ConfirmationTracker
from core.monitoring.mempool_tracker import MempoolTracker
from core.storage.database import initialize


class BlockchainMonitor:

    def __init__(
        self,
        confirmations=3,
    ):
        initialize()

        self.adapter = BitcoinAdapter()

        self.blocks = BlockTracker(
            self.adapter
        )

        self.transactions = TransactionTracker(
            self.adapter
        )

        self.confirmations = ConfirmationTracker(
            self.adapter,
            required=confirmations,
        )

        self.mempool = MempoolTracker(
            self.adapter
        )

    def status(self):
        height = self.adapter.latest_height()
        block_hash = self.adapter.latest_hash()

        return {
            "network": "bitcoin",
            "height": height,
            "tip_hash": block_hash,
            "timestamp": int(time.time()),
        }

    def scan_tip(self):
        status = self.blocks.scan()

        height = status["height"]

        block = self.blocks.process_height(
            height
        )

        return {
            "status": status,
            "block": block,
        }

    def track_transaction(self, txid):
        return self.transactions.inspect(
            txid
        )

    def refresh_confirmations(self):
        return self.confirmations.refresh_all()
