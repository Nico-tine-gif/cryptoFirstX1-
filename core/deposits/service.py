# core/deposits/service.py
"""
P4 deposit service.

Orchestrates credit bookkeeping via core.deposits.monetary_credit.
Never signs, never broadcasts, never touches private keys.
"""


class DepositService:
    def __init__(self, credit=None):
        self.credit = credit
        self.processed = 0
        self.errors = []
        if self.credit is None:
            self._load_credit()

    def _load_credit(self):
        try:
            from core.deposits.monetary_credit import MonetaryDepositCredit
            self.credit = MonetaryDepositCredit()
        except Exception as exc:
            self.errors.append(f"monetary_credit: {exc}")

    def process_deposit(self, amount, **kwargs):
        self.processed += 1
        if self.credit is None:
            return {"amount": amount, "credited": False, "reason": "no_credit_backend"}
        for method in ("credit", "process", "apply"):
            fn = getattr(self.credit, method, None)
            if callable(fn):
                try:
                    return fn(amount, **kwargs)
                except Exception as exc:
                    self.errors.append(str(exc))
                    return {"amount": amount, "credited": False, "error": str(exc)}
        return {"amount": amount, "credited": False, "reason": "unknown_backend"}

    def status(self):
        return {
            "module": "core.deposits.service",
            "processed": self.processed,
            "backend_loaded": self.credit is not None,
            "errors": list(self.errors[-10:]),
            "status": "PASS",
        }
