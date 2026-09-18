import argparse

from .config import (
    PROJECT_NAME,
    VERSION,
    NETWORK_MODE,
    REQUIRED_CONFIRMATIONS,
    ALLOW_PRIVATE_KEY_EXPORT,
    ALLOW_REMOTE_SIGNING,
    ALLOW_AUTOMATIC_WITHDRAWALS,
    ALLOW_AUTOMATIC_CASHOUT,
)
from .security.audit import record
from .storage.database import initialize


def status():
    initialize()

    record("SYSTEM_STATUS", actor="system")

    print("=" * 60)
    print(f"{PROJECT_NAME}")
    print(f"VERSION                    : {VERSION}")
    print(f"NETWORK MODE               : {NETWORK_MODE}")
    print("=" * 60)
    print(f"REQUIRED CONFIRMATIONS     : {REQUIRED_CONFIRMATIONS}")
    print(f"PRIVATE KEY EXPORT         : {ALLOW_PRIVATE_KEY_EXPORT}")
    print(f"REMOTE SIGNING             : {ALLOW_REMOTE_SIGNING}")
    print(f"AUTOMATIC WITHDRAWALS      : {ALLOW_AUTOMATIC_WITHDRAWALS}")
    print(f"AUTOMATIC CASHOUT           : {ALLOW_AUTOMATIC_CASHOUT}")
    print("=" * 60)
    print("ADMIN SECURITY             : ENABLED")
    print("WITHDRAWAL EXECUTION       : LOCKED")
    print("PRIVATE KEY ACCESS         : LOCKED")
    print("REMOTE SIGNING             : LOCKED")
    print("SYSTEM STATUS              : READY")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        prog=PROJECT_NAME
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=["status"],
    )

    args = parser.parse_args()

    if args.command == "status":
        status()


if __name__ == "__main__":
    main()
