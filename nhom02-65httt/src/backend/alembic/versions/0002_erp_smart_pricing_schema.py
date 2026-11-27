"""Create ERP, market, smart pricing, ML run, and audit log tables.

Revision ID: 0002_erp_smart_pricing_schema
Revises: 0001_create_users
Create Date: 2026-11-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_erp_smart_pricing_schema"
down_revision: str | Sequence[str] | None = "0001_create_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
    )
    op.create_index(op.f("ix_categories_code"), "categories", ["code"], unique=True)

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("supplier_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("contact_name", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column("last_quoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name=op.f("ck_suppliers_status_valid"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_suppliers")),
    )
    op.create_index(op.f("ix_suppliers_supplier_code"), "suppliers", ["supplier_code"], unique=True)

    op.create_table(
        "sales_channels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "integration_mode",
            sa.String(length=16),
            server_default=sa.text("'SIMULATED'"),
            nullable=False,
        ),
        sa.Column(
            "connection_status",
            sa.String(length=24),
            server_default=sa.text("'DEMO'"),
            nullable=False,
        ),
        sa.Column(
            "platform_fee_rate",
            sa.Numeric(precision=6, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "payment_fee_rate",
            sa.Numeric(precision=6, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "service_fee_rate",
            sa.Numeric(precision=6, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column(
            "fee_rate",
            sa.Numeric(precision=6, scale=4),
            server_default=sa.text("0.0000"),
            nullable=False,
        ),
        sa.Column("fee_effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fee_source", sa.String(length=150), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "code IN ('SHOPEE', 'LAZADA', 'TIKTOK_SHOP', 'TIKI', 'WEBSITE', 'OTHER')",
            name=op.f("ck_sales_channels_code_valid"),
        ),
        sa.CheckConstraint(
            "integration_mode IN ('SIMULATED', 'LIVE')",
            name=op.f("ck_sales_channels_integration_mode_valid"),
        ),
        sa.CheckConstraint(
            "connection_status IN ('NOT_CONNECTED', 'DEMO', 'CONNECTED', 'ERROR', 'DISABLED')",
            name=op.f("ck_sales_channels_connection_status_valid"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_channels")),
    )
    op.create_index(op.f("ix_sales_channels_code"), "sales_channels", ["code"], unique=True)

    op.create_table(
        "model_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("algorithm_type", sa.String(length=32), nullable=False),
        sa.Column("feature_columns_json", sa.JSON(), nullable=False),
        sa.Column("train_samples", sa.Integer(), nullable=False),
        sa.Column("test_samples", sa.Integer(), nullable=False),
        sa.Column("mae", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("rmse", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("artifact_path", sa.String(length=500), nullable=True),
        sa.Column(
            "trained_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_runs")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor", sa.String(length=150), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("before_summary", sa.Text(), nullable=True),
        sa.Column("after_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_request_id"), "audit_logs", ["request_id"], unique=False)
    op.create_index(
        op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sku_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("variant_name", sa.String(length=150), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("model_code", sa.String(length=100), nullable=True),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("primary_supplier_id", sa.Uuid(), nullable=True),
        sa.Column("unit", sa.String(length=32), server_default=sa.text("'Cái'"), nullable=False),
        sa.Column("current_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'ARCHIVED')",
            name=op.f("ck_products_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_products_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["primary_supplier_id"],
            ["suppliers.id"],
            name=op.f("fk_products_primary_supplier_id_suppliers"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
    )
    op.create_index(op.f("ix_products_category_id"), "products", ["category_id"], unique=False)
    op.create_index(op.f("ix_products_model_code"), "products", ["model_code"], unique=False)
    op.create_index(
        op.f("ix_products_primary_supplier_id"), "products", ["primary_supplier_id"], unique=False
    )
    op.create_index(op.f("ix_products_sku_code"), "products", ["sku_code"], unique=True)

    op.create_table(
        "supplier_products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("supplier_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_sku", sa.String(length=100), nullable=True),
        sa.Column("purchase_cost", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("min_order_qty", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column("last_quoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_preferred", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_supplier_products_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
            name=op.f("fk_supplier_products_supplier_id_suppliers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_supplier_products")),
        sa.UniqueConstraint(
            "supplier_id",
            "product_id",
            name=op.f("uq_supplier_products_supplier_product"),
        ),
    )

    op.create_table(
        "cost_components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column(
            "purchase_cost",
            sa.Numeric(precision=15, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "inbound_cost",
            sa.Numeric(precision=15, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "packaging_cost",
            sa.Numeric(precision=15, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "other_cost",
            sa.Numeric(precision=15, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_cost_components_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cost_components")),
        sa.UniqueConstraint("product_id", name=op.f("uq_cost_components_product_id")),
    )

    op.create_table(
        "inventory",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column(
            "warehouse_name",
            sa.String(length=150),
            server_default=sa.text("'Kho tổng'"),
            nullable=False,
        ),
        sa.Column("on_hand_qty", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("reserved_qty", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("reorder_point", sa.Integer(), server_default=sa.text("10"), nullable=False),
        sa.Column("days_of_supply", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("on_hand_qty >= 0", name=op.f("ck_inventory_on_hand_non_negative")),
        sa.CheckConstraint("reserved_qty >= 0", name=op.f("ck_inventory_reserved_non_negative")),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_inventory_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory")),
        sa.UniqueConstraint("product_id", name=op.f("uq_inventory_product_id")),
    )

    op.create_table(
        "channel_products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("external_listing_id", sa.String(length=120), nullable=False),
        sa.Column("external_sku", sa.String(length=120), nullable=False),
        sa.Column("external_url", sa.String(length=500), nullable=True),
        sa.Column("current_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column(
            "sync_status",
            sa.String(length=16),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sync_status IN ('SYNCED', 'PENDING', 'ERROR', 'NOT_MAPPED')",
            name=op.f("ck_channel_products_sync_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["sales_channels.id"],
            name=op.f("fk_channel_products_channel_id_sales_channels"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_channel_products_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_channel_products")),
        sa.UniqueConstraint(
            "product_id", "channel_id", name=op.f("uq_channel_products_product_channel")
        ),
    )

    op.create_table(
        "competitor_prices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("sku_code", sa.String(length=64), nullable=True),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("competitor_name", sa.String(length=150), nullable=False),
        sa.Column("marketplace_code", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=24), nullable=False),
        sa.Column("source_name", sa.String(length=150), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("external_item_id", sa.String(length=120), nullable=True),
        sa.Column("raw_title", sa.String(length=500), nullable=True),
        sa.Column("extracted_model_code", sa.String(length=100), nullable=True),
        sa.Column("listed_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("effective_price", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("sold_count", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column(
            "confidence",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("1.00"),
            nullable=False,
        ),
        sa.Column(
            "match_status",
            sa.String(length=24),
            server_default=sa.text("'AUTO_MATCHED'"),
            nullable=False,
        ),
        sa.Column("verdict", sa.String(length=100), nullable=True),
        sa.Column(
            "fake_sale_warning", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("is_outlier", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source_type IN ('MANUAL', 'CSV', 'API', 'PUBLIC_PAGE', 'DEMO')",
            name=op.f("ck_competitor_prices_source_type_valid"),
        ),
        sa.CheckConstraint(
            "match_status IN ('AUTO_MATCHED', 'NEEDS_REVIEW', 'REJECTED')",
            name=op.f("ck_competitor_prices_match_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_competitor_prices_product_id_products"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_competitor_prices")),
    )
    op.create_index(
        op.f("ix_competitor_prices_marketplace_code"),
        "competitor_prices",
        ["marketplace_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_competitor_prices_observed_at"),
        "competitor_prices",
        ["observed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_competitor_prices_product_id"),
        "competitor_prices",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_competitor_prices_sku_code"), "competitor_prices", ["sku_code"], unique=False
    )

    op.create_table(
        "competitor_price_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("competitor_price_id", sa.Uuid(), nullable=False),
        sa.Column("recorded_date", sa.Date(), nullable=False),
        sa.Column("price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["competitor_price_id"],
            ["competitor_prices.id"],
            name=op.f("fk_competitor_price_history_competitor_price_id_competitor_prices"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_competitor_price_history")),
        sa.UniqueConstraint(
            "competitor_price_id",
            "recorded_date",
            name=op.f("uq_competitor_price_history_competitor_price_date"),
        ),
    )
    op.create_index(
        op.f("ix_competitor_price_history_competitor_price_id"),
        "competitor_price_history",
        ["competitor_price_id"],
        unique=False,
    )

    op.create_table(
        "sales_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("gross_revenue", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("channel_fee_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("net_profit", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["sales_channels.id"],
            name=op.f("fk_sales_records_channel_id_sales_channels"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_sales_records_product_id_products"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_records")),
    )
    op.create_index(
        op.f("ix_sales_records_channel_id"), "sales_records", ["channel_id"], unique=False
    )
    op.create_index(
        op.f("ix_sales_records_order_date"), "sales_records", ["order_date"], unique=False
    )
    op.create_index(
        op.f("ix_sales_records_product_id"), "sales_records", ["product_id"], unique=False
    )

    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("rule_type", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), server_default=sa.text("100"), nullable=False),
        sa.Column("scope_label", sa.String(length=200), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("channel_id", sa.Uuid(), nullable=True),
        sa.Column("min_margin", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("max_price_change_pct", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column(
            "approval_required", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'DRAFT'"),
            nullable=False,
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rule_type IN ('FLASH_SALE', 'SKIMMING', 'CLEARANCE', "
            "'COMPETITOR_MATCH', 'MARGIN_GUARD')",
            name=op.f("ck_pricing_rules_rule_type_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'ARCHIVED')",
            name=op.f("ck_pricing_rules_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_pricing_rules_category_id_categories"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["sales_channels.id"],
            name=op.f("fk_pricing_rules_channel_id_sales_channels"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pricing_rules")),
    )

    op.create_table(
        "price_recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=24),
            server_default=sa.text("'DRAFT'"),
            nullable=False,
        ),
        sa.Column("current_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("floor_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("recommended_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("expected_profit_per_unit", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("expected_margin", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("channel_fee_rate", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("competitor_median", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("target_margin", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("predicted_demand", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "data_quality", sa.String(length=16), server_default=sa.text("'HIGH'"), nullable=False
        ),
        sa.Column(
            "algorithm_type",
            sa.String(length=24),
            server_default=sa.text("'RULE_BASED'"),
            nullable=False,
        ),
        sa.Column("algorithm_version", sa.String(length=64), nullable=False),
        sa.Column("explanation_json", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=150), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'EXECUTION_QUEUED', "
            "'EXECUTED', 'REJECTED', 'EXPIRED', 'FAILED', 'CANCELLED')",
            name=op.f("ck_price_recommendations_status_valid"),
        ),
        sa.CheckConstraint(
            "data_quality IN ('HIGH', 'MEDIUM', 'LOW')",
            name=op.f("ck_price_recommendations_data_quality_valid"),
        ),
        sa.CheckConstraint(
            "algorithm_type IN ('RULE_BASED', 'ML_ASSISTED')",
            name=op.f("ck_price_recommendations_algorithm_type_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["sales_channels.id"],
            name=op.f("fk_price_recommendations_channel_id_sales_channels"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_price_recommendations_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["pricing_rules.id"],
            name=op.f("fk_price_recommendations_rule_id_pricing_rules"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_price_recommendations")),
    )
    op.create_index(
        op.f("ix_price_recommendations_channel_id"),
        "price_recommendations",
        ["channel_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_price_recommendations_product_id"),
        "price_recommendations",
        ["product_id"],
        unique=False,
    )

    op.create_table(
        "price_approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("reviewer_name", sa.String(length=150), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("adjusted_price", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "decision IN ('APPROVED', 'REJECTED')",
            name=op.f("ck_price_approvals_decision_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["price_recommendations.id"],
            name=op.f("fk_price_approvals_recommendation_id_price_recommendations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
            name=op.f("fk_price_approvals_reviewer_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_price_approvals")),
    )
    op.create_index(
        op.f("ix_price_approvals_recommendation_id"),
        "price_approvals",
        ["recommendation_id"],
        unique=False,
    )

    op.create_table(
        "price_sync_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_id", sa.Uuid(), nullable=True),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("channel_id", sa.Uuid(), nullable=True),
        sa.Column("sku_code", sa.String(length=64), nullable=False),
        sa.Column("channel_code", sa.String(length=32), nullable=False),
        sa.Column("channel_name", sa.String(length=100), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("sync_mode", sa.String(length=16), nullable=False),
        sa.Column("requested_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("previous_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'QUEUED'"),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("external_reference", sa.String(length=120), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "mode IN ('SIMULATED', 'LIVE')",
            name=op.f("ck_price_sync_logs_mode_valid"),
        ),
        sa.CheckConstraint(
            "sync_mode IN ('SIMULATED', 'API_CONFIRMED')",
            name=op.f("ck_price_sync_logs_sync_mode_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'PARTIAL', 'FAILED', 'CANCELLED')",
            name=op.f("ck_price_sync_logs_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["sales_channels.id"],
            name=op.f("fk_price_sync_logs_channel_id_sales_channels"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_price_sync_logs_product_id_products"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["price_recommendations.id"],
            name=op.f("fk_price_sync_logs_recommendation_id_price_recommendations"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_price_sync_logs")),
    )
    op.create_index(
        op.f("ix_price_sync_logs_channel_id"), "price_sync_logs", ["channel_id"], unique=False
    )
    op.create_index(
        op.f("ix_price_sync_logs_idempotency_key"),
        "price_sync_logs",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_price_sync_logs_product_id"), "price_sync_logs", ["product_id"], unique=False
    )
    op.create_index(
        op.f("ix_price_sync_logs_recommendation_id"),
        "price_sync_logs",
        ["recommendation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_price_sync_logs_sku_code"), "price_sync_logs", ["sku_code"], unique=False
    )
    op.create_index(
        op.f("ix_price_sync_logs_status"), "price_sync_logs", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_price_sync_logs_status"), table_name="price_sync_logs")
    op.drop_index(op.f("ix_price_sync_logs_sku_code"), table_name="price_sync_logs")
    op.drop_index(op.f("ix_price_sync_logs_recommendation_id"), table_name="price_sync_logs")
    op.drop_index(op.f("ix_price_sync_logs_product_id"), table_name="price_sync_logs")
    op.drop_index(op.f("ix_price_sync_logs_idempotency_key"), table_name="price_sync_logs")
    op.drop_index(op.f("ix_price_sync_logs_channel_id"), table_name="price_sync_logs")
    op.drop_table("price_sync_logs")

    op.drop_index(op.f("ix_price_approvals_recommendation_id"), table_name="price_approvals")
    op.drop_table("price_approvals")

    op.drop_index(op.f("ix_price_recommendations_product_id"), table_name="price_recommendations")
    op.drop_index(op.f("ix_price_recommendations_channel_id"), table_name="price_recommendations")
    op.drop_table("price_recommendations")

    op.drop_table("pricing_rules")

    op.drop_index(op.f("ix_sales_records_product_id"), table_name="sales_records")
    op.drop_index(op.f("ix_sales_records_order_date"), table_name="sales_records")
    op.drop_index(op.f("ix_sales_records_channel_id"), table_name="sales_records")
    op.drop_table("sales_records")

    op.drop_index(
        op.f("ix_competitor_price_history_competitor_price_id"),
        table_name="competitor_price_history",
    )
    op.drop_table("competitor_price_history")

    op.drop_index(op.f("ix_competitor_prices_sku_code"), table_name="competitor_prices")
    op.drop_index(op.f("ix_competitor_prices_product_id"), table_name="competitor_prices")
    op.drop_index(op.f("ix_competitor_prices_observed_at"), table_name="competitor_prices")
    op.drop_index(op.f("ix_competitor_prices_marketplace_code"), table_name="competitor_prices")
    op.drop_table("competitor_prices")

    op.drop_table("channel_products")
    op.drop_table("inventory")
    op.drop_table("cost_components")
    op.drop_table("supplier_products")

    op.drop_index(op.f("ix_products_sku_code"), table_name="products")
    op.drop_index(op.f("ix_products_primary_supplier_id"), table_name="products")
    op.drop_index(op.f("ix_products_model_code"), table_name="products")
    op.drop_index(op.f("ix_products_category_id"), table_name="products")
    op.drop_table("products")

    op.drop_index(op.f("ix_audit_logs_resource_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_request_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_table("model_runs")

    op.drop_index(op.f("ix_sales_channels_code"), table_name="sales_channels")
    op.drop_table("sales_channels")

    op.drop_index(op.f("ix_suppliers_supplier_code"), table_name="suppliers")
    op.drop_table("suppliers")

    op.drop_index(op.f("ix_categories_code"), table_name="categories")
    op.drop_table("categories")
