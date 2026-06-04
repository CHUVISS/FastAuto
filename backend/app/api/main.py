from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.ai import router as ai_router
from app.api.routes.auth import router as auth_router
from app.api.routes.catalog import router as catalog_router
from app.api.routes.favorites import router as favorites_router
from app.api.routes.geo import router as geo_router
from app.api.routes.listings import router as listings_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.payments import router as payments_router
from app.api.routes.reservations import router as reservations_router
from app.api.routes.system import router as system_router
from app.api.routes.tickets import router as tickets_router
from app.api.routes.user import router as user_router
from app.api.routes.webhooks import router as webhooks_router

__all__ = ["api_router", "system_router"]

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(catalog_router)
api_router.include_router(geo_router)
api_router.include_router(listings_router)
api_router.include_router(reservations_router)
api_router.include_router(payments_router)
api_router.include_router(favorites_router)
api_router.include_router(notifications_router)
api_router.include_router(tickets_router)
api_router.include_router(webhooks_router)
api_router.include_router(admin_router)
api_router.include_router(user_router)
api_router.include_router(ai_router)
