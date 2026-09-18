import time
import json

from core.storage.database import connect


class BlockTracker:

    def __init__(self, adapter):
        self.adapter = adapter
        self.last_height = None

    def current(self):
        return self.adapter.latest_height()

    def scan(self):
        height = self.current()

        if self.last_height is None:
            previous = height
        else:
            previous = self.last_height

        self.last_height = height

        return {
            "network": "bitcoin",
            "height": height,
            "previous_height": previous,
            "new_block": height != previous,
        }

    def save_block(self, block):
        now = int(time.time())

        with connect() as db:
            db.execute(
                """
                INSERT OR REPLACE INTO blocks (
                    network,
                    height,
                    block_hash,
                    previous_hash,
                    timestamp,
                    transaction_count,
                    detected_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "bitcoin",
                    block.get("height"),
                    block.get("id"),
                    block.get("previousblockhash"),
                    block.get("timestamp"),
                    block.get("tx_count", 0),
                    now,
                ),
            )
            db.commit()

    def process_height(self, height):
        block_hash = self.adapter.block_hash(height)

        if not block_hash:
            raise RuntimeError(
                f"Unable to resolve block height {height}"
            )

        block = self.adapter.block(block_hash)

        if not block:
            raise RuntimeError(
                f"Unable to load block {block_hash}"
            )

        self.save_block(block)

        return block
