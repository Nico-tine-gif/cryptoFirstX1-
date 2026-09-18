import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("data/cryptoFirstX1.db")

class WithdrawalStore:
    STATES = (
        "REQUESTED",
        "VALIDATING",
        "APPROVAL_REQUIRED",
        "APPROVED",
        "SIGNING",
        "BROADCASTING",
        "CONFIRMING",
        "COMPLETED",
        "REJECTED",
        "CANCELLED",
        "FAILED",
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
                CREATE TABLE IF NOT EXISTS withdrawals (
                    withdrawal_id TEXT PRIMARY KEY,
                    network TEXT NOT NULL,
                    address TEXT NOT NULL,
                    value_sats INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    txid TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_withdrawals_state
                ON withdrawals(state)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_withdrawals_txid
                ON withdrawals(txid)
            """)

    def create(self, withdrawal_id, network, address, value_sats,
               state="REQUESTED", metadata=None):
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute("""
                INSERT INTO withdrawals
                (withdrawal_id, network, address, value_sats, state,
                 txid, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
            """, (
                withdrawal_id,
                network,
                address,
                int(value_sats),
                state,
                now,
                now,
                json.dumps(metadata or {}, sort_keys=True),
            ))

    def update(self, withdrawal_id, state=None, txid=None, metadata=None):
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as db:
            row = db.execute("""
                SELECT state, txid, metadata_json
                FROM withdrawals
                WHERE withdrawal_id=?
            """, (withdrawal_id,)).fetchone()

            if not row:
                raise KeyError(withdrawal_id)

            new_state = state if state is not None else row[0]
            new_txid = txid if txid is not None else row[1]

            old_meta = json.loads(row[2] or "{}")
            if metadata:
                old_meta.update(metadata)

            db.execute("""
                UPDATE withdrawals
                SET state=?, txid=?, updated_at=?, metadata_json=?
                WHERE withdrawal_id=?
            """, (
                new_state,
                new_txid,
                now,
                json.dumps(old_meta, sort_keys=True),
                withdrawal_id,
            ))

    def get(self, withdrawal_id):
        with self._connect() as db:
            row = db.execute("""
                SELECT withdrawal_id, network, address, value_sats,
                       state, txid, created_at, updated_at, metadata_json
                FROM withdrawals
                WHERE withdrawal_id=?
            """, (withdrawal_id,)).fetchone()

        if not row:
            return None

        return {
            "withdrawal_id": row[0],
            "network": row[1],
            "address": row[2],
            "value_sats": row[3],
            "state": row[4],
            "txid": row[5],
            "created_at": row[6],
            "updated_at": row[7],
            "metadata": json.loads(row[8] or "{}"),
        }

    def counts(self):
        with self._connect() as db:
            rows = db.execute("""
                SELECT state, COUNT(*)
                FROM withdrawals
                GROUP BY state
                ORDER BY state
            """).fetchall()
        return dict(rows)
