import json
import sqlite3
import time
from pathlib import Path

from core.networks.bitcoin import BitcoinAdapter
from core.transactions.realtime_ledger import RealtimeTransactionLedger
from core.monitoring.blockchain_monitor import BlockchainMonitor
from core.monitoring.realtime_transactions import RealtimeTransactionMonitor
from core.monitoring.p7_monitor import P7Monitor
from core.deposits.service import DepositService


class P7Hardening:
    """
    Continuous P7 monitor.

    Mempool target:
        1,000 transactions/hour maximum

    The monitor uses a persistent rotating cursor so it does not
    repeatedly process the same initial mempool slice.

    Signing and broadcasting remain locked at P6.
    """

    HOURLY_MEMPOOL_TARGET = 1000
    CYCLE_SECONDS = 60

    def __init__(
        self,
        db_path="data/cryptoFirstX1.db",
        confirmations=3,
        interval=60,
    ):
        self.db_path = str(db_path)
        self.interval = interval

        # 1000/hour ~= 16 transactions/minute.
        # Time-based rate limit.
        # Target is 1,000 transactions per rolling hourly window.
        self.per_cycle = None

        Path(self.db_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.adapter = BitcoinAdapter()

        self.ledger = RealtimeTransactionLedger(
            db_path=self.db_path
        )

        self.blockchain = BlockchainMonitor(
            confirmations=confirmations
        )

        self.realtime = RealtimeTransactionMonitor(
            network=self.adapter,
            ledger=self.ledger,
            interval=interval,
        )

        self.p7 = P7Monitor(
            network_adapter=self.adapter,
            network="bitcoin",
            db_path=self.db_path,
        )

        self._ensure_state_table()

    # =========================================================
    # DATABASE
    # =========================================================

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_state_table(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS p7_scan_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    height INTEGER,
                    block_hash TEXT,
                    mempool_cursor INTEGER NOT NULL DEFAULT 0,
                    hourly_started REAL,
                    hourly_count INTEGER NOT NULL DEFAULT 0,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    def _state(self):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    height,
                    block_hash,
                    mempool_cursor,
                    hourly_started,
                    hourly_count,
                    updated_at
                FROM p7_scan_state
                WHERE id = 1
                """
            ).fetchone()

        if not row:
            return {
                "height": None,
                "block_hash": None,
                "mempool_cursor": 0,
                "hourly_started": None,
                "hourly_count": 0,
                "updated_at": None,
            }

        return {
            "height": row[0],
            "block_hash": row[1],
            "mempool_cursor": row[2] or 0,
            "hourly_started": row[3],
            "hourly_count": row[4] or 0,
            "updated_at": row[5],
        }

    def _save_state(
        self,
        height,
        block_hash,
        mempool_cursor,
        hourly_started,
        hourly_count,
    ):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO p7_scan_state (
                    id,
                    height,
                    block_hash,
                    mempool_cursor,
                    hourly_started,
                    hourly_count,
                    updated_at
                )
                VALUES (1, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(id) DO UPDATE SET
                    height=excluded.height,
                    block_hash=excluded.block_hash,
                    mempool_cursor=excluded.mempool_cursor,
                    hourly_started=excluded.hourly_started,
                    hourly_count=excluded.hourly_count,
                    updated_at=excluded.updated_at
                """,
                (
                    height,
                    block_hash,
                    mempool_cursor,
                    hourly_started,
                    hourly_count,
                    time.time(),
                ),
            )
            conn.commit()

    # =========================================================
    # HOURLY RATE LIMIT
    # =========================================================

    def _hour_window(self, state):
        now = time.time()

        started = state["hourly_started"]
        count = state["hourly_count"]

        if started is None or now - started >= 3600:
            return now, 0

        return started, count

    # =========================================================
    # BLOCK MONITOR
    # =========================================================

    def scan_tip(self):
        height = self.adapter.latest_height()
        block_hash = self.adapter.latest_hash()

        state = self._state()

        event = "TIP_INITIALIZED"

        if state["height"] is not None:

            if height > state["height"]:
                event = "NEW_BLOCK"

            elif height == state["height"]:

                if (
                    state["block_hash"]
                    and block_hash != state["block_hash"]
                ):
                    event = "REORG_DETECTED"

            elif height < state["height"]:
                event = "TIP_ROLLBACK"

        self.p7.record_block(
            height,
            block_hash,
            state["block_hash"],
        )

        if event == "REORG_DETECTED":
            self.p7.record_network_error(
                "REORG_DETECTED: "
                f"height={height} "
                f"old_hash={state['block_hash']} "
                f"new_hash={block_hash}"
            )

        elif event == "TIP_ROLLBACK":
            self.p7.record_network_error(
                "TIP_ROLLBACK: "
                f"height={height} "
                f"previous={state['height']}"
            )

        return {
            "event": event,
            "height": height,
            "block_hash": block_hash,
            "previous_height": state["height"],
            "previous_hash": state["block_hash"],
        }

    # =========================================================
    # MEMPOOL
    # =========================================================

    def scan_mempool(self):
        state = self._state()

        txids = self.adapter.mempool_txids()

        total = len(txids)

        if not total:
            return {
                "processed": 0,
                "network_mempool_count": 0,
                "hourly_count": state["hourly_count"],
                "hourly_target": self.HOURLY_MEMPOOL_TARGET,
            }

        hourly_started, hourly_count = self._hour_window(state)

        remaining_hourly = max(
            0,
            self.HOURLY_MEMPOOL_TARGET - hourly_count,
        )

        if remaining_hourly == 0:
            return {
                "processed": 0,
                "network_mempool_count": total,
                "hourly_count": hourly_count,
                "hourly_target": self.HOURLY_MEMPOOL_TARGET,
                "hourly_limit_reached": True,
            }

        # Time-based hourly allowance.
        # 1000 transactions/hour = 16/17 transactions per minute,
        # with the allowance catching up when a cycle is delayed.
        import time as _time

        elapsed = max(
            0.0,
            _time.time() - hourly_started,
        )

        expected_allowed = int(
            min(
                self.HOURLY_MEMPOOL_TARGET,
                (elapsed / 3600.0)
                * self.HOURLY_MEMPOOL_TARGET,
            )
        )

        allowance = max(
            0,
            expected_allowed - hourly_count,
        )

        # Always allow the first transaction of a fresh window,
        # while never exceeding the 1000/hour hard limit.
        if hourly_count == 0 and allowance == 0:
            allowance = 1

        amount = min(
            allowance,
            remaining_hourly,
            total,
        )

        cursor = state["mempool_cursor"] % total

        selected = []

        for i in range(amount):
            selected.append(
                txids[(cursor + i) % total]
            )

        processed = 0

        for txid in selected:

            self.ledger.record(
                txid,
                network="bitcoin",
                status="MEMPOOL",
            )

            self.p7.record_transaction(
                txid,
                state="MEMPOOL",
            )

            processed += 1

        new_cursor = (
            cursor + processed
        ) % total

        new_hourly_count = (
            hourly_count + processed
        )

        self._save_state(
            state["height"],
            state["block_hash"],
            new_cursor,
            hourly_started,
            new_hourly_count,
        )

        return {
            "processed": processed,
            "network_mempool_count": total,
            "cursor": new_cursor,
            "hourly_count": new_hourly_count,
            "hourly_target": self.HOURLY_MEMPOOL_TARGET,
            "hourly_remaining": (
                self.HOURLY_MEMPOOL_TARGET
                - new_hourly_count
            ),
            "hourly_limit_reached": (
                new_hourly_count
                >= self.HOURLY_MEMPOOL_TARGET
            ),
        }

    # =========================================================
    # CONFIRMATIONS
    # =========================================================

    def refresh_confirmations(self):
        try:
            return self.blockchain.refresh_confirmations()
        except Exception as exc:
            self.p7.record_network_error(
                f"CONFIRMATION_REFRESH_ERROR: {exc}"
            )

            return {
                "error": str(exc),
            }

    # =========================================================
    # DEPOSITS
    # =========================================================

    def reconcile_deposits(self):
        try:
            service = DepositService(
                network=self.adapter,
                required_confirmations=3,
            )

            result = service.reconcile()

            return {
                "status": "OK",
                "result": result,
            }

        except Exception as exc:
            self.p7.record_network_error(
                f"DEPOSIT_RECONCILIATION_ERROR: {exc}"
            )

            return {
                "status": "ERROR",
                "error": str(exc),
            }

    # =========================================================
    # ONE CYCLE
    # =========================================================

    def cycle(self):

        started = time.time()

        result = {
            "started_at": started,
        }

        try:
            result["tip"] = self.scan_tip()
        except Exception as exc:
            result["tip"] = {
                "error": str(exc),
            }

            self.p7.record_network_error(
                f"TIP_SCAN_ERROR: {exc}"
            )

        try:
            result["mempool"] = self.scan_mempool()
        except Exception as exc:
            result["mempool"] = {
                "error": str(exc),
            }

            self.p7.record_network_error(
                f"MEMPOOL_SCAN_ERROR: {exc}"
            )

        result["confirmations"] = (
            self.refresh_confirmations()
        )

        result["deposits"] = (
            self.reconcile_deposits()
        )

        result["finished_at"] = time.time()

        result["duration_seconds"] = (
            result["finished_at"] - started
        )

        return result

    # =========================================================
    # STATUS
    # =========================================================

    def status(self):

        state = self._state()

        try:
            network_height = (
                self.adapter.latest_height()
            )
        except Exception:
            network_height = None

        return {
            "network": "bitcoin",
            "monitoring": True,
            "last_height": state["height"],
            "last_hash": state["block_hash"],
            "network_height": network_height,
            "mempool_hourly_target":
                self.HOURLY_MEMPOOL_TARGET,
            "mempool_rate_limit_per_hour":
                self.HOURLY_MEMPOOL_TARGET,
            "mempool_hourly_count":
                state["hourly_count"],
            "mempool_hourly_remaining":
                max(
                    0,
                    self.HOURLY_MEMPOOL_TARGET
                    - state["hourly_count"]
                ),
            "mempool_rate_limit_per_hour": self.HOURLY_MEMPOOL_TARGET,
            "cycle_seconds": self.interval,
            "hourly_count": state["hourly_count"],
            "state_persistence": True,
            "mempool_monitoring": True,
            "confirmation_monitoring": True,
            "deposit_reconciliation": True,
            "reorg_detection": True,
            "signing": "P6 BOUNDARY",
            "broadcasting": "P6 BOUNDARY",
            "private_keys_stored": False,
        }

    # =========================================================
    # CONTINUOUS RUNNER
    # =========================================================

    def run_forever(self):

        print("============================================================")
        print(" P7 CONTINUOUS MONITOR")
        print("============================================================")
        print(
            "MEMPOOL TARGET / HOUR :",
            self.HOURLY_MEMPOOL_TARGET,
        )
        print(
            "MEMPOOL / CYCLE       :",
            self.per_cycle,
        )
        print(
            "CYCLE INTERVAL        :",
            self.interval,
            "seconds",
        )
        print("SIGNING               : P6 BOUNDARY")
        print("BROADCASTING          : P6 BOUNDARY")
        print("============================================================")

        while True:

            started = time.time()

            try:
                result = self.cycle()

                print()
                print(
                    "P7 CYCLE",
                    time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )

                print(
                    "HEIGHT:",
                    result.get("tip", {}).get(
                        "height"
                    ),
                )

                mempool = result.get(
                    "mempool",
                    {},
                )

                print(
                    "MEMPOOL:",
                    mempool.get(
                        "network_mempool_count"
                    ),
                )

                print(
                    "PROCESSED:",
                    mempool.get(
                        "processed",
                        0,
                    ),
                )

                print(
                    "HOURLY:",
                    mempool.get(
                        "hourly_count"
                    ),
                    "/",
                    self.HOURLY_MEMPOOL_TARGET,
                )

                print(
                    "CYCLE TIME:",
                    round(
                        result.get(
                            "duration_seconds",
                            0,
                        ),
                        2,
                    ),
                    "s",
                )

            except KeyboardInterrupt:
                print()
                print("P7 STOPPED BY USER")
                break

            except Exception as exc:
                print(
                    "P7 CYCLE ERROR:",
                    repr(exc),
                )

            elapsed = time.time() - started

            sleep_for = max(
                1,
                self.interval - elapsed,
            )

            time.sleep(sleep_for)


if __name__ == "__main__":

    monitor = P7Hardening()

    print("=== P7 CONFIGURATION ===")

    print(
        json.dumps(
            monitor.status(),
            indent=2,
            default=str,
        )
    )

    print()
    print("=== FIRST LIVE CYCLE ===")

    result = monitor.cycle()

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )

    print()
    print("P7 FIRST CYCLE COMPLETE")
    print(
        "To run continuously:",
        "python -m core.monitoring.p7_hardening --continuous",
    )
