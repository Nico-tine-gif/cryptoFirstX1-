import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("data/cryptoFirstX1.db")


class NetworkTracker:
    def __init__(self, db_path=DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS network_state (
                    network TEXT PRIMARY KEY,
                    latest_height INTEGER,
                    latest_hash TEXT,
                    previous_hash TEXT,
                    last_scan TEXT,
                    status TEXT NOT NULL,
                    error TEXT
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    network TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    height INTEGER,
                    txid TEXT,
                    details TEXT,
                    created_at TEXT NOT NULL
                )
            """)

    def update_tip(self, network, height, block_hash,
                   previous_hash=None, status="HEALTHY"):
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as db:
            db.execute("""
                INSERT INTO network_state
                (network, latest_height, latest_hash, previous_hash,
                 last_scan, status, error)
                VALUES (?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(network) DO UPDATE SET
                    latest_height=excluded.latest_height,
                    latest_hash=excluded.latest_hash,
                    previous_hash=excluded.previous_hash,
                    last_scan=excluded.last_scan,
                    status=excluded.status,
                    error=NULL
            """, (
                network,
                int(height),
                block_hash,
                previous_hash,
                now,
                status,
            ))

    def record_event(self, network, event_type,
                     height=None, txid=None, details=None):
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as db:
            db.execute("""
                INSERT INTO monitoring_events
                (network, event_type, height, txid, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                network,
                event_type,
                height,
                txid,
                details,
                now,
            ))

    def get_state(self, network):
        with self._connect() as db:
            row = db.execute("""
                SELECT network, latest_height, latest_hash,
                       previous_hash, last_scan, status, error
                FROM network_state
                WHERE network=?
            """, (network,)).fetchone()

        if not row:
            return None

        return {
            "network": row[0],
            "latest_height": row[1],
            "latest_hash": row[2],
            "previous_hash": row[3],
            "last_scan": row[4],
            "status": row[5],
            "error": row[6],
        }

    def counts(self):
        with self._connect() as db:
            rows = db.execute("""
                SELECT event_type, COUNT(*)
                FROM monitoring_events
                GROUP BY event_type
                ORDER BY event_type
            """).fetchall()

        return dict(rows)
