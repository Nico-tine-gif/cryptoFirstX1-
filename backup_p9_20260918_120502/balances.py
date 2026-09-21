from .accounts import AccountStore
from .money import Money


class BalanceService:

    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.accounts = AccountStore(db_path)

    def dashboard(self, account_id="admin"):
        account = self.accounts.ensure_account(account_id)

        available = int(account["available_cents"])
        reserved = int(account["reserved_cents"])

        return {
            "account_id": account_id,
            "currency": "USD",
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
        }
