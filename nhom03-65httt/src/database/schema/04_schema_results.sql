-- EduVision BI - Nhóm 03: bảng kết quả (lịch sử ETL, nhật ký chất lượng, nhãn cảm xúc M1), dữ liệu khởi tạo và view cho Superset.
-- Chạy sau 03_schema_news.sql. Tất cả nằm trong schema dw. Chạy lại nhiều lần không lỗi, không sinh dòng trùng.
-- KHÔNG seed dim_platform và dim_source (ETL tự nạp), KHÔNG seed dim_event (việc của Thái Anh).

-- ---------------------------------------------------------------- dw: bảng
-- Mỗi BƯỚC của mỗi LẦN CHẠY ETL một dòng (khớp bản ghi JSONL của run_etl.py và run_pipeline.py).
CREATE TABLE IF NOT EXISTS dw.etl_run_log (
    log_key        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id         text        NOT NULL,
    step           text        NOT NULL
        CHECK (step IN ('collect', 'raw', 'clean', 'dw', 'news', 'platform_period', 'score', 'alert')),
    started_at     timestamptz NOT NULL,
    finished_at    timestamptz,
    status         text        NOT NULL CHECK (status IN ('success', 'partial', 'failed', 'dry_run')),
    input_name     text,                    -- chỉ tên tệp đầu vào, không lưu đường dẫn máy cá nhân
    rows_read      integer,
    rows_inserted  integer,
    rows_dropped   integer,
    error_message  text
);
CREATE INDEX IF NOT EXISTS ix_etl_run_log_started ON dw.etl_run_log (started_at);
CREATE INDEX IF NOT EXISTS ix_etl_run_log_run_id  ON dw.etl_run_log (run_id);
COMMENT ON TABLE dw.etl_run_log IS 'Lịch sử chạy ETL: mỗi bước của mỗi lần chạy một dòng (trạng thái, số dòng đọc/nạp/loại, lỗi). Dashboard 6 và bằng chứng pipeline tự chạy truy vấn bảng này';

CREATE TABLE IF NOT EXISTS dw.data_quality_log (
    check_key    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    checked_at   timestamptz NOT NULL DEFAULT now(),
    run_id       text,
    source_name  text,
    check_type   text CHECK (check_type IN
        ('trung_khoa', 'thieu_van_ban', 'sao_ngoai_mien', 'ngay_ngoai_mien', 'mo_coi_khoa_ngoai', 'trung_noi_dung')),
    rows_checked integer NOT NULL,
    rows_failed  integer NOT NULL,
    details      text
);
CREATE INDEX IF NOT EXISTS ix_data_quality_log_checked ON dw.data_quality_log (checked_at);
CREATE INDEX IF NOT EXISTS ix_data_quality_log_run_id  ON dw.data_quality_log (run_id);
COMMENT ON TABLE dw.data_quality_log IS 'Nhật ký kiểm tra chất lượng dữ liệu: mỗi lần kiểm tra ghi một đợt dòng (loại kiểm tra, số dòng kiểm, số dòng lỗi)';

-- Nhãn cảm xúc M1 cho từng đánh giá, mỗi đánh giá một dòng (giữ kết quả mới nhất).
CREATE TABLE IF NOT EXISTS dw.fact_review_sentiment (
    review_key       bigint       PRIMARY KEY REFERENCES dw.fact_review (review_key),
    model_key        smallint     NOT NULL REFERENCES dw.dim_model (model_key),
    sentiment_label  text         NOT NULL CHECK (sentiment_label IN ('tich_cuc', 'trung_tinh', 'tieu_cuc')),
    sentiment_score  numeric(4,3) CHECK (sentiment_score BETWEEN -1 AND 1),
    confidence       numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
    scored_at        timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_fact_review_sentiment_model ON dw.fact_review_sentiment (model_key);
CREATE INDEX IF NOT EXISTS ix_fact_review_sentiment_label ON dw.fact_review_sentiment (sentiment_label);
COMMENT ON TABLE dw.fact_review_sentiment IS 'Fact nhãn cảm xúc M1 theo đánh giá, grain: một đánh giá (giữ kết quả mới nhất). Là nguồn để tổng hợp fact_platform_period';

-- ---------------------------------------------------------------- dw: dữ liệu khởi tạo
INSERT INTO dw.dim_aspect (aspect_name) VALUES
    ('Technical'), ('Academic'), ('Customer Service'), ('Pricing'), ('Other')
ON CONFLICT (aspect_name) DO NOTHING;

INSERT INTO dw.dim_model (model_name, model_version) VALUES
    ('M1_phobert', 'v0'),
    ('M1_tfidf_lr_baseline', 'v0'),
    ('M1_llm_zero_shot', 'v0'),
    ('M2_absa', 'v0'),
    ('M2_keyword_baseline', 'v0'),
    ('M3_sentiment_index', 'v0'),
    ('M3_negative_rate', 'v0'),
    ('M3_baseline_last_period', 'v0'),
    ('M3_baseline_moving_avg', 'v0')
ON CONFLICT (model_name, model_version) DO NOTHING;

-- Cùng công thức với ETL (src/etl/load/load_dw.py) nên không xung đột khi ETL sinh thêm ngày.
INSERT INTO dw.dim_time (time_key, full_date, week, month, quarter, year)
SELECT to_char(d, 'YYYYMMDD')::int, d::date,
       extract(week FROM d)::smallint, extract(month FROM d)::smallint,
       extract(quarter FROM d)::smallint, extract(year FROM d)::smallint
FROM generate_series('2011-01-01'::date, '2027-12-31'::date, interval '1 day') AS g(d)
ON CONFLICT (time_key) DO NOTHING;

-- ---------------------------------------------------------------- dw: view chỉ đọc cho Superset và chatbot
-- Không có cột văn bản đánh giá, tên người hay hồ sơ tác giả.
CREATE OR REPLACE VIEW dw.v_review_enriched AS
SELECT f.review_key,
       t.full_date,
       t.year,
       t.month,
       p.platform_name,
       p.platform_group,
       s.source_name,
       s.source_type,
       f.rating,
       f.thumbs_up,
       rs.sentiment_label
FROM dw.fact_review f
JOIN dw.dim_time     t ON t.time_key     = f.time_key
JOIN dw.dim_platform p ON p.platform_key = f.platform_key
JOIN dw.dim_source   s ON s.source_key   = f.source_key
LEFT JOIN dw.fact_review_sentiment rs ON rs.review_key = f.review_key;
COMMENT ON VIEW dw.v_review_enriched IS 'View đánh giá đã nối ngày, nền tảng, nguồn và nhãn cảm xúc M1; không có văn bản đánh giá. Một dòng mỗi đánh giá';

CREATE OR REPLACE VIEW dw.v_platform_month AS
SELECT fp.platform_key,
       p.platform_name,
       p.platform_group,
       t.full_date AS month_start,
       fp.new_review_count,
       fp.positive_rate,
       fp.negative_rate,
       fp.avg_rating,
       fp.sentiment_index,
       fp.bhi,
       fp.review_share_in_group
FROM dw.fact_platform_period fp
JOIN dw.dim_platform p ON p.platform_key = fp.platform_key
JOIN dw.dim_time     t ON t.time_key     = fp.time_key;
COMMENT ON VIEW dw.v_platform_month IS 'View tổng hợp theo nền tảng và tháng (month_start là ngày đầu tháng) kèm đủ các số đo của fact_platform_period';

CREATE OR REPLACE VIEW dw.v_alert_open AS
SELECT a.alert_key,
       a.detected_at,
       t.full_date AS detected_date,
       p.platform_name,
       asp.aspect_name,
       a.metric_name,
       a.metric_value,
       a.threshold,
       a.status
FROM dw.fact_alert a
JOIN dw.dim_platform p ON p.platform_key = a.platform_key
JOIN dw.dim_time     t ON t.time_key     = a.time_key
LEFT JOIN dw.dim_aspect asp ON asp.aspect_key = a.aspect_key
WHERE a.status <> 'da_xu_ly';
COMMENT ON VIEW dw.v_alert_open IS 'View cảnh báo chưa xử lý (status khác da_xu_ly) kèm tên nền tảng và tên khía cạnh';
