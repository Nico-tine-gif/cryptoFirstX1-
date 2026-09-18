import os, hashlib
from core.security.admin import AdminController
from core.security.gates import PolicyEngine

CRED = "p9-test-credential"


def _admin(auth=True):
    os.environ["CRYPTOFIRSTX1_ADMIN_CREDENTIAL_SHA256"] = (
        hashlib.sha256(CRED.encode()).hexdigest()
    )
    a = AdminController()
    if auth:
        a.authenticate("operator", CRED)
    return a


def test_flag_off_denies_withdrawal(tmp_path):
    db = str(tmp_path / "t.db")
    engine = PolicyEngine(_admin(), db=db, flags={
        "ALLOW_AUTOMATIC_WITHDRAWALS": False,
        "WITHDRAWAL_MIN_ALLOWLIST": 1,
    })
    d = engine.evaluate_withdrawal("admin", 1000, "bc1q")
    assert d.status == "DENIED_FLAG"


def test_allowlist_precondition(tmp_path):
    db = str(tmp_path / "t.db")
    engine = PolicyEngine(_admin(), db=db, flags={
        "ALLOW_AUTOMATIC_WITHDRAWALS": True,
        "WITHDRAWAL_MIN_ALLOWLIST": 1,
    })
    d = engine.evaluate_withdrawal("admin", 1000, "bc1q")
    assert d.status == "DENIED_PRECONDITION"

    engine.allowlist.add("bc1q", "test")
    d = engine.evaluate_withdrawal("admin", 1000, "bc1q")
    assert d.status == "ALLOWED"


def test_admin_required(tmp_path):
    db = str(tmp_path / "t.db")
    unauth = _admin(auth=False)
    engine = PolicyEngine(unauth, db=db, flags={
        "ALLOW_AUTOMATIC_WITHDRAWALS": True,
        "WITHDRAWAL_MIN_ALLOWLIST": 0,
    })
    engine.allowlist.add("bc1q", "test")
    d = engine.evaluate_withdrawal("admin", 1000, "bc1q")
    assert d.status == "REQUIRES_ADMIN"


def test_rate_limit(tmp_path):
    db = str(tmp_path / "t.db")
    engine = PolicyEngine(_admin(), db=db, flags={
        "ALLOW_AUTOMATIC_WITHDRAWALS": True,
        "WITHDRAWAL_MIN_ALLOWLIST": 0,
        "WITHDRAWAL_MAX_PER_HOUR": 2,
    })
    engine.allowlist.add("bc1q", "test")
    engine.record_withdrawal("admin", 100)
    engine.record_withdrawal("admin", 100)
    d = engine.evaluate_withdrawal("admin", 100, "bc1q")
    assert d.status == "DENIED_PRECONDITION"


def test_daily_cap(tmp_path):
    db = str(tmp_path / "t.db")
    engine = PolicyEngine(_admin(), db=db, flags={
        "ALLOW_AUTOMATIC_WITHDRAWALS": True,
        "WITHDRAWAL_MIN_ALLOWLIST": 0,
        "WITHDRAWAL_DAILY_CAP_CENTS": 5000,
    })
    engine.allowlist.add("bc1q", "test")
    engine.record_withdrawal("admin", 4000)
    d = engine.evaluate_withdrawal("admin", 2000, "bc1q")
    assert d.status == "DENIED_PRECONDITION"


def test_signing_flag_off(tmp_path):
    engine = PolicyEngine(_admin(), db=str(tmp_path / "t.db"), flags={
        "ALLOW_REMOTE_SIGNING": False,
    })
    assert engine.evaluate_signing().status == "DENIED_FLAG"


def test_signing_flag_on_requires_admin(tmp_path):
    engine = PolicyEngine(_admin(auth=False), db=str(tmp_path / "t.db"), flags={
        "ALLOW_REMOTE_SIGNING": True,
    })
    assert engine.evaluate_signing().status == "REQUIRES_ADMIN"


def test_signing_flag_on_and_auth_allows(tmp_path):
    engine = PolicyEngine(_admin(), db=str(tmp_path / "t.db"), flags={
        "ALLOW_REMOTE_SIGNING": True,
    })
    assert engine.evaluate_signing().status == "ALLOWED"
