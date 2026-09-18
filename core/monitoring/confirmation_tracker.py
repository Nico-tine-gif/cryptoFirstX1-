import time

from core.storage.database import connect


class ConfirmationTracker:

    def __init__(
        self,
        adapter,
        required=3,
    ):
        self.adapter = adapter
        self.required = required

    @staticmethod
    def calculate(
        transaction_height,
        current_height,
    ):
        if transaction_height is None:
            return 0

        if current_height < transaction_height:
            return 0

        return (
            current_height
            - transaction_height
            + 1
        )

    def update_transaction(
        self,
        txid,
        block_height,
        current_height,
    ):
        confirmations = self.calculate(
            block_height,
            current_height,
        )

        confirmed = (
            confirmations >= self.required
        )

        status = (
            "CONFIRMED"
            if confirmed
            else "CONFIRMING"
        )

        with connect() as db:
            db.execute(
                """
                UPDATE transactions
                SET confirmations = ?,
                    confirmed = ?,
                    status = ?,
                    last_seen = ?
                WHERE network = 'bitcoin'
                  AND txid = ?
                """,
                (
                    confirmations,
                    int(confirmed),
                    status,
                    int(time.time()),
                    txid,
                ),
            )
            db.commit()

        return {
            "txid": txid,
            "confirmations": confirmations,
            "required": self.required,
            "confirmed": confirmed,
            "status": status,
        }

    def refresh_all(self):
        current = self.adapter.latest_height()

        with connect() as db:
            rows = db.execute(
                """
                SELECT txid, block_height
                FROM transactions
                WHERE network = 'bitcoin'
                  AND block_height IS NOT NULL
                """
            ).fetchall()

        results = []

        for row in rows:
            results.append(
                self.update_transaction(
                    row["txid"],
                    row["block_height"],
                    current,
                )
            )

        return results
