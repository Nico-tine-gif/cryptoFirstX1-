import sqlite3
from dataclasses import dataclass, field

LEDGER_ENTRY_TYPE = "DEPOSIT_CREDIT"
ADMIN_ACCOUNT_ID = "admin"


@dataclass
class ReconcileReport:
    chain_count: int = 0
    credited_count: int = 0
    both_sides_count: int = 0
    pending_credit: list = field(default_factory=list)
    orphan_credits: list = field(default_factory=list)
    non_admin_accounts: list = field(default_factory=list)

    @property
    def balanced(self) -> bool:
        return not self.orphan_credits and not self.non_admin_accounts


def reconcile(db_path="data/cryptoFirstX1.db") -> ReconcileReport:
    con = sqlite3.connect(db_path)
    try:
        # Chain side — EVERY deposit ever recorded, any state
        chain = {r[0] for r in con.execute(
            "SELECT deposit_id FROM deposits WHERE deposit_id IS NOT NULL"
        )}

        # Ledger side — every DEPOSIT_CREDIT and who it credits
        rows = list(con.execute(
            "SELECT reference_id, account_id FROM monetary_ledger "
            "WHERE entry_type = ? AND reference_id IS NOT NULL",
            (LEDGER_ENTRY_TYPE,),
        ))
        credited = {r[0] for r in rows}
        non_admin = sorted({r[1] for r in rows if r[1] != ADMIN_ACCOUNT_ID})

        return ReconcileReport(
            chain_count=len(chain),
            credited_count=len(credited),
            both_sides_count=len(chain & credited),
            pending_credit=sorted(chain - credited),
            orphan_credits=sorted(credited - chain),
            non_admin_accounts=non_admin,
        )
    finally:
        con.close()


if __name__ == "__main__":
    r = reconcile()
    print("chain deposits    :", r.chain_count)
    print("ledger credits    :", r.credited_count)
    print("matched           :", r.both_sides_count)
    print("pending credit    :", r.pending_credit)
    print("orphan credits    :", r.orphan_credits)
    print("non-admin credits :", r.non_admin_accounts)
    print("balanced          :", r.balanced)
    raise SystemExit(0 if r.balanced else 1)
