from enum import StrEnum


class ReturnStatus(StrEnum):
    ok = "ok"
    pending = "pending"
    failed = "failed"
    cancelled = "cancelled"
