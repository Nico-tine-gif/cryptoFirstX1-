class BroadcastBoundary:
    """
    Network broadcast boundary.

    Broadcasting is explicit and never performed implicitly by the
    withdrawal lifecycle.
    """

    def __init__(self):
        self.broadcast_enabled = False

    def status(self):
        return {
            "broadcast_enabled": self.broadcast_enabled,
            "automatic_broadcast": False,
        }

    def broadcast(self, signed_transaction):
        if not signed_transaction:
            raise ValueError("signed transaction required")

        if not self.broadcast_enabled:
            raise RuntimeError(
                "BROADCAST_BOUNDARY_LOCKED: broadcasting is disabled"
            )

        raise RuntimeError(
            "BROADCAST_PROVIDER_NOT_ATTACHED"
        )
