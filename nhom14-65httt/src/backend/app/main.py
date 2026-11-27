"""Entry point – FastAPI application cho Vị Việt."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.admin.router import router as admin_router
from app.auth.router import router as auth_router
from app.menu.router import router as menu_router
from app.middleware import setup_middleware
from app.orders.router import router as orders_router
from app.preferences.router import router as preferences_router
from app.restaurants.router import router as restaurants_router
from app.reviews.router import router as reviews_router
from app.search.router import router as search_router
from app.tracking.router import router as tracking_router
from app.vendor.router import router as vendor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    yield


app = FastAPI(
    title="Vị Việt API",
    description="API đặt món Việt tích hợp gợi ý cá nhân hóa",
    version="0.1.0",
    lifespan=lifespan,
)

setup_middleware(app)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(restaurants_router, prefix="/api/v1")
app.include_router(vendor_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(menu_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(preferences_router, prefix="/api/v1")
app.include_router(tracking_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    """Kiểm tra backend đang chạy."""
    return {"status": "ok"}
