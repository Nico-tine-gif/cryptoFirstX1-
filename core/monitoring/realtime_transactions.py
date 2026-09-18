import time


class RealtimeTransactionMonitor:

    def __init__(
        self,
        network,
        ledger,
        interval=10,
    ):
        self.network = network
        self.ledger = ledger
        self.interval = max(2, int(interval))
        self.running = False
        self.last_height = None

    def scan_mempool(self):
        txids = self.network.adapter.mempool_txids()

        for txid in txids:
            self.ledger.record(
                txid=txid,
                network=self.network.name,
                status="MEMPOOL",
            )

        return len(txids)

    def scan_address(self, address):
        transactions = self.network.adapter.address_transactions(address)

        count = 0

        for tx in transactions:
            txid = tx.get("txid")

            if not txid:
                continue

            status = tx.get("status") or {}

            confirmed = bool(status.get("confirmed"))
            block_height = status.get("block_height")
            block_hash = status.get("block_hash")

            confirmations = 0

            if confirmed and block_height is not None:
                tip = self.network.adapter.latest_height()
                confirmations = max(0, tip - int(block_height) + 1)

            self.ledger.record(
                txid=txid,
                network=self.network.name,
                status="CONFIRMED" if confirmed else "MEMPOOL",
                block_height=block_height,
                block_hash=block_hash,
                confirmations=confirmations,
                raw=tx,
            )

            count += 1

        return count

    def scan_block(self):
        height = self.network.adapter.latest_height()

        if self.last_height == height:
            return 0

        block_hash = self.network.adapter.latest_hash()
        block = self.network.adapter.block(block_hash)

        txs = block.get("tx", [])

        for tx in txs:
            txid = tx.get("txid")

            if not txid:
                continue

            self.ledger.record(
                txid=txid,
                network=self.network.name,
                status="CONFIRMED",
                block_height=height,
                block_hash=block_hash,
                confirmations=1,
                raw=tx,
            )

        self.last_height = height

        return len(txs)

    def cycle(self):
        result = {
            "mempool": 0,
            "block_transactions": 0,
        }

        result["mempool"] = self.scan_mempool()
        result["block_transactions"] = self.scan_block()

        return result

    def run(self, cycles=None):
        self.running = True
        completed = 0

        while self.running:
            self.cycle()

            completed += 1

            if cycles is not None and completed >= cycles:
                break

            time.sleep(self.interval)

        self.running = False

    def stop(self):
        self.running = False
