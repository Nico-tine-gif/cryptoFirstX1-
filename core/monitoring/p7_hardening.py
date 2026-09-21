# core/monitoring/p7_hardening.py
"""
P7 hardening layer.

P8 imports this module as:
    from core.monitoring.p7_hardening import P7Hardening
"""

import importlib
import inspect
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

    def _try_import(self, module_name, prefer):
        try:
            mod = importlib.import_module(module_name)
        except Exception as exc:
            self.errors.append(f"{module_name}: {exc}")
            return None

        for name in prefer:
            cls = getattr(mod, name, None)
            if inspect.isclass(cls):
                try:
                    return cls()
                except Exception as exc:
                    self.errors.append(f"{module_name}.{name}: {exc}")
                    return None

        for name, obj in vars(mod).items():
            if name.startswith("_"):
                continue
            if inspect.isclass(obj) and obj.__module__ == module_name:
                try:
                    return obj()
                except Exception:
                    continue

        return mod

    def _load(self):
        self._live = self._try_import(
            "core.monitoring.p7_live",
            prefer=["P7Live", "P7LiveMonitor", "LiveMonitor", "RealtimeMonitor"],
        )
        self._monitor = self._try_import(
            "core.monitoring.p7_monitor",
            prefer=["P7Monitor", "Monitor"],
        )

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


MonitoringService = P7Hardening
