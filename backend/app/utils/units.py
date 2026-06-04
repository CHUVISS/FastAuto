from decimal import Decimal, InvalidOperation


def cc_to_litres(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return value
    try:
        litres = Decimal(raw) / Decimal(1000)
    except InvalidOperation:
        return value
    return f"{litres.normalize():f}"
