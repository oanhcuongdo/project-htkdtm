-- ==============================================================================
-- KHO DỮ LIỆU NHÀ THUÊ THÔNG MINH - HÀ NỘI (STAR SCHEMA)
-- Học phần: Hệ Thống Kinh Doanh Thông Minh - Nhóm 12 (65HTTT - TLU)
-- Hạ tầng: Supabase (PostgreSQL 17) + pgvector
-- ==============================================================================

-- 1. Kích hoạt Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Bảng Staging: Lưu trữ Dữ liệu cào thô (Raw Data Lake)
CREATE TABLE IF NOT EXISTS public.staging_raw_listings (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL, -- 'chotot', 'phongtro123', v.v.
    external_id VARCHAR(100) NOT NULL,
    raw_payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL, -- 'pending', 'processed', 'failed'
    error_message TEXT,
    scraped_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    processed_at TIMESTAMPTZ,
    CONSTRAINT uq_staging_source_external UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_staging_status ON public.staging_raw_listings (status);
CREATE INDEX IF NOT EXISTS idx_staging_source ON public.staging_raw_listings (source);
CREATE INDEX IF NOT EXISTS idx_staging_scraped_at ON public.staging_raw_listings (scraped_at DESC);

-- 3. CÁC BẢNG CHIỀU (DIMENSION TABLES)

-- 3.1. Chiều Thời Gian (dim_time)
CREATE TABLE IF NOT EXISTS public.dim_time (
    time_id INT PRIMARY KEY, -- YYYYMMDD
    full_date DATE NOT NULL UNIQUE,
    day_of_week SMALLINT NOT NULL, -- 0: CN, 1: T2, ..., 6: T7
    day_name VARCHAR(20) NOT NULL,
    day_of_month SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter SMALLINT NOT NULL,
    year SMALLINT NOT NULL,
    is_weekend BOOLEAN NOT NULL DEFAULT false,
    is_peak_student_season BOOLEAN NOT NULL DEFAULT false -- Tháng 7-9 và Tháng 1-2
);

-- 3.2. Chiều Vị Trí Địa Lý (dim_location)
CREATE TABLE IF NOT EXISTS public.dim_location (
    location_id SERIAL PRIMARY KEY,
    province VARCHAR(100) NOT NULL DEFAULT 'Hà Nội',
    district VARCHAR(100) NOT NULL,
    ward VARCHAR(100),
    street VARCHAR(255),
    full_address TEXT,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    nearest_university VARCHAR(255),
    distance_to_university_km NUMERIC(6, 2),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_location_district ON public.dim_location (district);
CREATE INDEX IF NOT EXISTS idx_location_lat_lng ON public.dim_location (latitude, longitude);

-- 3.3. Chiều Loại Hình Nhà Ở (dim_property_type)
CREATE TABLE IF NOT EXISTS public.dim_property_type (
    property_type_id SERIAL PRIMARY KEY,
    type_code VARCHAR(50) NOT NULL UNIQUE,
    type_name VARCHAR(100) NOT NULL,
    description TEXT
);

INSERT INTO public.dim_property_type (type_code, type_name, description) VALUES
('phong_tro', 'Phòng trọ / Nhà trọ', 'Phòng cho thuê trong dãy trọ hoặc nhà dân'),
('chung_cu_mini', 'Chung cư mini / Căn hộ dịch vụ', 'Căn hộ mini khép kín, có thang máy hoặc bảo vệ'),
('nha_nguyen_can', 'Nhà nguyên căn', 'Nhà mặt đất nhiều tầng, phù hợp nhóm đông người hoặc hộ gia đình'),
('ktx_sleepbox', 'Ký túc xá / Sleepbox', 'Giường tầng hoặc hộp ngủ cá nhân đầy đủ tiện nghi chung'),
('can_ho', 'Căn hộ chung cư', 'Căn hộ trong tòa nhà chung cư thương mại')
ON CONFLICT (type_code) DO NOTHING;

-- 3.4. Chiều Tiện Ích & Cơ Sở Vật Chất (dim_amenities)
CREATE TABLE IF NOT EXISTS public.dim_amenities (
    amenity_id SERIAL PRIMARY KEY,
    has_air_conditioner BOOLEAN DEFAULT false,
    has_water_heater BOOLEAN DEFAULT false,
    has_washing_machine BOOLEAN DEFAULT false,
    has_refrigerator BOOLEAN DEFAULT false,
    has_private_bathroom BOOLEAN DEFAULT false,
    has_kitchen BOOLEAN DEFAULT false,
    has_balcony BOOLEAN DEFAULT false,
    has_elevator BOOLEAN DEFAULT false,
    has_parking BOOLEAN DEFAULT false,
    has_security BOOLEAN DEFAULT false,
    has_flexible_hours BOOLEAN DEFAULT false,
    has_mezzanine BOOLEAN DEFAULT false,
    raw_amenities JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3.5. Chiều Người Đăng Tin (dim_landlord)
CREATE TABLE IF NOT EXISTS public.dim_landlord (
    landlord_id SERIAL PRIMARY KEY,
    poster_code VARCHAR(100) UNIQUE,
    poster_name VARCHAR(255),
    phone_masked VARCHAR(50),
    poster_type VARCHAR(50) DEFAULT 'unknown', -- 'chinh_chu', 'moi_gioi', 'unknown'
    total_listings INT DEFAULT 1,
    trust_score NUMERIC(4, 2) DEFAULT 5.0,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_landlord_poster_type ON public.dim_landlord (poster_type);

-- 4. BẢNG SỰ KIỆN TRUNG TÂM (FACT TABLE)
CREATE TABLE IF NOT EXISTS public.fact_rental_listings (
    fact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    staging_id BIGINT REFERENCES public.staging_raw_listings(id) ON DELETE SET NULL,
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    original_url TEXT,
    images JSONB DEFAULT '[]'::jsonb,
    
    -- Khóa ngoại liên kết tới các Dimensions
    time_id INT REFERENCES public.dim_time(time_id),
    location_id INT REFERENCES public.dim_location(location_id),
    property_type_id INT REFERENCES public.dim_property_type(property_type_id),
    amenity_id INT REFERENCES public.dim_amenities(amenity_id),
    landlord_id INT REFERENCES public.dim_landlord(landlord_id),
    
    -- Metrics
    price NUMERIC(14, 2) NOT NULL, -- Giá niêm yết (VNĐ/tháng)
    area NUMERIC(8, 2), -- Diện tích (m²)
    price_per_m2 NUMERIC(14, 2), -- Đơn giá VNĐ/m²
    deposit_amount NUMERIC(14, 2) DEFAULT 0, -- Tiền cọc (VNĐ)
    electricity_cost NUMERIC(10, 2), -- Giá điện (VNĐ/kWh hoặc cố định)
    water_cost NUMERIC(10, 2), -- Giá nước (VNĐ/m³ hoặc người)
    service_cost NUMERIC(10, 2) DEFAULT 0, -- Chi phí dịch vụ (VNĐ/tháng)
    estimated_total_cost NUMERIC(14, 2), -- Tổng chi phí ước tính thực tế hàng tháng
    price_diff_rate NUMERIC(6, 2) DEFAULT 0.0, -- Tỷ lệ chênh lệch giá so với khu vực (%)
    price_segment VARCHAR(50) DEFAULT 'trung_cap', -- binh_dan, trung_cap, cao_cap
    risk_score NUMERIC(5, 2) DEFAULT 0.0, -- Điểm rủi ro tin ảo / tin mồi (0 - 100)
    completeness_score NUMERIC(5, 2) DEFAULT 0.0, -- Điểm đầy đủ thông tin (0 - 100)
    
    -- AI Vector Embedding (768 chiều)
    embedding vector(768),
    
    is_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
    CONSTRAINT uq_fact_source_external UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_time_id ON public.fact_rental_listings (time_id);
CREATE INDEX IF NOT EXISTS idx_fact_location_id ON public.fact_rental_listings (location_id);
CREATE INDEX IF NOT EXISTS idx_fact_property_type_id ON public.fact_rental_listings (property_type_id);
CREATE INDEX IF NOT EXISTS idx_fact_price ON public.fact_rental_listings (price);
CREATE INDEX IF NOT EXISTS idx_fact_area ON public.fact_rental_listings (area);
CREATE INDEX IF NOT EXISTS idx_fact_price_per_m2 ON public.fact_rental_listings (price_per_m2);
CREATE INDEX IF NOT EXISTS idx_fact_is_active ON public.fact_rental_listings (is_active);

-- HNSW Vector Index
CREATE INDEX IF NOT EXISTS idx_fact_embedding_hnsw 
ON public.fact_rental_listings 
USING hnsw (embedding vector_cosine_ops);

-- 5. PHÂN QUYỀN VÀ RLS (ROW LEVEL SECURITY)
ALTER TABLE public.staging_raw_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_time ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_location ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_property_type ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_amenities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_landlord ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fact_rental_listings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read-only access to staging" ON public.staging_raw_listings FOR SELECT USING (true);
CREATE POLICY "Allow full access for service role on staging" ON public.staging_raw_listings FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow public read-only access to dim_time" ON public.dim_time FOR SELECT USING (true);
CREATE POLICY "Allow public read-only access to dim_location" ON public.dim_location FOR SELECT USING (true);
CREATE POLICY "Allow public read-only access to dim_property_type" ON public.dim_property_type FOR SELECT USING (true);
CREATE POLICY "Allow public read-only access to dim_amenities" ON public.dim_amenities FOR SELECT USING (true);
CREATE POLICY "Allow public read-only access to dim_landlord" ON public.dim_landlord FOR SELECT USING (true);

CREATE POLICY "Allow public read-only access to fact_rental_listings" ON public.fact_rental_listings FOR SELECT USING (true);
CREATE POLICY "Allow full access for service role on fact_rental_listings" ON public.fact_rental_listings FOR ALL USING (true) WITH CHECK (true);
