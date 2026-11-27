"""Xác thực Bearer token, phân quyền và đối chiếu membership của quán."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.utils import decode_token
from app.database import get_db
from app.exceptions import AppError, ForbiddenError
from app.restaurants.models import RestaurantMembership
from app.users.models import User, UserRole

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise AppError("UNAUTHENTICATED", "Vui lòng đăng nhập.", 401)
    user = db.get(User, decode_token(credentials.credentials, "access"))
    if user is None:
        raise AppError("UNAUTHENTICATED", "Vui lòng đăng nhập lại.", 401)
    return user


def require_role(*roles: UserRole):
    allowed = {UserRole(role) for role in roles}

    def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise ForbiddenError()
        return user

    return dependency


def require_vendor_owner(
    restaurant_id: int,
    user: Annotated[User, Depends(require_role(UserRole.VENDOR))],
    db: Annotated[Session, Depends(get_db)],
) -> int:
    membership = db.get(RestaurantMembership, user.id)
    if membership is None or membership.restaurant_id != restaurant_id:
        raise ForbiddenError("Bạn không quản lý quán này.")
    return membership.restaurant_id
