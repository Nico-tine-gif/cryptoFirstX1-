import sqlite3
from pathlib import Path


class P9AdminAccount:

    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.db_path = str(db_path)

    def _db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def dashboard(self, account_id="admin"):

        with self._db() as db:

            row = db.execute("""
                SELECT
                    COALESCE(available_cents,0),
                    COALESCE(reserved_cents,0)
                FROM monetary_accounts
                WHERE account_id=?
            """, (account_id,)).fetchone()

            if row:
                available = int(row[0])
                reserved = int(row[1])
            else:
                available = 0
                reserved = 0

            deposit = db.execute("""
                SELECT
                    COALESCE(SUM(amount_cents),0)
                FROM monetary_ledger
                WHERE account_id=?
                  AND entry_type='DEPOSIT_CREDIT'
            """, (account_id,)).fetchone()[0]

            earnings = db.execute("""
                SELECT
                    COALESCE(SUM(amount_cents),0)
                FROM monetary_ledger
                WHERE account_id=?
                  AND entry_type='SYSTEM_EARNING_CREDIT'
            """, (account_id,)).fetchone()[0]

            withdrawals = db.execute("""
                SELECT
                    COALESCE(SUM(amount_cents),0)
                FROM monetary_ledger
                WHERE account_id=?
                  AND entry_type='WITHDRAWAL_DEBIT'
            """, (account_id,)).fetchone()[0]

        total = available + reserved

        return {
            "account_id": account_id,
            "currency": "USD",
            "available_cents": available,
            "reserved_cents": reserved,
            "total_cents": total,

            "available_units": available / 100,
            "reserved_units": reserved / 100,
            "total_units": total / 100,

            "deposit_backed_cents": int(deposit),
            "deposit_backed_units": int(deposit) / 100,

            "system_earned_cents": int(earnings),
            "system_earned_units": int(earnings) / 100,

            "withdrawal_debits_cents": int(withdrawals),
            "withdrawal_debits_units": int(withdrawals) / 100,

            "unit_definition": "1 platform unit = $1.00 internal monetary value",
        }


__all__ = ["P9AdminAccount"]
