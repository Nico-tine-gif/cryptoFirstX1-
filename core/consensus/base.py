from abc import ABC, abstractmethod


class ConsensusEngine(ABC):

    @abstractmethod
    def validate_block(self, block) -> bool:
        raise NotImplementedError

    @abstractmethod
    def block_reward(self, height: int) -> int:
        raise NotImplementedError
