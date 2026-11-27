"""FastAPI dependencies for JWT authentication and RBAC enforcement."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.rbac import Permission, has_permission
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and validate the authenticated active user from Bearer JWT."""
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
    ):
        raise UnauthorizedError("Thiếu thông tin xác thực Bearer token.")

    payload = decode_token(credentials.credentials)
    try:
        user_id = UUID(str(payload["sub"]))
    except (ValueError, KeyError, TypeError) as exc:
        raise UnauthorizedError("Token xác thực không hợp lệ.") from exc

    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("Phiên đăng nhập không hợp lệ.")
    if not user.is_active:
        raise ForbiddenError("Tài khoản đã bị vô hiệu hóa.")
    return user


def _build_permission_dependency(
    permissions: tuple[Permission, ...],
    *,
    require_all: bool,
) -> Callable[[User], User]:
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        checks = (has_permission(current_user.role, perm) for perm in permissions)
        allowed = all(checks) if require_all else any(checks)
        if not allowed:
            raise ForbiddenError("Bạn không có quyền thực hiện thao tác này.")
        return current_user

    return _dependency


def require_permission(*permissions: Permission) -> Callable[[User], User]:
    """Require all specified RBAC permissions for an endpoint."""
    return _build_permission_dependency(permissions, require_all=True)


def require_any_permission(*permissions: Permission) -> Callable[[User], User]:
    """Require at least one of the specified RBAC permissions for an endpoint."""
    return _build_permission_dependency(permissions, require_all=False)
