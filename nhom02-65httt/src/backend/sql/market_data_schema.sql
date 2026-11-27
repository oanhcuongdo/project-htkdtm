-- Additive schema for Member 3. Does not replace the group's 16 ERP OLTP tables.
CREATE TABLE IF NOT EXISTS competitor_prices (
    id BIGSERIAL PRIMARY KEY,
    marketplace VARCHAR(40) NOT NULL,
    external_product_id VARCHAR(120) NOT NULL,
    category VARCHAR(255),
    title TEXT NOT NULL,
    seller TEXT,
    brand VARCHAR(255),
    price_vnd NUMERIC(18,2) NOT NULL CHECK (price_vnd > 0),
    original_price_vnd NUMERIC(18,2),
    discount_percent NUMERIC(8,2),
    rating NUMERIC(4,2),
    review_count INTEGER,
    sold_count TEXT,
    product_url TEXT,
    confidence NUMERIC(4,3),
    observed_at TIMESTAMPTZ NOT NULL,
    source_key VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_key, observed_at)
);
CREATE INDEX IF NOT EXISTS idx_competitor_prices_market_time
    ON competitor_prices(marketplace, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_competitor_prices_title
    ON competitor_prices USING GIN (to_tsvector('simple', title));

CREATE TABLE IF NOT EXISTS sku_match_results (
    id BIGSERIAL PRIMARY KEY,
    erp_sku VARCHAR(120) NOT NULL,
    competitor_product_id VARCHAR(120) NOT NULL,
    marketplace VARCHAR(40),
    score NUMERIC(6,2) NOT NULL,
    status VARCHAR(30) NOT NULL CHECK (status IN ('MATCHED','NEEDS_REVIEW','REJECTED')),
    brand_match BOOLEAN NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE VIEW bi_competitor_latest_price AS
SELECT DISTINCT ON (marketplace, external_product_id)
    marketplace, external_product_id, category, title, brand,
    price_vnd, original_price_vnd, discount_percent, rating,
    review_count, observed_at
FROM competitor_prices
ORDER BY marketplace, external_product_id, observed_at DESC;

CREATE OR REPLACE VIEW bi_competitor_marketplace_summary AS
SELECT marketplace, COUNT(*) AS product_count,
       ROUND(AVG(price_vnd), 0) AS avg_price_vnd,
       ROUND(AVG(discount_percent), 2) AS avg_discount_percent,
       ROUND(AVG(rating), 2) AS avg_rating,
       MAX(observed_at) AS latest_observed_at
FROM bi_competitor_latest_price
GROUP BY marketplace;

-- QA/audit log for dry-run simulator; no real marketplace write is performed.
CREATE TABLE IF NOT EXISTS marketplace_simulation_logs (
    id BIGSERIAL PRIMARY KEY,
    erp_sku VARCHAR(120) NOT NULL,
    channel VARCHAR(40) NOT NULL,
    current_price_vnd NUMERIC(18,2) NOT NULL,
    proposed_price_vnd NUMERIC(18,2) NOT NULL,
    pmin_vnd NUMERIC(18,2) NOT NULL,
    status VARCHAR(40) NOT NULL CHECK (status IN ('SIMULATED','BLOCKED_BELOW_PMIN')),
    reason TEXT NOT NULL,
    simulated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE VIEW bi_competitor_price_daily AS
SELECT marketplace, external_product_id, category, title, brand,
       DATE_TRUNC('day', observed_at)::date AS observed_date,
       MIN(price_vnd) AS min_price_vnd,
       MAX(price_vnd) AS max_price_vnd,
       AVG(price_vnd)::numeric(18,2) AS avg_price_vnd,
       COUNT(*) AS observations
FROM competitor_prices
GROUP BY marketplace, external_product_id, category, title, brand,
         DATE_TRUNC('day', observed_at)::date;

CREATE OR REPLACE VIEW bi_sku_matching_quality AS
SELECT status, marketplace, COUNT(*) AS match_count,
       ROUND(AVG(score), 2) AS avg_score
FROM sku_match_results
GROUP BY status, marketplace;

CREATE INDEX IF NOT EXISTS idx_competitor_prices_product_time
    ON competitor_prices(external_product_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_sku_match_results_sku
    ON sku_match_results(erp_sku, checked_at DESC);
