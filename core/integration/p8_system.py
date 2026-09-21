#!/usr/bin/env python3

import importlib
import json
import time
import traceback
from pathlib import Path


class P8System:
    """
    Final cryptoFirstX1 integration/supervision layer.

    P8 does not replace P1-P7.
    It supervises them and preserves the existing P6 safety boundary.
    """

    PHASES = {
        "P1": "core.blockchain.p1_foundation",
        "P2": "core.wallet.wallet",
        "P3": [
            "core.transactions.ledger",
            "core.transactions.realtime_ledger",
            "core.transactions.deposits",
            "core.transactions.withdrawals",
            "core.transactions.system_tracker",
        ],
        "P4": "core.deposits.service",
        "P5": "core.withdrawals.service",
        "P6": "core.settlement.service",
        "P7": "core.monitoring.p7_hardening",
        "P9": "core.p9",
    }

    def __init__(self, interval=60, db_path="data/cryptoFirstX1.db"):
        self.interval = interval
        self.db_path = Path(db_path)
        self.running = False
        self.p7 = None
        self.last_cycle = None
        self.errors = []

        self.signing_enabled = False
        self.broadcast_enabled = False
        self.private_keys_stored = False

    def check_imports(self):
        results = {}

        for phase, module_names in self.PHASES.items():
            if isinstance(module_names, str):
                module_names = [module_names]

            failures = []

            for module_name in module_names:
                try:
                    importlib.import_module(module_name)
                except Exception as exc:
                    failures.append(
                        f"{module_name}: {exc}"
                    )

            if failures:
                results[phase] = "FAIL: " + " | ".join(failures)
            else:
                results[phase] = "PASS"

        return results

    def check_p9(self):
        """Report P9 monetary/admin primitives exposed by core.p9."""
        try:
            from core import p9 as p9_mod
        except Exception as exc:
            return {"status": "FAIL", "error": str(exc)}

        primitives = [
            "Money", "MonetaryLedger", "BalanceService",
            "P9MonetaryFoundation", "AdminFunds", "AdminController",
            "MonetaryDepositCredit", "MonetaryWithdrawal", "P9AdminAccount",
        ]
        present, missing = [], []
        for name in primitives:
            if getattr(p9_mod, name, None) is not None:
                present.append(name)
            else:
                missing.append(name)

        bridge = getattr(p9_mod, "P9EarningsBridge", None)
        return {
            "status": "PASS" if not missing else "FAIL",
            "present": present,
            "missing": missing,
            "earnings_bridge": "loaded" if bridge is not None else "unavailable",
        }

    def check_database(self):
        if not self.db_path.exists():
            return {
                "exists": False,
                "status": "FAIL",
                "path": str(self.db_path),
            }

        return {
            "exists": True,
            "status": "PASS",
            "path": str(self.db_path),
            "size_bytes": self.db_path.stat().st_size,
        }

    def initialize_p7(self):
        from core.monitoring.p7_hardening import P7Hardening

        self.p7 = P7Hardening(
            db_path=str(self.db_path),
            interval=self.interval,
        )

        return self.p7

    def safety_status(self):
        return {
            "signing": "P6 BOUNDARY",
            "broadcasting": "P6 BOUNDARY",
            "signing_enabled": False,
            "broadcast_enabled": False,
            "private_keys_stored": False,
            "withdrawals_automatic": False,
        }

    def status(self):
        p7_status = {}

        if self.p7 is not None:
            try:
                p7_status = self.p7.status()
            except Exception as exc:
                p7_status = {
                    "status_error": str(exc)
                }

        return {
            "system": "cryptoFirstX1",
            "phase": "P8",
            "integration": True,
            "database": self.check_database(),
            "p9": self.check_p9(),
            "phases": self.check_imports(),
            "p7": p7_status,
            "safety": self.safety_status(),
            "last_cycle": self.last_cycle,
            "errors": list(self.errors[-20:]),
        }

    def cycle(self):
        if self.p7 is None:
            self.initialize_p7()

        started = time.time()

        result = {
            "started_at": started,
            "p7": None,
            "safety": self.safety_status(),
        }

        try:
            result["p7"] = self.p7.cycle()
        except Exception as exc:
            error = {
                "time": time.time(),
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }

            self.errors.append(error)
            result["p7"] = {
                "status": "ERROR",
                "error": str(exc),
            }

        result["finished_at"] = time.time()
        result["duration_seconds"] = (
            result["finished_at"] - started
        )

        self.last_cycle = result

        return result

    def run_forever(self):
        self.running = True

        print("=" * 60)
        print("cryptoFirstX1 P8 FINAL SYSTEM MONITOR")
        print("=" * 60)
        print("Monitoring : P1 -> P7")
        print("Supervisor : P8")
        print("Cycle      :", self.interval, "seconds")
        print("Signing    : P6 BOUNDARY")
        print("Broadcast  : P6 BOUNDARY")
        print("Private keys: NOT STORED")
        print("=" * 60)

        while self.running:
            try:
                result = self.cycle()

                print("\n=== P8 SYSTEM CYCLE ===")
                print(json.dumps(result, indent=2, default=str))

                time.sleep(self.interval)

            except KeyboardInterrupt:
                self.running = False
                print("\nP8 MONITOR STOPPED")
                break

            except Exception:
                self.errors.append({
                    "time": time.time(),
                    "error": traceback.format_exc(),
                })
                time.sleep(self.interval)

    def stop(self):
        self.running = False


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--continuous",
        action="store_true",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
    )

    args = parser.parse_args()

    system = P8System(interval=args.interval)

    print("=== P8 CONFIGURATION ===")
    print(json.dumps(system.status(), indent=2, default=str))

    print("\n=== P8 INITIALIZATION ===")
    system.initialize_p7()

    print("P8 INITIALIZATION: PASS")

    print("\n=== P8 FIRST FULL CYCLE ===")
    result = system.cycle()
    print(json.dumps(result, indent=2, default=str))

    print("\n=== P8 FINAL STATUS ===")
    print(json.dumps(system.status(), indent=2, default=str))

    if args.continuous:
        system.run_forever()
    else:
        print("\nP8 FIRST CYCLE COMPLETE")
        print(
            "To run complete P1->P8 monitor continuously:"
        )
        print(
            "python -m core.integration.p8_system --continuous"
        )


if __name__ == "__main__":
    main()
