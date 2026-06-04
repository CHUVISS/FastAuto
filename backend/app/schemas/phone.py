from typing import Literal

from pydantic import BaseModel, model_validator

from app.schemas.common import normalize_russian_phone


class PhoneSendIn(BaseModel):
    phone: str = ""
    purpose: Literal["phone_verify", "payout_change"] = "phone_verify"

    @model_validator(mode="after")
    def _normalize(self) -> "PhoneSendIn":
        if self.purpose == "phone_verify":
            normalized = normalize_russian_phone(self.phone)
            if normalized is None:
                raise ValueError("phone is required for phone_verify")
            self.phone = normalized
        return self


class PhoneVerifyIn(BaseModel):
    phone: str
    code: str

    @model_validator(mode="after")
    def _normalize(self) -> "PhoneVerifyIn":
        normalized = normalize_russian_phone(self.phone)
        if normalized is None:
            raise ValueError("phone is required")
        self.phone = normalized
        return self
