-- =============================================================================
-- ERP Smart Pricing Multi-Channel (PostgreSQL 15 Reference Schema)
-- Dong bo 100% voi SQLAlchemy ORM models & Alembic migrations (0001 + 0002).
-- Luu y: Alembic la nguon chan ly (source of truth) khi chay Docker / migrate.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- NHOM 1: QUAN TRI HE THONG & AUDIT
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL CHECK (
        role IN ('ADMIN', 'MANAGER', 'PRICING_ANALYST', 'INVENTORY_STAFF', 'VIEWER')
    ),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    actor VARCHAR(150) NOT NULL,
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    reason TEXT NULL,
    request_id VARCHAR(64) NOT NULL,
    before_summary TEXT NULL,
    after_summary TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_resource_type ON audit_logs (resource_type);
CREATE INDEX IF NOT EXISTS ix_audit_logs_request_id ON audit_logs (request_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);

-- -----------------------------------------------------------------------------
-- NHOM 2: DANH MUC, NGUON CUNG, GIA VON & TON KHO (ERP LOI)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY,
    supplier_code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(150) NULL,
    email VARCHAR(255) NULL,
    phone VARCHAR(32) NULL,
    lead_time_days INTEGER NOT NULL DEFAULT 3,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    last_quoted_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY,
    sku_code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    variant_name VARCHAR(150) NULL,
    brand VARCHAR(100) NULL,
    model_code VARCHAR(100) NULL,
    category_id UUID NOT NULL REFERENCES categories (id) ON DELETE RESTRICT,
    primary_supplier_id UUID NULL REFERENCES suppliers (id) ON DELETE SET NULL,
    unit VARCHAR(32) NOT NULL DEFAULT 'Cái',
    current_price NUMERIC(15, 2) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ARCHIVED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_products_category_id ON products (category_id);
CREATE INDEX IF NOT EXISTS ix_products_model_code ON products (model_code);
CREATE INDEX IF NOT EXISTS ix_products_primary_supplier_id ON products (primary_supplier_id);

CREATE TABLE IF NOT EXISTS supplier_products (
    id UUID PRIMARY KEY,
    supplier_id UUID NOT NULL REFERENCES suppliers (id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    supplier_sku VARCHAR(100) NULL,
    purchase_cost NUMERIC(15, 2) NOT NULL,
    min_order_qty INTEGER NOT NULL DEFAULT 1,
    lead_time_days INTEGER NOT NULL DEFAULT 3,
    last_quoted_at TIMESTAMPTZ NULL,
    is_preferred BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (supplier_id, product_id)
);

CREATE TABLE IF NOT EXISTS cost_components (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL UNIQUE REFERENCES products (id) ON DELETE CASCADE,
    purchase_cost NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    inbound_cost NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    packaging_cost NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    other_cost NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL UNIQUE REFERENCES products (id) ON DELETE CASCADE,
    warehouse_name VARCHAR(150) NOT NULL DEFAULT 'Kho tổng',
    on_hand_qty INTEGER NOT NULL DEFAULT 0 CHECK (on_hand_qty >= 0),
    reserved_qty INTEGER NOT NULL DEFAULT 0 CHECK (reserved_qty >= 0),
    reorder_point INTEGER NOT NULL DEFAULT 10,
    days_of_supply INTEGER NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- NHOM 3: KENH BAN & DU LIEU THI TRUONG THAT (CRAWLER + SALES)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sales_channels (
    id UUID PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE CHECK (
        code IN ('SHOPEE', 'LAZADA', 'TIKTOK_SHOP', 'TIKI', 'WEBSITE', 'OTHER')
    ),
    name VARCHAR(100) NOT NULL,
    integration_mode VARCHAR(16) NOT NULL DEFAULT 'SIMULATED' CHECK (
        integration_mode IN ('SIMULATED', 'LIVE')
    ),
    connection_status VARCHAR(24) NOT NULL DEFAULT 'DEMO' CHECK (
        connection_status IN ('NOT_CONNECTED', 'DEMO', 'CONNECTED', 'ERROR', 'DISABLED')
    ),
    platform_fee_rate NUMERIC(6, 4) NOT NULL DEFAULT 0.0000,
    payment_fee_rate NUMERIC(6, 4) NOT NULL DEFAULT 0.0000,
    service_fee_rate NUMERIC(6, 4) NOT NULL DEFAULT 0.0000,
    fee_rate NUMERIC(6, 4) NOT NULL DEFAULT 0.0000,
    fee_effective_from TIMESTAMPTZ NULL,
    fee_source VARCHAR(150) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS channel_products (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES sales_channels (id) ON DELETE CASCADE,
    external_listing_id VARCHAR(120) NOT NULL,
    external_sku VARCHAR(120) NOT NULL,
    external_url VARCHAR(500) NULL,
    current_price NUMERIC(15, 2) NOT NULL,
    sync_status VARCHAR(16) NOT NULL DEFAULT 'PENDING' CHECK (
        sync_status IN ('SYNCED', 'PENDING', 'ERROR', 'NOT_MAPPED')
    ),
    last_synced_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (product_id, channel_id)
);

CREATE TABLE IF NOT EXISTS competitor_prices (
    id UUID PRIMARY KEY,
    product_id UUID NULL REFERENCES products (id) ON DELETE SET NULL,
    sku_code VARCHAR(64) NULL,
    product_name VARCHAR(255) NOT NULL,
    competitor_name VARCHAR(150) NOT NULL,
    marketplace_code VARCHAR(32) NOT NULL,
    source_type VARCHAR(24) NOT NULL CHECK (
        source_type IN ('MANUAL', 'CSV', 'API', 'PUBLIC_PAGE', 'DEMO')
    ),
    source_name VARCHAR(150) NOT NULL,
    source_url VARCHAR(500) NULL,
    external_item_id VARCHAR(120) NULL,
    raw_title VARCHAR(500) NULL,
    extracted_model_code VARCHAR(100) NULL,
    listed_price NUMERIC(15, 2) NOT NULL,
    effective_price NUMERIC(15, 2) NULL,
    sold_count INTEGER NULL,
    rating NUMERIC(3, 2) NULL,
    confidence NUMERIC(5, 2) NOT NULL DEFAULT 1.00,
    match_status VARCHAR(24) NOT NULL DEFAULT 'AUTO_MATCHED' CHECK (
        match_status IN ('AUTO_MATCHED', 'NEEDS_REVIEW', 'REJECTED')
    ),
    verdict VARCHAR(100) NULL,
    fake_sale_warning BOOLEAN NOT NULL DEFAULT FALSE,
    is_outlier BOOLEAN NOT NULL DEFAULT FALSE,
    observed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_competitor_prices_product_id ON competitor_prices (product_id);
CREATE INDEX IF NOT EXISTS ix_competitor_prices_sku_code ON competitor_prices (sku_code);
CREATE INDEX IF NOT EXISTS ix_competitor_prices_marketplace_code ON competitor_prices (marketplace_code);
CREATE INDEX IF NOT EXISTS ix_competitor_prices_observed_at ON competitor_prices (observed_at);

CREATE TABLE IF NOT EXISTS competitor_price_history (
    id UUID PRIMARY KEY,
    competitor_price_id UUID NOT NULL REFERENCES competitor_prices (id) ON DELETE CASCADE,
    recorded_date DATE NOT NULL,
    price NUMERIC(15, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (competitor_price_id, recorded_date)
);

CREATE TABLE IF NOT EXISTS sales_records (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products (id) ON DELETE RESTRICT,
    channel_id UUID NOT NULL REFERENCES sales_channels (id) ON DELETE RESTRICT,
    order_date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(15, 2) NOT NULL,
    gross_revenue NUMERIC(15, 2) NOT NULL,
    unit_cost NUMERIC(15, 2) NOT NULL,
    channel_fee_amount NUMERIC(15, 2) NOT NULL,
    net_profit NUMERIC(15, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sales_records_product_id ON sales_records (product_id);
CREATE INDEX IF NOT EXISTS ix_sales_records_channel_id ON sales_records (channel_id);
CREATE INDEX IF NOT EXISTS ix_sales_records_order_date ON sales_records (order_date);

-- -----------------------------------------------------------------------------
-- NHOM 4: SMART PRICING, PHE DUYET, DONG BO & ML MODEL RUNS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pricing_rules (
    id UUID PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    rule_type VARCHAR(32) NOT NULL CHECK (
        rule_type IN ('FLASH_SALE', 'SKIMMING', 'CLEARANCE', 'COMPETITOR_MATCH', 'MARGIN_GUARD')
    ),
    priority INTEGER NOT NULL DEFAULT 100,
    scope_label VARCHAR(200) NOT NULL,
    category_id UUID NULL REFERENCES categories (id) ON DELETE SET NULL,
    channel_id UUID NULL REFERENCES sales_channels (id) ON DELETE SET NULL,
    min_margin NUMERIC(6, 4) NOT NULL,
    max_price_change_pct NUMERIC(6, 4) NOT NULL,
    approval_required BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(16) NOT NULL DEFAULT 'DRAFT' CHECK (
        status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'ARCHIVED')
    ),
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS price_recommendations (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES sales_channels (id) ON DELETE CASCADE,
    rule_id UUID NULL REFERENCES pricing_rules (id) ON DELETE SET NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'DRAFT' CHECK (
        status IN (
            'DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'EXECUTION_QUEUED',
            'EXECUTED', 'REJECTED', 'EXPIRED', 'FAILED', 'CANCELLED'
        )
    ),
    current_price NUMERIC(15, 2) NOT NULL,
    floor_price NUMERIC(15, 2) NOT NULL,
    recommended_price NUMERIC(15, 2) NOT NULL,
    expected_profit_per_unit NUMERIC(15, 2) NOT NULL,
    expected_margin NUMERIC(6, 4) NOT NULL,
    unit_cost NUMERIC(15, 2) NOT NULL,
    channel_fee_rate NUMERIC(6, 4) NOT NULL,
    competitor_median NUMERIC(15, 2) NULL,
    target_margin NUMERIC(6, 4) NOT NULL,
    predicted_demand NUMERIC(12, 2) NULL,
    data_quality VARCHAR(16) NOT NULL DEFAULT 'HIGH' CHECK (data_quality IN ('HIGH', 'MEDIUM', 'LOW')),
    algorithm_type VARCHAR(24) NOT NULL DEFAULT 'RULE_BASED' CHECK (
        algorithm_type IN ('RULE_BASED', 'ML_ASSISTED')
    ),
    algorithm_version VARCHAR(64) NOT NULL,
    explanation_json JSONB NOT NULL,
    created_by VARCHAR(150) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_price_recommendations_product_id ON price_recommendations (product_id);
CREATE INDEX IF NOT EXISTS ix_price_recommendations_channel_id ON price_recommendations (channel_id);

CREATE TABLE IF NOT EXISTS price_approvals (
    id UUID PRIMARY KEY,
    recommendation_id UUID NOT NULL REFERENCES price_recommendations (id) ON DELETE CASCADE,
    reviewer_id UUID NULL REFERENCES users (id) ON DELETE SET NULL,
    reviewer_name VARCHAR(150) NOT NULL,
    decision VARCHAR(16) NOT NULL CHECK (decision IN ('APPROVED', 'REJECTED')),
    adjusted_price NUMERIC(15, 2) NULL,
    reason TEXT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_price_approvals_recommendation_id ON price_approvals (recommendation_id);

CREATE TABLE IF NOT EXISTS price_sync_logs (
    id UUID PRIMARY KEY,
    recommendation_id UUID NULL REFERENCES price_recommendations (id) ON DELETE SET NULL,
    product_id UUID NULL REFERENCES products (id) ON DELETE SET NULL,
    channel_id UUID NULL REFERENCES sales_channels (id) ON DELETE SET NULL,
    sku_code VARCHAR(64) NOT NULL,
    channel_code VARCHAR(32) NOT NULL,
    channel_name VARCHAR(100) NOT NULL,
    mode VARCHAR(16) NOT NULL CHECK (mode IN ('SIMULATED', 'LIVE')),
    sync_mode VARCHAR(16) NOT NULL CHECK (sync_mode IN ('SIMULATED', 'API_CONFIRMED')),
    requested_price NUMERIC(15, 2) NOT NULL,
    previous_price NUMERIC(15, 2) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'QUEUED' CHECK (
        status IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'PARTIAL', 'FAILED', 'CANCELLED')
    ),
    attempts INTEGER NOT NULL DEFAULT 1,
    http_status INTEGER NULL,
    external_reference VARCHAR(120) NULL,
    error_code VARCHAR(64) NULL,
    error_message TEXT NULL,
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_price_sync_logs_status ON price_sync_logs (status);
CREATE INDEX IF NOT EXISTS ix_price_sync_logs_sku_code ON price_sync_logs (sku_code);

CREATE TABLE IF NOT EXISTS model_runs (
    id UUID PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    algorithm_type VARCHAR(32) NOT NULL,
    feature_columns_json JSONB NOT NULL,
    train_samples INTEGER NOT NULL,
    test_samples INTEGER NOT NULL,
    mae NUMERIC(12, 4) NOT NULL,
    rmse NUMERIC(12, 4) NOT NULL,
    artifact_path VARCHAR(500) NULL,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
