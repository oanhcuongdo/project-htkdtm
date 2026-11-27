"""Aggregate API v1 router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    audit_logs,
    auth,
    channels,
    dashboard,
    executions,
    health,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(audit_logs.router)
api_router.include_router(channels.router)
api_router.include_router(dashboard.router)
api_router.include_router(executions.router)
