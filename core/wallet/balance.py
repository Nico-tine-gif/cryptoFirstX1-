from dataclasses import dataclass
from typing import Iterable

from core.wallet.utxo import UTXO


@dataclass
class WalletBalance:
    confirmed_sats: int = 0
    unconfirmed_sats: int = 0

    @property
    def total_sats(self):
        return self.confirmed_sats + self.unconfirmed_sats

    def btc(self, sats):
        return sats / 100_000_000

    def as_dict(self):
        return {
            "confirmed_sats": self.confirmed_sats,
            "unconfirmed_sats": self.unconfirmed_sats,
            "total_sats": self.total_sats,
            "confirmed_btc": self.btc(self.confirmed_sats),
            "unconfirmed_btc": self.btc(self.unconfirmed_sats),
            "total_btc": self.btc(self.total_sats),
        }


def calculate_balance(utxos: Iterable[UTXO]):
    balance = WalletBalance()

    for utxo in utxos:
        if utxo.confirmed:
            balance.confirmed_sats += utxo.value_sats
        else:
            balance.unconfirmed_sats += utxo.value_sats

    return balance
