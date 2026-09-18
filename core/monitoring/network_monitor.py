import time


class NetworkMonitor:

    def __init__(self):
        self.events = []

    def record(self, event: str, data=None):
        item = {
            "timestamp": int(time.time()),
            "event": event,
            "data": data or {},
        }

        self.events.append(item)
        return item

    def recent(self, limit=100):
        return self.events[-limit:]
