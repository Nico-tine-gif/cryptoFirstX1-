from .audit import record


class AdminActions:
    """
    Authenticated administrative actions.

    This layer can approve/reject withdrawals but cannot sign,
    broadcast, export private keys, or bypass P6 boundaries.
    """

    def __init__(self, admin_controller, withdrawal_store):
        self.admin = admin_controller
        self.store = withdrawal_store

    def _require_admin(self):
        if not self.admin.authorized():
            raise PermissionError("ADMIN_AUTH_REQUIRED")

    def approve_withdrawal(self, withdrawal_id):
        self._require_admin()

        item = self.store.get(withdrawal_id)
        if not item:
            raise KeyError(withdrawal_id)

        result = self.store.update_state(
            withdrawal_id,
            "APPROVED",
        )

        record(
            "WITHDRAWAL_APPROVED",
            actor=self.admin.session.administrator,
            withdrawal_id=withdrawal_id,
        )

        return result

    def reject_withdrawal(self, withdrawal_id, reason="ADMIN_REJECTED"):
        self._require_admin()

        item = self.store.get(withdrawal_id)
        if not item:
            raise KeyError(withdrawal_id)

        result = self.store.update_state(
            withdrawal_id,
            "REJECTED",
        )

        record(
            "WITHDRAWAL_REJECTED",
            actor=self.admin.session.administrator,
            withdrawal_id=withdrawal_id,
            reason=reason,
        )

        return result
