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
from .withdrawals.monetary_debit import MonetaryWithdrawal


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
    _funds()  # auth check
    view = {}
    try:
        from .p9.admin_account import P9AdminAccount
        view = P9AdminAccount().dashboard()
    except Exception:
        view = _funds().dashboard()
    for key in ("available_units", "reserved_units",
                "deposit_backed_units", "system_earned_units",
                "total_units"):
        print(f"{key:22s}: {view.get(key, 'n/a')}")


def cmd_deposits(args):
    for row in _funds().deposits(limit=args.limit):
        print(row)


def cmd_withdrawals(args):
    for row in _funds().withdrawals(limit=args.limit):
        print(row)


def cmd_ledger(args):
    for row in _funds().ledger_history(limit=args.limit):
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


def cmd_reserve(args):
    _admin_from_env()
    reservation_id = MonetaryWithdrawal().reserve(
        account_id=args.account,
        amount_cents=args.amount_cents,
        withdrawal_id=args.withdrawal_id,
    )
    print(f"reserved: {reservation_id}")


def cmd_settle(args):
    _admin_from_env()
    result = MonetaryWithdrawal().settle(args.reservation_id)
    print(f"settled: {result}")


def cmd_release(args):
    _admin_from_env()
    result = MonetaryWithdrawal().release(args.reservation_id)
    print(f"released: {result}")


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

    for name, fn in (("deposits", cmd_deposits),
                     ("withdrawals", cmd_withdrawals),
                     ("ledger", cmd_ledger)):
        sp = sub.add_parser(name)
        sp.add_argument("--limit", type=int, default=100)
        sp.set_defaults(func=fn)

    sub.add_parser("security").set_defaults(func=cmd_security)

    c = sub.add_parser("credit")
    c.add_argument("deposit_id")
    c.add_argument("--amount-cents", type=int, required=True)
    c.add_argument("--account", default="admin")
    c.set_defaults(func=cmd_credit)

    r = sub.add_parser("reserve")
    r.add_argument("withdrawal_id")
    r.add_argument("--amount-cents", type=int, required=True)
    r.add_argument("--account", default="admin")
    r.set_defaults(func=cmd_reserve)

    s = sub.add_parser("settle")
    s.add_argument("reservation_id")
    s.set_defaults(func=cmd_settle)

    rl = sub.add_parser("release")
    rl.add_argument("reservation_id")
    rl.set_defaults(func=cmd_release)

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
    try:
        return func(args) or 0
    except SystemExit:
        raise
    except KeyError as e:
        sys.stderr.write(f"ERROR: not found: {e}\n")
        return 4
    except ValueError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 5
    except PermissionError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 6
    except Exception as e:
        sys.stderr.write(f"ERROR: {type(e).__name__}: {e}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
