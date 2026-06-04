def mask_tail(value: str | None, keep: int = 2) -> str | None:
    """Mask all but the last ``keep`` characters of ``value``.
    ``"WVWZZZ1KZ6W123456")`` -> ``"***************56"``
    length is ``<= keep`` are fully masked. ``None`` passes through.
    """
    if value is None:
        return None
    if len(value) <= keep:
        return "*" * len(value)
    return "*" * (len(value) - keep) + value[-keep:]
