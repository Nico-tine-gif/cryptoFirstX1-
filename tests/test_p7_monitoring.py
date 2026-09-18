from core.p2p.network_tracker import NetworkTracker
from core.monitoring.p7_monitor import P7Monitor


def test_network_tracker():
    tracker = NetworkTracker()

    tracker.update_tip(
        network="p7-test",
        height=100,
        block_hash="hash100",
        previous_hash="hash99",
    )

    state = tracker.get_state("p7-test")

    assert state is not None
    assert state["latest_height"] == 100
    assert state["latest_hash"] == "hash100"
    assert state["status"] == "HEALTHY"

    print("P7 NETWORK TRACKER: PASS")


def test_block_monitoring():
    monitor = P7Monitor(network="p7-monitor-test")

    result = monitor.record_block(
        height=200,
        block_hash="hash200",
        previous_hash=None,
    )

    assert result == "HEALTHY"

    state = monitor.tracker.get_state("p7-monitor-test")

    assert state["latest_height"] == 200
    assert state["latest_hash"] == "hash200"

    print("P7 BLOCK MONITOR: PASS")


def test_transaction_monitoring():
    monitor = P7Monitor(network="p7-tx-test")

    monitor.record_transaction(
        txid="p7-test-tx",
        state="MEMPOOL",
    )

    counts = monitor.events()

    assert counts["TX_MEMPOOL"] >= 1

    print("P7 TRANSACTION MONITOR: PASS")


def test_reorg_detection():
    monitor = P7Monitor(network="p7-reorg-test")

    monitor.record_block(
        height=300,
        block_hash="original300",
    )

    result = monitor.record_block(
        height=301,
        block_hash="replacement301",
        previous_hash="wrong-parent",
    )

    assert result == "REORG_DETECTED"

    counts = monitor.events()

    assert counts["REORG_DETECTED"] >= 1

    print("P7 REORG DETECTION: PASS")


if __name__ == "__main__":
    test_network_tracker()
    test_block_monitoring()
    test_transaction_monitoring()
    test_reorg_detection()
    print("P7 MONITORING TEST: PASS")
