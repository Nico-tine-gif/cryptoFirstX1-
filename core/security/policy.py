class SecurityPolicy:
    """
    Central security policy.

    Monetary validation is performed here.
    Sensitive operations remain explicitly locked unless a future
    deployment deliberately enables them.
    """

    def __init__(self):
        self.manual_withdrawal_approval = True
        self.private_key_export = False
        self.remote_signing = False
        self.signing_enabled = False
        self.broadcast_enabled = False

    def validate_amount(self, amount_sats: int):
        if not isinstance(amount_sats, int):
            return False, "INVALID_AMOUNT"
        if amount_sats <= 0:
            return False, "INVALID_AMOUNT"
        return True, "OK"

    def validate_fee(self, fee_sats: int):
        if not isinstance(fee_sats, int):
            return False, "INVALID_FEE"
        if fee_sats < 0:
            return False, "INVALID_FEE"
        return True, "OK"

    def requires_approval(self, amount_sats: int):
        return True


POLICY = SecurityPolicy()
