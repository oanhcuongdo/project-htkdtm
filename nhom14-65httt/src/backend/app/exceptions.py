"""Exception classes nghiệp vụ và handler trả JSON chuẩn."""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class AppError(Exception):
    """Base exception cho lỗi nghiệp vụ."""

    def __init__(
        self, code: str, message: str, status_code: int = 400, details: dict | None = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Không tìm thấy tài nguyên.", details: dict | None = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=404, details=details)


class ForbiddenError(AppError):
    def __init__(
        self, message: str = "Không đủ quyền thực hiện thao tác này.", details: dict | None = None
    ):
        super().__init__(code="FORBIDDEN", message=message, status_code=403, details=details)


class ConflictError(AppError):
    def __init__(
        self,
        code: str = "CONFLICT",
        message: str = "Xung đột dữ liệu.",
        details: dict | None = None,
    ):
        super().__init__(code=code, message=message, status_code=409, details=details)


class InvalidStateTransitionError(ConflictError):
    def __init__(self, current: str, target: str):
        super().__init__(
            code="INVALID_STATE_TRANSITION",
            message=f"Không thể chuyển từ trạng thái '{current}' sang '{target}'.",
            details={"current_status": current, "target_status": target},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Đăng ký handler bắt AppError và trả JSON chuẩn."""

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, exc):
        errors = [
            {"field": list(e["loc"]), "message": e["msg"], "type": e["type"]} for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Dữ liệu không hợp lệ.",
                    "details": jsonable_encoder(errors),
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error(_request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": str(exc.detail),
                    "details": {},
                }
            },
        )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            headers={"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
