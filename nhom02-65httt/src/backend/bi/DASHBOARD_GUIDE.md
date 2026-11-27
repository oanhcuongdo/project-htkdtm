# Apache Superset – 3 Dashboard của Thành viên 3

## Kết nối
- Database: PostgreSQL của nhóm.
- Schema bổ sung: chạy `../sql/market_data_schema.sql` sau khi thành viên Database duyệt.
- Dataset Superset: `bi_competitor_latest_price`, `bi_competitor_marketplace_summary`, `bi_competitor_price_daily`, `bi_sku_matching_quality`.

## Dashboard 1 – Profitability Dashboard
Mục tiêu theo đề cương: doanh thu, lợi nhuận gộp, biên lợi nhuận ròng theo thời gian; phân tích theo danh mục/kênh; cảnh báo SKU sát Pmin.

Nguồn bắt buộc: fact_sales và bảng/nguồn giá đề xuất Pmin của nhóm. Hiện repository chưa có schema fact_sales hoặc tên cột đã được thống nhất, vì vậy không tạo SQL giả định làm sai số liệu. Sau khi thành viên Database cung cấp schema, tạo chart:
1. Big Number: tổng doanh thu, lợi nhuận gộp, net margin.
2. Time-series: doanh thu và lợi nhuận theo ngày.
3. Bar: lợi nhuận theo category/channel.
4. Table: SKU có giá bán gần Pmin.

## Dashboard 2 – Competitor & Price History
Nguồn hiện có: `bi_competitor_latest_price`, `bi_competitor_marketplace_summary`, `bi_competitor_price_daily`.

Chart đề xuất:
1. Big Number: số sản phẩm đối thủ, số sàn, thời điểm crawl mới nhất.
2. Bar: số sản phẩm và giá trung bình theo marketplace.
3. Time-series: giá trung bình/min/max theo ngày (lọc SKU/sàn).
4. Table: tên sản phẩm, sàn, giá hiện tại, giá gốc, discount, rating, observed_at.

Price Index = (giá shop / giá đối thủ) × 100%. Chỉ tính sau khi có bảng ánh xạ SKU nội bộ với sản phẩm đối thủ và giá shop hiện hành. Fake-sale rate chỉ tính khi nhóm đã thống nhất tiêu chí và cột `fake_sale_warning`.

## Dashboard 3 – Pricing Strategy Performance
Mục tiêu theo đề cương: so sánh doanh thu, sản lượng, biên lợi nhuận trước/sau 4 chiến lược; tỷ lệ duyệt và đồng bộ.

Nguồn bắt buộc: pricing_rules, price_recommendations, price_approvals, price_sync_logs và fact_sales. Repository hiện chưa chứa schema đầy đủ của các bảng này. Sau khi thành viên Database/AI chốt schema, tạo:
1. Bar: revenue/units/margin theo strategy.
2. Funnel: recommendations → approved → synced.
3. Big Number: approval rate, sync success rate.
4. Table: strategy, SKU, old/new price, expected margin, approval status, sync status.

## Bộ lọc chung
Date range, marketplace/channel, category, brand, SKU, strategy. Không gắn nhãn “90 ngày” nếu dữ liệu nguồn chưa có đủ 90 ngày quan sát.
