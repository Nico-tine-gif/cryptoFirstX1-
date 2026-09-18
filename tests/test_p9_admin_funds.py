import os
import tempfile

from core.admin.funds import AdminFunds
from core.deposits.monetary_credit import MonetaryDepositCredit
from core.security.admin import AdminController


def main():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        admin = AdminController()

        # Test unauthenticated access first.
        funds = AdminFunds(admin, db_path)

        try:
            funds.dashboard()
            raise AssertionError("unauthenticated access was allowed")
        except PermissionError as exc:
            assert str(exc) == "ADMIN_AUTH_REQUIRED"

        # No real credential is placed in source code.
        os.environ["CRYPTOFIRSTX1_ADMIN"] = "P9_TEST_ADMIN"
        os.environ["CRYPTOFIRSTX1_ADMIN_CREDENTIAL_SHA256"] = (
            "ef92b778ba3e1e7a9e5b5e3a7c5e5b7b"
            "e7f4c7e7c8c9f0f2e3c4d5e6f7a8b9c0"
        )

        # Use the actual SHA-256 generated locally for the test credential.
        import hashlib

        credential = "p9-test-credential"
        os.environ["CRYPTOFIRSTX1_ADMIN_CREDENTIAL_SHA256"] = (
            hashlib.sha256(credential.encode()).hexdigest()
        )

        admin.authenticate("P9_TEST_ADMIN", credential)

        assert admin.authorized() is True

        # Dashboard starts at zero.
        dashboard = funds.dashboard()

        assert dashboard["available_cents"] == 0
        assert dashboard["reserved_cents"] == 0
        assert dashboard["total_cents"] == 0

        # Simulate a VERIFIED/RECONCILED deposit through the proper path.
        deposit = MonetaryDepositCredit(db_path)

        deposit.credit_reconciled_deposit(
            account_id="admin",
            amount_cents=12500,
            deposit_id="P9-VERIFIED-DEPOSIT-001",
        )

        dashboard = funds.dashboard()

        assert dashboard["available_cents"] == 12500
        assert dashboard["reserved_cents"] == 0
        assert dashboard["total_cents"] == 12500
        assert dashboard["total_units"] == "125"

        deposits = funds.deposits()

        assert len(deposits) == 1
        assert deposits[0]["amount_cents"] == 12500

        withdrawals = funds.withdrawals()
        assert withdrawals == []

        ledger = funds.ledger_history()

        assert len(ledger) == 1
        assert ledger[0]["entry_type"] == "DEPOSIT_CREDIT"

        security = funds.security_status()

        assert security["admin_authenticated"] is True
        assert security["p6_signing"] == "LOCKED"
        assert security["p6_broadcast"] == "LOCKED"
        assert security["private_keys_stored"] is False
        assert security["automatic_withdrawals"] is False

        print("==============================================")
        print("P9 ADMIN FUNDS TEST")
        print("==============================================")
        print("ADMIN AUTHENTICATION  : PASS")
        print("UNAUTHENTICATED BLOCK : PASS")
        print("ADMIN DASHBOARD       : PASS")
        print("DEPOSIT SECTION       : PASS")
        print("WITHDRAWAL SECTION    : PASS")
        print("LEDGER SECTION        : PASS")
        print("SECURITY SECTION      : PASS")
        print("BALANCE               : $125.00")
        print("P6 SIGNING            : LOCKED")
        print("P6 BROADCAST          : LOCKED")
        print("PRIVATE KEYS           : NOT STORED")
        print("P9 ADMIN FUNDS        : PASS")
        print("==============================================")

    finally:
        os.environ.pop("CRYPTOFIRSTX1_ADMIN", None)
        os.environ.pop("CRYPTOFIRSTX1_ADMIN_CREDENTIAL_SHA256", None)
        os.unlink(db_path)


if __name__ == "__main__":
    main()
