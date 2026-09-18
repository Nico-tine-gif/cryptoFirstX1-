from core.wallet.address import WalletAddress
from core.wallet.balance import calculate_balance


class Wallet:

    def __init__(self, network="bitcoin"):
        self.network = network
        self.addresses = {}
        self.utxos = {}

    def add_address(self, address, label=""):
        item = WalletAddress(
            address=address,
            network=self.network,
            label=label,
        )
        self.addresses[address] = item
        return item

    def add_utxo(self, utxo):
        self.utxos[utxo.outpoint] = utxo

    def remove_utxo(self, txid, vout):
        self.utxos.pop(f"{txid}:{vout}", None)

    def balance(self):
        return calculate_balance(self.utxos.values())

    def list_addresses(self):
        return list(self.addresses.values())

    def list_utxos(self):
        return list(self.utxos.values())

    def summary(self):
        return {
            "network": self.network,
            "addresses": len(self.addresses),
            "utxos": len(self.utxos),
            "balance": self.balance().as_dict(),
        }
