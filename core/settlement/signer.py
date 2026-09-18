class SignerBoundary:
    """
    P6 signing boundary.

    This implementation deliberately does not store or accept private keys.
    A production signer can be attached behind this interface later.
    """

    def __init__(self):
        self.private_keys_stored = False
        self.signing_enabled = False

    def status(self):
        return {
            "private_keys_stored": False,
            "signing_enabled": self.signing_enabled,
            "external_signer_required": True,
        }

    def sign(self, unsigned_transaction):
        if not unsigned_transaction:
            raise ValueError("unsigned transaction required")

        raise RuntimeError(
            "SIGNING_BOUNDARY_LOCKED: attach an external signer for P6 signing"
        )
