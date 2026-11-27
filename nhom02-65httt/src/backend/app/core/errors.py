"""Unified error hierarchy and FastAPI exception handlers."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

_HTTP_STATUS_CODES: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_409_CONFLICT: "CONFLICT",
    _HTTP_422: "VALIDATION_ERROR",
    status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
    status.HTTP_503_SERVICE_UNAVAILABLE: "PROVIDER_UNAVAILABLE",
}


class AppError(Exception):
    """Base application exception rendered in the standard error envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = headers


class UnauthorizedError(AppError):
    """401 authentication failure."""

    def __init__(
        self,
        message: str = "Yêu cầu đăng nhập hoặc phiên đăng nhập đã hết hạn.",
        details: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(AppError):
    """403 RBAC or account-status failure."""

    def __init__(
        self,
        message: str = "Bạn không có quyền thực hiện thao tác này.",
        details: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class NotFoundError(AppError):
    """404 missing resource."""

    def __init__(
        self,
        message: str = "Không tìm thấy tài nguyên yêu cầu.",
        details: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(AppError):
    """409 state or uniqueness conflict."""

    def __init__(
        self,
        message: str = "Dữ liệu xung đột với trạng thái hiện tại.",
        details: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ProviderUnavailableError(AppError):
    """503 external marketplace or downstream provider unavailable."""

    def __init__(
        self,
        message: str = "Dịch vụ tích hợp tạm thời không khả dụng.",
        details: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(
            code="PROVIDER_UNAVAILABLE",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


def build_error_payload(
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build standard API error envelope."""
    error_body: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if details is not None:
        error_body["details"] = details
    return {"error": error_body}


async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_payload(exc.code, exc.message, exc.details),
        headers=exc.headers,
    )


async def _http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    default_code = "INTERNAL_ERROR" if exc.status_code >= 500 else "HTTP_ERROR"
    code = _HTTP_STATUS_CODES.get(exc.status_code, default_code)
    message = exc.detail if isinstance(exc.detail, str) else "Yêu cầu không hợp lệ."
    headers = dict(exc.headers) if exc.headers else None
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        headers = headers or {}
        headers.setdefault("WWW-Authenticate", "Bearer")
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_payload(code, message),
        headers=headers,
    )


async def _validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details: list[dict[str, str]] = []
    for err in exc.errors():
        loc_parts = [str(part) for part in err.get("loc", ()) if part != "body"]
        field_name = ".".join(loc_parts) if loc_parts else "body"
        message = str(err.get("msg", "Giá trị không hợp lệ."))
        details.append({"field": field_name, "message": message})
    return JSONResponse(
        status_code=_HTTP_422,
        content=build_error_payload(
            code="VALIDATION_ERROR",
            message="Dữ liệu đầu vào không hợp lệ.",
            details=details,
        ),
    )


async def _unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception while processing request", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_payload(
            code="INTERNAL_ERROR",
            message="Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application."""
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
