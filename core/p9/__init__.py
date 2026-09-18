"""
core.p9 — P9 admin/monetary surface.

The old monolith core/p9/p9.py has been retired. All primitives now
live in core/finance, core/admin, core/security, core/deposits,
core/withdrawals. Re-export them here for convenience.
"""

# Monetary primitives
from core.finance.money      import Money
from core.finance.ledger     import MonetaryLedger
from core.finance.balances   import BalanceService
from core.finance.p9_monetary import P9MonetaryFoundation

# Admin + security
from core.admin.funds        import AdminFunds
from core.security.admin     import AdminController

# Deposit / withdrawal bridges
from core.deposits.monetary_credit  import MonetaryDepositCredit
from core.withdrawals.monetary_debit import MonetaryWithdrawal

# P9-specific
from .admin_account   import P9AdminAccount
try:
    from .earnings_bridge import P9EarningsBridge
except Exception:
    P9EarningsBridge = None

__all__ = [
    "Money",
    "MonetaryLedger",
    "BalanceService",
    "P9MonetaryFoundation",
    "AdminFunds",
    "AdminController",
    "MonetaryDepositCredit",
    "MonetaryWithdrawal",
    "P9AdminAccount",
    "P9EarningsBridge",
]
