#!/usr/bin/env python3
"""
cryptoFirstX1 Android entry point.

Boots the P8 supervisor loop headlessly. Runs the P1->P9 cycle on an
interval and keeps logging to logcat on Android (or stdout elsewhere).
"""

import json
import os
import sys
import time
import traceback

# Make `core` importable when running as a packaged app
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    from core.integration.p8_system import P8System

    interval = int(os.environ.get("CRYPTOFIRSTX1_INTERVAL", "60"))
    db_path = os.environ.get("CRYPTOFIRSTX1_DB", "data/cryptoFirstX1.db")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    system = P8System(interval=interval, db_path=db_path)
    print("=== cryptoFirstX1 P8 (Android) ===")
    print(json.dumps(system.status(), indent=2, default=str))
    system.initialize_p7()

    while True:
        try:
            result = system.cycle()
            print("=== P8 CYCLE ===")
            print(json.dumps(result, indent=2, default=str))
        except KeyboardInterrupt:
            print("stopped")
            break
        except Exception:
            print("cycle error:", traceback.format_exc())
        time.sleep(interval)


if __name__ == "__main__":
    main()
