import sqlite3
from core.finance.accounts import AccountStore
from core.deposits.store import DepositStore
from core.deposits.monetary_credit import MonetaryDepositCredit
from core.p9.reconcile import reconcile


def _seed(db):
    AccountStore(db).ensure_account("admin")
    DepositStore(db)


def _dep(db, did, state="CONFIRMED"):
    con = sqlite3.connect(db)
    con.execute(
        "INSERT INTO deposits (deposit_id,txid,vout,address,value_sats,network,state,confirmations,required_confirmations,first_seen,last_seen) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (did, "t-"+did, 0, "addr", 100000, "bitcoin", state, 0, 3, 1, 1),
    )
    con.commit(); con.close()


def test_empty(tmp_path):
    db = str(tmp_path/"t.db"); _seed(db)
    r = reconcile(db)
    assert r.balanced
    assert r.chain_count == 0


def test_chain_pending_not_yet_credited(tmp_path):
    db = str(tmp_path/"t.db"); _seed(db); _dep(db, "D1")
    r = reconcile(db)
    assert r.balanced
    assert r.chain_count == 1
    assert r.credited_count == 0
    assert r.pending_credit == ["D1"]


def test_ghost_parked_at_admin(tmp_path):
    """A MEMPOOL deposit (ghost) can still be parked at admin."""
    db = str(tmp_path/"t.db"); _seed(db); _dep(db, "G1", state="MEMPOOL")
    MonetaryDepositCredit(db).credit_reconciled_deposit(
        account_id="admin", amount_cents=1000, deposit_id="G1",
    )
    r = reconcile(db)
    assert r.balanced
    assert r.both_sides_count == 1
    assert r.pending_credit == []


def test_orphan_credit_is_a_bug(tmp_path):
    db = str(tmp_path/"t.db"); _seed(db)
    MonetaryDepositCredit(db).credit_reconciled_deposit(
        account_id="admin", amount_cents=5000, deposit_id="NOWHERE",
    )
    r = reconcile(db)
    assert not r.balanced
    assert r.orphan_credits == ["NOWHERE"]
