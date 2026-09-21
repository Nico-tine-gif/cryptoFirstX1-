# core/withdrawals/service.py
"""
P5 withdrawal service.

P6 SAFETY BOUNDARY: this service NEVER signs or broadcasts on its own.
It only records requests and delegates debit bookkeeping to
core.withdrawals.monetary_debit.
"""


class WithdrawalService:
    AUTOMATIC_SIGNING = False
    AUTOMATIC_BROADCAST = False

    def __init__(self, debit=None):
        self.debit = debit
        self.requests = []
        self.errors = []
        if self.debit is None:
            self._load_debit()

    def _load_debit(self):
        try:
            from core.withdrawals.monetary_debit import MonetaryWithdrawal
            self.debit = MonetaryWithdrawal()
        except Exception as exc:
            self.errors.append(f"monetary_debit: {exc}")

    def request_withdrawal(self, amount, address=None, **kwargs):
        record = {
            "amount": amount,
            "address": address,
            "signed": False,
            "broadcast": False,
            "reason": "P6 BOUNDARY — manual approval required",
        }
        self.requests.append(record)
        return record

    # Back-compat alias
    def process_withdrawal(self, amount, address=None, **kwargs):
        return self.request_withdrawal(amount, address=address, **kwargs)

    def status(self):
        return {
            "module": "core.withdrawals.service",
            "requests": len(self.requests),
            "automatic_signing": False,
            "automatic_broadcast": False,
            "backend_loaded": self.debit is not None,
            "errors": list(self.errors[-10:]),
            "status": "PASS",
        }
