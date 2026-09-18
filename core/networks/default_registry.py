from core.networks.registry import NetworkRegistry
from core.networks.bitcoin_network import BitcoinNetwork


def create_registry():
    registry = NetworkRegistry()
    registry.register("bitcoin", BitcoinNetwork())
    return registry
