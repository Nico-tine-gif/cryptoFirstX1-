import json
import time

from core.storage.database import connect


class TransactionTracker:

    def __init__(self, adapter):
        self.adapter = adapter

    def inspect(self, txid):
        tx = self.adapter.transaction(txid)

        if not tx:
            return None

        status = tx.get("status", {})

        now = int(time.time())

        with connect() as db:
            db.execute(
                """
                INSERT INTO transactions (
                    network,
                    txid,
                    block_height,
                    block_hash,
                    confirmed,
                    confirmations,
                    fee,
                    size,
                    weight,
                    first_seen,
                    last_seen,
                    status,
                    raw_json
                )
                VALUES (
                    'bitcoin', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(network, txid)
                DO UPDATE SET
                    block_height = excluded.block_height,
                    block_hash = excluded.block_hash,
                    confirmed = excluded.confirmed,
                    fee = excluded.fee,
                    size = excluded.size,
                    weight = excluded.weight,
                    last_seen = excluded.last_seen,
                    status = excluded.status,
                    raw_json = excluded.raw_json
                """,
                (
                    txid,
                    status.get("block_height"),
                    status.get("block_hash"),
                    int(status.get("confirmed", False)),
                    0,
                    tx.get("fee"),
                    tx.get("size"),
                    tx.get("weight"),
                    now,
                    now,
                    (
                        "CONFIRMED"
                        if status.get("confirmed")
                        else "MEMPOOL"
                    ),
                    json.dumps(tx),
                ),
            )
            db.commit()

        return tx

    def scan_block_transactions(
        self,
        block_hash,
    ):
        txs = self.adapter.block_transactions(
            block_hash
        )

        if not txs:
            return []

        results = []

        for tx in txs:
            txid = tx.get("txid")

            if txid:
                results.append(
                    self.inspect(txid)
                )

        return results
