from datetime import date, time

from pydantic import BaseModel, Field

from app.models.listings import Condition


class ListingCreate(BaseModel):
    modification_id: str
    year: int
    price: int
    mileage: int
    color_id: str
    condition: Condition
    city_id: str
    sale_address: str | None = None
    accepts_cash: bool = False
    accepts_transfer: bool = False
    vin: str | None = None
    license_plate: str | None = None
    description: str | None = None
    viewing_enabled: bool = True
    viewing_repeat_weekly: bool = False


class ListingUpdate(BaseModel):
    price: int | None = None
    sale_address: str | None = None
    accepts_cash: bool | None = None
    accepts_transfer: bool | None = None
    vin: str | None = None
    license_plate: str | None = None
    mileage: int | None = None
    color_id: str | None = None
    condition: Condition | None = None
    description: str | None = None
    city_id: str | None = None
    modification_id: str | None = None
    year: int | None = None
    viewing_enabled: bool | None = None
    viewing_repeat_weekly: bool | None = None


class ViewingWindowCreate(BaseModel):
    window_date: date
    time_from: time
    time_to: time


class WeeklySlot(BaseModel):
    weekday: int = Field(ge=0, le=6)
    time_from: time
    time_to: time


class ViewingScheduleSet(BaseModel):
    template: list[WeeklySlot]
    repeat_weekly: bool = False
