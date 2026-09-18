from core.p8_5.system_earnings import SystemEarningsEngine


class P9EarningsBridge:

    def __init__(
        self,
        db_path="data/cryptoFirstX1.db",
        account_id="admin",
    ):
        self.engine = SystemEarningsEngine(
            db_path=db_path,
            account_id=account_id,
        )

    def process_approved_activity(
        self,
        event_type,
        event_id=None,
        source_reference=None,
        description=None,
    ):
        return self.engine.process(
            event_type=event_type,
            event_id=event_id,
            source_reference=source_reference,
            description=description,
        )

    def earnings(self, limit=100):
        return self.engine.history(limit)

    def earnings_totals(self):
        return self.engine.totals()


__all__ = ["P9EarningsBridge"]
