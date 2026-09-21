from .money import Money
from .accounts import AccountStore
from .ledger import MonetaryLedger
from .balances import BalanceService


class P9MonetaryFoundation:

    NAME = "P9 Monetary Ledger & Admin Funds"

    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.db_path = db_path
        self.accounts = AccountStore(db_path)
        self.ledger = MonetaryLedger(db_path)
        self.balances = BalanceService(db_path)

    def status(self):
        account = self.accounts.ensure_account("admin")

        available = int(account["available_cents"])
        reserved = int(account["reserved_cents"])

        return {
            "phase": "P9",
            "name": self.NAME,
            "currency": "USD",
            "unit_definition": "1 platform unit = $1.00 internal ledger value",
            "integer_cents": True,
            "available_cents": available,
            "reserved_cents": reserved,
            "total_cents": available + reserved,
            "available_units": str(
                Money.cents_to_dollars(available)
            ),
            "reserved_units": str(
                Money.cents_to_dollars(reserved)
            ),
            "total_units": str(
                Money.cents_to_dollars(available + reserved)
            ),
            "monitoring_counts_convertible_to_money": False,
            "deposit_verification_required": True,
            "p6_signing_boundary": "LOCKED",
            "p6_broadcast_boundary": "LOCKED",
        }
