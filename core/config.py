PROJECT_NAME = "cryptoFirstX1"
VERSION = "0.1.0"

NETWORK_MODE = "READ_ONLY"

REQUIRED_CONFIRMATIONS = 3

ALLOW_PRIVATE_KEY_EXPORT = False
ALLOW_REMOTE_SIGNING = False
ALLOW_AUTOMATIC_WITHDRAWALS = False
ALLOW_AUTOMATIC_CASHOUT = False


# ------------------------------------------------------------------
# P10 — TRUST BOUNDARY PRECONDITIONS
# ------------------------------------------------------------------
# Default limits. 0 = unlimited. -1 = disabled.
# Only consulted when the matching ALLOW_* flag is True.
WITHDRAWAL_MAX_PER_HOUR     = 0
WITHDRAWAL_DAILY_CAP_CENTS  = 0
WITHDRAWAL_MIN_ALLOWLIST    = 1
