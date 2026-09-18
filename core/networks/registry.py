class NetworkRegistry:

    def __init__(self):
        self._networks = {}

    def register(self, name, adapter):
        self._networks[name.lower()] = adapter

    def get(self, name):
        key = name.lower()
        if key not in self._networks:
            raise KeyError(f"NETWORK_NOT_REGISTERED:{name}")
        return self._networks[key]

    def names(self):
        return sorted(self._networks.keys())
