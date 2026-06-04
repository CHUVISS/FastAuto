import base64
import uuid
from datetime import date, timedelta
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.api.dependencies.auth import (
    CurrentUser,
    OptionalUser,
    RedisDep,
    SessionDep,
    StorageDep,
)
from app.api.dependencies.rate_limit import public_browse_limit
from app.core.config import settings
from app.crud import catalog as catalog_crud
from app.crud import favorites as favorites_crud
from app.crud import listings as crud
from app.crud import reservations as reservations_crud
from app.models.listings import Listing, ListingImage, ListingStatus, ViewingWindow
from app.models.users import User
from app.schemas.listings import (
    ListingCreate,
    ListingUpdate,
    ViewingScheduleSet,
    ViewingWindowCreate,
)
from app.services.catalog import catalog_service
from app.services.images.image_service import delete_image_files, validate_and_save
from app.services.listings import listing_service as svc
from app.services.viewings.viewing_schedule import generate_windows
from app.utils.masking import mask_tail
from app.utils.units import cc_to_litres

router = APIRouter(prefix="/listings", tags=["listings"])


def _decode_cursor(cursor: str | None) -> tuple[str | None, str | None]:
    if not cursor:
        return None, None
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    a, b = raw.split("|", 1)
    return a, b


def _encode_cursor(a: object, b: object) -> str:
    return base64.urlsafe_b64encode(f"{a}|{b}".encode()).decode()


def _filename_from_url(url: str) -> str:
    return url.rsplit("/", 1)[-1].split("?", 1)[0]


@router.get("", dependencies=[Depends(public_browse_limit)], response_model=None)
async def list_listings(
    session: SessionDep,
    sort: str = Query("newest", pattern="^(newest|price_asc|price_desc)$"),
    cursor: str | None = None,
    mark_id: str | None = None,
    model_id: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    body_type: str | None = None,
    engine_type: str | None = None,
    city: str | None = None,
    limit: int = Query(20, le=100),
) -> dict[str, Any]:
    cur_a, cur_b = _decode_cursor(cursor)
    rows = await crud.search_active(
        session,
        sort=sort,
        cursor_a=cur_a,
        cursor_b=cur_b,
        mark_id=mark_id,
        model_id=model_id,
        price_min=price_min,
        price_max=price_max,
        year_min=year_min,
        year_max=year_max,
        body_type=body_type,
        engine_type=engine_type,
        city=city,
        limit=limit,
    )
    next_cursor = None
    if len(rows) == limit:
        last = rows[-1]
        key = last["price"] if sort.startswith("price") else last["created_at"]
        next_cursor = _encode_cursor(key, last["id"])
    for row in rows:
        row["vin"] = mask_tail(row.get("vin"))
        row["license_plate"] = mask_tail(row.get("license_plate"))
        if "displacement" in row:
            row["displacement"] = cc_to_litres(row.get("displacement"))
    return {"items": rows, "next_cursor": next_cursor}


@router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_listing(
    body: ListingCreate, user: CurrentUser, session: SessionDep
) -> Listing:
    active = await crud.count_active(session, user.id)
    try:
        svc.assert_can_create(active, settings.MAX_ACTIVE_LISTINGS)
    except svc.MaxActiveListingsError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e

    full = await catalog_crud.get_modification_full(session, body.modification_id)
    if full is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Unknown modification"
        )
    gen = full.generation
    try:
        svc.validate_year(
            body.year,
            gen_from=gen.year_from if gen else None,
            gen_to=gen.year_to if gen else None,
        )
    except svc.PublishValidationError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e

    listing = Listing(
        seller_id=user.id,
        mark_id=full.modification.mark_id,
        model_id=full.modification.model_id,
        body_type=full.configuration.body_type if full.configuration else None,
        engine_type=full.specification.engine_type if full.specification else None,
        **body.model_dump(),
    )
    await crud.create(session, listing)
    await session.commit()
    await session.refresh(listing)
    return listing


@router.get("/my", response_model=None)
async def my_listings(user: CurrentUser, session: SessionDep) -> list[Listing]:
    return await crud.get_for_owner(session, user.id)


def _serialize_listing(
    listing: Listing, *, is_owner: bool, seller: User | None
) -> dict[str, Any]:
    """Public listing payload.

    Non-owners get VIN / licence plate masked to the last 2 chars and no
    ``sale_address`` (revealed to a buyer only after a reservation). The seller
    phone is included only for the owner or when the seller is ``phone_visible``.
    """
    data = listing.model_dump()
    if not is_owner:
        data["vin"] = mask_tail(listing.vin)
        data["license_plate"] = mask_tail(listing.license_plate)
        data.pop("sale_address", None)
    if seller is not None and (is_owner or seller.phone_visible):
        data["seller_phone"] = seller.phone
    return data


@router.get("/{listing_id}", response_model=None)
async def get_listing(
    listing_id: uuid.UUID,
    session: SessionDep,
    redis: RedisDep,
    viewer: OptionalUser,
) -> dict[str, Any]:
    listing = await crud.get(session, listing_id)
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    seller = await session.get(User, listing.seller_id)
    is_owner = viewer is not None and viewer.id == listing.seller_id
    full = await catalog_service.get_modification_full(
        session, redis, listing.modification_id
    )
    images = await crud.list_images(session, listing.id)
    data = _serialize_listing(listing, is_owner=is_owner, seller=seller)
    if is_owner:
        data["favorites_count"] = await favorites_crud.count_for_listing(
            session, listing.id
        )
    data["catalog_specs"] = full["specification"] if full else None
    data["catalog_options"] = full["options"] if full else None
    data["images"] = [img.model_dump() for img in images]
    return data


async def _owned(
    session: SessionDep, listing_id: uuid.UUID, user: CurrentUser
) -> Listing:
    listing = await crud.get(session, listing_id)
    if listing is None or listing.seller_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return listing


@router.patch("/{listing_id}", response_model=None)
async def edit_listing(
    listing_id: uuid.UUID,
    body: ListingUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> Listing:
    listing = await _owned(session, listing_id, user)
    changes = body.model_dump(exclude_unset=True)
    try:
        svc.apply_edit(listing, changes)
    except svc.ImmutableFieldError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e
    await session.commit()
    await session.refresh(listing)
    return listing


@router.post("/{listing_id}/publish", response_model=None)
async def publish_listing(
    listing_id: uuid.UUID,
    user: CurrentUser,
    session: SessionDep,
) -> Listing:
    listing = await _owned(session, listing_id, user)
    image_count = await crud.count_images(session, listing.id)
    window_count = await crud.count_windows(session, listing.id)
    try:
        svc.do_publish(listing, image_count, window_count)
    except svc.PublishValidationError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e
    await session.commit()
    await session.refresh(listing)
    return listing


@router.delete("/{listing_id}", response_model=None)
async def delete_listing(
    listing_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> dict[str, Any]:
    listing = await _owned(session, listing_id, user)
    if (
        listing.status == ListingStatus.reserved
        or await reservations_crud.has_active_reservation(session, listing.id)
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Listing has an active reservation or deal"
        )
    listing.status = ListingStatus.archived
    await session.commit()
    return {"archived": True}


@router.post(
    "/{listing_id}/images", status_code=status.HTTP_201_CREATED, response_model=None
)
async def upload_listing_image(
    listing_id: uuid.UUID,
    user: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
    file: UploadFile = File(...),
) -> ListingImage:
    listing = await _owned(session, listing_id, user)
    existing = await crud.count_images(session, listing.id)
    saved = await validate_and_save(file, listing.id, storage)
    image = ListingImage(
        listing_id=listing.id,
        url=saved.url,
        thumbnail_url=saved.thumb_url,
        is_primary=existing == 0,
        sort_order=existing,
    )
    try:
        await crud.add_image(session, image)
        await session.commit()
    except Exception:
        await delete_image_files(listing.id, saved.filename, storage)
        raise
    await session.refresh(image)
    return image


@router.delete("/{listing_id}/images/{image_id}", response_model=None)
async def delete_listing_image(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    user: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
) -> dict[str, Any]:
    listing = await _owned(session, listing_id, user)
    image = await crud.get_image(session, image_id)
    if image is None or image.listing_id != listing.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    await crud.delete_image(session, image)
    await session.commit()
    await delete_image_files(listing.id, _filename_from_url(image.url), storage)
    return {"deleted": True}


@router.get("/{listing_id}/viewing-windows", response_model=None)
async def list_viewing_windows(
    listing_id: uuid.UUID, session: SessionDep
) -> list[ViewingWindow]:
    return await crud.list_windows(session, listing_id)


@router.post(
    "/{listing_id}/viewing-windows",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
)
async def add_viewing_window(
    listing_id: uuid.UUID,
    body: ViewingWindowCreate,
    user: CurrentUser,
    session: SessionDep,
) -> ViewingWindow:
    listing = await _owned(session, listing_id, user)
    window = ViewingWindow(
        listing_id=listing.id,
        window_date=body.window_date,
        time_from=body.time_from,
        time_to=body.time_to,
    )
    await crud.add_window(session, window)
    await session.commit()
    await session.refresh(window)
    return window


@router.delete("/{listing_id}/viewing-windows/{window_id}", response_model=None)
async def delete_viewing_window(
    listing_id: uuid.UUID,
    window_id: uuid.UUID,
    user: CurrentUser,
    session: SessionDep,
) -> dict[str, Any]:
    listing = await _owned(session, listing_id, user)
    window = await crud.get_window(session, window_id)
    if window is None or window.listing_id != listing.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if await crud.window_has_active_booking(session, window_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Window has an active booking")
    await crud.delete_window(session, window)
    await session.commit()
    return {"deleted": True}


@router.put("/{listing_id}/viewing-schedule", response_model=None)
async def set_viewing_schedule(
    listing_id: uuid.UUID,
    body: ViewingScheduleSet,
    user: CurrentUser,
    session: SessionDep,
) -> dict[str, Any]:
    listing = await _owned(session, listing_id, user)
    start = date.today()
    expires = (
        listing.expires_at.date() if listing.expires_at else start + timedelta(days=7)
    )
    template = [
        {"weekday": s.weekday, "time_from": s.time_from, "time_to": s.time_to}
        for s in body.template
    ]
    windows = generate_windows(template, start, expires, body.repeat_weekly)
    created = await crud.upsert_windows(session, listing.id, windows)
    await session.commit()
    return {"generated": created}
