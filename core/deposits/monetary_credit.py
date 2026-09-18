from core.finance.ledger import MonetaryLedger
from core.finance.money import Money


class MonetaryDepositCredit:
    """
    Converts a VERIFIED/RECONCILED deposit into monetary ledger value.

    A blockchain detection alone never creates spendable funds.
    """

    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.ledger = MonetaryLedger(db_path)

    def credit_reconciled_deposit(
        self,
        account_id,
        amount_cents,
        deposit_id,
    ):
        Money.validate_cents(amount_cents)

        if amount_cents <= 0:
            raise ValueError("deposit amount must be positive")

        if not deposit_id:
            raise ValueError("deposit_id required")

        return self.ledger.credit(
            account_id=account_id,
            amount_cents=amount_cents,
            reference_type="DEPOSIT",
            reference_id=deposit_id,
            description="Verified and reconciled deposit",
        )
