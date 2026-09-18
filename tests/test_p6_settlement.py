from core.settlement.service import SettlementService


def test_p6_status():
    service = SettlementService()

    status = service.status()

    assert status["private_keys_stored"] is False
    assert status["signing"]["external_signer_required"] is True
    assert status["broadcasting"]["automatic_broadcast"] is False

    print("P6 STATUS: PASS")


def test_prepare_signing():
    service = SettlementService()

    withdrawal = {
        "withdrawal_id": "p6-test-withdrawal",
        "network": "bitcoin",
        "address": "p6-test-address",
        "value_sats": 1000,
        "state": "APPROVED",
    }

    prepared = service.prepare_signing(withdrawal)

    assert prepared["withdrawal_id"] == "p6-test-withdrawal"
    assert prepared["network"] == "bitcoin"
    assert prepared["value_sats"] == 1000
    assert prepared["state"] == "SIGNING"

    print("P6 SIGNING PREPARATION: PASS")


def test_signing_boundary():
    service = SettlementService()

    try:
        service.sign({"tx": "unsigned"})
    except RuntimeError as exc:
        assert "SIGNING_BOUNDARY_LOCKED" in str(exc)
    else:
        raise AssertionError("signing boundary must remain locked")

    print("P6 SIGNING BOUNDARY: PASS")


def test_broadcast_boundary():
    service = SettlementService()

    try:
        service.broadcast({"tx": "signed"})
    except RuntimeError as exc:
        assert "BROADCAST_BOUNDARY_LOCKED" in str(exc)
    else:
        raise AssertionError("broadcast boundary must remain locked")

    print("P6 BROADCAST BOUNDARY: PASS")


if __name__ == "__main__":
    test_p6_status()
    test_prepare_signing()
    test_signing_boundary()
    test_broadcast_boundary()
    print("P6 SETTLEMENT TEST: PASS")
