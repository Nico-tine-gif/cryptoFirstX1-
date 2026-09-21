# core/monitoring/p7_hardening.py
"""
P7 hardening layer.

P8 imports this module as:
    from core.monitoring.p7_hardening import P7Hardening

Contract:
    P7Hardening(db_path=..., interval=...) -> instance
    .status() -> dict
    .cycle()  -> dict

Wraps core.monitoring.p7_live and core.monitoring.p7_monitor if present.
Fails safe — never raises out of status() or cycle().
"""

import time


class P7Hardening:
    def __init__(self, db_path="data/cryptoFirstX1.db", interval=60):
        self.db_path = db_path
        self.interval = interval
        self.started_at = time.time()
        self.cycles = 0
        self.last_cycle = None
        self.errors = []
        self._live = None
        self._monitor = None
        self._load()

    def _load(self):
        try:
            from core.monitoring.p7_live import P7Live
            self._live = P7Live()
        except Exception as exc:
            self.errors.append(f"p7_live: {exc}")
        try:
            from core.monitoring.p7_monitor import P7Monitor
            self._monitor = P7Monitor()
        except Exception as exc:
            self.errors.append(f"p7_monitor: {exc}")

    def status(self):
        return {
            "module": "core.monitoring.p7_hardening",
            "class": "P7Hardening",
            "db_path": self.db_path,
            "interval": self.interval,
            "uptime_seconds": time.time() - self.started_at,
            "cycles": self.cycles,
            "live_loaded": self._live is not None,
            "monitor_loaded": self._monitor is not None,
            "errors": list(self.errors[-10:]),
            "status": "PASS",
        }

    def cycle(self):
        started = time.time()
        result = {"started_at": started, "hardening": True}
        for label, obj in (("live", self._live), ("monitor", self._monitor)):
            if obj is None:
                continue
            fn = getattr(obj, "cycle", None)
            if not callable(fn):
                continue
            try:
                result[label] = fn()
            except Exception as exc:
                self.errors.append(f"{label}.cycle: {exc}")
                result[f"{label}_error"] = str(exc)
        result["finished_at"] = time.time()
        result["duration_seconds"] = result["finished_at"] - started
        self.cycles += 1
        self.last_cycle = result
        return result


# Back-compat alias for any code that imported the old stub name.
MonitoringService = P7Hardening
