import json
import sqlite3
import time
from pathlib import Path

from core.deposits.model import Deposit


DB_PATH = Path("data/cryptoFirstX1.db")


class DepositStore:

    def __init__(self, db_path=DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _migrate_existing_schema(self, db):
        rows = db.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='deposits'"
        ).fetchall()

        if not rows:
            return

        columns = {
            row[1]
            for row in db.execute(
                "PRAGMA table_info(deposits)"
            ).fetchall()
        }

        required = {
            "deposit_id": "TEXT",
            "txid": "TEXT",
            "vout": "INTEGER DEFAULT 0",
            "address": "TEXT",
            "value_sats": "INTEGER DEFAULT 0",
            "network": "TEXT DEFAULT 'bitcoin'",
            "state": "TEXT DEFAULT 'DETECTED'",
            "block_height": "INTEGER",
            "block_hash": "TEXT",
            "confirmations": "INTEGER DEFAULT 0",
            "required_confirmations": "INTEGER DEFAULT 3",
            "first_seen": "INTEGER DEFAULT 0",
            "last_seen": "INTEGER DEFAULT 0",
            "metadata_json": "TEXT DEFAULT '{}'",
        }

        for name, definition in required.items():
            if name not in columns:
                db.execute(
                    f"ALTER TABLE deposits "
                    f"ADD COLUMN {name} {definition}"
                )

        now = int(time.time())

        db.execute(
            """
            UPDATE deposits
            SET state = COALESCE(NULLIF(state, ''), 'DETECTED'),
                network = COALESCE(NULLIF(network, ''), 'bitcoin'),
                confirmations = COALESCE(confirmations, 0),
                required_confirmations =
                    COALESCE(required_confirmations, 3),
                first_seen = COALESCE(first_seen, ?),
                last_seen = COALESCE(last_seen, ?),
                metadata_json =
                    COALESCE(metadata_json, '{}')
            """,
            (now, now),
        )

    def _init_db(self):
        with self._connect() as db:
            self._migrate_existing_schema(db)

            db.execute("""
                CREATE TABLE IF NOT EXISTS watched_wallet_addresses (
                    address TEXT PRIMARY KEY,
                    network TEXT NOT NULL,
                    label TEXT DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at INTEGER NOT NULL,
                    last_scan INTEGER
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS deposits (
                    deposit_id TEXT PRIMARY KEY,
                    txid TEXT NOT NULL,
                    vout INTEGER NOT NULL,
                    address TEXT NOT NULL,
                    value_sats INTEGER NOT NULL,
                    network TEXT NOT NULL,
                    state TEXT NOT NULL,
                    block_height INTEGER,
                    block_hash TEXT,
                    confirmations INTEGER NOT NULL DEFAULT 0,
                    required_confirmations INTEGER NOT NULL DEFAULT 3,
                    first_seen INTEGER NOT NULL,
                    last_seen INTEGER NOT NULL,
                    metadata_json TEXT
                )
            """)

            db.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_deposit_outpoint
                ON deposits(network, txid, vout)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_deposit_address
                ON deposits(address)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_deposit_state
                ON deposits(state)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_deposit_txid
                ON deposits(txid)
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS reconciliation_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deposit_id TEXT,
                    event TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    details_json TEXT
                )
            """)

    def watch_address(self, address, network="bitcoin", label=""):
        now = int(time.time())

        with self._connect() as db:
            db.execute(
                """
                INSERT INTO watched_wallet_addresses
                    (address, network, label, enabled, created_at)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(address) DO UPDATE SET
                    network = excluded.network,
                    label = excluded.label,
                    enabled = 1
                """,
                (address, network, label, now),
            )

    def unwatch_address(self, address):
        with self._connect() as db:
            db.execute(
                """
                UPDATE watched_wallet_addresses
                SET enabled = 0
                WHERE address = ?
                """,
                (address,),
            )

    def watched_addresses(self, enabled_only=True):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            if enabled_only:
                rows = db.execute(
                    """
                    SELECT *
                    FROM watched_wallet_addresses
                    WHERE enabled = 1
                    ORDER BY address
                    """
                ).fetchall()
            else:
                rows = db.execute(
                    """
                    SELECT *
                    FROM watched_wallet_addresses
                    ORDER BY address
                    """
                ).fetchall()

            return [dict(row) for row in rows]

    def mark_scanned(self, address):
        with self._connect() as db:
            db.execute(
                """
                UPDATE watched_wallet_addresses
                SET last_scan = ?
                WHERE address = ?
                """,
                (int(time.time()), address),
            )

    def save(self, deposit: Deposit):
        with self._connect() as db:
            existing = db.execute(
                """
                SELECT deposit_id, state
                FROM deposits
                WHERE deposit_id = ?
                """,
                (deposit.deposit_id,),
            ).fetchone()

            now = int(time.time())

            if not deposit.first_seen:
                deposit.first_seen = now

            deposit.last_seen = now

            if existing:
                old_state = existing[1]

                db.execute(
                    """
                    UPDATE deposits
                    SET txid = ?,
                        vout = ?,
                        address = ?,
                        value_sats = ?,
                        network = ?,
                        state = ?,
                        block_height = ?,
                        block_hash = ?,
                        confirmations = ?,
                        required_confirmations = ?,
                        last_seen = ?,
                        metadata_json = ?
                    WHERE deposit_id = ?
                    """,
                    (
                        deposit.txid,
                        deposit.vout,
                        deposit.address,
                        deposit.value_sats,
                        deposit.network,
                        deposit.state,
                        deposit.block_height,
                        deposit.block_hash,
                        deposit.confirmations,
                        deposit.required_confirmations,
                        deposit.last_seen,
                        json.dumps(
                            deposit.metadata,
                            sort_keys=True,
                        ),
                        deposit.deposit_id,
                    ),
                )

                if old_state != deposit.state:
                    self.event(
                        deposit.deposit_id,
                        f"STATE:{old_state}->{deposit.state}",
                        {
                            "old_state": old_state,
                            "new_state": deposit.state,
                        },
                        db=db,
                    )

            else:
                db.execute(
                    """
                    INSERT INTO deposits (
                        deposit_id,
                        txid,
                        vout,
                        address,
                        value_sats,
                        network,
                        state,
                        block_height,
                        block_hash,
                        confirmations,
                        required_confirmations,
                        first_seen,
                        last_seen,
                        metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        deposit.deposit_id,
                        deposit.txid,
                        deposit.vout,
                        deposit.address,
                        deposit.value_sats,
                        deposit.network,
                        deposit.state,
                        deposit.block_height,
                        deposit.block_hash,
                        deposit.confirmations,
                        deposit.required_confirmations,
                        deposit.first_seen,
                        deposit.last_seen,
                        json.dumps(
                            deposit.metadata,
                            sort_keys=True,
                        ),
                    ),
                )

                self.event(
                    deposit.deposit_id,
                    f"STATE:{deposit.state}",
                    {"state": deposit.state},
                    db=db,
                )

        return self.get(deposit.deposit_id)

    def get(self, deposit_id):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            row = db.execute(
                """
                SELECT *
                FROM deposits
                WHERE deposit_id = ?
                """,
                (deposit_id,),
            ).fetchone()

            return dict(row) if row else None

    def by_address(self, address, limit=100):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            rows = db.execute(
                """
                SELECT *
                FROM deposits
                WHERE address = ?
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (address, int(limit)),
            ).fetchall()

            return [dict(row) for row in rows]

    def by_state(self, state, limit=100):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            rows = db.execute(
                """
                SELECT *
                FROM deposits
                WHERE state = ?
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (state.upper(), int(limit)),
            ).fetchall()

            return [dict(row) for row in rows]

    def all(self, limit=1000):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            rows = db.execute(
                """
                SELECT *
                FROM deposits
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()

            return [dict(row) for row in rows]

    def event(self, deposit_id, event, details=None, db=None):
        owns_connection = db is None

        if owns_connection:
            db = self._connect()

        db.execute(
            """
            INSERT INTO reconciliation_events (
                deposit_id,
                event,
                timestamp,
                details_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                deposit_id,
                event,
                int(time.time()),
                json.dumps(details or {}, sort_keys=True),
            ),
        )

        if owns_connection:
            db.commit()
            db.close()

    def events(self, deposit_id=None, limit=100):
        with self._connect() as db:
            db.row_factory = sqlite3.Row

            if deposit_id:
                rows = db.execute(
                    """
                    SELECT *
                    FROM reconciliation_events
                    WHERE deposit_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (deposit_id, int(limit)),
                ).fetchall()
            else:
                rows = db.execute(
                    """
                    SELECT *
                    FROM reconciliation_events
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
                SELECT state, COUNT(*)
                FROM deposits
                GROUP BY state
                """
            ).fetchall()

        return dict(rows)
