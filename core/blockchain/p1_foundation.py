from core.networks.default_registry import create_registry


class BlockchainFoundation:

    def __init__(self):
        self.networks = create_registry()

    def sync(self, network="bitcoin"):
        adapter = self.networks.get(network)
        state = adapter.sync_tip()
        return state.as_dict()

    def networks_available(self):
        return self.networks.names()
