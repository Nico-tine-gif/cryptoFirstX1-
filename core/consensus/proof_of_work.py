from .base import ConsensusEngine


class ProofOfWork(ConsensusEngine):

    def __init__(
        self,
        difficulty: int = 4,
        reward: int = 0,
    ):
        self.difficulty = difficulty
        self.reward = reward

    def validate_block(self, block) -> bool:
        return bool(
            block.hash
            and block.hash.startswith(
                "0" * self.difficulty
            )
        )

    def block_reward(self, height: int) -> int:
        return self.reward
