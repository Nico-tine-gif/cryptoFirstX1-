import os
import sqlite3
import tempfile

from core.finance.money import Money
from core.finance.accounts import AccountStore
from core.finance.ledger import MonetaryLedger
from core.deposits.monetary_credit import MonetaryDepositCredit
from core.withdrawals.monetary_debit import MonetaryWithdrawal


def main():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        store = AccountStore(path)

        account = store.ensure_account("admin")

        assert account["available_cents"] == 0
        assert account["reserved_cents"] == 0

        assert Money.dollars_to_cents("1.00") == 100
        assert Money.dollars_to_cents("10.00") == 1000
        assert Money.dollars_to_cents("100.00") == 10000

        deposit = MonetaryDepositCredit(path)

        entry = deposit.credit_reconciled_deposit(
            account_id="admin",
            amount_cents=10000,
            deposit_id="DEP-001",
        )

        assert entry

        ledger = MonetaryLedger(path)
        balance = ledger.accounts.get("admin")

        assert balance["available_cents"] == 10000
        assert balance["reserved_cents"] == 0

        withdrawal = MonetaryWithdrawal(path)

        reservation = withdrawal.reserve(
            account_id="admin",
            amount_cents=2500,
            withdrawal_id="WD-001",
        )

        balance = ledger.accounts.get("admin")

        assert balance["available_cents"] == 7500
        assert balance["reserved_cents"] == 2500

        withdrawal.release(reservation)

        balance = ledger.accounts.get("admin")

        assert balance["available_cents"] == 10000
        assert balance["reserved_cents"] == 0

        reservation = withdrawal.reserve(
            account_id="admin",
            amount_cents=3000,
            withdrawal_id="WD-002",
        )

        withdrawal.settle(reservation)

        balance = ledger.accounts.get("admin")

        assert balance["available_cents"] == 7000
        assert balance["reserved_cents"] == 0

        try:
            withdrawal.reserve(
                account_id="admin",
                amount_cents=8000,
                withdrawal_id="WD-003",
            )
            raise AssertionError("insufficient funds was not rejected")
        except ValueError as exc:
            assert str(exc) == "INSUFFICIENT_AVAILABLE_FUNDS"

        print("==============================================")
        print("P9 MONETARY LEDGER TEST")
        print("==============================================")
        print("1 UNIT              : $1.00")
        print("INTEGER ACCOUNTING  : PASS")
        print("DEPOSIT CREDIT      : PASS")
        print("WITHDRAW RESERVE    : PASS")
        print("WITHDRAW RELEASE    : PASS")
        print("WITHDRAW SETTLE     : PASS")
        print("INSUFFICIENT FUNDS  : PASS")
        print("FINAL AVAILABLE     : $70.00")
        print("FINAL RESERVED      : $0.00")
        print("P9 FOUNDATION       : PASS")
        print("==============================================")

    finally:
        os.unlink(path)


if __name__ == "__main__":
    main()
