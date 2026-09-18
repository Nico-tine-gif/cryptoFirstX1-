import argparse
import json
import sys

from core.monitoring.blockchain_monitor import (
    BlockchainMonitor,
)
from core.transactions.deposits import (
    DepositTracker,
)
from core.networks.bitcoin import BitcoinAdapter
from core.storage.database import initialize


def output(data):
    print(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        )
    )


def main():
    parser = argparse.ArgumentParser(
        prog="cryptoFirstX1-blockchain"
    )

    sub = parser.add_subparsers(
        dest="command"
    )

    sub.add_parser("status")
    sub.add_parser("tip")
    sub.add_parser("mempool")
    sub.add_parser("fees")
    sub.add_parser("scan-tip")
    sub.add_parser("confirmations")

    tx = sub.add_parser("tx")
    tx.add_argument("txid")

    addr = sub.add_parser("address")
    addr.add_argument("address")

    watch = sub.add_parser("watch")
    watch.add_argument("address")
    watch.add_argument(
        "--label",
        default="",
    )

    args = parser.parse_args()

    initialize()

    monitor = BlockchainMonitor()

    if args.command in ("status", "tip"):
        output(
            monitor.status()
        )

    elif args.command == "scan-tip":
        output(
            monitor.scan_tip()
        )

    elif args.command == "tx":
        result = monitor.track_transaction(
            args.txid
        )

        if result is None:
            print("TRANSACTION NOT FOUND")
            sys.exit(1)

        output(result)

    elif args.command == "mempool":
        output(
            monitor.mempool.snapshot()
        )

    elif args.command == "fees":
        output(
            monitor.mempool.fees()
        )

    elif args.command == "confirmations":
        output(
            monitor.refresh_confirmations()
        )

    elif args.command == "watch":
        tracker = DepositTracker(
            BitcoinAdapter()
        )

        output(
            tracker.watch(
                args.address,
                args.label,
            )
        )

        print()
        print("Use:")
        print(
            f"python blockchain_monitor.py address {args.address}"
        )

    elif args.command == "address":
        tracker = DepositTracker(
            BitcoinAdapter()
        )

        output(
            tracker.scan_address(
                args.address
            )
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
