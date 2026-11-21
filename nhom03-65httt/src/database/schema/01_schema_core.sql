-- EduVision BI - Nhóm 03: phần lõi của kho dữ liệu galaxy schema (PostgreSQL).
-- Gồm 3 schema (raw, clean, dw), 1 bảng thô, 1 bảng văn bản đã làm sạch, 3 dimension và fact_review.
-- Chạy lại nhiều lần không lỗi. Các fact và dimension còn lại làm ở commit sau.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS clean;
CREATE SCHEMA IF NOT EXISTS dw;

COMMENT ON SCHEMA raw   IS 'Dữ liệu thô nguyên trạng từ các collector';
COMMENT ON SCHEMA clean IS 'Dữ liệu đã làm sạch, chuẩn hóa; chứa văn bản đánh giá';
COMMENT ON SCHEMA dw    IS 'Kho dữ liệu galaxy schema: fact chỉ có khóa ngoại và số đo';

-- ---------------------------------------------------------------- raw
CREATE TABLE IF NOT EXISTS raw.review_raw (
    source       text,           -- nguồn: google_play, app_store, youtube, ...
    product      text,           -- tên nền tảng / sản phẩm
    review_id    text,           -- mã đánh giá gốc của nguồn
    author_hash  text,           -- định danh tác giả đã băm
    rating       smallint,       -- số sao (có thể rỗng)
    text         text,           -- nội dung đánh giá, cho phép rỗng
    lang_guess   text,           -- ngôn ngữ đoán được
    created_at   timestamptz,    -- thời điểm đăng đánh giá
    app_version  text,
    thumbs_up    integer,
    reply_text   text,           -- phản hồi của nhà phát triển, cho phép rỗng
    crawled_at   timestamptz     -- thời điểm thu thập
);
COMMENT ON TABLE raw.review_raw IS 'Đánh giá thô theo đúng các cột CSV thu thập, chưa làm sạch, không ràng buộc';

-- ---------------------------------------------------------------- clean
CREATE TABLE IF NOT EXISTS clean.review_text (
    review_key   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id    text NOT NULL,
    source       text NOT NULL,
    text         text,
    lang_guess   text,
    text_hash    text,           -- băm nội dung chuẩn hóa, dùng để loại trùng nội dung
    CONSTRAINT uq_review_text_source_review UNIQUE (source, review_id)
);
CREATE INDEX IF NOT EXISTS ix_review_text_hash ON clean.review_text (text_hash);
COMMENT ON TABLE clean.review_text IS 'Văn bản đánh giá đã làm sạch; nơi duy nhất lưu nội dung đánh giá (fact không lưu văn bản)';

-- ---------------------------------------------------------------- dw: dimension
CREATE TABLE IF NOT EXISTS dw.dim_time (
    time_key   integer PRIMARY KEY,          -- dạng yyyymmdd, ví dụ 20261121
    full_date  date     NOT NULL UNIQUE,
    week       smallint NOT NULL,
    month      smallint NOT NULL CHECK (month BETWEEN 1 AND 12),
    quarter    smallint NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    year       smallint NOT NULL
);
COMMENT ON TABLE dw.dim_time IS 'Chiều thời gian theo ngày: tuần, tháng, quý, năm (hỗ trợ roll-up)';

CREATE TABLE IF NOT EXISTS dw.dim_platform (
    platform_key   integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    platform_name  text NOT NULL UNIQUE,
    platform_group text NOT NULL CHECK (platform_group IN ('trong_nuoc', 'quoc_te')),
    play_id        text,                     -- mã ứng dụng Google Play
    ios_id         text                      -- mã ứng dụng App Store
);
COMMENT ON TABLE dw.dim_platform IS 'Chiều nền tảng E-learning, chia nhóm trong nước / quốc tế';

CREATE TABLE IF NOT EXISTS dw.dim_source (
    source_key   smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name  text NOT NULL UNIQUE,
    source_type  text NOT NULL CHECK (source_type IN ('kho_ung_dung', 'youtube', 'bao_chi', 'khac'))
);
COMMENT ON TABLE dw.dim_source IS 'Chiều nguồn dữ liệu: kho ứng dụng, YouTube, báo chí, khác';

-- ---------------------------------------------------------------- dw: fact
CREATE TABLE IF NOT EXISTS dw.fact_review (
    review_key    bigint PRIMARY KEY REFERENCES clean.review_text (review_key),
    time_key      integer  NOT NULL REFERENCES dw.dim_time (time_key),
    platform_key  integer  NOT NULL REFERENCES dw.dim_platform (platform_key),
    source_key    smallint NOT NULL REFERENCES dw.dim_source (source_key),
    rating        smallint CHECK (rating BETWEEN 1 AND 5),
    thumbs_up     integer  NOT NULL DEFAULT 0 CHECK (thumbs_up >= 0)
);
CREATE INDEX IF NOT EXISTS ix_fact_review_time     ON dw.fact_review (time_key);
CREATE INDEX IF NOT EXISTS ix_fact_review_platform ON dw.fact_review (platform_key);
CREATE INDEX IF NOT EXISTS ix_fact_review_source   ON dw.fact_review (source_key);
COMMENT ON TABLE dw.fact_review IS 'Fact đánh giá, grain: một đánh giá; chỉ khóa ngoại và số đo, văn bản ở clean.review_text';
