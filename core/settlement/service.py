from .signer import SignerBoundary
from .broadcaster import BroadcastBoundary


class SettlementService:
    """
    P6 settlement coordinator.

    Flow:
        APPROVED
          -> SIGNING
          -> BROADCASTING
          -> CONFIRMING
          -> COMPLETED

    Actual signing and network broadcasting remain explicit boundaries.
    """

    def __init__(self, withdrawal_store=None, transaction_tracker=None):
        self.signer = SignerBoundary()
        self.broadcaster = BroadcastBoundary()
        self.withdrawal_store = withdrawal_store
        self.transaction_tracker = transaction_tracker

    def status(self):
        return {
            "private_keys_stored": False,
            "signing": self.signer.status(),
            "broadcasting": self.broadcaster.status(),
            "settlement": "BOUNDARY_READY",
        }

    def prepare_signing(self, withdrawal):
        if not withdrawal:
            raise ValueError("withdrawal required")

        if withdrawal.get("state") != "APPROVED":
            raise ValueError(
                f"withdrawal must be APPROVED, got {withdrawal.get('state')}"
            )

        return {
            "withdrawal_id": withdrawal["withdrawal_id"],
            "network": withdrawal["network"],
            "address": withdrawal["address"],
            "value_sats": withdrawal["value_sats"],
            "state": "SIGNING",
        }

    def sign(self, unsigned_transaction):
        return self.signer.sign(unsigned_transaction)

    def broadcast(self, signed_transaction):
        return self.broadcaster.broadcast(signed_transaction)
