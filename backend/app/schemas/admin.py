from __future__ import annotations

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_listings: int
    active_listings: int
    reserved_listings: int
    sold_listings: int
    total_reservations: int
    active_reservations: int
    settling_reservations: int
    completed_reservations: int
    total_users: int
    open_tickets: int


class ListingRejectIn(BaseModel):
    reason: str | None = None
