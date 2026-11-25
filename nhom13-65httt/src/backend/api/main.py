from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.dependencies import check_db_connection
from api.routers import ai_routes, analytics_routes, auth_routes, chat_routes, ingestion_routes, sources_routes
from api.security import ensure_demo_user_ready
from scheduler.cron_jobs import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_demo_user_ready()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API phục vụ Hệ thống Quản lý Tài chính Cá nhân Thông minh (Nhóm 13 - 65HTTT)",
    lifespan=lifespan,
)

# Cấu hình CORS cho phép truy cập từ React Portal (:3000) và Superset (:8088)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn toàn bộ các router nghiệp vụ
app.include_router(auth_routes.router)
app.include_router(sources_routes.router)
app.include_router(ingestion_routes.router)
app.include_router(ai_routes.router)
app.include_router(analytics_routes.router)
app.include_router(chat_routes.router)


@app.get("/")
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "team": "nhom13-65httt",
        "class": "65HTTT - Hệ thống Kinh doanh Thông minh",
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
    }


@app.get("/health")
def healthcheck():
    """Kiểm tra tình trạng hoạt động của backend service và kết nối PostgreSQL."""
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database_connected": db_ok,
        "gemini_configured": bool(settings.GEMINI_API_KEY and "your_gemini" not in settings.GEMINI_API_KEY),
        "database_target": f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
    }


@app.get("/api/v1/system-status")
def system_status():
    """Trả về trạng thái các module trong hệ thống."""
    return {
        "modules": {
            "auth_multi_user": "active",
            "user_data_sources": "active",
            "ingestion_email": "active",
            "ingestion_statement": "active",
            "ingestion_telegram_ocr": "active",
            "etl_deduplication": "active",
            "data_quality_gate": "active",
            "scheduler": "running",
            "data_warehouse": "initialized",
            "ai_classifier": "active",
            "ai_anomaly_detector": "active",
            "ai_forecaster": "active",
            "ai_gemini_chat": "active",
            "analytics_kpi_api": "active",
            "superset_bi": "active",
            "react_portal": "active",
        }
    }
