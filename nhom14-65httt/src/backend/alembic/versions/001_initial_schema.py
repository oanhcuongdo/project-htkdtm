"""Initial schema for the 15 OLTP tables in design step F.5.

Revision ID: 001
Revises: none
Create Date: 2026-11-26 17:53:01.522211
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Frozen operations: do not import application models in this revision.
    op.create_table(
        "canonical_dishes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("region", sa.String(length=40), nullable=False),
        sa.Column("spice_level", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("method", sa.String(length=40), nullable=False),
        sa.Column(
            "ingredients",
            sa.JSON(none_as_null=True),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "labels", sa.JSON(none_as_null=True), server_default=sa.text("'[]'"), nullable=False
        ),
        sa.Column("source_id", sa.String(length=120), nullable=True),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint(
            "length(trim(method)) BETWEEN 1 AND 40", name="ck_canonical_dishes_method"
        ),
        sa.CheckConstraint("length(trim(name)) BETWEEN 1 AND 180", name="ck_canonical_dishes_name"),
        sa.CheckConstraint(
            "length(trim(region)) BETWEEN 1 AND 40", name="ck_canonical_dishes_region"
        ),
        sa.CheckConstraint(
            "source_id IS NULL OR length(trim(source_id)) BETWEEN 1 AND 120",
            name="ck_canonical_dishes_source_id",
        ),
        sa.CheckConstraint("spice_level BETWEEN 0 AND 3", name="ck_canonical_dishes_spice_level"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_canonical_dishes_name"),
        sa.UniqueConstraint("source_id", name="uq_canonical_dishes_source_id"),
    )
    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint("length(trim(name)) BETWEEN 1 AND 100", name="ck_ingredients_name"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_ingredients_name"),
    )
    op.create_table(
        "restaurants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("delivery_radius_km", sa.Float(), server_default=sa.text("5"), nullable=False),
        sa.Column("opens_at", sa.Time(), server_default=sa.text("'00:00:00'"), nullable=False),
        sa.Column("closes_at", sa.Time(), server_default=sa.text("'00:00:00'"), nullable=False),
        sa.Column("accepting_orders", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "approved",
                "suspended",
                name="ck_restaurants_status",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint(
            "delivery_radius_km > 0 AND delivery_radius_km <= 50",
            name="ck_restaurants_delivery_radius",
        ),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_restaurants_latitude"),
        sa.CheckConstraint(
            "length(trim(address)) BETWEEN 1 AND 500", name="ck_restaurants_address"
        ),
        sa.CheckConstraint("length(trim(name)) BETWEEN 1 AND 160", name="ck_restaurants_name"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_restaurants_longitude"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("hashed_password", sa.String(length=256), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "customer",
                "vendor",
                "admin",
                name="ck_users_role",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            server_default="customer",
            nullable=False,
        ),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "menu_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("canonical_dish_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("ingredients_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint("length(trim(name)) BETWEEN 1 AND 180", name="ck_menu_items_name"),
        sa.CheckConstraint("price > 0 AND price <= 10000000", name="ck_menu_items_price"),
        sa.ForeignKeyConstraint(
            ["canonical_dish_id"], ["canonical_dishes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_menu_items_canonical_dish_id"), "menu_items", ["canonical_dish_id"], unique=False
    )
    op.create_index(
        op.f("ix_menu_items_restaurant_id"), "menu_items", ["restaurant_id"], unique=False
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "confirmed",
                "preparing",
                "delivering",
                "completed",
                "cancelled",
                "rejected",
                name="ck_orders_status",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("total", sa.BigInteger(), nullable=False),
        sa.Column("delivery_address", sa.String(length=500), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_orders_latitude"),
        sa.CheckConstraint("length(payload_hash) = 64", name="ck_orders_payload_hash"),
        sa.CheckConstraint(
            "length(trim(delivery_address)) BETWEEN 5 AND 500", name="ck_orders_delivery_address"
        ),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_orders_longitude"),
        sa.CheckConstraint("total > 0", name="ck_orders_total"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_orders_idempotency_key"),
    )
    op.create_index(op.f("ix_orders_restaurant_id"), "orders", ["restaurant_id"], unique=False)
    op.create_index(op.f("ix_orders_session_id"), "orders", ["session_id"], unique=False)
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)
    op.create_table(
        "preferences",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "regions", sa.JSON(none_as_null=True), server_default=sa.text("'[]'"), nullable=False
        ),
        sa.Column("spice_level", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "liked_ingredients",
            sa.JSON(none_as_null=True),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "avoided_ingredients",
            sa.JSON(none_as_null=True),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column("exploration_level", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "exploration_level BETWEEN 0 AND 2", name="ck_preferences_exploration_level"
        ),
        sa.CheckConstraint("spice_level BETWEEN 0 AND 3", name="ck_preferences_spice_level"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "recommendation_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint(
            "length(trim(algorithm_version)) BETWEEN 1 AND 40",
            name="ck_rec_requests_algorithm_version",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "user_id", "session_id", name="uq_rec_requests_owner_session"),
    )
    op.create_index(
        op.f("ix_recommendation_requests_session_id"),
        "recommendation_requests",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendation_requests_user_id"),
        "recommendation_requests",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "restaurant_memberships",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_restaurant_memberships_restaurant_id"),
        "restaurant_memberships",
        ["restaurant_id"],
        unique=False,
    )
    op.create_table(
        "menu_item_ingredients",
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("menu_item_id", "ingredient_id"),
    )
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("snapshot_price", sa.Integer(), nullable=False),
        sa.Column("snapshot_name", sa.String(length=180), nullable=False),
        sa.CheckConstraint(
            "length(trim(snapshot_name)) BETWEEN 1 AND 180", name="ck_order_items_snapshot_name"
        ),
        sa.CheckConstraint("quantity BETWEEN 1 AND 99", name="ck_order_items_quantity"),
        sa.CheckConstraint(
            "snapshot_price > 0 AND snapshot_price <= 10000000",
            name="ck_order_items_snapshot_price",
        ),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "menu_item_id", name="uq_order_items_order_menu_item"),
    )
    op.create_index(
        op.f("ix_order_items_menu_item_id"), "order_items", ["menu_item_id"], unique=False
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_table(
        "order_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "confirmed",
                "preparing",
                "delivering",
                "completed",
                "cancelled",
                "rejected",
                name="ck_order_history_status",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status <> 'rejected' OR reason IS NOT NULL", name="ck_order_history_rejection_reason"
        ),
        sa.CheckConstraint(
            "reason IS NULL OR length(trim(reason)) BETWEEN 1 AND 500",
            name="ck_order_history_reason",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_order_status_history_actor_id"), "order_status_history", ["actor_id"], unique=False
    )
    op.create_index(
        op.f("ix_order_status_history_order_id"), "order_status_history", ["order_id"], unique=False
    )
    op.create_table(
        "recommendation_impressions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("displayed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint("rank BETWEEN 1 AND 5", name="ck_rec_impressions_rank"),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["request_id"], ["recommendation_requests.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id", "menu_item_id", name="uq_rec_impressions_request_item"),
        sa.UniqueConstraint("request_id", "rank", name="uq_rec_impressions_request_rank"),
    )
    op.create_index(
        op.f("ix_recommendation_impressions_menu_item_id"),
        "recommendation_impressions",
        ["menu_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendation_impressions_request_id"),
        "recommendation_impressions",
        ["request_id"],
        unique=False,
    )
    op.create_table(
        "interaction_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "impression",
                "click",
                "add_to_cart",
                "feedback",
                "session_start",
                "session_end",
                name="ck_interaction_events_type",
                native_enum=False,
                create_constraint=True,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("request_id", sa.Uuid(), nullable=True),
        sa.Column("menu_item_id", sa.Integer(), nullable=True),
        sa.Column("value", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint(
            "(event_type = 'feedback' AND value IS NOT NULL AND value IN (0, 1)) "
            "OR (event_type <> 'feedback' AND value IS NULL)",
            name="ck_interaction_events_feedback",
        ),
        sa.CheckConstraint(
            "(event_type IN ('impression', 'click', 'feedback') "
            "AND request_id IS NOT NULL AND menu_item_id IS NOT NULL) "
            "OR (event_type = 'add_to_cart' AND menu_item_id IS NOT NULL) "
            "OR (event_type IN ('session_start', 'session_end') "
            "AND request_id IS NULL AND menu_item_id IS NULL)",
            name="ck_interaction_events_context",
        ),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["request_id", "menu_item_id"],
            ["recommendation_impressions.request_id", "recommendation_impressions.menu_item_id"],
            name="fk_interaction_events_impression",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["request_id", "user_id", "session_id"],
            [
                "recommendation_requests.id",
                "recommendation_requests.user_id",
                "recommendation_requests.session_id",
            ],
            name="fk_interaction_events_request_owner",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        op.f("ix_interaction_events_menu_item_id"),
        "interaction_events",
        ["menu_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_interaction_events_request_id"), "interaction_events", ["request_id"], unique=False
    )
    op.create_index(
        op.f("ix_interaction_events_session_id"), "interaction_events", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_interaction_events_user_id"), "interaction_events", ["user_id"], unique=False
    )
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column(
            "comment", sa.String(length=2000), server_default=sa.text("('')"), nullable=False
        ),
        sa.Column("is_simulated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint("length(comment) <= 2000", name="ck_reviews_comment"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["order_id", "menu_item_id"],
            ["order_items.order_id", "order_items.menu_item_id"],
            name="fk_reviews_purchased_item",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "menu_item_id", name="uq_reviews_order_menu_item"),
    )
    op.create_index(op.f("ix_reviews_menu_item_id"), "reviews", ["menu_item_id"], unique=False)
    op.create_index(op.f("ix_reviews_order_id"), "reviews", ["order_id"], unique=False)
    op.create_index(op.f("ix_reviews_user_id"), "reviews", ["user_id"], unique=False)


def downgrade() -> None:
    # Frozen operations: do not import application models in this revision.
    op.drop_index(op.f("ix_reviews_user_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_order_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_menu_item_id"), table_name="reviews")
    op.drop_table("reviews")
    op.drop_index(op.f("ix_interaction_events_user_id"), table_name="interaction_events")
    op.drop_index(op.f("ix_interaction_events_session_id"), table_name="interaction_events")
    op.drop_index(op.f("ix_interaction_events_request_id"), table_name="interaction_events")
    op.drop_index(op.f("ix_interaction_events_menu_item_id"), table_name="interaction_events")
    op.drop_table("interaction_events")
    op.drop_index(
        op.f("ix_recommendation_impressions_request_id"), table_name="recommendation_impressions"
    )
    op.drop_index(
        op.f("ix_recommendation_impressions_menu_item_id"), table_name="recommendation_impressions"
    )
    op.drop_table("recommendation_impressions")
    op.drop_index(op.f("ix_order_status_history_order_id"), table_name="order_status_history")
    op.drop_index(op.f("ix_order_status_history_actor_id"), table_name="order_status_history")
    op.drop_table("order_status_history")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_menu_item_id"), table_name="order_items")
    op.drop_table("order_items")
    op.drop_table("menu_item_ingredients")
    op.drop_index(
        op.f("ix_restaurant_memberships_restaurant_id"), table_name="restaurant_memberships"
    )
    op.drop_table("restaurant_memberships")
    op.drop_index(op.f("ix_recommendation_requests_user_id"), table_name="recommendation_requests")
    op.drop_index(
        op.f("ix_recommendation_requests_session_id"), table_name="recommendation_requests"
    )
    op.drop_table("recommendation_requests")
    op.drop_table("preferences")
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_session_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_restaurant_id"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_menu_items_restaurant_id"), table_name="menu_items")
    op.drop_index(op.f("ix_menu_items_canonical_dish_id"), table_name="menu_items")
    op.drop_table("menu_items")
    op.drop_table("users")
    op.drop_table("restaurants")
    op.drop_table("ingredients")
    op.drop_table("canonical_dishes")
