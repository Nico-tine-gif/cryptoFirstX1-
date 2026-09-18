"""Regression: settle writes WITHDRAWAL_DEBIT to monetary_ledger."""
import sqlite3
from core.finance.accounts import AccountStore
from core.deposits.monetary_credit import MonetaryDepositCredit
from core.withdrawals.monetary_debit import MonetaryWithdrawal


def test_settle_writes_ledger_debit(tmp_path):
    db = str(tmp_path / "t.db")
    AccountStore(db).ensure_account("admin")

    MonetaryDepositCredit(db).credit_reconciled_deposit(
        account_id="admin", amount_cents=10000, deposit_id="D1",
    )
    rid = MonetaryWithdrawal(db).reserve(
        account_id="admin", amount_cents=2500, withdrawal_id="W1",
    )
    MonetaryWithdrawal(db).settle(rid)

    con = sqlite3.connect(db)
    credit = con.execute(
        "SELECT COALESCE(SUM(amount_cents),0) FROM monetary_ledger "
        "WHERE entry_type='DEPOSIT_CREDIT'"
    ).fetchone()[0]
    debit = con.execute(
        "SELECT COALESCE(SUM(amount_cents),0) FROM monetary_ledger "
        "WHERE entry_type='WITHDRAWAL_DEBIT'"
    ).fetchone()[0]
    available = con.execute(
        "SELECT available_cents FROM monetary_accounts WHERE account_id='admin'"
    ).fetchone()[0]
    con.close()

    assert credit == 10000
    assert debit == 2500
    assert credit - debit == available   # ledger matches reality


def test_release_does_not_write_debit(tmp_path):
    """Release cancels a reservation — no money leaves, no debit entry."""
    db = str(tmp_path / "t.db")
    AccountStore(db).ensure_account("admin")
    MonetaryDepositCredit(db).credit_reconciled_deposit(
        account_id="admin", amount_cents=10000, deposit_id="D1",
    )
    rid = MonetaryWithdrawal(db).reserve(
        account_id="admin", amount_cents=2500, withdrawal_id="W1",
    )
    MonetaryWithdrawal(db).release(rid)

    con = sqlite3.connect(db)
    debits = con.execute(
        "SELECT COUNT(*) FROM monetary_ledger WHERE entry_type='WITHDRAWAL_DEBIT'"
    ).fetchone()[0]
    available = con.execute(
        "SELECT available_cents FROM monetary_accounts WHERE account_id='admin'"
    ).fetchone()[0]
    con.close()

    assert debits == 0
    assert available == 10000   # nothing left the system


def test_double_settle_is_rejected(tmp_path):
    import pytest
    db = str(tmp_path / "t.db")
    AccountStore(db).ensure_account("admin")
    MonetaryDepositCredit(db).credit_reconciled_deposit(
        account_id="admin", amount_cents=10000, deposit_id="D1",
    )
    rid = MonetaryWithdrawal(db).reserve(
        account_id="admin", amount_cents=2500, withdrawal_id="W1",
    )
    MonetaryWithdrawal(db).settle(rid)

    with pytest.raises(ValueError, match="cannot settle from SETTLED"):
        MonetaryWithdrawal(db).settle(rid)
