"""SQLModel модели таблиц (ORM слой)"""

from app.models.catalog import (
    CatalogColor,
    CatalogSeedState,
    Configuration,
    Generation,
    Mark,
    Model,
    Modification,
    Options,
    Specification,
)
from app.models.favorites import Favorite
from app.models.geo import GeoCity, GeoRegion
from app.models.listings import (
    BookingStatus,
    Condition,
    Listing,
    ListingImage,
    ListingStatus,
    ViewingBooking,
    ViewingWindow,
)
from app.models.notifications import Notification
from app.models.payout import PhoneOTPAudit
from app.models.reservations import (
    CancelReason,
    OutcomeParty,
    Reservation,
    ReservationOutcome,
    ReservationStatus,
)
from app.models.tickets import Ticket, TicketMessage, TicketStatus, TicketType

__all__ = [
    "BookingStatus",
    "CancelReason",
    "CatalogColor",
    "CatalogSeedState",
    "Condition",
    "Configuration",
    "Favorite",
    "Generation",
    "GeoCity",
    "GeoRegion",
    "Listing",
    "ListingImage",
    "ListingStatus",
    "Mark",
    "Model",
    "Modification",
    "Notification",
    "Options",
    "OutcomeParty",
    "PhoneOTPAudit",
    "Reservation",
    "ReservationOutcome",
    "ReservationStatus",
    "Specification",
    "Ticket",
    "TicketMessage",
    "TicketStatus",
    "TicketType",
    "ViewingBooking",
    "ViewingWindow",
]
