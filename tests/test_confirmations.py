import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.blockchain.confirmations import (
    calculate,
    confirmed,
)

assert calculate(100, 100) == 1
assert calculate(100, 102) == 3
assert confirmed(100, 102, 3)
assert not confirmed(100, 101, 3)

print("CONFIRMATION TEST: PASS")
