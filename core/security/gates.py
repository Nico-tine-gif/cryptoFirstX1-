"""
core/security/gates.py — trust boundaries for privileged operations.

Each privileged operation passes through three gates:
    1. Config flag        (from core.config)
    2. Preconditions      (rate limit, daily cap, allowlist)
    3. Admin authentication

All three must pass. Any failure = DENIED.
"""
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

DEFAULT_DB = "data/cryptoFirstX1.db"


@dataclass
class Decision:
    status: str
    reason: str = ""

    @property
    def allowed(self):
        return self.status == "ALLOWED"


def _schema(db):
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS policy_rate_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            occurred_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_pre_time
            ON policy_rate_events(account_id, operation, occurred_at);

        CREATE TABLE IF NOT EXISTS policy_daily_totals (
            account_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            day TEXT NOT NULL,
            total_cents INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(account_id, operation, day)
        );

        CREATE TABLE IF NOT EXISTS policy_allowlist (
            address TEXT PRIMARY KEY,
            label TEXT DEFAULT '',
            added_at TEXT NOT NULL
        );
    """)
    con.commit()
    con.close()


class RateLimiter:
    def __init__(self, db=DEFAULT_DB):
        self.db = db
        _schema(db)

    def record(self, account_id, operation):
        now = int(datetime.now(timezone.utc).timestamp())
        con = sqlite3.connect(self.db)
        con.execute(
            "INSERT INTO policy_rate_events (account_id, operation, occurred_at) "
            "VALUES (?,?,?)", (account_id, operation, now))
        con.commit(); con.close()

    def count(self, account_id, operation, seconds):
        cutoff = int(datetime.now(timezone.utc).timestamp()) - seconds
        con = sqlite3.connect(self.db)
        n = con.execute(
            "SELECT COUNT(*) FROM policy_rate_events "
            "WHERE account_id=? AND operation=? AND occurred_at>=?",
            (account_id, operation, cutoff)).fetchone()[0]
        con.close()
        return int(n)


class DailyCap:
    def __init__(self, db=DEFAULT_DB):
        self.db = db
        _schema(db)

    def _today(self):
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def add(self, account_id, operation, amount_cents):
        con = sqlite3.connect(self.db)
        con.execute(
            "INSERT INTO policy_daily_totals (account_id, operation, day, total_cents) "
            "VALUES (?,?,?,?) "
            "ON CONFLICT(account_id, operation, day) "
            "DO UPDATE SET total_cents = total_cents + excluded.total_cents",
            (account_id, operation, self._today(), amount_cents))
        con.commit(); con.close()

    def used(self, account_id, operation):
        con = sqlite3.connect(self.db)
        row = con.execute(
            "SELECT total_cents FROM policy_daily_totals "
            "WHERE account_id=? AND operation=? AND day=?",
            (account_id, operation, self._today())).fetchone()
        con.close()
        return int(row[0]) if row else 0


class Allowlist:
    def __init__(self, db=DEFAULT_DB):
        self.db = db
        _schema(db)

    def add(self, address, label=""):
        con = sqlite3.connect(self.db)
        con.execute(
            "INSERT OR REPLACE INTO policy_allowlist (address, label, added_at) "
            "VALUES (?,?,?)",
            (address, label, datetime.now(timezone.utc).isoformat()))
        con.commit(); con.close()

    def remove(self, address):
        con = sqlite3.connect(self.db)
        con.execute("DELETE FROM policy_allowlist WHERE address=?", (address,))
        con.commit(); con.close()

    def entries(self):
        con = sqlite3.connect(self.db)
        rows = list(con.execute(
            "SELECT address, label, added_at FROM policy_allowlist ORDER BY address"))
        con.close()
        return rows

    def is_allowed(self, address):
        con = sqlite3.connect(self.db)
        n = con.execute(
            "SELECT COUNT(*) FROM policy_allowlist WHERE address=?",
            (address,)).fetchone()[0]
        con.close()
        return int(n) > 0


def _read_flags():
    try:
        from core import config
        return {
            "ALLOW_PRIVATE_KEY_EXPORT":    getattr(config, "ALLOW_PRIVATE_KEY_EXPORT", False),
            "ALLOW_REMOTE_SIGNING":        getattr(config, "ALLOW_REMOTE_SIGNING", False),
            "ALLOW_AUTOMATIC_WITHDRAWALS": getattr(config, "ALLOW_AUTOMATIC_WITHDRAWALS", False),
            "ALLOW_AUTOMATIC_CASHOUT":     getattr(config, "ALLOW_AUTOMATIC_CASHOUT", False),
            "WITHDRAWAL_MAX_PER_HOUR":     getattr(config, "WITHDRAWAL_MAX_PER_HOUR", 0),
            "WITHDRAWAL_DAILY_CAP_CENTS":  getattr(config, "WITHDRAWAL_DAILY_CAP_CENTS", 0),
            "WITHDRAWAL_MIN_ALLOWLIST":    getattr(config, "WITHDRAWAL_MIN_ALLOWLIST", 1),
        }
    except Exception:
        return {}


class PolicyEngine:
    def __init__(self, admin_controller, db=DEFAULT_DB, flags=None):
        self.admin = admin_controller
        self.db = db
        self.flags = flags if flags is not None else _read_flags()
        self.rate = RateLimiter(db)
        self.daily = DailyCap(db)
        self.allowlist = Allowlist(db)

    def evaluate_withdrawal(self, account_id, amount_cents, address):
        if not self.flags.get("ALLOW_AUTOMATIC_WITHDRAWALS"):
            return Decision("DENIED_FLAG",
                            "ALLOW_AUTOMATIC_WITHDRAWALS is False")

        min_al = int(self.flags.get("WITHDRAWAL_MIN_ALLOWLIST", 1) or 0)
        if min_al > 0 and len(self.allowlist.entries()) < min_al:
            return Decision("DENIED_PRECONDITION",
                            f"allowlist requires >= {min_al} entries")

        if not self.allowlist.is_allowed(address):
            return Decision("DENIED_PRECONDITION",
                            f"address {address} not on allowlist")

        per_hour = int(self.flags.get("WITHDRAWAL_MAX_PER_HOUR", 0) or 0)
        if per_hour > 0:
            n = self.rate.count(account_id, "withdrawal", 3600)
            if n >= per_hour:
                return Decision("DENIED_PRECONDITION",
                                f"rate limit {per_hour}/hour exceeded")

        cap = int(self.flags.get("WITHDRAWAL_DAILY_CAP_CENTS", 0) or 0)
        if cap > 0:
            used = self.daily.used(account_id, "withdrawal")
            if used + amount_cents > cap:
                return Decision("DENIED_PRECONDITION",
                                f"daily cap {cap} cents exceeded")

        if not self.admin.authorized():
            return Decision("REQUIRES_ADMIN",
                            "all preconditions met; admin auth required")

        return Decision("ALLOWED", "all gates passed")

    def record_withdrawal(self, account_id, amount_cents):
        self.rate.record(account_id, "withdrawal")
        self.daily.add(account_id, "withdrawal", amount_cents)

    def evaluate_signing(self):
        if not self.flags.get("ALLOW_REMOTE_SIGNING"):
            return Decision("DENIED_FLAG", "ALLOW_REMOTE_SIGNING is False")
        if not self.admin.authorized():
            return Decision("REQUIRES_ADMIN", "admin auth required")
        return Decision("ALLOWED", "signing allowed")

    def evaluate_cashout(self):
        if not self.flags.get("ALLOW_AUTOMATIC_CASHOUT"):
            return Decision("DENIED_FLAG", "ALLOW_AUTOMATIC_CASHOUT is False")
        if not self.admin.authorized():
            return Decision("REQUIRES_ADMIN", "admin auth required")
        return Decision("ALLOWED", "cashout allowed")

    def snapshot(self):
        return {
            "ALLOW_PRIVATE_KEY_EXPORT":    self.flags.get("ALLOW_PRIVATE_KEY_EXPORT"),
            "ALLOW_REMOTE_SIGNING":        self.flags.get("ALLOW_REMOTE_SIGNING"),
            "ALLOW_AUTOMATIC_WITHDRAWALS": self.flags.get("ALLOW_AUTOMATIC_WITHDRAWALS"),
            "ALLOW_AUTOMATIC_CASHOUT":     self.flags.get("ALLOW_AUTOMATIC_CASHOUT"),
            "WITHDRAWAL_MAX_PER_HOUR":     self.flags.get("WITHDRAWAL_MAX_PER_HOUR"),
            "WITHDRAWAL_DAILY_CAP_CENTS":  self.flags.get("WITHDRAWAL_DAILY_CAP_CENTS"),
            "WITHDRAWAL_MIN_ALLOWLIST":    self.flags.get("WITHDRAWAL_MIN_ALLOWLIST"),
            "allowlist_size":              len(self.allowlist.entries()),
            "admin_authorized":            self.admin.authorized(),
        }
