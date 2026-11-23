# Định nghĩa KPI, BHI và Dashboard Superset

Tài liệu tham chiếu trực tiếp Mục 9 đề cương **Hệ thống BI: KPI và dashboard**.

## Giới hạn dữ liệu hiện có

Schema hiện tại trong `src/database/schema/01_schema_core.sql` chỉ cung cấp:

- `dw.dim_time`: `time_key`, `full_date`, `week`, `month`, `quarter`, `year`.
- `dw.dim_platform`: `platform_key`, `platform_name`, `platform_group`, `play_id`, `ios_id`.
- `dw.dim_source`: `source_key`, `source_name`, `source_type`.
- `dw.fact_review`: `review_key`, `time_key`, `platform_key`, `source_key`, `rating`, `thumbs_up`.

Các bảng nhãn cảm xúc, cảm xúc theo khía cạnh, dự báo, bất thường và nhật ký pipeline chưa có trong schema lõi. Các công thức yêu cầu dữ liệu mô hình vì vậy được quy ước tạm bằng điểm sao và ghi rõ phần chờ bảng kết quả tương ứng; không bịa dữ liệu.

## Bảng định nghĩa KPI

| Mã | Tên KPI | Công thức | Đơn vị | Kỳ tính | Bảng nguồn hiện có | SQL mẫu |
|---|---|---|---|---|---|---|
| KPI-01 | Số đánh giá mới | $N=\sum_{i}1$ cho mọi đánh giá thỏa bộ lọc kỳ | đánh giá | ngày, tuần, tháng, quý, năm | `dw.fact_review`, `dw.dim_time`, `dw.dim_platform`, `dw.dim_source` | `queries/kpi_01_danh_gia_moi.sql` |
| KPI-02 | Tỷ lệ tích cực, trung tính, tiêu cực | $R_c=100\times N_c/N$, trong đó $c$ là từng nhãn cảm xúc | % | ngày, tuần, tháng, quý, năm | `dw.fact_review.rating`; quy tắc tạm 4–5 sao tích cực, 3 sao trung tính, 1–2 sao tiêu cực | `queries/kpi_02_ty_le_cam_xuc.sql` |
| KPI-03 | Sentiment Index | $SI=(P-N)/T\times100$; $P,N,T$ là số đánh giá tích cực, tiêu cực và tổng đánh giá | điểm, thang -100 đến 100 | ngày, tuần, hai tuần, tháng, quý, năm | `dw.fact_review.rating`, các bảng chiều tương ứng | `queries/kpi_03_sentiment_index.sql` |
| KPI-04 | Tỷ lệ tiêu cực theo khía cạnh | $NR_a=100\times N_{negative,a}/T_a$, với $T_a$ là đánh giá nhắc khía cạnh $a$ | % | tuần, tháng, quý | Chưa có bảng khía cạnh/cảm xúc theo khía cạnh; chỉ có thể trả khung dữ liệu tạm từ `dw.fact_review.rating` | `queries/kpi_04_ty_le_tieu_cuc_khia_canh.sql` |
| KPI-05 | Tỷ trọng đánh giá (Share of Voice) | $SOV_p=100\times N_p/\sum_iN_i$ | % | ngày, tuần, tháng, quý, năm | `dw.fact_review.platform_key`, `dw.dim_platform.platform_name` | `queries/kpi_05_share_of_voice.sql` |
| KPI-06 | Tỷ lệ lệch pha | $Mismatch=100\times(N_{rating\ge4,negative}+N_{rating\le2,positive})/T$ | % | tuần, tháng, quý, năm | Cần nhãn cảm xúc mô hình; điểm sao hiện có tại `dw.fact_review.rating` chỉ dùng xác nhận | `queries/kpi_06_ty_le_lech_pha.sql` |
| KPI-07 | Độ lệch báo chí và người học | $Gap=SI_{bao\ chi}-SI_{nguoi\ hoc}$ | điểm SI; -100 đến 100 | tuần, tháng, quý | `dw.dim_source.source_type`, `dw.fact_review.rating`, `dw.dim_platform`, `dw.dim_time` | `queries/kpi_07_lech_bao_chi_nguoi_hoc.sql` |
| KPI-08 | Độ chính xác dự báo | $MAE=N^{-1}\sum|y_i-\hat y_i|$; $DA=100\times N_{dung\ chieu}/N$ | MAE: điểm SI; DA: % | tháng, $N$ kỳ gần nhất | Chưa có bảng dự báo; truy vấn tạm chỉ mô tả chuỗi SI lịch sử từ `dw.fact_review` | `queries/kpi_08_do_chinh_xac_du_bao.sql` |
| KPI-09 | Số kỳ bất thường | Số kỳ có $SI>mean(SI_8\ ky)+2\times sd(SI_8\ ky)$ | số kỳ | hai tuần | `dw.fact_review`, `dw.dim_time.full_date`, `dw.dim_platform` | `queries/kpi_09_so_ky_bat_thuong.sql` |
| KPI-10 | Sức khỏe pipeline | $ThanhCong=COUNT(bản\ ghi\ hop\ le)$; $ErrorRate=100\times N_{loi}/(N_{thanh\ cong}+N_{loi})$ | bản ghi/ngày; %; ngày giờ | ngày | Chưa có bảng pipeline/nhật ký; không truy vấn được từ bảng lõi hiện có | `queries/kpi_10_suc_khoe_pipeline.sql` |

## Định nghĩa BHI

**Brand Health Index (BHI)** là điểm sức khỏe thương hiệu tổng hợp cảm xúc và số sao.

### Công thức đề cương

$$BHI=0,6\times SI_{chuẩn hóa}+0,4\times((\bar R-1)/4\times100)$$

Trong đó:

- $SI_{chuẩn hóa}$ chuyển SI từ [-100, 100] sang [0, 100]: $50+(SI/200\times100)$.
- $\bar R$ là số sao trung bình trong kỳ.
- Điểm cảm xúc: trọng số **60%**.
- Điểm số sao: trọng số **40%**.

Hai trọng số là **trọng số đề xuất theo đề cương và cần nhóm duyệt ở tuần 5**, không phải trọng số đã có dữ liệu mô hình xác nhận.

- Đơn vị: điểm 0–100.
- Kỳ tính: ngày, tuần, tháng, quý, năm.
- Thang tham chiếu đề xuất: `<50: suy yếu; 50–69: trung bình; 70–84: tốt; >=85: rất tốt`.
- Bảng nguồn: `dw.fact_review.rating`, `dw.dim_time`, `dw.dim_platform`, `dw.dim_source`.
- SQL mẫu: `queries/bhi_brand_health_index.sql`.

## Danh sách 6 Dashboard

### 1. Tổng quan và BHI

- **Câu hỏi:** Nền tảng nào được học viên đánh giá tốt nhất và xu hướng theo thời gian ra sao? Số sao và nội dung bình luận có lệch nhau không?
- **KPI chính:** KPI-01, KPI-02, KPI-03, BHI, KPI-05, KPI-06.
- **Biểu đồ:** thẻ KPI tổng; cột theo nền tảng; đường theo thời gian; phân bố số sao; drill-down đánh giá gốc.
- **Bộ lọc:** thời gian, nền tảng, nguồn, khía cạnh, phiên bản, ngôn ngữ.

### 2. Khía cạnh và chủ đề

- **Câu hỏi:** Khía cạnh nào gây phản hồi tiêu cực nhiều nhất?
- **KPI chính:** KPI-04, KPI-03.
- **Biểu đồ:** cột tỷ lệ tiêu cực theo khía cạnh; heatmap nền tảng × khía cạnh; treemap hoặc đám mây chủ đề.
- **Bộ lọc:** thời gian, nền tảng, nguồn, khía cạnh, phiên bản, ngôn ngữ.

### 3. So sánh nền tảng

- **Câu hỏi:** So với đối thủ, mỗi nền tảng mạnh và yếu ở khía cạnh nào?
- **KPI chính:** BHI, KPI-03, KPI-04, KPI-05.
- **Biểu đồ:** heatmap nền tảng × khía cạnh; cột BHI/SI/SOV; radar nếu dữ liệu đủ.
- **Bộ lọc:** thời gian, nền tảng, nguồn, khía cạnh, phiên bản, ngôn ngữ.

### 4. Xu hướng và sự kiện

- **Câu hỏi:** Cảm xúc thay đổi thế nào sau bản cập nhật, khuyến mãi hoặc mùa thi?
- **KPI chính:** KPI-03, KPI-06, KPI-07.
- **Biểu đồ:** đường cảm xúc theo thời gian; cột số sao; mốc sự kiện; đối chiếu cảm xúc báo chí với cảm xúc người học.
- **Bộ lọc:** thời gian, nền tảng, nguồn, khía cạnh, phiên bản, ngôn ngữ.

### 5. Dự báo và khuyến nghị

- **Câu hỏi:** Khi nào cần can thiệp vì tỷ lệ tiêu cực tăng bất thường và kỳ tới xu hướng ra sao?
- **KPI chính:** KPI-08, KPI-09, KPI-03, KPI-04.
- **Biểu đồ:** đường lịch sử và dự báo; cảnh báo bất thường; bảng khuyến nghị.
- **Bộ lọc:** thời gian, nền tảng, nguồn, khía cạnh, phiên bản, ngôn ngữ.

### 6. Sức khỏe pipeline và chất lượng dữ liệu

- **Câu hỏi:** Hệ thống thu thập có chạy ổn, dữ liệu có lỗi và cập nhật gần nhất khi nào?
- **KPI chính:** KPI-10.
- **Biểu đồ:** thẻ số bản ghi thành công/lỗi; đường chất lượng theo ngày; bảng thời điểm chạy gần nhất.
- **Bộ lọc:** thời gian, nguồn, nền tảng theo dữ liệu có sẵn.
