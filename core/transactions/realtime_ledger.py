import json
import sqlite3
import time
from pathlib import Path


DB_PATH = Path("data/cryptoFirstX1.db")


class RealtimeTransactionLedger:

    def __init__(self, db_path=DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS realtime_transactions (
                    txid TEXT PRIMARY KEY,
                    network TEXT NOT NULL,
                    status TEXT NOT NULL,
                    first_seen INTEGER NOT NULL,
                    last_seen INTEGER NOT NULL,
                    block_height INTEGER,
                    block_hash TEXT,
                    confirmations INTEGER DEFAULT 0,
                    fee_sats INTEGER DEFAULT 0,
                    input_total_sats INTEGER DEFAULT 0,
                    output_total_sats INTEGER DEFAULT 0,
                    raw_json TEXT
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS transaction_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    txid TEXT NOT NULL,
                    network TEXT NOT NULL,
                    event TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    details_json TEXT
                )
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_rt_status
                ON realtime_transactions(status)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_rt_block
                ON realtime_transactions(block_height)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_rt_seen
                ON realtime_transactions(last_seen)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_te_txid
                ON transaction_events(txid)
            """)

    def record(
        self,
        txid,
        network="bitcoin",
        status="SEEN",
        block_height=None,
        block_hash=None,
        confirmations=0,
        fee_sats=0,
        input_total_sats=0,
        output_total_sats=0,
        raw=None,
    ):
        now = int(time.time())

        with self._connect() as db:
            existing = db.execute(
                """
                SELECT status, block_height, block_hash,
                       confirmations, fee_sats
                FROM realtime_transactions
                WHERE txid = ?
                """,
                (txid,),
            ).fetchone()

            if existing:
                old_status = existing[0]

                db.execute(
                    """
                    UPDATE realtime_transactions
                    SET network = ?,
                        status = ?,
                        last_seen = ?,
                        block_height = ?,
                        block_hash = ?,
                        confirmations = ?,
                        fee_sats = ?,
                        input_total_sats = ?,
                        output_total_sats = ?,
                        raw_json = ?
                    WHERE txid = ?
                    """,
                    (
                        network,
                        status,
                        now,
                        block_height,
                        block_hash,
                        confirmations,
                        fee_sats,
                        input_total_sats,
                        output_total_sats,
                        json.dumps(raw or {}, sort_keys=True),
                        txid,
                    ),
                )

                if old_status != status:
                    self._event(
                        db,
                        txid,
                        network,
                        f"STATUS:{old_status}->{status}",
                        {
                            "old_status": old_status,
                            "new_status": status,
                        },
                    )

            else:
                db.execute(
                    """
                    INSERT INTO realtime_transactions (
                        txid,
                        network,
                        status,
                        first_seen,
                        last_seen,
                        block_height,
                        block_hash,
                        confirmations,
                        fee_sats,
                        input_total_sats,
                        output_total_sats,
                        raw_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        txid,
                        network,
                        status,
                        now,
                        now,
                        block_height,
                        block_hash,
                        confirmations,
                        fee_sats,
                        input_total_sats,
                        output_total_sats,
                        json.dumps(raw or {}, sort_keys=True),
                    ),
                )

                self._event(
                    db,
                    txid,
                    network,
                    f"STATUS:{status}",
                    {"status": status},
                )

        return self.get(txid)

    def _event(self, db, txid, network, event, details):
        db.execute(
            """
            INSERT INTO transaction_events (
                txid,
                network,
                event,
                timestamp,
                details_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                txid,
                network,
                event,
                int(time.time()),
                json.dumps(details or {}, sort_keys=True),
            ),
        )

    def get(self, txid):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            row = db.execute(
                """
                SELECT *
                FROM realtime_transactions
                WHERE txid = ?
                """,
                (txid,),
            ).fetchone()

            return dict(row) if row else None

    def recent(self, limit=100):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            rows = db.execute(
                """
                SELECT *
                FROM realtime_transactions
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()

            return [dict(row) for row in rows]

    def by_status(self, status, limit=100):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            rows = db.execute(
                """
                SELECT *
                FROM realtime_transactions
                WHERE status = ?
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (status, int(limit)),
            ).fetchall()

            return [dict(row) for row in rows]

    def events(self, txid=None, limit=100):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            if txid:
                rows = db.execute(
                    """
                    SELECT *
                    FROM transaction_events
                    WHERE txid = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (txid, int(limit)),
                ).fetchall()
            else:
                rows = db.execute(
                    """
                    SELECT *
                    FROM transaction_events
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (int(limit),),
                ).fetchall()

            return [dict(row) for row in rows]

    def counts(self):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT status, COUNT(*)
                FROM realtime_transactions
                GROUP BY status
                """
            ).fetchall()

        return dict(rows)
