import uuid

from .store import WithdrawalStore
from .transaction_tracker import TransactionTracker


class WithdrawalService:
    """
    P5 withdrawal lifecycle.

    P5 creates and validates withdrawal state only.
    Private-key signing and network broadcasting remain P6.
    """

    def __init__(self, db_path="data/cryptoFirstX1.db"):
        self.store = WithdrawalStore(db_path)
        self.tracker = TransactionTracker(db_path)

    def create_request(self, network, address, value_sats, metadata=None):
        if not network:
            raise ValueError("network required")

        if not address:
            raise ValueError("destination address required")

        if int(value_sats) <= 0:
            raise ValueError("withdrawal amount must be positive")

        withdrawal_id = uuid.uuid4().hex

        self.store.create(
            withdrawal_id=withdrawal_id,
            network=network,
            address=address,
            value_sats=int(value_sats),
            state="REQUESTED",
            metadata=metadata,
        )

        return self.store.get(withdrawal_id)

    def validate(self, withdrawal_id):
        item = self.store.get(withdrawal_id)

        if not item:
            raise KeyError(withdrawal_id)

        if item["value_sats"] <= 0:
            self.store.update(
                withdrawal_id,
                state="REJECTED",
                metadata={"reason": "INVALID_AMOUNT"},
            )
            return self.store.get(withdrawal_id)

        self.store.update(
            withdrawal_id,
            state="APPROVAL_REQUIRED",
        )

        return self.store.get(withdrawal_id)

    def approve(self, withdrawal_id):
        item = self.store.get(withdrawal_id)

        if not item:
            raise KeyError(withdrawal_id)

        if item["state"] != "APPROVAL_REQUIRED":
            raise ValueError(
                f"cannot approve from state {item['state']}"
            )

        self.store.update(
            withdrawal_id,
            state="APPROVED",
        )

        return self.store.get(withdrawal_id)

    def attach_txid(self, withdrawal_id, txid):
        item = self.store.get(withdrawal_id)

        if not item:
            raise KeyError(withdrawal_id)

        self.store.update(
            withdrawal_id,
            state="BROADCASTING",
            txid=txid,
        )

        self.tracker.track(
            txid=txid,
            network=item["network"],
            state="BROADCAST",
        )

        return self.store.get(withdrawal_id)
