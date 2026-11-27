"""Health check endpoint."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiModel, Envelope

router = APIRouter(tags=["health"])


class HealthData(ApiModel):
    """Service and database readiness status."""

    status: Literal["ok"] = "ok"
    database: Literal["ok", "error"]


@router.get("/health", response_model=Envelope[HealthData])
def health_check(db: Session = Depends(get_db)) -> Envelope[HealthData]:
    """Verify API liveness and database connectivity via SELECT 1."""
    db_status: Literal["ok", "error"] = "ok"
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db_status = "error"
    return Envelope(data=HealthData(status="ok", database=db_status))
