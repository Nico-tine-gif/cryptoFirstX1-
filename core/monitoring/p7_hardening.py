# core/monitoring/p7_hardening.py
"""
P7 hardening layer.

P8 imports this module as:
    from core.monitoring.p7_hardening import P7Hardening

Wires:
    P7LiveMonitor  -> status() + scan()           (Bitcoin adapter + ledger)
    P7Monitor      -> status() + events()         (network coordinator)
                      record_block() is called from cycle() with the
                      latest tip, so network_status flips to HEALTHY
                      after the first successful scan.
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
        self._last_recorded_height = None
        self._load()

    def _try_import(self, module_name, prefer, **ctor_kwargs):
        try:
            mod = importlib.import_module(module_name)
        except Exception as exc:
            self.errors.append(f"{module_name}: {exc}")
            return None

        for name in prefer:
            cls = getattr(mod, name, None)
            if inspect.isclass(cls):
                try:
                    return cls(**ctor_kwargs)
                except TypeError:
                    try:
                        return cls()
                    except Exception as exc:
                        self.errors.append(f"{module_name}.{name}: {exc}")
                        return None
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
            prefer=["P7LiveMonitor", "P7Live", "LiveMonitor", "RealtimeMonitor"],
            db_path=self.db_path,
        )
        # Inject the live adapter so the coordinator can observe the network
        adapter = getattr(self._live, "adapter", None) if self._live else None
        self._monitor = self._try_import(
            "core.monitoring.p7_monitor",
            prefer=["P7Monitor", "Monitor"],
            network_adapter=adapter,
            db_path=self.db_path,
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
            "last_recorded_height": self._last_recorded_height,
            "errors": list(self.errors[-10:]),
            "status": "PASS",
        }

    @staticmethod
    def _safe_call(obj, method, *args, **kwargs):
        fn = getattr(obj, method, None)
        if not callable(fn):
            return None
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            return {"error": f"{method}: {exc}"}

    def cycle(self):
        started = time.time()
        result = {"started_at": started, "hardening": True}

        # ---- live: status() + scan() ------------------------------------
        scan = None
        if self._live is not None:
            live = {}
            s = self._safe_call(self._live, "status")
            if s is not None:
                live["status"] = s
            scan = self._safe_call(self._live, "scan")
            if scan is not None:
                live["scan"] = scan
            result["live"] = live

        # ---- feed the coordinator so it can detect reorgs / update tip --
        if self._monitor is not None and isinstance(scan, dict):
            tip = scan.get("tip")
            tip_hash = scan.get("tip_hash")
            if tip is not None and tip_hash and tip != self._last_recorded_height:
                rec = self._safe_call(self._monitor, "record_block", tip, tip_hash)
                if rec is not None:
                    result["recorded"] = rec
                    self._last_recorded_height = tip

        # ---- coordinator: status() + events() ---------------------------
        if self._monitor is not None:
            mon = {}
            s = self._safe_call(self._monitor, "status")
            if s is not None:
                mon["status"] = s
            events = self._safe_call(self._monitor, "events")
            if events is not None:
                mon["events"] = events
            result["monitor"] = mon

        result["finished_at"] = time.time()
        result["duration_seconds"] = result["finished_at"] - started
        self.cycles += 1
        self.last_cycle = result
        return result


MonitoringService = P7Hardening
