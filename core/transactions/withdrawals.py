from ..security.policy import SecurityPolicy
from ..transactions.ledger import record

POLICY = SecurityPolicy()


def request_withdrawal(
    network: str,
    destination: str,
    amount: int,
):
    valid, reason = POLICY.validate_amount(amount)

    if not valid:
        raise ValueError(reason)

    if not network or not isinstance(network, str):
        raise ValueError("INVALID_NETWORK")

    if not destination or not isinstance(destination, str):
        raise ValueError("INVALID_DESTINATION")

    # Security boundary:
    # withdrawal requests require explicit approval.
    # Signing and broadcasting remain P6-locked.
    record(
        "WITHDRAWAL_REQUESTED",
        {
            "network": network,
            "destination": destination,
            "amount": amount,
            "status": "AWAITING_ADMIN_APPROVAL",
        },
    )

    return {
        "status": "AWAITING_ADMIN_APPROVAL",
        "network": network,
        "destination": destination,
        "amount": amount,
    }
