import argparse
import hashlib
import os
import sys

from .config import (
    PROJECT_NAME, VERSION, NETWORK_MODE, REQUIRED_CONFIRMATIONS,
    ALLOW_PRIVATE_KEY_EXPORT, ALLOW_REMOTE_SIGNING,
    ALLOW_AUTOMATIC_WITHDRAWALS, ALLOW_AUTOMATIC_CASHOUT,
)
from .security.audit import record
from .storage.database import initialize
from .security.admin import AdminController
from .admin.funds import AdminFunds
from .p9.reconcile import reconcile as _reconcile
from .deposits.monetary_credit import MonetaryDepositCredit


def _admin_from_env():
    name = os.environ.get("CRYPTOFIRSTX1_ADMIN")
    cred = os.environ.get("CRYPTOFIRSTX1_ADMIN_CREDENTIAL")
    if not name or not cred:
        sys.stderr.write(
            "ERROR: set CRYPTOFIRSTX1_ADMIN and "
            "CRYPTOFIRSTX1_ADMIN_CREDENTIAL env vars\n"
        )
        raise SystemExit(2)
    os.environ["CRYPTOFIRSTX1_ADMIN_CREDENTIAL_SHA256"] = (
        hashlib.sha256(cred.encode()).hexdigest()
    )
    admin = AdminController()
    admin.authenticate(name, cred)
    if not admin.authorized():
        sys.stderr.write("ERROR: authentication failed\n")
        raise SystemExit(3)
    return admin


def _funds():
    return AdminFunds(_admin_from_env())


def cmd_status(_args):
    initialize()
    record("SYSTEM_STATUS", actor="system")
    print("=" * 60)
    print(PROJECT_NAME)
    print(f"VERSION                : {VERSION}")
    print(f"NETWORK MODE           : {NETWORK_MODE}")
    print("=" * 60)
    print(f"REQUIRED CONFIRMATIONS : {REQUIRED_CONFIRMATIONS}")
    print(f"PRIVATE KEY EXPORT     : {ALLOW_PRIVATE_KEY_EXPORT}")
    print(f"REMOTE SIGNING         : {ALLOW_REMOTE_SIGNING}")
    print(f"AUTOMATIC WITHDRAWALS  : {ALLOW_AUTOMATIC_WITHDRAWALS}")
    print(f"AUTOMATIC CASHOUT      : {ALLOW_AUTOMATIC_CASHOUT}")
    print("=" * 60)
    print("SYSTEM STATUS          : READY")


def cmd_login_help(_args):
    print("Set these env vars before admin commands:")
    print()
    print('  export CRYPTOFIRSTX1_ADMIN="your-name"')
    print('  export CRYPTOFIRSTX1_ADMIN_CREDENTIAL="your-credential"')
    print()
    print("Then run:  python -m core dashboard")


def cmd_reconcile(_args):
    r = _reconcile()
    print(f"chain deposits     : {r.chain_count}")
    print(f"ledger credits     : {r.credited_count}")
    print(f"matched            : {r.both_sides_count}")
    print(f"pending credit     : {r.pending_credit}")
    print(f"orphan credits     : {r.orphan_credits}")
    print(f"non-admin accounts : {r.non_admin_accounts}")
    print(f"balanced           : {r.balanced}")
    return 0 if r.balanced else 1


def cmd_dashboard(_args):
    d = _funds().dashboard()
    for key in ("available_units", "reserved_units",
                "deposit_backed_units", "system_earned_units",
                "total_units"):
        print(f"{key:22s}: {d.get(key)}")


def cmd_deposits(_args):
    for row in _funds().deposits():
        print(row)


def cmd_withdrawals(_args):
    for row in _funds().withdrawals():
        print(row)


def cmd_ledger(_args):
    for row in _funds().ledger_history():
        print(row)


def cmd_security(_args):
    print(_funds().security_status())


def cmd_credit(args):
    _admin_from_env()
    entry = MonetaryDepositCredit().credit_reconciled_deposit(
        account_id=args.account,
        amount_cents=args.amount_cents,
        deposit_id=args.deposit_id,
    )
    print(f"credited: {entry}")


def cmd_lock(_args):
    admin = _admin_from_env()
    admin.lock()
    record("ADMIN_LOCK", actor=os.environ.get("CRYPTOFIRSTX1_ADMIN", "?"))
    print("emergency lock ENGAGED")


def cmd_unlock(_args):
    admin = _admin_from_env()
    admin.unlock()
    record("ADMIN_UNLOCK", actor=os.environ.get("CRYPTOFIRSTX1_ADMIN", "?"))
    print("emergency lock RELEASED")


def build_parser():
    p = argparse.ArgumentParser(
        prog=PROJECT_NAME,
        description="cryptoFirstX1 operator CLI",
    )
    sub = p.add_subparsers(dest="command")

    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("login-help").set_defaults(func=cmd_login_help)
    sub.add_parser("reconcile").set_defaults(func=cmd_reconcile)
    sub.add_parser("dashboard").set_defaults(func=cmd_dashboard)
    sub.add_parser("deposits").set_defaults(func=cmd_deposits)
    sub.add_parser("withdrawals").set_defaults(func=cmd_withdrawals)
    sub.add_parser("ledger").set_defaults(func=cmd_ledger)
    sub.add_parser("security").set_defaults(func=cmd_security)

    c = sub.add_parser("credit")
    c.add_argument("deposit_id")
    c.add_argument("--amount-cents", type=int, required=True)
    c.add_argument("--account", default="admin")
    c.set_defaults(func=cmd_credit)

    sub.add_parser("lock").set_defaults(func=cmd_lock)
    sub.add_parser("unlock").set_defaults(func=cmd_unlock)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0
    return func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
