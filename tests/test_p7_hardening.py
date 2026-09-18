#!/usr/bin/env python3

import inspect

from core.monitoring.p7_hardening import P7Hardening


def test_p7_hardening():

    # ---------------------------------------------------------
    # USE THE ACTUAL P7HARDENING CONSTRUCTOR
    # ---------------------------------------------------------

    signature = inspect.signature(
        P7Hardening.__init__
    )

    print(
        "P7 CONSTRUCTOR:",
        signature
    )

    params = signature.parameters

    kwargs = {}

    if "interval" in params:
        kwargs["interval"] = 60

    if "db_path" in params:
        kwargs["db_path"] = "data/cryptoFirstX1.db"

    if "network_adapter" in params:
        kwargs["network_adapter"] = None

    if "network" in params:
        kwargs["network"] = "bitcoin"

    monitor = P7Hardening(**kwargs)

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    status = monitor.status()

    assert monitor is not None

    assert status["monitoring"] is True

    # ---------------------------------------------------------
    # RATE LIMIT
    # ---------------------------------------------------------

    assert (
        status["mempool_rate_limit_per_hour"]
        == 1000
    )

    assert (
        status["mempool_hourly_target"]
        == 1000
    )

    assert (
        0 <= status["mempool_hourly_count"]
        <= 1000
    )

    assert (
        0 <= status["mempool_hourly_remaining"]
        <= 1000
    )

    # ---------------------------------------------------------
    # CYCLE
    # ---------------------------------------------------------

    if "cycle_seconds" in status:
        assert status["cycle_seconds"] == 60

    # ---------------------------------------------------------
    # SAFETY BOUNDARIES
    # ---------------------------------------------------------

    assert (
        status["signing"]
        == "P6 BOUNDARY"
    )

    assert (
        status["broadcasting"]
        == "P6 BOUNDARY"
    )

    assert (
        status["private_keys_stored"]
        is False
    )

    # ---------------------------------------------------------
    # MONITORING FEATURES
    # ---------------------------------------------------------

    if "state_persistence" in status:
        assert status["state_persistence"] is True

    if "mempool_monitoring" in status:
        assert status["mempool_monitoring"] is True

    if "confirmation_monitoring" in status:
        assert (
            status["confirmation_monitoring"]
            is True
        )

    if "deposit_reconciliation" in status:
        assert (
            status["deposit_reconciliation"]
            is True
        )

    if "reorg_detection" in status:
        assert (
            status["reorg_detection"]
            is True
        )

    # ---------------------------------------------------------
    # OUTPUT
    # ---------------------------------------------------------

    print("P7 HARDENING OBJECT: PASS")

    print(
        "NETWORK:",
        status.get("network")
    )

    print(
        "HOURLY RATE LIMIT:",
        status["mempool_rate_limit_per_hour"]
    )

    print(
        "HOURLY TARGET:",
        status["mempool_hourly_target"]
    )

    print(
        "HOURLY COUNT:",
        status["mempool_hourly_count"]
    )

    print(
        "HOURLY REMAINING:",
        status["mempool_hourly_remaining"]
    )

    print(
        "CYCLE:",
        status.get("cycle_seconds")
    )

    print(
        "SIGNING:",
        status["signing"]
    )

    print(
        "BROADCASTING:",
        status["broadcasting"]
    )

    print(
        "PRIVATE KEYS:",
        status["private_keys_stored"]
    )

    print("P7 HARDENING TEST: PASS")


if __name__ == "__main__":
    test_p7_hardening()
