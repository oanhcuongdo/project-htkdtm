"""Điểm vào của API FastAPI (EduVision BI, nhóm 03)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, platforms, predict
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="EduVision BI API",
        description="API phục vụ website, n8n và Superset. Các điểm cuối AI hiện là khung (trả 501).",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(platforms.router)
    app.include_router(predict.router)
    app.include_router(auth.router)
    return app


app = create_app()
