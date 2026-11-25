# Kế hoạch hoàn thiện sản phẩm TH5 (Nhóm 03, EduVision BI)

Hạn nộp: **30/11/2026 20:34** (chỉ nộp 1 lần). Lập ngày 25/11/2026.
Phạm vi: **đầy đủ như đã chốt trong [danhsachnhom.md](../danhsachnhom.md) và đề cương**, không cắt việc nào. Bảng dưới chỉ xếp **thứ tự ưu tiên**: việc nào làm trước thì người khác mới làm tiếp được.
Prompt giao việc và tiêu chí kiểm thử từng việc: [prompt_va_tieu_chi_kiem_thu.md](prompt_va_tieu_chi_kiem_thu.md) (mỗi dòng việc ở đây có mã, ví dụ `T1`, khớp với mã trong tệp đó).
Quy tắc git theo [CONTRIBUTING.md](../CONTRIBUTING.md): một việc, một nhánh, một PR, nhóm trưởng merge, không co-author.

## Mức ưu tiên

| Mức | Ý nghĩa | Hạn mục tiêu |
|---|---|---|
| **P1** | Chặn người khác: làm trước, xong sớm | 26/11 (12:00 hoặc 18:00, xem bảng Lịch hạn) |
| **P2** | Lõi sản phẩm: chạy được từ đầu đến cuối | 28/11, 18:00 |
| **P3** | Hoàn thiện và mở rộng | 29/11, 12:00 (đóng băng tính năng) |

**Mốc chung:** đóng băng tính năng **29/11, 12:00**; kiểm thử tích hợp, README, báo cáo kỹ thuật xong **29/11, 16:00**; 30/11 chỉ để dự phòng, nộp trước 18:00 (hạn hệ thống 20:34). Giờ theo giờ Việt Nam.

## Lịch hạn (hoàn thành toàn bộ trước 16:00 ngày 29/11)

Lập ngày 25/11/2026. Mỗi mốc là hạn **merge PR** (không phải hạn bắt đầu làm). Trễ hơn nửa buổi thì báo ngay trong nhóm chat.

| Hạn | Việc (mã, người) | Vì sao đúng mốc này |
|---|---|---|
| **25/11, 22:00** | Merge PR ETL; Tùng nhắn Ngọc Anh dùng migration **0004** | Mở khóa cho cả nhóm |
| **25/11, 23:00** | **T8a** Tùng: bộ lập lịch tự chạy hằng ngày. **Hạn cứng 27/11, 20:00** | Cần chạy đủ 3 ngày liên tục trước 30/11 |
| **26/11, 12:00** | **N1** Ngọc Anh: migration 0004, seed chiều, bảng lịch sử ETL, script chất lượng | Tùng nạp `dw` và ghi lịch sử ETL |
| **26/11, 12:00** | **T0** Tùng: gán tập vàng (tối thiểu 140 dòng) | Chấm điểm M1 |
| **26/11, 12:00** | **T5** Tùng: Superset trong Docker Compose | Ngọc Anh và Hưng dựng dashboard |
| **26/11, 18:00** | **HA1** Hoàng Anh: nhãn LLM khoảng 4.000 mẫu, TF-IDF | M1 và M2 cần để huấn luyện |
| **26/11, 18:00** | **HU1** Hưng: sửa Decimal, `from_dttm`, KPI-09 theo kỳ hai tuần | API KPI và dashboard |
| **26/11, 18:00** | **TA2** Thái Anh: rà `dim_event` (và TA1 nếu còn làm) | E2 và đặc trưng sự kiện của M3 |
| **27/11, 12:00** | **N0, TA0, HA0, HU0**: gán tập vàng (tối thiểu 140 dòng mỗi người) | Đánh giá M1, M2 và kappa |
| **27/11, 18:00** | **T4** Tùng: collector YouTube, báo chí, Trends, thông tin ứng dụng | Chuyển mã vào repo, dữ liệu đã có |
| **28/11, 12:00** | **T2 (1)** Tùng: M1 chấm điểm toàn bộ vào `fact_review` | T3, KPI, M3, bất thường |
| **28/11, 18:00** | **T2 (2)** E1 và API `sentiment.py`; **TA3** Thái Anh: M2, E2, API `aspects.py`; **N2** Ngọc Anh: M3, E4, API `forecast.py`; **N3** dashboard 5, 6; **N4** bất thường và API; **N6** OLAP; **HA2** website nối API và API tìm kiếm; **HA3** JWT; **HU2** API KPI, BHI và dashboard 1 đến 4; **HU3** API cảnh báo | Lõi sản phẩm (P2); N4 sớm vì T7 cần |
| **28/11, 20:00** | **T3** Tùng: `fact_platform_period` | Sau khi M1 chấm điểm |
| **29/11, 10:00** | **T7** Tùng: cảnh báo và khuyến nghị tự sinh | Cần N4 và HU2 |
| **29/11, 12:00** | **T6** chatbot (tầng 1, tầng 2 nếu kịp); **T8b** email n8n; **N5**; **TA4** cảm xúc báo chí; **HA4**, **HA5**; **HU4**, **HU5**, **HU6**, **HU7** | P3, **đóng băng tính năng lúc 12:00** |
| **29/11, 16:00** | **T11** Tùng: kiểm thử tích hợp trên máy sạch (mục D), README, báo cáo kỹ thuật. **Hoàn thành toàn bộ** | Dự phòng 30/11 |

**Cắt trước khi trễ:** T10 (M4 phân cụm, E3) bỏ nếu không còn thời gian; T6 chỉ làm tầng 1 nếu tầng 2 không kịp; TA1 (thu thập sâu) là tùy chọn.

## Việc của từng người (đối chiếu danhsachnhom.md)

### Tùng (nhóm trưởng)
| Mã | Mức | Việc |
|---|---|---|
| T0 | P1 | Gán tay tập vàng (tối thiểu 140 dòng, tệp gán nhãn v2 giao 280 dòng mỗi người) |
| T1 | P1 | ETL raw, clean, dw (nạp `reviews.csv` 28.638 dòng, báo chí) và **lịch sử ETL** |
| T2 | P2 | M1 cảm xúc (PhoBERT) và **thí nghiệm E1**; khung backend và API M1 (`sentiment.py`) |
| T3 | P2 | Tác vụ tổng hợp `fact_platform_period` |
| T4 | P2 | Collector **YouTube, báo chí RSS, Google Trends, thông tin ứng dụng** đưa vào `src/etl/collectors/` (dữ liệu đã thu, cần mã tái chạy được trong repo) |
| T5 | P2 | Docker Compose đủ dịch vụ (PostgreSQL, API, thêm Superset, n8n khi có) |
| T6 | P3 | Chatbot LLM (hai tầng: truy vấn có tham số, rồi Text-to-SQL chỉ đọc; giải thích kết quả mô hình) |
| T7 | P3 | Khuyến nghị và cảnh báo tự sinh (ghi `fact_alert`, kèm số liệu dẫn chứng và bộ phận phụ trách) |
| T8a | **P2, bật trước tối 27/11** | **Bộ lập lịch tự chạy hằng ngày** (collector rồi ETL, chấm điểm, tổng hợp), ghi lịch sử ETL; giữ chạy liên tục để đạt chỉ tiêu **pipeline tự chạy ít nhất 3 ngày** của đề cương |
| T8b | P3 | Workflow n8n: gửi email cảnh báo khi vượt ngưỡng (và lịch ETL nếu chọn n8n làm bộ lập lịch) |
| T10 | P3 | M4 phân cụm chủ đề và E3 (tùy chọn) |
| T11 | P3 | Tích hợp, kiểm thử, tổng hợp báo cáo kỹ thuật (kết quả E1, E2, E4, câu hỏi Q1 đến Q6), nộp bài |

### Ngọc Anh
| Mã | Mức | Việc |
|---|---|---|
| N0 | P1 | Gán tay tập vàng (tối thiểu 140 dòng, tệp gán nhãn v2 giao 280 dòng mỗi người) |
| N1 | P1 | Galaxy schema và ERD (đã có, gồm `fact_review_aspect`, `fact_forecast`, `fact_alert`); migration **0004** (0003 đã dùng cho bảng bài báo `clean.news_article`, Tùng đã làm) **thêm bảng lịch sử ETL và bảng nhật ký chất lượng dữ liệu** (hiện chưa có trong schema); seed chiều tĩnh (`dim_time`, `dim_aspect`, `dim_platform`, `dim_source`, `dim_model`); script kiểm tra chất lượng; view chỉ đọc cho dashboard và chatbot |
| N2 | P2 | M3 dự báo và **thí nghiệm E4**; API `forecast.py` |
| N3 | P2 | Dashboard Superset số 5 (Dự báo và khuyến nghị) và số 6 (Sức khỏe pipeline, chất lượng dữ liệu), **có bộ lọc và drill-down** |
| N4 | P3 | Phát hiện bất thường bằng quy tắc thống kê; API `anomaly.py` |
| N5 | P3 | Mở rộng: cảm xúc theo phiên bản ứng dụng và cảnh báo bản phát hành bị đánh giá thấp; tỷ lệ đánh giá trùng nội dung |
| N6 | P2 | **OLAP trên `dw`**: tài liệu và 5 truy vấn mẫu cho roll-up, drill-down, slice, dice, pivot (đề cương mục 2, kho dữ liệu hỗ trợ OLAP; chưa giao ai, giao thêm ngày 25/11) |

### Thái Anh
| Mã | Mức | Việc |
|---|---|---|
| TA0 | P1 | Gán tay tập vàng (tối thiểu 140 dòng, tệp gán nhãn v2 giao 280 dòng mỗi người) |
| TA1 | P1 | Collector Google Play, App Store (đã có); thu thập sâu bổ sung phần còn mỏng |
| TA2 | P1 | Bảng sự kiện `dim_event` và rà lại các dòng "cần kiểm tra" |
| TA3 | P2 | M2 khía cạnh (ABSA) và **thí nghiệm E2**; API `aspects.py` |
| TA4 | P3 | **Chấm cảm xúc báo chí** vào `dw.fact_news_sentiment` (đề cương có bảng này, KPI-07 và đặc trưng của M3 dùng nó, nhưng đề cương và `danhsachnhom.md` chưa giao cho ai; giao thêm ngày 25/11) |

### Hoàng Anh
| Mã | Mức | Việc |
|---|---|---|
| HA0 | P1 | Gán tay tập vàng (tối thiểu 140 dòng, tệp gán nhãn v2 giao 280 dòng mỗi người) |
| HA1 | P1 | Chạy LLM gán nhãn (khoảng 4.000 đánh giá, cảm xúc và khía cạnh sơ bộ) và đo độ khớp với nhãn người (kappa); mô hình nền TF-IDF |
| HA2 | P2 | Website (giao diện) nối API thật thay dữ liệu mẫu; API tìm kiếm và lọc đánh giá (`reviews.py`) |
| HA3 | P2 | API xác thực và phân quyền JWT (Admin, Viewer), bảo vệ các điểm cuối |
| HA4 | P3 | API nút "Cập nhật dữ liệu" (`refresh.py`); API quản lý nguồn dữ liệu và bảng sự kiện (`sources.py`) |
| HA5 | P3 | Nhúng Superset kèm điểm cuối guest token (`embed.py`); kiểm thử người dùng |

### Hưng
| Mã | Mức | Việc |
|---|---|---|
| HU0 | P1 | Gán tay tập vàng (tối thiểu 140 dòng, tệp gán nhãn v2 giao 280 dòng mỗi người) |
| HU1 | P1 | Sửa tồn đọng: `Decimal` trong `compute_bhi`, `from_dttm` cho 6 KPI SQL, thống nhất KPI-09 theo đề cương (kỳ hai tuần) |
| HU2 | P2 | API KPI và BHI (`kpi.py`); dashboard Superset số 1 đến 4, **có bộ lọc và drill-down** |
| HU3 | P2 | API xem cảnh báo và đánh dấu đã xử lý (`alerts.py`) |
| HU4 | P3 | Mục khuyến nghị hành động trên website |
| HU5 | P3 | Sentiment Index có trọng số lượt hữu ích (mở rộng) |
| HU6 | P3 | Kịch bản demo và slide |
| HU7 | P3 | Bộ công cụ kiểm tra cho nhóm: script kiểm tra trước khi tạo PR (chuyển từ Tùng, trước đây là T9) |

## Thí nghiệm bắt buộc (đề cương mục 8.3)

| Mã | Nội dung | Người | Mức |
|---|---|---|---|
| E1 | So sánh mô hình sentiment: TF-IDF với Logistic Regression, PhoBERT, LLM zero-shot; macro-F1 trên tập kiểm thử và chéo nền tảng | Tùng (T2) | P2 |
| E2 | Điểm sao so với cảm xúc văn bản quanh sự kiện đã biết; tỷ lệ lệch pha | Thái Anh (TA3) | P2 |
| E4 | Mô hình dự báo có và không có đặc trưng cảm xúc, sự kiện, cùng baseline; MAE, RMSE theo walk-forward | Ngọc Anh (N2) | P2 |
| E3 | Đối chiếu độc lập (tùy chọn) | Tùng (T10) | P3 |

## Ràng buộc: ai xong trước thì ai mới làm tiếp được

**Chặn cứng (không có đầu vào thì không làm được)**

| # | Phải xong trước | Thì mới làm được | Cách làm song song trong lúc chờ |
|---|---|---|---|
| R1 | N1: migration 0004 và **seed chiều** (`dim_time`, `dim_aspect`, `dim_platform`, `dim_source`, `dim_model`) | T1 nạp `dw.fact_review` (khóa ngoại cần chiều); ghi lịch sử ETL | Tùng làm xong `raw` và `clean` trước, `dw` sau |
| R2 | T1: ETL nạp dữ liệu thật | HU2 (số KPI thật), HA2 (website số thật), N3 và HU2 (dashboard có dữ liệu), T3, N2, N4 | Viết truy vấn, hợp đồng API, giao diện trên dữ liệu mẫu nhỏ trong `src/database/seed/` |
| R3 | HA1: nhãn LLM khoảng 4.000 mẫu | T2 huấn luyện M1; TA3 huấn luyện M2; HA1 chạy TF-IDF | Chạy thử quy trình huấn luyện trên mẫu nhỏ hoặc nhãn giả để sửa lỗi mã trước |
| R4 | Tập vàng của cả nhóm (T0, N0, TA0, HA0, HU0) | Đánh giá macro-F1 của M1, M2; kappa LLM với người (HA1); E1 | Huấn luyện không cần tập vàng, chỉ phần chấm điểm cuối cần |
| R5 | T2: M1 chấm điểm toàn bộ vào `fact_review` | T3 (`sentiment_index`, `negative_rate`, `bhi`), rồi HU2 (BHI, SI), N2 (mục tiêu dự báo), N4, T7 | HU2 làm trước các KPI không cần cảm xúc (số đánh giá, sao trung bình, `avg_rating`) |
| R6 | TA3: M2 ghi `fact_review_aspect` | KPI theo khía cạnh, M3 đặc trưng khía cạnh, cảnh báo theo khía cạnh, E2 | Làm phần chưa cần khía cạnh trước |
| R7 | TA2: `dim_event` đã rà | E2 (TA3), đặc trưng sự kiện của M3 (N2) và E4, gắn nhãn sự kiện cho bất thường (N4) | Chạy M3 không có đặc trưng sự kiện trước (đúng cấu hình E4 "không sự kiện") |
| R8 | N4 (bất thường) và HU2 (KPI) | T7 sinh cảnh báo vào `fact_alert`, rồi T8b (email n8n) và HU3 (xem cảnh báo, có dữ liệu thật) | HU3 viết API và kiểm thử trên cảnh báo chèn tay |
| R9 | HA3: JWT | HA4 (Admin gọi cập nhật), HA5 (guest token chỉ cho người đăng nhập), HU3 (chỉ Admin đánh dấu) | Viết điểm cuối trước, gắn bảo vệ sau khi HA3 merge |
| R10 | T5: Superset trong Docker Compose (một dịch vụ dùng chung) | N3 và HU2 dựng dashboard; HA5 nhúng | Viết truy vấn dataset trước; chỉ **một người** thêm dịch vụ Superset, người kia dùng lại |
| R11 | N1: view chỉ đọc và vai trò `chatbot_ro` | T6 chatbot tầng Text-to-SQL | Tầng 1 (truy vấn có tham số) không cần chờ |
| R12 | Một số API đã chốt hợp đồng | HA2 nối website | Website gọi qua lớp `services/`, dùng dữ liệu mẫu cho đến khi API merge |

| R13 | TA4: cảm xúc báo chí trong `fact_news_sentiment` | KPI-07 (độ lệch báo chí và người học, Hưng), đặc trưng cảm xúc báo chí của M3 (N2), E3 phần (c) | M3 chạy không có đặc trưng báo chí trước; KPI-07 trả 501 có lý do đến khi có dữ liệu |

| R14 | T1: ETL chạy lại được và không sinh trùng | T8a bật lịch tự chạy (mỗi vòng thu thập lại đoạn mới nhất, ETL loại trùng theo `(source, review_id)`) | Dựng lịch và chạy thử bằng dữ liệu mẫu trước khi ETL xong |

**Chặn mềm (cùng một tài nguyên chung)**
- **Số phiên bản migration:** **0003 đã dùng** cho bảng bài báo `clean.news_article` (Tùng, đã làm); N1 lấy **0004**; chatbot (`chatbot_ro`) lấy 0005 trở đi. Ai cần migration thì hỏi Tùng số trước khi viết, merge theo thứ tự; người merge sau đổi `down_revision`.
- **`main.py` và `predict.py`:** mỗi PR chỉ sửa đúng dòng của mình; merge lần lượt, không gộp cùng lúc.
- **`docker-compose.yml`:** T5 là người duy nhất sửa; người khác gửi đoạn cấu hình cần thêm qua nhóm chat.
- **`docs/kpi_bhi.md`:** chỉ Hưng sửa (HU1, HU5).

**Đường găng (chậm một mắt xích là chậm cả nhóm)**
N1 (seed) → T1 (ETL dw) → T8a (bật lịch trước 27/11, chạy song song ở nền); chuỗi chính tiếp: HA1 (nhãn LLM) → T2 (M1 chấm điểm) → T3 → HU2 và N2 → N4 và T7 → T8b, cùng song song với tập vàng (R4) và M2 (R6).
Nên merge N1, T1 và HA1 **trước 26/11**; nếu một trong ba trễ, báo ngay để dời P2.

**Có thể bắt đầu ngay, không chờ ai**
Gán tập vàng (cả nhóm); HU1 (sửa KPI); TA1, TA2 (thu thập sâu, rà sự kiện); N1; T1 (phần `raw`, `clean`); HA1 (nhãn LLM chạy trên `reviews.csv` do Tùng gửi); HA2 (giao diện trên dữ liệu mẫu); T4 (collector).

## Việc chung

- **Dữ liệu:** `reviews.csv`, báo chí, Trends, thông tin ứng dụng nằm ở máy Tùng (`data/raw/`, không có trong Git). Gửi cho nhóm qua kênh riêng, không qua Git.
- **README:** Tùng viết khung, mỗi người điền mục của mình (cách chạy, đã làm, chưa làm) trước 29/11. Phần nào chưa kịp thì ghi rõ là hạn chế, không ghi như đã xong.
- **Vướng quá nửa buổi** thì báo ngay trong nhóm chat.
- Phần P3 không kịp trước đóng băng thì ghi rõ trong README là chưa hoàn thành.
