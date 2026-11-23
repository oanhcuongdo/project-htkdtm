from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API phục vụ Hệ thống Quản lý Tài chính Cá nhân Thông minh (Nhóm 13 - 65HTTT)"
)

# Cấu hình CORS cho phép truy cập từ các ứng dụng frontend/dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "team": "nhom13-65httt",
        "class": "65HTTT - Hệ thống Kinh doanh Thông minh",
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs"
    }

@app.get("/health")
def healthcheck():
    """Kiểm tra tình trạng hoạt động của backend service."""
    return {
        "status": "healthy",
        "database_configured": bool(settings.POSTGRES_HOST),
        "database_target": f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    }

@app.get("/api/v1/system-status")
def system_status():
    """Trả về trạng thái các module trong hệ thống."""
    return {
        "modules": {
            "ingestion_email": "ready",
            "ingestion_statement": "ready",
            "ingestion_telegram_ocr": "ready",
            "data_warehouse": "initialized",
            "ai_classifier": "ready",
            "ai_anomaly_detector": "ready",
            "ai_forecaster": "ready",
            "superset_bi": "ready"
        }
    }
