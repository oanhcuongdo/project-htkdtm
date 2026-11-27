"""Luồng E.2, quyền sở hữu, lịch sử nguyên tử và bảo vệ cập nhật cạnh tranh."""

from uuid import uuid4

import pytest
from sqlalchemy import event, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.exceptions import AppError, ForbiddenError, InvalidStateTransitionError, NotFoundError
from app.orders.models import Order, OrderStatus, OrderStatusHistory
from app.orders.service import transition_order
from app.orders.state_machine import validate_transition
from app.users.models import User, UserRole

EDGES = {
    ("pending", "confirmed"): "vendor",
    ("pending", "rejected"): "vendor",
    ("pending", "cancelled"): "customer",
    ("confirmed", "preparing"): "vendor",
    ("preparing", "delivering"): "vendor",
    ("delivering", "completed"): "vendor",
}


@pytest.mark.parametrize("current", list(OrderStatus))
@pytest.mark.parametrize("target", list(OrderStatus))
@pytest.mark.parametrize("role", list(UserRole))
def test_all_state_and_role_combinations(current, target, role):
    expected = EDGES.get((current.value, target.value))
    if expected is None:
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(current, target, role)
    elif expected != role:
        with pytest.raises(ForbiddenError):
            validate_transition(current, target, role)
    else:
        validate_transition(current, target, role)


@pytest.fixture
def order_db(restaurant_api):
    _, engine = restaurant_api
    with Session(engine) as db:
        db.add_all(
            [
                Order(
                    id=i,
                    user_id=1,
                    restaurant_id=rid,
                    total=40000,
                    delivery_address="Hà Nội",
                    latitude=21,
                    longitude=105,
                    session_id=uuid4(),
                    idempotency_key=uuid4(),
                    payload_hash="a" * 64,
                )
                for i, rid in [(1, 1), (2, 2)]
            ]
        )
        db.flush()
        db.add(OrderStatusHistory(order_id=1, status="pending", actor_id=1))
        db.commit()
    return engine


def history(db, oid=1):
    return db.scalars(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == oid)
        .order_by(OrderStatusHistory.id)
    ).all()


def test_full_vendor_lifecycle_records_actor_and_preserves_order_data(order_db):
    with Session(order_db) as db:
        for target, actor in [
            ("confirmed", 2),
            ("preparing", 7),
            ("delivering", 2),
            ("completed", 7),
        ]:
            row = transition_order(db, 1, actor, OrderStatus(target))
            assert row.status == target
            assert row.total == 40000 and row.user_id == 1 and row.restaurant_id == 1
        rows = history(db)
        assert [r.status for r in rows] == [
            "pending",
            "confirmed",
            "preparing",
            "delivering",
            "completed",
        ]
        assert [r.actor_id for r in rows] == [1, 2, 7, 2, 7]
        assert all(r.reason is None and r.created_at is not None for r in rows)


@pytest.mark.parametrize(
    "actor,target,reason", [(1, "cancelled", None), (2, "rejected", "  Hết nguyên liệu  ")]
)
def test_pending_terminal_actions(order_db, actor, target, reason):
    with Session(order_db) as db:
        transition_order(db, 1, actor, OrderStatus(target), reason=reason)
        assert history(db)[-1].reason == (reason.strip() if reason else None)
        with pytest.raises(InvalidStateTransitionError):
            transition_order(db, 1, actor, OrderStatus(target), reason=reason)
        assert len(history(db)) == 2


@pytest.mark.parametrize(
    "actor,oid,error",
    [
        (3, 1, ForbiddenError),
        (999, 1, ForbiddenError),
        (4, 1, NotFoundError),
        (5, 1, NotFoundError),
        (6, 1, NotFoundError),
        (2, 999, NotFoundError),
    ],
)
def test_forbidden_or_foreign_order_leaves_no_history(order_db, actor, oid, error):
    with Session(order_db) as db:
        with pytest.raises(error):
            transition_order(db, oid, actor, OrderStatus.CONFIRMED)
        assert db.get(Order, 1).status == "pending"
        assert len(history(db)) == 1


def test_customer_cannot_cancel_another_customers_order(order_db):
    with Session(order_db) as db:
        db.add(
            User(
                id=10,
                email="another@example.vn",
                full_name="Khách khác",
                role="customer",
                hashed_password="fixture-unused",
            )
        )
        db.commit()
        with pytest.raises(NotFoundError):
            transition_order(db, 1, 10, OrderStatus.CANCELLED)
        assert len(history(db)) == 1


@pytest.mark.parametrize("reason", [None, "", "   ", "x" * 501, 123])
def test_rejection_requires_valid_reason(order_db, reason):
    with Session(order_db) as db:
        with pytest.raises(AppError) as exc:
            transition_order(db, 1, 2, OrderStatus.REJECTED, reason=reason)
        assert exc.value.code == "INVALID_REJECTION_REASON"
        assert db.get(Order, 1).status == "pending" and len(history(db)) == 1


def test_reason_not_accepted_on_other_actions(order_db):
    with Session(order_db) as db:
        with pytest.raises(AppError) as exc:
            transition_order(db, 1, 1, OrderStatus.CANCELLED, reason="Lý do")
        assert exc.value.code == "UNEXPECTED_ORDER_REASON"
        assert db.get(Order, 1).status == "pending"


def test_current_db_role_and_state_override_cached_objects(order_db):
    with Session(order_db) as db:
        actor = db.get(User, 2)
        order = db.get(Order, 1)
        with Session(order_db) as other:
            other.execute(update(User).where(User.id == 2).values(role="customer"))
            other.execute(update(Order).where(Order.id == 1).values(status="cancelled"))
            other.commit()
        assert actor.role == "vendor" and order.status == "pending"
        with pytest.raises(NotFoundError):
            transition_order(db, 1, 2, OrderStatus.CONFIRMED)
        with pytest.raises(InvalidStateTransitionError):
            transition_order(db, 1, 1, OrderStatus.CANCELLED)
        assert db.get(Order, 1).status == "cancelled" and len(history(db)) == 1


@pytest.mark.parametrize("failure", ["history", "commit"])
def test_transaction_failure_rolls_back_status_and_history(order_db, monkeypatch, failure):
    def fail_insert(_conn, _cursor, statement, _params, _context, _many):
        if statement.startswith("INSERT INTO order_status_history"):
            raise OperationalError(statement, {}, RuntimeError("injected history failure"))

    with Session(order_db) as db:
        if failure == "history":
            event.listen(order_db, "before_cursor_execute", fail_insert)
        else:

            def fail_commit():
                db.flush()
                raise OperationalError("commit", {}, RuntimeError("injected commit failure"))

            monkeypatch.setattr(db, "commit", fail_commit)
        try:
            with pytest.raises(OperationalError):
                transition_order(db, 1, 2, OrderStatus.CONFIRMED)
        finally:
            if failure == "history":
                event.remove(order_db, "before_cursor_execute", fail_insert)
        assert db.get(Order, 1).status == "pending" and len(history(db)) == 1


def test_conditional_update_rejects_competing_state_change(order_db):
    # Mô phỏng thay đổi sau đọc/kiểm tra trên cùng kết nối; không phải test tải PostgreSQL.
    def compete(conn, _cursor, statement, _params, _context, _many):
        if statement.startswith("UPDATE orders SET status="):
            conn.exec_driver_sql("UPDATE orders SET status = 'cancelled' WHERE id = 1")

    event.listen(order_db, "before_cursor_execute", compete)
    try:
        with Session(order_db) as db:
            with pytest.raises(AppError) as exc:
                transition_order(db, 1, 2, OrderStatus.CONFIRMED)
            assert exc.value.code == "ORDER_STATE_CHANGED"
            assert len(history(db)) == 1
    finally:
        event.remove(order_db, "before_cursor_execute", compete)
