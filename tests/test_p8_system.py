import json
import py_compile
from pathlib import Path

from core.integration.p8_system import P8System


def main():
    print("=" * 60)
    print("P8 FINAL INTEGRATION TEST")
    print("=" * 60)

    print("\n=== COMPILE ===")

    files = [
        "core/integration/p8_system.py",
        "core/monitoring/p7_hardening.py",
    ]

    for path in files:
        py_compile.compile(path, doraise=True)

    print("COMPILE: PASS")

    print("\n=== P8 OBJECT ===")

    p8 = P8System()

    print("P8 OBJECT: PASS")
    print("INTERVAL:", p8.interval)

    print("\n=== PHASE IMPORT AUDIT ===")

    imports = p8.check_imports()

    for phase, status in imports.items():
        print(f"{phase}: {status}")

    failed = [
        phase
        for phase, status in imports.items()
        if status != "PASS"
    ]

    if failed:
        raise RuntimeError(
            "Phase import failure: " + ", ".join(failed)
        )

    print("P1-P7 IMPORTS: PASS")

    print("\n=== DATABASE ===")

    db = p8.check_database()
    print(json.dumps(db, indent=2))

    if db["status"] != "PASS":
        raise RuntimeError("Database check failed")

    print("DATABASE: PASS")

    print("\n=== SAFETY BOUNDARY ===")

    safety = p8.safety_status()
    print(json.dumps(safety, indent=2))

    assert safety["signing_enabled"] is False
    assert safety["broadcast_enabled"] is False
    assert safety["private_keys_stored"] is False
    assert safety["withdrawals_automatic"] is False

    print("SAFETY BOUNDARY: PASS")

    print("\n=== P7 INITIALIZATION ===")

    p8.initialize_p7()

    status = p8.p7.status()

    print("NETWORK:", status["network"])
    print(
        "MEMPOOL RATE/HOUR:",
        status["mempool_rate_limit_per_hour"],
    )
    print(
        "MEMPOOL HOURLY COUNT:",
        status["mempool_hourly_count"],
    )
    print(
        "MEMPOOL HOURLY REMAINING:",
        status["mempool_hourly_remaining"],
    )
    print(
        "SIGNING:",
        status["signing"],
    )
    print(
        "BROADCASTING:",
        status["broadcasting"],
    )
    print(
        "PRIVATE KEYS:",
        status["private_keys_stored"],
    )

    assert status["mempool_rate_limit_per_hour"] == 1000
    assert status["private_keys_stored"] is False

    print("P7 STATUS: PASS")

    print("\n=== P8 FIRST CYCLE ===")

    result = p8.cycle()

    print(json.dumps(result, indent=2, default=str))

    if result.get("p7") is None:
        raise RuntimeError("P7 cycle returned no result")

    print("P8 CYCLE: PASS")

    print("\n" + "=" * 60)
    print("P8 FINAL INTEGRATION: PASS")
    print("P1 -> P8: READY")
    print("=" * 60)


if __name__ == "__main__":
    main()
