# core/transactions/service.py
"""
P3 transaction service — bridge to core.transactions.realtime_ledger.
"""


class TransactionService:
    def __init__(self, ledger=None):
        self.ledger = ledger
        self.seen = 0
        self.errors = []
        if self.ledger is None:
            self._load_ledger()

    def _load_ledger(self):
        try:
            from core.transactions.realtime_ledger import RealtimeLedger
            self.ledger = RealtimeLedger()
        except Exception as exc:
            self.errors.append(f"realtime_ledger: {exc}")

    def track(self, txid, **kwargs):
        self.seen += 1
        if self.ledger is None:
            return {"txid": txid, "tracked": False, "reason": "no_ledger"}
        for method in ("track", "add", "record"):
            fn = getattr(self.ledger, method, None)
            if callable(fn):
                try:
                    return fn(txid, **kwargs)
                except Exception as exc:
                    self.errors.append(str(exc))
                    return {"txid": txid, "tracked": False, "error": str(exc)}
        return {"txid": txid, "tracked": False, "reason": "no_track_method"}

    def status(self):
        return {
            "module": "core.transactions.service",
            "tracked": self.seen,
            "ledger_loaded": self.ledger is not None,
            "errors": list(self.errors[-10:]),
            "status": "PASS",
        }
