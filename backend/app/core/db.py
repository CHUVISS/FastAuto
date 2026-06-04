from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import Session, create_engine

import app.models.ai  # noqa: F401
import app.models.users  # noqa: F401
from app.core.config import settings


def _patch_asyncpg_transport() -> None:
    # rloop's TCPTransport.write() (PyO3 Cow<[u8]>) rejects memoryview objects
    # but asyncpg's _write() always calls transport.write(memoryview(buf))
    # mine solution is to wrap the transport on connection_made to transparently convert memoryview to bytes
    # it's safe on all event loops and harmless no-op when asyncpg is not installed
    try:
        import asyncpg.protocol.protocol as _pgp  # type: ignore[import-untyped]  # noqa: PLC0415
    except ImportError:
        return
    if getattr(_pgp.BaseProtocol, "_rloop_compat", False):
        return
    _orig = _pgp.BaseProtocol.connection_made

    class _T:
        __slots__ = ("_t",)

        def __init__(self, t: object) -> None:
            object.__setattr__(self, "_t", t)

        def write(self, data: object) -> None:
            t = object.__getattribute__(self, "_t")
            t.write(bytes(data) if isinstance(data, memoryview) else data)

        def __getattr__(self, n: str) -> object:
            return getattr(object.__getattribute__(self, "_t"), n)

        def __setattr__(self, n: str, v: object) -> None:
            if n == "_t":
                object.__setattr__(self, n, v)
            else:
                setattr(object.__getattribute__(self, "_t"), n, v)

    def _conn_made(self: object, transport: object) -> None:
        _orig(self, _T(transport))

    _pgp.BaseProtocol.connection_made = _conn_made
    _pgp.BaseProtocol._rloop_compat = True


_patch_asyncpg_transport()

_connect_args: dict[str, Any] = {}
if settings.DB_DRIVER == "asyncpg":
    _connect_args["ssl"] = settings.DB_SSL_MODE
    if settings.USE_PGBOUNCER:
        _connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    str(settings.sqlalchemy_database_uri),
    connect_args=_connect_args,
    pool_pre_ping=not settings.USE_PGBOUNCER,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

sync_engine = create_engine(
    str(settings.sqlalchemy_sync_database_uri),
    pool_pre_ping=True,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_sync_session() -> Session:
    return Session(sync_engine)


async def init_db() -> None:
    from app.crud.users import create_user, get_user_by_email
    from app.models.users import UserRole
    from app.schemas.users import UserCreate

    async with async_session_factory() as session:
        existing = await get_user_by_email(session, settings.FIRST_SUPERUSER_EMAIL)
        if not existing:
            await create_user(
                session,
                UserCreate(
                    email=settings.FIRST_SUPERUSER_EMAIL,
                    password=settings.FIRST_SUPERUSER_PASSWORD,
                    full_name=settings.FIRST_SUPERUSER_FULL_NAME,
                    role=UserRole.admin,
                ),
            )
            await session.commit()
