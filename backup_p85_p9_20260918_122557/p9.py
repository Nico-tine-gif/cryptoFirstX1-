import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# P9 — UNIFIED MONETARY LEDGER & ADMIN FUNDS
# ============================================================

CENTS_PER_UNIT = 100
CURRENCY = "USD"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# MONEY
# ============================================================

class Money:
    @staticmethod
    def dollars_to_cents(value):
        amount = Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        return int(amount * CENTS_PER_UNIT)

    @staticmethod
    def cents_to_dollars(cents):
        return Decimal(int(cents)) / CENTS_PER_UNIT

    @staticmethod
    def validate_cents(cents):
        if isinstance(cents, bool):
            raise ValueError("amount must be integer cents")

        cents = int(cents)

        if cents <= 0:
            raise ValueError("amount must be positive")

        return cents


# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

@dataclass
class AdminSession:
    authenticated: bool = False
    administrator: str = ""
    emergency_lock: bool = False


class AdminController:
    def __init__(self):
        self.session = AdminSession()

    def authenticate(self, administrator, credential=None):
        expected_admin = os.environ.get("CRYPTOFIRSTX1_ADMIN")
        expected_hash = os.environ.get(
            "CRYPTOFIRSTX1_ADMIN_CREDENTIAL_SHA256"
        )

        if not administrator:
            raise ValueError("Administrator identity required")

        if not expected_admin or not expected_hash:
            raise PermissionError("ADMIN_CREDENTIALS_NOT_CONFIGURED")

        if not hmac.compare_digest(
            administrator,
            expected_admin,
        ):
            raise PermissionError("ADMIN_AUTH_FAILED")

        if credential is None:
            raise PermissionError("ADMIN_CREDENTIAL_REQUIRED")

        supplied_hash = hashlib.sha256(
            credential.encode("utf-8")
        ).hexdigest()

        if not hmac.compare_digest(
            supplied_hash,
            expected_hash,
        ):
            raise PermissionError("ADMIN_AUTH_FAILED")

        self.session.authenticated = True
        self.session.administrator = administrator

    def lock(self):
        self.session.emergency_lock = True

    def unlock(self):
        if not self.session.authenticated:
            raise PermissionError("ADMIN_AUTH_REQUIRED")

        self.session.emergency_lock = False

    def authorized(self):
        return (
            self.session.authenticated
            and not self.session.emergency_lock
        )


# ============================================================
# DATABASE
# ============================================================

class P9Database:
    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.db_path = str(db_path)

        parent = Path(self.db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)

        self._initialize()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self):
        with self.connect() as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS monetary_accounts (
                    account_id TEXT PRIMARY KEY,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    available_cents INTEGER NOT NULL DEFAULT 0,
                    reserved_cents INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.execute("""
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

            conn.execute("""
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

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_monetary_ledger_account
                ON monetary_ledger(account_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_monetary_ledger_type
                ON monetary_ledger(entry_type)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_monetary_reservation_account
                ON monetary_reservations(account_id)
            """)

            conn.commit()


# ============================================================
# ACCOUNT / BALANCE
# ============================================================

class AccountService:
    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.db = P9Database(db_path)

    def ensure(self, account_id="admin"):
        now = utc_now()

        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO monetary_accounts
                (
                    account_id,
                    currency,
                    available_cents,
                    reserved_cents,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, 0, 0, ?, ?)
                """,
                (
                    account_id,
                    CURRENCY,
                    now,
                    now,
                ),
            )
            conn.commit()

    def get(self, account_id="admin"):
        self.ensure(account_id)

        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM monetary_accounts
                WHERE account_id=?
                """,
                (account_id,),
            ).fetchone()

        return dict(row)


class BalanceService:
    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.accounts = AccountService(db_path)

    def dashboard(self, account_id="admin"):
        row = self.accounts.get(account_id)

        available = int(row["available_cents"])
        reserved = int(row["reserved_cents"])
        total = available + reserved

        return {
            "account_id": account_id,
            "currency": CURRENCY,

            "available_cents": available,
            "reserved_cents": reserved,
            "total_cents": total,

            "available_units": str(
                Money.cents_to_dollars(available)
            ),
            "reserved_units": str(
                Money.cents_to_dollars(reserved)
            ),
            "total_units": str(
                Money.cents_to_dollars(total)
            ),

            "available_dollars": f"${available / 100:.2f}",
            "reserved_dollars": f"${reserved / 100:.2f}",
            "total_dollars": f"${total / 100:.2f}",
        }


# ============================================================
# IMMUTABLE MONETARY LEDGER
# ============================================================

class MonetaryLedger:
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
        self.db = P9Database(db_path)
        self.accounts = AccountService(db_path)

    def _entry(
        self,
        account_id,
        entry_type,
        amount_cents,
        reference_type=None,
        reference_id=None,
        description=None,
    ):
        amount_cents = Money.validate_cents(amount_cents)

        if entry_type not in (
            self.CREDIT_TYPES | self.DEBIT_TYPES
        ):
            raise ValueError(
                f"invalid ledger entry type: {entry_type}"
            )

        self.accounts.ensure(account_id)

        entry_id = uuid.uuid4().hex
        now = utc_now()

        with self.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            row = conn.execute(
                """
                SELECT available_cents
                FROM monetary_accounts
                WHERE account_id=?
                """,
                (account_id,),
            ).fetchone()

            available = int(row["available_cents"])

            if entry_type in self.CREDIT_TYPES:
                new_available = available + amount_cents
            else:
                if available < amount_cents:
                    raise ValueError("INSUFFICIENT_FUNDS")

                new_available = available - amount_cents

            conn.execute(
                """
                UPDATE monetary_accounts
                SET available_cents=?,
                    updated_at=?
                WHERE account_id=?
                """,
                (
                    new_available,
                    now,
                    account_id,
                ),
            )

            conn.execute(
                """
                INSERT INTO monetary_ledger
                (
                    entry_id,
                    account_id,
                    entry_type,
                    amount_cents,
                    reference_type,
                    reference_id,
                    description,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    account_id,
                    entry_type,
                    amount_cents,
                    reference_type,
                    reference_id,
                    description,
                    now,
                ),
            )

            conn.commit()

        return entry_id

    def credit(
        self,
        account_id,
        amount_cents,
        reference_type="DEPOSIT",
        reference_id=None,
        description="Verified/reconciled deposit credit",
    ):
        return self._entry(
            account_id=account_id,
            entry_type="DEPOSIT_CREDIT",
            amount_cents=amount_cents,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )

    def debit(
        self,
        account_id,
        amount_cents,
        reference_type="WITHDRAWAL",
        reference_id=None,
        description="Settled withdrawal debit",
    ):
        return self._entry(
            account_id=account_id,
            entry_type="WITHDRAWAL_DEBIT",
            amount_cents=amount_cents,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )

    def history(self, account_id="admin", limit=100):
        limit = max(1, min(int(limit), 1000))

        self.accounts.ensure(account_id)

        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM monetary_ledger
                WHERE account_id=?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (
                    account_id,
                    limit,
                ),
            ).fetchall()

        return [dict(row) for row in rows]


# ============================================================
# VERIFIED DEPOSITS
# ============================================================

class MonetaryDepositCredit:
    """
    Only VERIFIED/RECONCILED deposits may reach this method.
    Mempool detection or unconfirmed blockchain activity does not
    create spendable monetary credit.
    """

    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.ledger = MonetaryLedger(db_path)

    def credit_reconciled_deposit(
        self,
        account_id,
        amount_cents,
        deposit_id,
    ):
        if not deposit_id:
            raise ValueError("deposit_id required")

        return self.ledger.credit(
            account_id=account_id,
            amount_cents=amount_cents,
            reference_type="DEPOSIT",
            reference_id=deposit_id,
            description="VERIFIED/RECONCILED deposit credit",
        )


# ============================================================
# WITHDRAWAL RESERVATION / SETTLEMENT
# ============================================================

class MonetaryWithdrawal:
    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.db = P9Database(db_path)
        self.accounts = AccountService(db_path)

    def reserve(
        self,
        account_id,
        amount_cents,
        withdrawal_id,
    ):
        amount_cents = Money.validate_cents(amount_cents)

        if not withdrawal_id:
            raise ValueError("withdrawal_id required")

        self.accounts.ensure(account_id)

        reservation_id = uuid.uuid4().hex
        now = utc_now()

        with self.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            row = conn.execute(
                """
                SELECT available_cents
                FROM monetary_accounts
                WHERE account_id=?
                """,
                (account_id,),
            ).fetchone()

            available = int(row["available_cents"])

            if available < amount_cents:
                raise ValueError("INSUFFICIENT_FUNDS")

            conn.execute(
                """
                UPDATE monetary_accounts
                SET available_cents=?,
                    reserved_cents=reserved_cents + ?,
                    updated_at=?
                WHERE account_id=?
                """,
                (
                    available - amount_cents,
                    amount_cents,
                    now,
                    account_id,
                ),
            )

            conn.execute(
                """
                INSERT INTO monetary_reservations
                (
                    reservation_id,
                    account_id,
                    amount_cents,
                    reference_type,
                    reference_id,
                    state,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reservation_id,
                    account_id,
                    amount_cents,
                    "WITHDRAWAL",
                    withdrawal_id,
                    "RESERVED",
                    now,
                    now,
                ),
            )

            conn.commit()

        return reservation_id

    def _get(self, reservation_id):
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM monetary_reservations
                WHERE reservation_id=?
                """,
                (reservation_id,),
            ).fetchone()

        if not row:
            raise KeyError(reservation_id)

        return dict(row)

    def release(self, reservation_id):
        item = self._get(reservation_id)

        if item["state"] != "RESERVED":
            raise ValueError(
                f"cannot release from state {item['state']}"
            )

        now = utc_now()

        with self.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            conn.execute(
                """
                UPDATE monetary_accounts
                SET reserved_cents=reserved_cents - ?,
                    available_cents=available_cents + ?,
                    updated_at=?
                WHERE account_id=?
                """,
                (
                    item["amount_cents"],
                    item["amount_cents"],
                    now,
                    item["account_id"],
                ),
            )

            conn.execute(
                """
                UPDATE monetary_reservations
                SET state='RELEASED',
                    updated_at=?
                WHERE reservation_id=?
                """,
                (
                    now,
                    reservation_id,
                ),
            )

            conn.commit()

        return self._get(reservation_id)

    def settle(self, reservation_id):
        item = self._get(reservation_id)

        if item["state"] != "RESERVED":
            raise ValueError(
                f"cannot settle from state {item['state']}"
            )

        now = utc_now()

        with self.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            conn.execute(
                """
                UPDATE monetary_accounts
                SET reserved_cents=reserved_cents - ?,
                    updated_at=?
                WHERE account_id=?
                """,
                (
                    item["amount_cents"],
                    now,
                    item["account_id"],
                ),
            )

            conn.execute(
                """
                UPDATE monetary_reservations
                SET state='SETTLED',
                    updated_at=?
                WHERE reservation_id=?
                """,
                (
                    now,
                    reservation_id,
                ),
            )

            conn.commit()

        return self._get(reservation_id)


# ============================================================
# ADMIN FUNDS
# ============================================================

class AdminFunds:
    def __init__(
        self,
        admin_controller,
        db_path="data/cryptoFirstX1.db",
    ):
        self.admin = admin_controller
        self.balance = BalanceService(db_path)
        self.ledger = MonetaryLedger(db_path)

    def _require_admin(self):
        if not self.admin.authorized():
            raise PermissionError("ADMIN_AUTH_REQUIRED")

    def dashboard(self, account_id="admin"):
        self._require_admin()
        return self.balance.dashboard(account_id)

    def deposits(
        self,
        account_id="admin",
        limit=100,
    ):
        self._require_admin()

        return [
            item
            for item in self.ledger.history(
                account_id,
                limit,
            )
            if item["entry_type"] == "DEPOSIT_CREDIT"
        ]

    def withdrawals(
        self,
        account_id="admin",
        limit=100,
    ):
        self._require_admin()

        return [
            item
            for item in self.ledger.history(
                account_id,
                limit,
            )
            if item["entry_type"] == "WITHDRAWAL_DEBIT"
        ]

    def ledger_history(
        self,
        account_id="admin",
        limit=100,
    ):
        self._require_admin()

        return self.ledger.history(
            account_id,
            limit,
        )

    def security_status(self):
        self._require_admin()

        return {
            "admin_authenticated": True,
            "p6_signing": "LOCKED",
            "p6_broadcast": "LOCKED",
            "private_keys_stored": False,
            "automatic_withdrawals": False,
        }


# ============================================================
# P9 FOUNDATION
# ============================================================

class P9MonetaryFoundation:
    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.db_path = db_path
        self.balance = BalanceService(db_path)

    def status(self):
        dashboard = self.balance.dashboard("admin")

        return {
            "phase": "P9",
            "name": "P9 Monetary Ledger & Admin Funds",
            "currency": CURRENCY,
            "unit_definition":
                "1 platform unit = $1.00 internal ledger value",
            "integer_cents": True,

            "available_cents":
                dashboard["available_cents"],
            "reserved_cents":
                dashboard["reserved_cents"],
            "total_cents":
                dashboard["total_cents"],

            "available_units":
                dashboard["available_units"],
            "reserved_units":
                dashboard["reserved_units"],
            "total_units":
                dashboard["total_units"],

            "monitoring_counts_convertible_to_money": False,
            "deposit_verification_required": True,

            "p6_signing_boundary": "LOCKED",
            "p6_broadcast_boundary": "LOCKED",
        }


class P9:
    """
    Single public entry point for the complete P9 subsystem.
    """

    def __init__(
        self,
        db_path="data/cryptoFirstX1.db",
        admin_controller=None,
    ):
        self.db_path = db_path

        self.admin = (
            admin_controller
            if admin_controller is not None
            else AdminController()
        )

        self.foundation = P9MonetaryFoundation(db_path)
        self.accounts = AccountService(db_path)
        self.balance = BalanceService(db_path)
        self.ledger = MonetaryLedger(db_path)
        self.deposits = MonetaryDepositCredit(db_path)
        self.withdrawals = MonetaryWithdrawal(db_path)
        self.funds = AdminFunds(
            self.admin,
            db_path,
        )

    def status(self):
        return self.foundation.status()

    def dashboard(self):
        return self.funds.dashboard()

    def deposit_history(self):
        return self.funds.deposits()

    def withdrawal_history(self):
        return self.funds.withdrawals()

    def ledger_history(self):
        return self.funds.ledger_history()

    def security(self):
        return self.funds.security_status()


__all__ = [
    "P9",
    "P9MonetaryFoundation",
    "AdminController",
    "AdminFunds",
    "Money",
    "MonetaryLedger",
    "BalanceService",
    "MonetaryDepositCredit",
    "MonetaryWithdrawal",
]
