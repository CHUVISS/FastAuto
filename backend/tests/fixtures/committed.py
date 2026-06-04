from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

TRUNCATE_TABLES = [
    "notifications",
    "ticket_messages",
    "tickets",
    "favorites",
    "viewing_bookings",
    "viewing_windows",
    "reservations",
    "listing_images",
    "listings",
    "phone_otp_audit",
    "ai_tool_calls",
    "ai_messages",
    "ai_conversations",
    "users",
    "catalog.options",
    "catalog.specifications",
    "catalog.modifications",
    "catalog.configurations",
    "catalog.generations",
    "catalog.models",
    "catalog.marks",
]


async def seed_user(eng, role: str, email: str, password: str = "TestPass123!") -> str:
    from app.crud.users import create_user as _create_user
    from app.models.users import UserRole
    from app.schemas.users import UserCreate

    async with eng.connect() as conn:
        async with AsyncSession(bind=conn, expire_on_commit=False) as s:
            u = await _create_user(
                s,
                UserCreate(
                    email=email,
                    password=password,
                    full_name=f"Test {role.title()}",
                    role=UserRole(role),
                ),
            )
            await conn.commit()
            return str(u.id)
