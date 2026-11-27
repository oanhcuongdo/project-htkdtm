"""Celery application configuration using Redis broker and Asia/Ho_Chi_Minh timezone."""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "erp_smart_pricing",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule={
        # Scheduled crawl, pricing, and sync jobs will be registered here.
    },
)

celery_app.autodiscover_tasks(["app.worker"])
