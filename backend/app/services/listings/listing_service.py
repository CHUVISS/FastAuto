from typing import Any

from app.models.listings import Listing, ListingStatus

_ALWAYS_EDITABLE = {"price", "sale_address", "accepts_cash", "accepts_transfer"}
_LOCKED_AFTER_PUBLISH = {"city_id", "modification_id", "year"}


class ImmutableFieldError(Exception):
    """Raised when an edit violates an immutability rule"""


class PublishValidationError(Exception):
    """Raised when a listing cannot be published"""


class MaxActiveListingsError(Exception):
    """Raised when a seller exceeds the active-listing limit"""


def assert_can_create(active_count: int, max_active: int) -> None:
    if active_count >= max_active:
        raise MaxActiveListingsError(f"Max {max_active} active listings reached")


def validate_year(year: int, gen_from: int | None, gen_to: int | None) -> None:
    lo = gen_from or 1900
    hi = (gen_to or 2100) + 2
    if not (lo <= year <= hi):
        raise PublishValidationError(f"Year {year} outside generation range {lo}..{hi}")


def apply_edit(listing: Listing, changes: dict[str, Any]) -> Listing:
    locked = listing.status != ListingStatus.draft
    published = listing.published_at is not None
    for field, value in changes.items():
        if field == "vin":
            if listing.vin is not None and value != listing.vin:
                raise ImmutableFieldError("VIN cannot be changed once set")
        elif field == "license_plate":
            if listing.license_plate_edit_count >= 1:
                raise ImmutableFieldError("License plate can be edited only once")
            listing.license_plate_edit_count += 1
        elif field in _ALWAYS_EDITABLE:
            pass
        elif published and field in _LOCKED_AFTER_PUBLISH:
            raise ImmutableFieldError(f"{field} is locked after publication")
        elif locked:
            raise ImmutableFieldError(f"{field} can only be edited while in draft")
        setattr(listing, field, value)
    return listing


def validate_publish(listing: Listing, image_count: int, window_count: int) -> None:
    if not (listing.vin or listing.license_plate):
        raise PublishValidationError("VIN or license plate is required")
    if not listing.city_id:
        raise PublishValidationError("City is required")
    if image_count < 1:
        raise PublishValidationError("At least one image is required")
    if listing.viewing_enabled and window_count < 1:
        raise PublishValidationError("At least one viewing window is required")
    if listing.viewing_enabled and not listing.sale_address:
        raise PublishValidationError("Sale address is required when viewing is enabled")
    if not (listing.accepts_cash or listing.accepts_transfer):
        raise PublishValidationError(
            "At least one buyer payment preference (cash/transfer) is required"
        )


def do_publish(listing: Listing, image_count: int, window_count: int) -> Listing:
    validate_publish(listing, image_count, window_count)
    listing.status = ListingStatus.pending_review
    return listing
