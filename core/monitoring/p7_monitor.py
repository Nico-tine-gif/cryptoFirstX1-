from core.p2p.network_tracker import NetworkTracker


class P7Monitor:
    """
    P7 real-time monitoring coordinator.

    Network adapters are injected so monitoring remains independent
    of a specific provider.
    """

    def __init__(self, network_adapter=None, network="bitcoin",
                 db_path="data/cryptoFirstX1.db"):
        self.adapter = network_adapter
        self.network = network
        self.tracker = NetworkTracker(db_path)

    def status(self):
        state = self.tracker.get_state(self.network)

        return {
            "network": self.network,
            "monitoring": True,
            "adapter_attached": self.adapter is not None,
            "last_height": (
                state["latest_height"] if state else None
            ),
            "network_status": (
                state["status"] if state else "NOT_SCANNED"
            ),
        }

    def record_block(self, height, block_hash, previous_hash=None):
        previous = self.tracker.get_state(self.network)

        if previous and previous["latest_hash"]:
            if previous_hash and previous_hash != previous["latest_hash"]:
                self.tracker.record_event(
                    self.network,
                    "REORG_DETECTED",
                    height=height,
                    details=(
                        f"expected_previous={previous['latest_hash']};"
                        f"actual_previous={previous_hash}"
                    ),
                )

                self.tracker.update_tip(
                    self.network,
                    height,
                    block_hash,
                    previous_hash,
                    status="REORG_DETECTED",
                )
                return "REORG_DETECTED"

        self.tracker.update_tip(
            self.network,
            height,
            block_hash,
            previous_hash,
            status="HEALTHY",
        )

        self.tracker.record_event(
            self.network,
            "NEW_BLOCK",
            height=height,
        )

        return "HEALTHY"

    def record_transaction(self, txid, state="SEEN",
                           height=None, details=None):
        self.tracker.record_event(
            self.network,
            f"TX_{state}",
            height=height,
            txid=txid,
            details=details,
        )

    def record_network_error(self, error):
        self.tracker.record_event(
            self.network,
            "NETWORK_ERROR",
            details=str(error),
        )

        state = self.tracker.get_state(self.network)

        if state:
            self.tracker.update_tip(
                self.network,
                state["latest_height"],
                state["latest_hash"],
                state["previous_hash"],
                status="DEGRADED",
            )

    def events(self):
        return self.tracker.counts()
