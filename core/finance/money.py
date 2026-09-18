from decimal import Decimal, ROUND_HALF_UP


CENTS_PER_UNIT = 100


class Money:
    """
    Internal monetary representation.

    1 platform unit = USD 1.00 of internal ledger value.
    All persistent amounts are integer cents.
    """

    @staticmethod
    def dollars_to_cents(value):
        amount = Decimal(str(value))
        if amount < 0:
            raise ValueError("amount cannot be negative")

        cents = (amount * CENTS_PER_UNIT).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
        return int(cents)

    @staticmethod
    def cents_to_dollars(cents):
        cents = int(cents)
        return Decimal(cents) / Decimal(CENTS_PER_UNIT)

    @staticmethod
    def validate_cents(cents):
        if not isinstance(cents, int):
            raise ValueError("amount must be integer cents")
        if cents < 0:
            raise ValueError("amount cannot be negative")
        return cents
