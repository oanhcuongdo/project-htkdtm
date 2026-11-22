-- EduVision BI - Nhóm 03: các dimension và fact còn lại của galaxy schema (PostgreSQL).
-- Chạy sau 01_schema_core.sql. Chỉ thêm bảng chưa có theo mục 7 của đề cương:
--   dimension thêm: dim_aspect, dim_app_version, dim_event, dim_model (cùng 3 dim ở tệp 01 thành 7 dim)
--   fact thêm: fact_review_aspect, fact_platform_period, fact_forecast, fact_news_sentiment, fact_alert
--              (cùng fact_review ở tệp 01 thành 6 fact)
-- Chạy lại nhiều lần không lỗi. Mục "cần xác nhận" là chỗ đề cương chưa nêu rõ.

-- ---------------------------------------------------------------- dw: dimension
CREATE TABLE IF NOT EXISTS dw.dim_aspect (
    aspect_key   smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aspect_name  text NOT NULL UNIQUE
        CHECK (aspect_name IN ('Technical', 'Academic', 'Customer Service', 'Pricing', 'Other'))
);
COMMENT ON TABLE dw.dim_aspect IS 'Chiều khía cạnh đánh giá: Technical, Academic, Customer Service, Pricing, Other (đúng 5 giá trị theo đề cương)';

CREATE TABLE IF NOT EXISTS dw.dim_app_version (
    app_version_key smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    platform_key    integer NOT NULL REFERENCES dw.dim_platform (platform_key),
    version_name    text    NOT NULL,
    release_date    date,
    release_notes   text,
    CONSTRAINT uq_app_version_platform_version UNIQUE (platform_key, version_name)
);
COMMENT ON TABLE dw.dim_app_version IS 'Chiều phiên bản ứng dụng: phiên bản, ngày phát hành, nội dung cập nhật. Cần xác nhận: đề cương không nêu khóa ngoại tới nền tảng; thêm platform_key vì một số phiên bản có thể trùng giữa các nền tảng';

CREATE TABLE IF NOT EXISTS dw.dim_event (
    event_key     integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type    text NOT NULL CHECK (event_type IN ('cap_nhat', 'khuyen_mai', 'mua_thi', 'su_co')),
    start_date    date NOT NULL,
    end_date      date,
    description   text,
    platform_key  integer REFERENCES dw.dim_platform (platform_key),  -- rỗng = sự kiện chung (vd mùa thi)
    needs_review  boolean NOT NULL DEFAULT false,                    -- dòng "cần kiểm tra" theo đề cương
    CONSTRAINT ck_event_dates CHECK (end_date IS NULL OR end_date >= start_date)
);
COMMENT ON TABLE dw.dim_event IS 'Chiều sự kiện: cập nhật, khuyến mãi, mùa thi, sự cố kèm thời gian và mô tả. Cần xác nhận: platform_key (rỗng nếu sự kiện chung) và needs_review do bổ sung từ ghi chú "cần kiểm tra" trong đề cương';

CREATE TABLE IF NOT EXISTS dw.dim_model (
    model_key      smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_name     text NOT NULL,
    model_version  text NOT NULL,
    trained_at     date,
    CONSTRAINT uq_model_name_version UNIQUE (model_name, model_version)
);
COMMENT ON TABLE dw.dim_model IS 'Chiều mô hình AI: tên mô hình, phiên bản, ngày huấn luyện';

-- ---------------------------------------------------------------- dw: fact
-- Grain: 1 đánh giá x 1 khía cạnh
CREATE TABLE IF NOT EXISTS dw.fact_review_aspect (
    review_key       bigint   NOT NULL REFERENCES dw.fact_review (review_key),
    aspect_key       smallint NOT NULL REFERENCES dw.dim_aspect (aspect_key),
    time_key         integer  NOT NULL REFERENCES dw.dim_time (time_key),
    platform_key     integer  NOT NULL REFERENCES dw.dim_platform (platform_key),
    model_key        smallint REFERENCES dw.dim_model (model_key),
    sentiment_label  text CHECK (sentiment_label IN ('tich_cuc', 'trung_tinh', 'tieu_cuc')),
    sentiment_score  numeric(4,3) CHECK (sentiment_score BETWEEN -1 AND 1),
    confidence       numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
    PRIMARY KEY (review_key, aspect_key)
);
CREATE INDEX IF NOT EXISTS ix_fact_review_aspect_time     ON dw.fact_review_aspect (time_key);
CREATE INDEX IF NOT EXISTS ix_fact_review_aspect_platform ON dw.fact_review_aspect (platform_key);
CREATE INDEX IF NOT EXISTS ix_fact_review_aspect_aspect   ON dw.fact_review_aspect (aspect_key);
COMMENT ON TABLE dw.fact_review_aspect IS 'Fact cảm xúc theo khía cạnh, grain: một đánh giá x một khía cạnh. Cần xác nhận: time_key, platform_key (sao chép từ fact_review để dice nhanh) và model_key (mô hình ABSA gán nhãn) không có trong đề cương';

-- Grain: 1 nền tảng x 1 tháng
CREATE TABLE IF NOT EXISTS dw.fact_platform_period (
    platform_key         integer NOT NULL REFERENCES dw.dim_platform (platform_key),
    time_key             integer NOT NULL REFERENCES dw.dim_time (time_key),  -- ngày đầu tháng
    new_review_count     integer CHECK (new_review_count >= 0),
    positive_rate        numeric(5,4) CHECK (positive_rate BETWEEN 0 AND 1),
    negative_rate        numeric(5,4) CHECK (negative_rate BETWEEN 0 AND 1),
    avg_rating           numeric(3,2) CHECK (avg_rating BETWEEN 1 AND 5),
    sentiment_index      numeric(6,3),
    bhi                  numeric(6,2),
    review_share_in_group numeric(5,4) CHECK (review_share_in_group BETWEEN 0 AND 1),
    PRIMARY KEY (platform_key, time_key)
);
CREATE INDEX IF NOT EXISTS ix_fact_platform_period_time ON dw.fact_platform_period (time_key);
COMMENT ON TABLE dw.fact_platform_period IS 'Fact tổng hợp theo kỳ, grain: một nền tảng x một tháng. Cần xác nhận: time_key trỏ ngày đầu tháng trong dim_time; thang đo Sentiment Index và BHI (BHI để numeric(6,2)) chưa chốt trong đề cương';

-- Grain: 1 nền tảng x 1 kỳ dự báo x 1 mô hình
CREATE TABLE IF NOT EXISTS dw.fact_forecast (
    platform_key    integer  NOT NULL REFERENCES dw.dim_platform (platform_key),
    time_key        integer  NOT NULL REFERENCES dw.dim_time (time_key),  -- ngày đầu kỳ (tháng) được dự báo
    model_key       smallint NOT NULL REFERENCES dw.dim_model (model_key),
    forecast_value  numeric(8,4) NOT NULL,
    ci_lower        numeric(8,4),
    ci_upper        numeric(8,4),
    actual_value    numeric(8,4),                                          -- cập nhật sau khi có số thực tế
    PRIMARY KEY (platform_key, time_key, model_key),
    CONSTRAINT ck_forecast_ci CHECK (ci_lower IS NULL OR ci_upper IS NULL OR ci_lower <= ci_upper)
);
CREATE INDEX IF NOT EXISTS ix_fact_forecast_time ON dw.fact_forecast (time_key);
COMMENT ON TABLE dw.fact_forecast IS 'Fact dự báo, grain: một nền tảng x một kỳ dự báo x một mô hình. Cần xác nhận: M3 dự báo cả Sentiment Index lẫn tỷ lệ tiêu cực nhưng grain không có cột chỉ số; tạm coi mỗi chỉ số ứng với một dòng dim_model riêng';

-- Grain: 1 bài báo x 1 nền tảng được nhắc
CREATE TABLE IF NOT EXISTS dw.fact_news_sentiment (
    source_key       smallint NOT NULL REFERENCES dw.dim_source (source_key),
    article_id       text     NOT NULL,                                    -- mã bài báo gốc (dimension suy biến)
    platform_key     integer  NOT NULL REFERENCES dw.dim_platform (platform_key),
    time_key         integer  NOT NULL REFERENCES dw.dim_time (time_key),  -- ngày đăng bài
    sentiment_score  numeric(4,3) CHECK (sentiment_score BETWEEN -1 AND 1),
    sentiment_label  text CHECK (sentiment_label IN ('tich_cuc', 'trung_tinh', 'tieu_cuc')),
    confidence       numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
    mention_count    integer CHECK (mention_count >= 0),
    PRIMARY KEY (source_key, article_id, platform_key)
);
CREATE INDEX IF NOT EXISTS ix_fact_news_sentiment_time     ON dw.fact_news_sentiment (time_key);
CREATE INDEX IF NOT EXISTS ix_fact_news_sentiment_platform ON dw.fact_news_sentiment (platform_key);
COMMENT ON TABLE dw.fact_news_sentiment IS 'Fact cảm xúc báo chí, grain: một bài báo x một nền tảng được nhắc. Cần xác nhận: đề cương chưa có dimension bài báo nên dùng article_id làm dimension suy biến cùng source_key; tiêu đề/nội dung bài chưa có nơi lưu';

-- Grain: 1 cảnh báo
CREATE TABLE IF NOT EXISTS dw.fact_alert (
    alert_key      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    time_key       integer NOT NULL REFERENCES dw.dim_time (time_key),     -- ngày phát hiện
    platform_key   integer NOT NULL REFERENCES dw.dim_platform (platform_key),
    aspect_key     smallint REFERENCES dw.dim_aspect (aspect_key),        -- rỗng nếu cảnh báo không theo khía cạnh
    metric_name    text    NOT NULL,                                       -- chỉ số bị cảnh báo
    metric_value   numeric(10,4) NOT NULL,
    threshold      numeric(10,4) NOT NULL,
    detected_at    timestamptz   NOT NULL,
    status         text NOT NULL DEFAULT 'moi' CHECK (status IN ('moi', 'dang_xu_ly', 'da_xu_ly'))
);
CREATE INDEX IF NOT EXISTS ix_fact_alert_time     ON dw.fact_alert (time_key);
CREATE INDEX IF NOT EXISTS ix_fact_alert_platform ON dw.fact_alert (platform_key);
COMMENT ON TABLE dw.fact_alert IS 'Fact cảnh báo, grain: một cảnh báo. Cần xác nhận: tập giá trị status; aspect_key; nơi lưu đề xuất hành động và bộ phận phụ trách (đề cương nói ghi vào fact_alert nhưng không liệt kê trong số đo)';
