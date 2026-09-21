"""Verify every module P8 supervises can be imported and exposes
the class P8 expects. Guards against silent stub regressions."""

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUIRED = {
    "core.blockchain.p1_foundation": "BlockchainFoundation",
    "core.deposits.service":         "DepositService",
    "core.withdrawals.service":      "WithdrawalService",
    "core.settlement.service":       "SettlementService",
    "core.transactions.service":     "TransactionService",
    "core.monitoring.p7_hardening":  "P7Hardening",
}

for module_name, class_name in REQUIRED.items():
    mod = importlib.import_module(module_name)
    assert hasattr(mod, class_name), f"{module_name} missing {class_name}"

# P6 safety boundary must hold
from core.settlement.service import SettlementService
s = SettlementService()
assert s.signing_enabled is False
assert s.broadcast_enabled is False
assert s.private_keys_stored is False

# P7 contract P8 depends on
from core.monitoring.p7_hardening import P7Hardening
p = P7Hardening()
assert isinstance(p.status(), dict)
assert isinstance(p.cycle(), dict)

print("P8 IMPORTS TEST: PASS")
