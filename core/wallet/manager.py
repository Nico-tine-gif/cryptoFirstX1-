from core.wallet.wallet import Wallet


class WalletManager:

    def __init__(self):
        self.wallets = {}

    def create(self, name, network="bitcoin"):
        if name in self.wallets:
            raise ValueError(f"WALLET_EXISTS:{name}")

        wallet = Wallet(network=network)
        self.wallets[name] = wallet
        return wallet

    def get(self, name):
        if name not in self.wallets:
            raise KeyError(f"WALLET_NOT_FOUND:{name}")
        return self.wallets[name]

    def names(self):
        return sorted(self.wallets)
