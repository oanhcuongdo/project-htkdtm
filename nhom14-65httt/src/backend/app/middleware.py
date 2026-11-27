"""Middleware: CORS, request logging, request-id."""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger("viviet")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Gắn X-Request-ID vào mỗi request/response."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path và status code."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        logger.info(
            "%s %s → %s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response


def setup_middleware(app: FastAPI) -> None:
    """Đăng ký tất cả middleware."""
    from app.exceptions import register_exception_handlers

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(app)
