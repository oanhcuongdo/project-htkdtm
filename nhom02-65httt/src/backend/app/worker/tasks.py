"""Base Celery tasks including background marketplace price synchronization."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.db.session import SessionLocal
from app.models.pricing import PriceSyncLog
from app.services.execution import execute_sync_log
from app.worker.celery_app import celery_app


@celery_app.task(name="app.worker.tasks.ping")
def ping() -> str:
    """Health ping task to verify worker connectivity."""
    return "pong"


@celery_app.task(name="app.worker.tasks.execute_price_sync_task")
def execute_price_sync_task(execution_id: str) -> dict[str, Any]:
    """Execute a queued PriceSyncLog record in the background via MarketplaceAdapter."""
    with SessionLocal() as db:
        sync_log = db.get(PriceSyncLog, UUID(execution_id))
        if sync_log is None:
            return {"id": execution_id, "status": "NOT_FOUND"}
        if sync_log.status != "QUEUED":
            return {"id": execution_id, "status": sync_log.status, "skipped": True}

        execute_sync_log(db, sync_log)
        db.commit()
        db.refresh(sync_log)
        return {
            "id": str(sync_log.id),
            "status": sync_log.status,
            "syncMode": sync_log.sync_mode,
        }
