#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"
for t in tests/test_p9_monetary.py tests/test_p9_admin_funds.py; do
    echo "=========================================="
    echo "  $t"
    echo "=========================================="
    python "$t"
    echo
done
echo "ALL P9 SMOKE TESTS PASSED"
