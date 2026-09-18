"""
cryptoFirstX1 P8.5
SYSTEM EARNINGS ENGINE

Purpose:
    Convert APPROVED qualifying platform events into internal
    monetary earning units.

Rule:
    1 approved qualifying event = 1 platform unit
    1 platform unit = $1.00 internal monetary value

IMPORTANT:
    - Database row counts alone are NOT earnings.
    - Every earning requires a unique event_id.
    - An event must be explicitly approved.
    - Duplicate event_ids cannot earn twice.
    - Earnings are recorded in an immutable ledger.
    - Earnings are credited into the existing P9 admin account.
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB = "data/cryptoFirstX1.db"

CENTS_PER_UNIT = 100
UNIT_CENTS = 100


QUALIFYING_EVENT_TYPES = {
    "DEPOSIT_RECORDED",
    "DEPOSIT_CONFIRMED",
    "DEPOSIT_RECONCILED",
    "WITHDRAWAL_RECORDED",
    "WITHDRAWAL_CONFIRMED",
    "TRANSACTION_RECORDED",
    "TRANSACTION_CONFIRMED",
    "BLOCK_PROCESSED",
    "NETWORK_TRANSACTION_PROCESSED",
    "APPROVED_SYSTEM_EVENT",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class SystemEarningsEngine:

    def __init__(self, db_path=DEFAULT_DB, account_id="admin"):
        self.db_path = str(db_path)
        self.account_id = account_id
        self._initialize()

    def _connect(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as db:

            db.execute("""
                CREATE TABLE IF NOT EXISTS system_earning_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    source_reference TEXT,
                    description TEXT,
                    status TEXT NOT NULL,
                    units INTEGER NOT NULL DEFAULT 0,
                    amount_cents INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    approved_at TEXT,
                    credited_at TEXT,
                    earning_entry_id TEXT UNIQUE
                )
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_system_earning_status
                ON system_earning_events(status)
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS
                system_earnings_ledger (
                    earning_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE,
                    account_id TEXT NOT NULL,
                    units INTEGER NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    entry_type TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_system_earnings_account
                ON system_earnings_ledger(account_id)
            """)

    def register_event(
        self,
        event_type,
        event_id=None,
        source_reference=None,
        description=None,
    ):
        event_type = str(event_type).strip().upper()

        if event_type not in QUALIFYING_EVENT_TYPES:
            raise ValueError(
                f"EVENT_TYPE_NOT_QUALIFYING:{event_type}"
            )

        event_id = event_id or uuid.uuid4().hex

        with self._connect() as db:
            db.execute("""
                INSERT INTO system_earning_events (
                    event_id,
                    event_type,
                    source_reference,
                    description,
                    status,
                    units,
                    amount_cents,
                    created_at
                )
                VALUES (?, ?, ?, ?, 'RECORDED', 0, 0, ?)
            """, (
                event_id,
                event_type,
                source_reference,
                description,
                utc_now(),
            ))

        return event_id

    def approve_event(self, event_id):
        with self._connect() as db:
            row = db.execute("""
                SELECT event_id, status
                FROM system_earning_events
                WHERE event_id=?
            """, (event_id,)).fetchone()

            if not row:
                raise KeyError(event_id)

            if row[1] != "RECORDED":
                raise ValueError(
                    f"EVENT_NOT_APPROVABLE:{row[1]}"
                )

            db.execute("""
                UPDATE system_earning_events
                SET
                    status='APPROVED',
                    units=1,
                    amount_cents=?,
                    approved_at=?
                WHERE event_id=?
            """, (
                UNIT_CENTS,
                utc_now(),
                event_id,
            ))

        return self.get_event(event_id)

    def credit_approved_event(self, event_id):
        """
        Atomically:
            APPROVED event
                ->
            P9 admin account +$1
                ->
            system earnings ledger

        This does NOT treat arbitrary database counts as money.
        """

        with self._connect() as db:

            db.execute("BEGIN IMMEDIATE")

            row = db.execute("""
                SELECT
                    event_id,
                    status,
                    units,
                    amount_cents,
                    earning_entry_id
                FROM system_earning_events
                WHERE event_id=?
            """, (event_id,)).fetchone()

            if not row:
                raise KeyError(event_id)

            event_id_db, status, units, amount_cents, existing = row

            if existing:
                return {
                    "status": "ALREADY_CREDITED",
                    "event_id": event_id_db,
                    "units": units,
                    "amount_cents": amount_cents,
                }

            if status != "APPROVED":
                raise ValueError(
                    f"EVENT_NOT_APPROVED:{status}"
                )

            if units != 1 or amount_cents != UNIT_CENTS:
                raise ValueError("INVALID_EARNING_VALUE")

            # Existing P9 monetary account.
            account = db.execute("""
                SELECT account_id
                FROM monetary_accounts
                WHERE account_id=?
            """, (self.account_id,)).fetchone()

            if not account:
                db.execute("""
                    INSERT INTO monetary_accounts (
                        account_id,
                        currency,
                        available_cents,
                        reserved_cents,
                        created_at,
                        updated_at
                    )
                    VALUES (?, 'USD', 0, 0, ?, ?)
                """, (
                    self.account_id,
                    utc_now(),
                    utc_now(),
                ))

            earning_id = uuid.uuid4().hex
            entry_id = uuid.uuid4().hex

            # P9 ledger entry.
            db.execute("""
                INSERT INTO monetary_ledger (
                    entry_id,
                    account_id,
                    entry_type,
                    amount_cents,
                    reference_type,
                    reference_id,
                    description,
                    created_at
                )
                VALUES (
                    ?,
                    ?,
                    'SYSTEM_EARNING_CREDIT',
                    ?,
                    'SYSTEM_EARNING',
                    ?,
                    ?,
                    ?
                )
            """, (
                entry_id,
                self.account_id,
                amount_cents,
                event_id,
                "Approved system earning: 1 platform unit = $1.00",
                utc_now(),
            ))

            # Increase P9 available balance.
            db.execute("""
                UPDATE monetary_accounts
                SET
                    available_cents =
                        available_cents + ?,
                    updated_at=?
                WHERE account_id=?
            """, (
                amount_cents,
                utc_now(),
                self.account_id,
            ))

            # Separate system-earnings ledger.
            db.execute("""
                INSERT INTO system_earnings_ledger (
                    earning_id,
                    event_id,
                    account_id,
                    units,
                    amount_cents,
                    entry_type,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, 'SYSTEM_EARNING_CREDIT', ?)
            """, (
                earning_id,
                event_id,
                self.account_id,
                units,
                amount_cents,
                utc_now(),
            ))

            db.execute("""
                UPDATE system_earning_events
                SET
                    status='CREDITED',
                    earning_entry_id=?,
                    credited_at=?
                WHERE event_id=?
            """, (
                entry_id,
                utc_now(),
                event_id,
            ))

            db.commit()

        return {
            "status": "CREDITED",
            "event_id": event_id,
            "account_id": self.account_id,
            "units": 1,
            "amount_cents": UNIT_CENTS,
            "amount": "$1.00",
            "ledger_entry_id": entry_id,
        }

    def process(
        self,
        event_type,
        event_id=None,
        source_reference=None,
        description=None,
    ):
        event_id = self.register_event(
            event_type=event_type,
            event_id=event_id,
            source_reference=source_reference,
            description=description,
        )

        self.approve_event(event_id)

        return self.credit_approved_event(event_id)

    def get_event(self, event_id):
        with self._connect() as db:
            row = db.execute("""
                SELECT
                    event_id,
                    event_type,
                    source_reference,
                    description,
                    status,
                    units,
                    amount_cents,
                    created_at,
                    approved_at,
                    credited_at,
                    earning_entry_id
                FROM system_earning_events
                WHERE event_id=?
            """, (event_id,)).fetchone()

        if not row:
            return None

        keys = [
            "event_id",
            "event_type",
            "source_reference",
            "description",
            "status",
            "units",
            "amount_cents",
            "created_at",
            "approved_at",
            "credited_at",
            "earning_entry_id",
        ]

        return dict(zip(keys, row))

    def history(self, limit=100):
        with self._connect() as db:
            rows = db.execute("""
                SELECT
                    event_id,
                    event_type,
                    source_reference,
                    description,
                    status,
                    units,
                    amount_cents,
                    created_at,
                    approved_at,
                    credited_at,
                    earning_entry_id
                FROM system_earning_events
                ORDER BY created_at DESC
                LIMIT ?
            """, (int(limit),)).fetchall()

        keys = [
            "event_id",
            "event_type",
            "source_reference",
            "description",
            "status",
            "units",
            "amount_cents",
            "created_at",
            "approved_at",
            "credited_at",
            "earning_entry_id",
        ]

        return [dict(zip(keys, row)) for row in rows]

    def totals(self):
        with self._connect() as db:
            row = db.execute("""
                SELECT
                    COALESCE(SUM(
                        CASE
                            WHEN status='CREDITED'
                            THEN units ELSE 0
                        END
                    ), 0),
                    COALESCE(SUM(
                        CASE
                            WHEN status='CREDITED'
                            THEN amount_cents ELSE 0
                        END
                    ), 0),
                    COALESCE(SUM(
                        CASE
                            WHEN status='APPROVED'
                            THEN units ELSE 0
                        END
                    ), 0)
                FROM system_earning_events
            """).fetchone()

        return {
            "credited_units": int(row[0]),
            "credited_cents": int(row[1]),
            "credited_dollars": f"{row[1] / 100:.2f}",
            "pending_approved_units": int(row[2]),
            "unit_value": "$1.00",
        }


__all__ = [
    "SystemEarningsEngine",
    "QUALIFYING_EVENT_TYPES",
]
