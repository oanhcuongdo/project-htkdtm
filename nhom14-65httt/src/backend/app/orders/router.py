"""API đơn COD cho khách hàng và chủ quán."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.orders import service
from app.orders.models import OrderStatus
from app.orders.schemas import OrderCreate, OrderDetail, RejectionInput
from app.users.models import User, UserRole

router = APIRouter(tags=["orders"])
Database = Annotated[Session, Depends(get_db)]
Customer = Annotated[User, Depends(require_role(UserRole.CUSTOMER))]
Vendor = Annotated[User, Depends(require_role(UserRole.VENDOR))]
OrderId = Annotated[int, Path(gt=0, le=2**31 - 1)]
Offset = Annotated[int, Query(ge=0, le=2**31 - 1)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.post("/orders/", response_model=OrderDetail, status_code=201)
def create(payload: OrderCreate, response: Response, db: Database, user: Customer):
    row, created = service.create_order(db, user.id, payload)
    response.status_code = 201 if created else 200
    return service.detail(db, user.id, row.id)


@router.get("/orders/", response_model=list[OrderDetail])
def customer_orders(db: Database, user: Customer, offset: Offset = 0, limit: Limit = 20):
    return service.listing(db, user.id, offset=offset, limit=limit)


@router.get("/orders/{order_id}", response_model=OrderDetail)
def customer_detail(order_id: OrderId, db: Database, user: Customer):
    return service.detail(db, user.id, order_id)


@router.patch("/orders/{order_id}/cancel", response_model=OrderDetail)
def cancel(order_id: OrderId, db: Database, user: Customer):
    service.transition_order(db, order_id, user.id, OrderStatus.CANCELLED)
    return service.detail(db, user.id, order_id)


@router.get("/vendor/orders", response_model=list[OrderDetail])
def vendor_orders(db: Database, user: Vendor, offset: Offset = 0, limit: Limit = 20):
    return service.listing(db, user.id, offset=offset, limit=limit)


@router.get("/vendor/orders/{order_id}", response_model=OrderDetail)
def vendor_detail(order_id: OrderId, db: Database, user: Vendor):
    return service.detail(db, user.id, order_id)


@router.patch("/vendor/orders/{order_id}/confirm", response_model=OrderDetail)
def confirm(order_id: OrderId, db: Database, user: Vendor):
    service.transition_order(db, order_id, user.id, OrderStatus.CONFIRMED)
    return service.detail(db, user.id, order_id)


@router.patch("/vendor/orders/{order_id}/reject", response_model=OrderDetail)
def reject(order_id: OrderId, payload: RejectionInput, db: Database, user: Vendor):
    service.transition_order(db, order_id, user.id, OrderStatus.REJECTED, reason=payload.reason)
    return service.detail(db, user.id, order_id)


@router.patch("/vendor/orders/{order_id}/preparing", response_model=OrderDetail)
def preparing(order_id: OrderId, db: Database, user: Vendor):
    service.transition_order(db, order_id, user.id, OrderStatus.PREPARING)
    return service.detail(db, user.id, order_id)


@router.patch("/vendor/orders/{order_id}/delivering", response_model=OrderDetail)
def delivering(order_id: OrderId, db: Database, user: Vendor):
    service.transition_order(db, order_id, user.id, OrderStatus.DELIVERING)
    return service.detail(db, user.id, order_id)


@router.patch("/vendor/orders/{order_id}/complete", response_model=OrderDetail)
def complete(order_id: OrderId, db: Database, user: Vendor):
    service.transition_order(db, order_id, user.id, OrderStatus.COMPLETED)
    return service.detail(db, user.id, order_id)
