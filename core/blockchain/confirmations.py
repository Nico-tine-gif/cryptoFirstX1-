def calculate(transaction_height: int, current_height: int) -> int:
    if transaction_height < 0:
        return 0

    if current_height < transaction_height:
        return 0

    return current_height - transaction_height + 1


def confirmed(
    transaction_height: int,
    current_height: int,
    required: int = 3,
) -> bool:
    return calculate(
        transaction_height,
        current_height,
    ) >= required
