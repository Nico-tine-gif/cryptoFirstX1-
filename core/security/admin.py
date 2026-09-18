import hashlib
import hmac
import os
from dataclasses import dataclass

from .audit import record


@dataclass
class AdminSession:
    authenticated: bool = False
    administrator: str = ""
    emergency_lock: bool = False


class AdminController:
    """
    Runtime administrator authentication.

    The credential is supplied through environment variables and is
    never written into source code or the audit log.
    """

    def __init__(self):
        self.session = AdminSession()

    def authenticate(self, administrator: str, credential: str = None) -> None:
        expected_admin = os.environ.get("CRYPTOFIRSTX1_ADMIN")
        expected_hash = os.environ.get("CRYPTOFIRSTX1_ADMIN_CREDENTIAL_SHA256")

        if not administrator:
            raise ValueError("Administrator identity required")

        if not expected_admin or not expected_hash:
            raise PermissionError("ADMIN_CREDENTIALS_NOT_CONFIGURED")

        if not hmac.compare_digest(administrator, expected_admin):
            record("ADMIN_AUTH_FAILED", actor=administrator)
            raise PermissionError("ADMIN_AUTH_FAILED")

        if credential is None:
            raise PermissionError("ADMIN_CREDENTIAL_REQUIRED")

        supplied_hash = hashlib.sha256(
            credential.encode("utf-8")
        ).hexdigest()

        if not hmac.compare_digest(supplied_hash, expected_hash):
            record("ADMIN_AUTH_FAILED", actor=administrator)
            raise PermissionError("ADMIN_AUTH_FAILED")

        self.session.authenticated = True
        self.session.administrator = administrator

        record("ADMIN_AUTHENTICATED", actor=administrator)

    def lock(self) -> None:
        self.session.emergency_lock = True
        record("ADMIN_EMERGENCY_LOCK", actor=self.session.administrator or "system")

    def unlock(self) -> None:
        if not self.session.authenticated:
            raise PermissionError("ADMIN_AUTH_REQUIRED")

        self.session.emergency_lock = False
        record("ADMIN_UNLOCKED", actor=self.session.administrator)

    def authorized(self) -> bool:
        return (
            self.session.authenticated
            and not self.session.emergency_lock
        )
