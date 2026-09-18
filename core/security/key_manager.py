from .policy import POLICY


class KeyManager:
    """
    Sensitive key material is deliberately unavailable to the
    monitoring/API layer by default.
    """

    def export_private_key(self):
        if not POLICY.private_key_export:
            raise PermissionError(
                "PRIVATE_KEY_EXPORT_LOCKED"
            )
        raise NotImplementedError(
            "Protected key export is not implemented"
        )

    def remote_sign(self, transaction):
        if not POLICY.remote_signing:
            raise PermissionError(
                "REMOTE_SIGNING_LOCKED"
            )
        raise NotImplementedError(
            "Protected signing backend is not configured"
        )
