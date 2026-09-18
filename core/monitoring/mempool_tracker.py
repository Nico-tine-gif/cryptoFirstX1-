import json
import time

from core.storage.database import connect


class MempoolTracker:

    def __init__(self, adapter):
        self.adapter = adapter

    def snapshot(self):
        data = self.adapter.mempool()

        self._event(
            "MEMPOOL_SNAPSHOT",
            data,
        )

        return data

    def recent(self):
        data = self.adapter.mempool_recent()

        self._event(
            "MEMPOOL_RECENT",
            data,
        )

        return data

    def fees(self):
        data = self.adapter.fees()

        self._event(
            "FEE_RECOMMENDATIONS",
            data,
        )

        return data

    def _event(self, event, data):
        with connect() as db:
            db.execute(
                """
                INSERT INTO mempool_events (
                    network,
                    event,
                    timestamp,
                    data
                )
                VALUES ('bitcoin', ?, ?, ?)
                """,
                (
                    event,
                    int(time.time()),
                    json.dumps(data),
                ),
            )
            db.commit()
