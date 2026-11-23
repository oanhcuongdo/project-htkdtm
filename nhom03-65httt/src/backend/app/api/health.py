from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.db import DatabaseUnavailable, check_database
from app.schemas.common import DbHealthOut, ErrorOut, HealthOut

router = APIRouter(tags=["Tình trạng"])


@router.get("/health", response_model=HealthOut, summary="API đang chạy")
def health() -> HealthOut:
    return HealthOut(env=get_settings().app_env)


@router.get(
    "/health/db",
    response_model=DbHealthOut,
    responses={503: {"model": ErrorOut, "description": "CSDL chưa sẵn sàng"}},
    summary="Kết nối được PostgreSQL và có các schema raw/clean/dw",
)
def health_db() -> DbHealthOut:
    try:
        info = check_database(get_settings().database_url)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return DbHealthOut(status="ok", **info)  # type: ignore[arg-type]
