from dataclasses import asdict


class P2PNetworkMonitor:

    def __init__(self, registry):
        self.registry = registry

    def snapshot(self):
        return [
            asdict(peer)
            for peer in self.registry.all()
        ]
