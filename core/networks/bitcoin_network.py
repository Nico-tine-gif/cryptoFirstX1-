from core.networks.bitcoin import BitcoinAdapter
from core.blockchain.chain import ChainState


class BitcoinNetwork:

    name = "bitcoin"

    def __init__(self, timeout=5):
        self.adapter = BitcoinAdapter(timeout=timeout)
        self.state = ChainState(network=self.name)

    def sync_tip(self):
        height = self.adapter.latest_height()
        block_hash = self.adapter.latest_hash()

        self.state.update(
            height=height,
            tip_hash=block_hash,
            provider=self.adapter.provider(),
        )

        return self.state

    def status(self):
        return self.state.as_dict()
