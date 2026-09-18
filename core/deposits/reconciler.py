import hashlib
import time

from core.deposits.model import Deposit


class DepositReconciler:

    def __init__(
        self,
        network,
        store,
        required_confirmations=3,
    ):
        self.network = network
        self.store = store
        self.required_confirmations = max(
            1,
            int(required_confirmations),
        )

    def deposit_id(self, txid, vout, address):
        raw = (
            f"{self.network.name}:"
            f"{txid}:"
            f"{vout}:"
            f"{address}"
        )

        return hashlib.sha256(raw.encode()).hexdigest()

    def process_transaction(
        self,
        tx,
        watched_address,
        tip_height=None,
    ):
        txid = tx.get("txid")

        if not txid:
            return []

        status = tx.get("status") or {}

        confirmed = bool(status.get("confirmed"))
        block_height = status.get("block_height")
        block_hash = status.get("block_hash")

        if tip_height is None and confirmed:
            tip_height = self.network.adapter.latest_height()

        confirmations = 0

        if confirmed and block_height is not None:
            confirmations = max(
                0,
                int(tip_height) - int(block_height) + 1,
            )

        outputs = tx.get("vout", [])

        deposits = []

        for vout_index, output in enumerate(outputs):
            value = output.get("value")

            if value is None:
                continue

            value = int(value)

            scriptpubkey = output.get("scriptpubkey_address")

            if scriptpubkey != watched_address:
                continue

            deposit = Deposit(
                deposit_id=self.deposit_id(
                    txid,
                    vout_index,
                    watched_address,
                ),
                txid=txid,
                vout=vout_index,
                address=watched_address,
                value_sats=value,
                network=self.network.name,
                state="CONFIRMING" if confirmed else "MEMPOOL",
                block_height=block_height,
                block_hash=block_hash,
                confirmations=confirmations,
                required_confirmations=self.required_confirmations,
                metadata={
                    "source": "blockchain",
                    "reconciled": False,
                },
            )

            deposit.update_confirmations(confirmations)

            saved = self.store.save(deposit)

            if deposit.confirmed:
                self.store.event(
                    deposit.deposit_id,
                    "CONFIRMATION_THRESHOLD_REACHED",
                    {
                        "confirmations": deposit.confirmations,
                        "required": deposit.required_confirmations,
                    },
                )

            deposits.append(saved)

        return deposits

    def scan_address(self, address):
        transactions = self.network.adapter.address_transactions(
            address
        )

        tip = self.network.adapter.latest_height()

        found = 0

        for tx in transactions:
            deposits = self.process_transaction(
                tx,
                watched_address=address,
                tip_height=tip,
            )

            found += len(deposits)

        self.store.mark_scanned(address)

        return found

    def scan_all(self):
        results = {}

        for item in self.store.watched_addresses():
            address = item["address"]

            try:
                results[address] = {
                    "status": "OK",
                    "deposits": self.scan_address(address),
                }
            except Exception as exc:
                results[address] = {
                    "status": "ERROR",
                    "error": str(exc),
                }

        return results

    def reconcile(self):
        mismatches = []

        for deposit in self.store.all():
            try:
                tx = self.network.adapter.transaction(
                    deposit["txid"]
                )
            except Exception as exc:
                mismatches.append({
                    "deposit_id": deposit["deposit_id"],
                    "type": "SOURCE_UNAVAILABLE",
                    "error": str(exc),
                })
                continue

            status = tx.get("status") or {}

            confirmed = bool(status.get("confirmed"))
            block_height = status.get("block_height")

            tip = self.network.adapter.latest_height()

            confirmations = 0

            if confirmed and block_height is not None:
                confirmations = max(
                    0,
                    tip - int(block_height) + 1,
                )

            expected_state = (
                "CONFIRMED"
                if confirmations >= self.required_confirmations
                else "CONFIRMING"
                if confirmations > 0
                else "MEMPOOL"
            )

            if (
                deposit["confirmations"] != confirmations
                or deposit["state"] != expected_state
            ):
                mismatches.append({
                    "deposit_id": deposit["deposit_id"],
                    "type": "STATE_MISMATCH",
                    "stored_state": deposit["state"],
                    "expected_state": expected_state,
                    "stored_confirmations": deposit["confirmations"],
                    "expected_confirmations": confirmations,
                })

                current = Deposit(
                    deposit_id=deposit["deposit_id"],
                    txid=deposit["txid"],
                    vout=deposit["vout"],
                    address=deposit["address"],
                    value_sats=deposit["value_sats"],
                    network=deposit["network"],
                    state=expected_state,
                    block_height=block_height,
                    block_hash=status.get("block_hash"),
                    confirmations=confirmations,
                    required_confirmations=deposit[
                        "required_confirmations"
                    ],
                    first_seen=deposit["first_seen"],
                    metadata={
                        "source": "reconciliation",
                        "reconciled": True,
                    },
                )

                self.store.save(current)

                self.store.event(
                    current.deposit_id,
                    "RECONCILED",
                    {
                        "confirmations": confirmations,
                        "state": expected_state,
                    },
                )

        return mismatches
