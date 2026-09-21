from core.finance.balances import BalanceService
from core.finance.ledger import MonetaryLedger


class AdminFunds:
    """
    Authenticated admin monetary dashboard.

    Read access is protected by the existing AdminController.
    Monetary credits must come from the verified deposit path.
    Withdrawal settlement remains separate from P6 signing/broadcasting.
    """

    def __init__(self, admin_controller, db_path="data/cryptoFirstX1.db"):
        self.admin = admin_controller
        self.balance = BalanceService(db_path)
        self.ledger = MonetaryLedger(db_path)

    def _require_admin(self):
        if not self.admin.authorized():
            raise PermissionError("ADMIN_AUTH_REQUIRED")

    def dashboard(self, account_id="admin"):
        self._require_admin()
        return self.balance.dashboard(account_id)

    def deposits(self, account_id="admin", limit=100):
        self._require_admin()

        return [
            item
            for item in self.ledger.history(account_id, limit)
            if item["entry_type"] == "DEPOSIT_CREDIT"
        ]

    def withdrawals(self, account_id="admin", limit=100):
        self._require_admin()

        return [
            item
            for item in self.ledger.history(account_id, limit)
            if item["entry_type"] == "WITHDRAWAL_DEBIT"
        ]

    def ledger_history(self, account_id="admin", limit=100):
        self._require_admin()
        return self.ledger.history(account_id, limit)

    def security_status(self):
        self._require_admin()

        return {
            "admin_authenticated": True,
            "p6_signing": "LOCKED",
            "p6_broadcast": "LOCKED",
            "private_keys_stored": False,
            "automatic_withdrawals": False,
        }
