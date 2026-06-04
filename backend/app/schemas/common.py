from __future__ import annotations

import re

from pydantic import BaseModel


class Message(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    error: str
    message: str


_PHONE_DIGITS = re.compile(r"\D")


def normalize_russian_phone(value: str | None) -> str | None:
    if value is None:
        return None
    digits = _PHONE_DIGITS.sub("", value)
    if len(digits) == 11 and digits[0] == "8":
        digits = "7" + digits[1:]
    if len(digits) != 11 or digits[0] != "7":
        raise ValueError(
            "Phone must be a Russian number: 11 digits starting with 7, "
            "e.g. 79991234567"
        )
    return digits
