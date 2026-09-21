import sqlite3
from pathlib import Path
from datetime import datetime, timezone


DB_PATH = Path("data/cryptoFirstX1.db")


class AccountStore:
    """
    Monetary account storage.

    available_cents:
        Spendable monetary value.

    reserved_cents:
        Value locked for pending withdrawals.

    total credits/debits are represented by immutable ledger entries.
    """

    def __init__(self, db_path=DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        return db

    def _init_db(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS monetary_accounts (
                    account_id TEXT PRIMARY KEY,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    available_cents INTEGER NOT NULL DEFAULT 0,
                    reserved_cents INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS monetary_ledger (
                    entry_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    reference_type TEXT,
                    reference_id TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_monetary_ledger_account
                ON monetary_ledger(account_id)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_monetary_ledger_reference
                ON monetary_ledger(reference_type, reference_id)
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS monetary_reservations (
                    reservation_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    reference_type TEXT NOT NULL,
                    reference_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    def ensure_account(self, account_id="admin"):
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as db:
            db.execute("""
                INSERT OR IGNORE INTO monetary_accounts
                (account_id, currency, available_cents, reserved_cents,
                 created_at, updated_at)
                VALUES (?, 'USD', 0, 0, ?, ?)
            """, (account_id, now, now))

        return self.get(account_id)

    def get(self, account_id="admin"):
        self.ensure_account_if_missing(account_id)

        with self._connect() as db:
            row = db.execute("""
                SELECT account_id, currency,
                       available_cents, reserved_cents,
                       created_at, updated_at
                FROM monetary_accounts
                WHERE account_id=?
            """, (account_id,)).fetchone()

        if not row:
            return None

        return dict(row)

    def ensure_account_if_missing(self, account_id):
        with self._connect() as db:
            exists = db.execute("""
                SELECT 1 FROM monetary_accounts
                WHERE account_id=?
            """, (account_id,)).fetchone()

        if not exists:
            now = datetime.now(timezone.utc).isoformat()
            with self._connect() as db:
                db.execute("""
                    INSERT INTO monetary_accounts
                    (account_id, currency, available_cents, reserved_cents,
                     created_at, updated_at)
                    VALUES (?, 'USD', 0, 0, ?, ?)
                """, (account_id, now, now))
