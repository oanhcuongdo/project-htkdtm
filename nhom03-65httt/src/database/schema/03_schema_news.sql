-- EduVision BI - Nhóm 03: bảng lưu bài báo gốc (tin tức báo chí về các nền tảng).
-- Lý do: dw.fact_news_sentiment chỉ giữ điểm cảm xúc theo (article_id, nền tảng, ngày); không có chỗ lưu tiêu đề,
-- tên báo, đường dẫn. Mô hình chấm cảm xúc báo chí (TA4) và dashboard cần đọc tiêu đề.
-- Chỉ lưu tiêu đề, tên báo, đường dẫn, ngày đăng; KHÔNG lưu toàn văn bài (docs/dao_duc_phap_ly.md mục 2).
-- Chạy lại nhiều lần không lỗi.

CREATE TABLE IF NOT EXISTS clean.news_article (
    article_id     text        NOT NULL,   -- mã bài: title_hash trong tệp thu thập; trùng với dw.fact_news_sentiment.article_id
    platform_name  text        NOT NULL,   -- nền tảng được nhắc tới (khớp dw.dim_platform.platform_name)
    origin         text,                   -- nguồn thu thập, ví dụ google_news
    title          text        NOT NULL,
    outlet         text,                   -- tên báo
    link           text,                   -- đường dẫn bài báo
    published_at   timestamptz,
    collected_at   timestamptz,
    PRIMARY KEY (article_id, platform_name)
);
CREATE INDEX IF NOT EXISTS ix_news_article_platform  ON clean.news_article (platform_name);
CREATE INDEX IF NOT EXISTS ix_news_article_published ON clean.news_article (published_at);
COMMENT ON TABLE clean.news_article IS
    'Bài báo gốc theo nền tảng: tiêu đề, tên báo, đường dẫn, ngày đăng. Không lưu toàn văn. Một bài nhắc nhiều nền tảng thì có nhiều dòng';
