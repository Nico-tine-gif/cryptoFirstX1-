import sqlite3
import uuid
from datetime import datetime, timezone

from .money import Money
from .accounts import AccountStore


class MonetaryLedger:
    """
    Double-entry-oriented monetary event ledger.

    A ledger credit/debit is immutable.
    Account balances are updated atomically with each entry.
    """

    CREDIT_TYPES = {
        "DEPOSIT_CREDIT",
        "ADMIN_CREDIT",
        "ADJUSTMENT_CREDIT",
    }

    DEBIT_TYPES = {
        "WITHDRAWAL_DEBIT",
        "ADMIN_DEBIT",
        "ADJUSTMENT_DEBIT",
    }

    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.accounts = AccountStore(db_path)
        self.db_path = db_path

    def _entry(
        self,
        account_id,
        entry_type,
        amount_cents,
        reference_type=None,
        reference_id=None,
        description=None,
    ):
        Money.validate_cents(amount_cents)

        if amount_cents == 0:
            raise ValueError("amount must be greater than zero")

        if entry_type not in self.CREDIT_TYPES | self.DEBIT_TYPES:
            raise ValueError("invalid ledger entry type")

        self.accounts.ensure_account(account_id)

        entry_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")

            row = db.execute("""
                SELECT available_cents, reserved_cents
                FROM monetary_accounts
                WHERE account_id=?
            """, (account_id,)).fetchone()

            if not row:
                raise KeyError(account_id)

            available = int(row[0])
            reserved = int(row[1])

            if entry_type in self.CREDIT_TYPES:
                new_available = available + amount_cents
            else:
                if available < amount_cents:
                    raise ValueError("INSUFFICIENT_AVAILABLE_FUNDS")
                new_available = available - amount_cents

            db.execute("""
                INSERT INTO monetary_ledger
                (entry_id, account_id, entry_type, amount_cents,
                 reference_type, reference_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                account_id,
                entry_type,
                amount_cents,
                reference_type,
                reference_id,
                description,
                now,
            ))

            db.execute("""
                UPDATE monetary_accounts
                SET available_cents=?, updated_at=?
                WHERE account_id=?
            """, (
                new_available,
                now,
                account_id,
            ))

        return entry_id

    def credit(
        self,
        account_id,
        amount_cents,
        reference_type=None,
        reference_id=None,
        description=None,
    ):
        return self._entry(
            account_id,
            "DEPOSIT_CREDIT",
            amount_cents,
            reference_type,
            reference_id,
            description,
        )

    def debit(
        self,
        account_id,
        amount_cents,
        reference_type=None,
        reference_id=None,
        description=None,
    ):
        return self._entry(
            account_id,
            "WITHDRAWAL_DEBIT",
            amount_cents,
            reference_type,
            reference_id,
            description,
        )

    def history(self, account_id="admin", limit=100):
        self.accounts.ensure_account(account_id)

        with sqlite3.connect(self.db_path) as db:
            rows = db.execute("""
                SELECT entry_id, account_id, entry_type,
                       amount_cents, reference_type,
                       reference_id, description, created_at
                FROM monetary_ledger
                WHERE account_id=?
                ORDER BY created_at DESC
                LIMIT ?
            """, (account_id, int(limit))).fetchall()

        return [
            {
                "entry_id": r[0],
                "account_id": r[1],
                "entry_type": r[2],
                "amount_cents": r[3],
                "reference_type": r[4],
                "reference_id": r[5],
                "description": r[6],
                "created_at": r[7],
            }
            for r in rows
        ]
