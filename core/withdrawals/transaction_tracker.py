import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("data/cryptoFirstX1.db")

class TransactionTracker:
    STATES = (
        "SEEN",
        "MEMPOOL",
        "BROADCAST",
        "CONFIRMING",
        "CONFIRMED",
        "FAILED",
        "ORPHANED",
    )

    def __init__(self, db_path=DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS tracked_transactions (
                    txid TEXT PRIMARY KEY,
                    network TEXT NOT NULL,
                    state TEXT NOT NULL,
                    block_height INTEGER,
                    block_hash TEXT,
                    confirmations INTEGER NOT NULL DEFAULT 0,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tracked_tx_state
                ON tracked_transactions(state)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tracked_tx_block
                ON tracked_transactions(block_height)
            """)

    def track(self, txid, network="bitcoin", state="SEEN",
              block_height=None, block_hash=None,
              confirmations=0, metadata=None):

        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as db:
            existing = db.execute("""
                SELECT txid FROM tracked_transactions
                WHERE txid=?
            """, (txid,)).fetchone()

            if existing:
                db.execute("""
                    UPDATE tracked_transactions
                    SET network=?,
                        state=?,
                        block_height=?,
                        block_hash=?,
                        confirmations=?,
                        last_seen=?,
                        metadata_json=?
                    WHERE txid=?
                """, (
                    network,
                    state,
                    block_height,
                    block_hash,
                    int(confirmations),
                    now,
                    json.dumps(metadata or {}, sort_keys=True),
                    txid,
                ))
            else:
                db.execute("""
                    INSERT INTO tracked_transactions
                    (txid, network, state, block_height, block_hash,
                     confirmations, first_seen, last_seen, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    txid,
                    network,
                    state,
                    block_height,
                    block_hash,
                    int(confirmations),
                    now,
                    now,
                    json.dumps(metadata or {}, sort_keys=True),
                ))

    def get(self, txid):
        with self._connect() as db:
            row = db.execute("""
                SELECT txid, network, state, block_height, block_hash,
                       confirmations, first_seen, last_seen, metadata_json
                FROM tracked_transactions
                WHERE txid=?
            """, (txid,)).fetchone()

        if not row:
            return None

        return {
            "txid": row[0],
            "network": row[1],
            "state": row[2],
            "block_height": row[3],
            "block_hash": row[4],
            "confirmations": row[5],
            "first_seen": row[6],
            "last_seen": row[7],
            "metadata": json.loads(row[8] or "{}"),
        }

    def update_state(self, txid, state, confirmations=None,
                     block_height=None, block_hash=None):

        current = self.get(txid)
        if not current:
            raise KeyError(txid)

        self.track(
            txid=txid,
            network=current["network"],
            state=state,
            block_height=(
                block_height
                if block_height is not None
                else current["block_height"]
            ),
            block_hash=(
                block_hash
                if block_hash is not None
                else current["block_hash"]
            ),
            confirmations=(
                confirmations
                if confirmations is not None
                else current["confirmations"]
            ),
            metadata=current["metadata"],
        )

    def counts(self):
        with self._connect() as db:
            rows = db.execute("""
                SELECT state, COUNT(*)
                FROM tracked_transactions
                GROUP BY state
                ORDER BY state
            """).fetchall()
        return dict(rows)
