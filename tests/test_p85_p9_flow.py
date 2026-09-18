import os
import tempfile

from core.p8_5 import SystemEarningsEngine
from core.p9.admin_account import P9AdminAccount


def create_p9_schema(db):
    import sqlite3

    con = sqlite3.connect(db)

    con.execute("""
        CREATE TABLE monetary_accounts (
            account_id TEXT PRIMARY KEY,
            currency TEXT NOT NULL,
            available_cents INTEGER NOT NULL DEFAULT 0,
            reserved_cents INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE monetary_ledger (
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

    con.execute("""
        INSERT INTO monetary_accounts (
            account_id,
            currency,
            available_cents,
            reserved_cents,
            created_at,
            updated_at
        )
        VALUES ('admin','USD',0,0,'test','test')
    """)

    con.commit()
    con.close()


def main():

    fd, db = tempfile.mkstemp(
        prefix="cryptoFirstX1_p85_",
        suffix=".db",
    )
    os.close(fd)

    try:
        create_p9_schema(db)

        engine = SystemEarningsEngine(db_path=db)

        # One approved blockchain/platform event = one unit.
        result = engine.process(
            event_type="TRANSACTION_CONFIRMED",
            event_id="TX-DEMO-001",
            source_reference="blockchain:TX-DEMO-001",
            description="Verified qualifying transaction",
        )

        assert result["status"] == "CREDITED"
        assert result["units"] == 1
        assert result["amount_cents"] == 100

        # Duplicate event must not be allowed.
        duplicate = engine.credit_approved_event("TX-DEMO-001")
        assert duplicate["status"] == "ALREADY_CREDITED"

        totals = engine.totals()

        assert totals["credited_units"] == 1
        assert totals["credited_cents"] == 100

        dashboard = P9AdminAccount(db).dashboard()

        assert dashboard["system_earned_units"] == 1
        assert dashboard["system_earned_cents"] == 100
        assert dashboard["available_cents"] == 100

        print("==============================================")
        print("P8.5 -> P9 SYSTEM EARNINGS TEST")
        print("==============================================")
        print("QUALIFYING EVENT       : PASS")
        print("APPROVAL                : PASS")
        print("1 EVENT = 1 UNIT       : PASS")
        print("1 UNIT = $1.00         : PASS")
        print("SYSTEM EARNINGS LEDGER : PASS")
        print("P9 ADMIN CREDIT        : PASS")
        print("DUPLICATE PROTECTION   : PASS")
        print("ADMIN AVAILABLE        : $1.00")
        print("==============================================")
        print("P8.5 -> P9 FLOW        : PASS")
        print("==============================================")

    finally:
        try:
            os.remove(db)
        except OSError:
            pass


if __name__ == "__main__":
    main()
