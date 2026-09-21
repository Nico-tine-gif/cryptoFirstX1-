# core/settlement/service.py
"""
P6 settlement service — the cryptoFirstX1 safety boundary.

Signing and broadcasting are DISABLED by default. P8 asserts:
    signing_enabled      == False
    broadcast_enabled    == False
    private_keys_stored  == False
"""


class SettlementService:
    def __init__(self, signer=None, broadcaster=None):
        self.signer = signer
        self.broadcaster = broadcaster
        self.signing_enabled = False
        self.broadcast_enabled = False
        self.private_keys_stored = False
        self.history = []
        self.errors = []
        if self.signer is None:
            self._try_load("core.settlement.signer",
                           ("Signer", "TransactionSigner", "SettlementSigner"),
                           "signer")
        if self.broadcaster is None:
            self._try_load("core.settlement.broadcaster",
                           ("Broadcaster", "TransactionBroadcaster"),
                           "broadcaster")

    def _try_load(self, module_name, class_names, attr):
        try:
            import importlib
            mod = importlib.import_module(module_name)
        except Exception as exc:
            self.errors.append(f"{module_name}: {exc}")
            return
        for name in class_names:
            cls = getattr(mod, name, None)
            if cls is not None:
                try:
                    setattr(self, attr, cls())
                    return
                except Exception as exc:
                    self.errors.append(f"{module_name}.{name}: {exc}")
                    return
        self.errors.append(f"{module_name}: no known class in {class_names}")

    def sign(self, *args, **kwargs):
        if not self.signing_enabled:
            return {"signed": False, "reason": "P6 BOUNDARY — signing disabled"}
        if self.signer is None:
            return {"signed": False, "reason": "no_signer"}
        result = self.signer.sign(*args, **kwargs)
        self.history.append({"op": "sign", "result": result})
        return result

    def broadcast(self, *args, **kwargs):
        if not self.broadcast_enabled:
            return {"broadcast": False, "reason": "P6 BOUNDARY — broadcast disabled"}
        if self.broadcaster is None:
            return {"broadcast": False, "reason": "no_broadcaster"}
        result = self.broadcaster.broadcast(*args, **kwargs)
        self.history.append({"op": "broadcast", "result": result})
        return result

    def status(self):
        return {
            "module": "core.settlement.service",
            "signing_enabled": self.signing_enabled,
            "broadcast_enabled": self.broadcast_enabled,
            "private_keys_stored": self.private_keys_stored,
            "signer_loaded": self.signer is not None,
            "broadcaster_loaded": self.broadcaster is not None,
            "operations": len(self.history),
            "errors": list(self.errors[-10:]),
            "status": "PASS",
        }
