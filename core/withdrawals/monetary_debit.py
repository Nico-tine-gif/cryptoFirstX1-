import sqlite3
import uuid
from datetime import datetime, timezone

from core.finance.accounts import AccountStore
from core.finance.money import Money


class MonetaryWithdrawal:
    """
    Reserves available monetary funds for an approved withdrawal.

    Actual network signing/broadcasting remains under P6.
    """

    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.db_path = db_path
        self.accounts = AccountStore(db_path)

    def reserve(
        self,
        account_id,
        amount_cents,
        withdrawal_id,
    ):
        Money.validate_cents(amount_cents)

        if amount_cents <= 0:
            raise ValueError("withdrawal amount must be positive")

        if not withdrawal_id:
            raise ValueError("withdrawal_id required")

        self.accounts.ensure_account(account_id)

        reservation_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")

            row = db.execute("""
                SELECT available_cents, reserved_cents
                FROM monetary_accounts
                WHERE account_id=?
            """, (account_id,)).fetchone()

            available = int(row[0])
            reserved = int(row[1])

            if available < amount_cents:
                raise ValueError("INSUFFICIENT_AVAILABLE_FUNDS")

            db.execute("""
                UPDATE monetary_accounts
                SET available_cents=?,
                    reserved_cents=?,
                    updated_at=?
                WHERE account_id=?
            """, (
                available - amount_cents,
                reserved + amount_cents,
                now,
                account_id,
            ))

            db.execute("""
                INSERT INTO monetary_reservations
                (reservation_id, account_id, amount_cents,
                 reference_type, reference_id, state,
                 created_at, updated_at)
                VALUES (?, ?, ?, 'WITHDRAWAL', ?, 'RESERVED', ?, ?)
            """, (
                reservation_id,
                account_id,
                amount_cents,
                withdrawal_id,
                now,
                now,
            ))

        return reservation_id

    def release(
        self,
        reservation_id,
    ):
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")

            row = db.execute("""
                SELECT account_id, amount_cents, state
                FROM monetary_reservations
                WHERE reservation_id=?
            """, (reservation_id,)).fetchone()

            if not row:
                raise KeyError(reservation_id)

            account_id, amount_cents, state = row

            if state != "RESERVED":
                raise ValueError(
                    f"reservation cannot be released from {state}"
                )

            account = db.execute("""
                SELECT available_cents, reserved_cents
                FROM monetary_accounts
                WHERE account_id=?
            """, (account_id,)).fetchone()

            available = int(account[0])
            reserved = int(account[1])

            if reserved < int(amount_cents):
                raise RuntimeError("RESERVED_BALANCE_CORRUPTION")

            db.execute("""
                UPDATE monetary_accounts
                SET available_cents=?,
                    reserved_cents=?,
                    updated_at=?
                WHERE account_id=?
            """, (
                available + int(amount_cents),
                reserved - int(amount_cents),
                now,
                account_id,
            ))

            db.execute("""
                UPDATE monetary_reservations
                SET state='RELEASED', updated_at=?
                WHERE reservation_id=?
            """, (now, reservation_id))

        return True

    def settle(self, reservation_id):
        """
        Consume a reserved withdrawal after external settlement.

        P6 still controls signing and broadcasting.
        """
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")

            row = db.execute("""
                SELECT account_id, amount_cents, state, reference_id
                FROM monetary_reservations
                WHERE reservation_id=?
            """, (reservation_id,)).fetchone()

            if not row:
                raise KeyError(reservation_id)

            account_id, amount_cents, state, withdrawal_id = row

            if state != "RESERVED":
                raise ValueError(
                    f"reservation cannot settle from {state}"
                )

            account = db.execute("""
                SELECT reserved_cents
                FROM monetary_accounts
                WHERE account_id=?
            """, (account_id,)).fetchone()

            reserved = int(account[0])

            if reserved < int(amount_cents):
                raise RuntimeError("RESERVED_BALANCE_CORRUPTION")

            db.execute("""
                UPDATE monetary_accounts
                SET reserved_cents=?,
                    updated_at=?
                WHERE account_id=?
            """, (
                reserved - int(amount_cents),
                now,
                account_id,
            ))

            db.execute("""
                UPDATE monetary_reservations
                SET state='SETTLED', updated_at=?
                WHERE reservation_id=?
            """, (now, reservation_id))

            db.execute("""
                INSERT INTO monetary_ledger
                (entry_id, account_id, entry_type, amount_cents,
                 reference_type, reference_id, description, created_at)
                VALUES (?, ?, 'WITHDRAWAL_DEBIT', ?, 'WITHDRAWAL', ?, ?, ?)
            """, (
                uuid.uuid4().hex,
                account_id,
                int(amount_cents),
                withdrawal_id,
                'Settled withdrawal',
                now,
            ))

        return True
