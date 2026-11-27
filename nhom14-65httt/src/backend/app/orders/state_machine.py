"""Quy tắc chuyển trạng thái theo E.2; không truy cập DB."""

from types import MappingProxyType

from app.exceptions import ForbiddenError, InvalidStateTransitionError
from app.orders.models import OrderStatus
from app.users.models import UserRole

TRANSITIONS = MappingProxyType(
    {
        OrderStatus.PENDING: MappingProxyType(
            {
                OrderStatus.CONFIRMED: UserRole.VENDOR,
                OrderStatus.REJECTED: UserRole.VENDOR,
                OrderStatus.CANCELLED: UserRole.CUSTOMER,
            }
        ),
        OrderStatus.CONFIRMED: MappingProxyType({OrderStatus.PREPARING: UserRole.VENDOR}),
        OrderStatus.PREPARING: MappingProxyType({OrderStatus.DELIVERING: UserRole.VENDOR}),
        OrderStatus.DELIVERING: MappingProxyType({OrderStatus.COMPLETED: UserRole.VENDOR}),
    }
)


def validate_transition(current: OrderStatus, target: OrderStatus, role: UserRole) -> None:
    required = TRANSITIONS.get(current, {}).get(target)
    if required is None:
        raise InvalidStateTransitionError(current, target)
    if role != required:
        raise ForbiddenError("Vai trò này không được thực hiện chuyển trạng thái đã chọn.")
