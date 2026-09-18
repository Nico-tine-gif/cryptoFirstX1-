from abc import ABC, abstractmethod


class BlockchainAdapter(ABC):

    @abstractmethod
    def latest_block(self):
        raise NotImplementedError

    @abstractmethod
    def get_transaction(self, txid: str):
        raise NotImplementedError

    @abstractmethod
    def get_address_activity(self, address: str):
        raise NotImplementedError
