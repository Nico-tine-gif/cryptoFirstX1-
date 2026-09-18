from core.monitoring.p7_live import P7LiveMonitor


def test_live_adapter_connection():
    monitor = P7LiveMonitor()

    status = monitor.status()

    assert status["adapter_attached"] is True
    assert status["network"] == "bitcoin"
    assert status["monitoring"] is True
    assert status["block_monitor"] is True
    assert status["transaction_monitor"] is True
    assert status["confirmation_monitor"] is True
    assert status["reorg_detection"] is True
    assert status["signing"] == "P6 BOUNDARY"
    assert status["broadcasting"] == "P6 BOUNDARY"
    assert status["private_keys_stored"] is False

    print("P7 LIVE ADAPTER CONNECTION: PASS")


if __name__ == "__main__":
    test_live_adapter_connection()
    print("P7 LIVE INTEGRATION TEST: PASS")
