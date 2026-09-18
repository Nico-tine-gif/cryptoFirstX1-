import time

from core.storage.database import connect


class DepositTracker:

    def __init__(self, adapter):
        self.adapter = adapter

    def watch(
        self,
        address,
        label="",
    ):
        validation = self.adapter.validate_address(
            address
        )

        if not validation.get("isvalid", False):
            raise ValueError(
                "INVALID_BITCOIN_ADDRESS"
            )

        with connect() as db:
            db.execute(
                """
                INSERT OR REPLACE INTO watched_addresses (
                    network,
                    address,
                    label,
                    enabled,
                    created_at
                )
                VALUES ('bitcoin', ?, ?, 1, ?)
                """,
                (
                    address,
                    label,
                    int(time.time()),
                ),
            )
            db.commit()

        return {
            "network": "bitcoin",
            "address": address,
            "label": label,
            "status": "WATCHING",
        }

    def scan_address(self, address):
        txs = self.adapter.address_transactions(
            address
        )

        if not txs:
            return []

        deposits = []

        with connect() as db:
            for tx in txs:
                txid = tx.get("txid")
                status = tx.get("status", {})

                block_height = status.get(
                    "block_height"
                )

                for index, output in enumerate(
                    tx.get("vout", [])
                ):
                    script = output.get(
                        "scriptpubkey_address"
                    )

                    if script != address:
                        continue

                    amount = int(
                        output.get("value", 0)
                    )

                    now = int(time.time())

                    db.execute(
                        """
                        INSERT OR IGNORE INTO deposits (
                            network,
                            address,
                            txid,
                            vout,
                            amount,
                            block_height,
                            confirmations,
                            status,
                            detected_at,
                            updated_at
                        )
                        VALUES (
                            'bitcoin',
                            ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                        """,
                        (
                            address,
                            txid,
                            index,
                            amount,
                            block_height,
                            0,
                            (
                                "CONFIRMED"
                                if status.get("confirmed")
                                else "MEMPOOL"
                            ),
                            now,
                            now,
                        ),
                    )

                    deposits.append({
                        "address": address,
                        "txid": txid,
                        "vout": index,
                        "amount_sats": amount,
                        "block_height": block_height,
                        "confirmed": bool(
                            status.get("confirmed")
                        ),
                    })

            db.commit()

        return deposits
