import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.withdrawals.service import WithdrawalService


def test_withdrawal_lifecycle():
    service = WithdrawalService()

    item = service.create_request(
        network="bitcoin",
        address="p5-test-address",
        value_sats=1000,
    )

    assert item["state"] == "REQUESTED"

    item = service.validate(item["withdrawal_id"])
    assert item["state"] == "APPROVAL_REQUIRED"

    item = service.approve(item["withdrawal_id"])
    assert item["state"] == "APPROVED"

    print("WITHDRAWAL LIFECYCLE: PASS")


if __name__ == "__main__":
    test_withdrawal_lifecycle()
    print("P5 WITHDRAWAL TEST: PASS")
