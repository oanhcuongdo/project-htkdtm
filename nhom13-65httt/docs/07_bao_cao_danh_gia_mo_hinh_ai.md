# 07. BÁO CÁO ĐÁNH GIÁ ĐỘ CHÍNH XÁC CÁC MÔ HÌNH AI (GIAI ĐOẠN 3)

- **Đề tài:** Hệ thống Quản lý Tài chính Cá nhân Thông minh tích hợp Thu thập Dữ liệu Tự động, AI phân loại và dự báo, trực quan hóa bằng Apache Superset.
- **Nhóm thực hiện:** `nhom13-65httt`
- **Phụ trách chính module AI:** Trương Quốc Thái (cùng nhóm trưởng tích hợp)
- **Thời điểm đánh giá:** `2026-11-25`

---

## 1. Tổng Hợp Kết Quả Đối Chiếu KPI Đề Cương

| Mô hình AI | Chỉ số đo lường | Ngưỡng mục tiêu Đề cương | Kết quả thực đo | Trạng thái |
| :--- | :--- | :---: | :---: | :---: |
| **1. NLP Phân loại danh mục tiếng Việt** | Weighted F1-Score / Accuracy (tập toàn bộ 1.028 mẫu) | $\ge 85.0\%$ | **98.62% F1 / 98.54% Acc** | ✅ **ĐẠT** |
| **1b. NLP Kiểm thử khắt khe (Unseen Slang)** | Weighted F1-Score / Accuracy (chỉ chuỗi không dấu/viết tắt chưa từng thấy) | $\ge 85.0\%$ | **89.88% F1 / 90.20% Acc** | ✅ **ĐẠT** |
| **1c. Kiểm chứng chéo 5-Fold CV** | 5-Fold Cross-Validation Weighted F1 | $\ge 85.0\%$ | **96.06% $\pm$ 1.61%** | ✅ **ĐẠT** |
| **2. Dự báo dòng tiền (SARIMAX/ARIMA)** | Sai số dự báo tổng chi tiêu tháng (**MAPE**) | $< 15.0\%$ | **8.77%** | ✅ **ĐẠT** |
| **3. Phát hiện bất thường (Ensemble)** | Isolation Forest + Z-Score ($> 2.5\sigma$) | Phát hiện chính xác giao dịch đột biến | **8/716 giao dịch (1.12%)** | ✅ **ĐẠT** |

---

## 2. Đánh Giá Chi Tiết Mô Hình 1: NLP Phân Loại Danh Mục Giao Dịch Tiếng Việt

### 2.1. Kiến trúc mô hình
- **Tiền xử lý (`vietnamese_text.py`):** Chuẩn hóa Unicode, chuyển tiếng Việt sang không dấu đồng nhất, loại bỏ mã giao dịch tự sinh của ngân hàng (`MBVCB.*`, `FT\d+`, `CUSTOMER`, số dài $\ge 5$ chữ số), mở rộng từ điển viết tắt ngân hàng (`ck` $\rightarrow$ `chuyen khoan`, `cty` $\rightarrow$ `cong ty`, `t1..t12` $\rightarrow$ `thang`, `cf` $\rightarrow$ `ca phe`, `bh` $\rightarrow$ `bao hiem`).
- **Tầng phân loại lai (Hybrid Architecture):**
  1. *High-Precision Rule Matcher:* Nhận diện tức thời các mẫu tuyệt đối rõ ràng (`MOMO-CASHIN`, `Tra lai tien gui`, `EVN`, `CGV`, `Highlands Coffee`, `Long Chau`).
  2. *Machine Learning Pipeline:* `FeatureUnion` kết hợp **Word TF-IDF (1-2 gram)** và **Character-WB TF-IDF (3-5 gram)** (bắt chính xác lỗi gõ thiếu dấu cách như `chuye n tien nha tro` hoặc từ dính `muathecao`), đưa qua **Calibrated `LinearSVC` (`C=1.2`, `class_weight="balanced"`)** để xuất xác suất tin cậy cho từng danh mục.

### 2.2. Kết quả chi tiết theo từng danh mục (Tập kiểm thử 206 mẫu / 13 lớp)

| ID | Tên danh mục | Precision | Recall | F1-Score | Support |
| :-: | :--- | :---: | :---: | :---: | :---: |
| 1 | Ăn uống & Cà phê | 1.000 | 1.000 | 1.000 | 64 |
| 2 | Tiền thuê nhà & Phòng trọ | 1.000 | 0.833 | 0.909 | 6 |
| 3 | Điện nước & Internet | 1.000 | 1.000 | 1.000 | 8 |
| 4 | Xăng xe & Đi lại | 1.000 | 0.957 | 0.978 | 23 |
| 5 | Chăm sóc sức khỏe & Y tế | 1.000 | 1.000 | 1.000 | 15 |
| 6 | Mua sắm & Đồ dùng | 1.000 | 1.000 | 1.000 | 25 |
| 7 | Giải trí & Phim ảnh | 1.000 | 1.000 | 1.000 | 16 |
| 8 | Gặp gỡ bạn bè & Tiệc tùng | 1.000 | 1.000 | 1.000 | 17 |
| 10 | Quỹ tiết kiệm dự phòng | 1.000 | 1.000 | 1.000 | 6 |
| 12 | Lương cố định hàng tháng | 1.000 | 1.000 | 1.000 | 6 |
| 13 | Thưởng & Thu nhập ngoài (Freelance) | 0.727 | 1.000 | 0.842 | 8 |
| 14 | Lãi tiền gửi & Cổ tức | 1.000 | 1.000 | 1.000 | 3 |
| 15 | Chuyển tiền nội bộ giữa các ví | 1.000 | 0.889 | 0.941 | 9 |
| | **Macro Avg** | **0.979** | **0.975** | **0.975** | **206** |
| | **Weighted Avg** | **0.989** | **0.985** | **0.986** | **206** |

### 2.3. Ma trận nhầm lẫn (Confusion Matrix - 13 Danh mục)

*Hàng: Nhãn thực tế (True Category ID) — Cột: Nhãn dự đoán (Predicted Category ID)*

| True \ Pred | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 10 | 12 | 13 | 14 | 15 |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **1** | **64** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **2** | 0 | **5** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| **3** | 0 | 0 | **8** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **4** | 0 | 0 | 0 | **22** | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| **5** | 0 | 0 | 0 | 0 | **15** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **6** | 0 | 0 | 0 | 0 | 0 | **25** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **7** | 0 | 0 | 0 | 0 | 0 | 0 | **16** | 0 | 0 | 0 | 0 | 0 | 0 |
| **8** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **17** | 0 | 0 | 0 | 0 | 0 |
| **10** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **6** | 0 | 0 | 0 | 0 |
| **12** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **6** | 0 | 0 | 0 |
| **13** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **8** | 0 | 0 |
| **14** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **3** | 0 |
| **15** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | **8** |

**Nhận xét:** Tổng cộng **203/206** giao dịch trong tập kiểm thử được phân loại hoàn toàn chính xác. 3 trường hợp nhầm lẫn duy nhất đều rơi vào lớp 13 (*Thu nhập ngoài / Chuyển khoản chung*), có thể được khử triệt để khi kết hợp thêm ràng buộc chiều dòng tiền (`direction = INCOME / EXPENSE`) ở tầng suy luận API.

---

## 3. Đánh Giá Chi Tiết Mô Hình 2: Phát Hiện Giao Dịch Bất Thường (Anomaly Detection)

- **Phương pháp:** Ensemble giữa **Isolation Forest** (150 cây, trên 5 đặc trưng chuẩn hóa: `log_amount`, `ratio_to_median`, `z_score`, `is_late_night`, `is_weekend`) và **Category Z-Score ($> 2.5\sigma$)**.
- **Dữ liệu đánh giá:** Toàn bộ **716 giao dịch chi tiêu thực** trong `fact_transactions`.
- **Kết quả phát hiện:** **8 giao dịch bất thường** (tỷ lệ `1.12%`), đã ghi trực tiếp cờ `is_anomaly = TRUE` và `anomaly_score` ngược lại bảng `fact_transactions`:

| Ngày | Số tiền (VND) | Danh mục | Z-Score | Điểm bất thường | Nội dung giao dịch |
| :--- | ---: | :--- | :---: | :---: | :--- |
| `2026-11-15` | `-6,208,600` | Ăn uống & Cà phê | `9.95σ` | `0.9999` | Chuyển tiền lớn (MB Bank) DEN: HA KIEU LIEN |
| `2026-10-10` | `-6,053,200` | Ăn uống & Cà phê | `9.69σ` | `0.9931` | Chuyển tiền lớn (MB Bank) DEN: HA KIEU LIEN |
| `2026-09-12` | `-5,837,800` | Ăn uống & Cà phê | `9.34σ` | `0.9923` | Chuyển tiền lớn (MB Bank) DEN: HA KIEU LIEN |
| `2026-04-15` | `-14,500,000` | Mua sắm & Đồ dùng | `9.19σ` | `0.9644` | Sửa chữa màn hình Laptop MacBook Pro |
| `2026-10-10` | `-5,200,000` | Gặp gỡ bạn bè & Tiệc tùng | `7.62σ` | `0.9235` | Tiệc sinh nhật nhà hàng Sen Tây Hồ |
| `2026-08-22` | `-6,800,000` | Mua sắm & Đồ dùng | `4.06σ` | `0.8244` | Mua máy hút bụi Robot lau nhà (lúc 23h) |
| `2026-06-30` | `-1,250,000` | Ăn uống & Cà phê | `>2.5σ` | `>=0.82` | Phí dịch vụ bất thường lúc 2h sáng |

---

## 4. Đánh Giá Chi Tiết Mô Hình 3: Dự Báo Dòng Tiền 30 Ngày & Burn-Rate

- **Phương pháp:** Chuỗi thời gian **SARIMAX(1,0,1)(1,0,0,7)** nắm bắt chu kỳ chi tiêu hàng tuần + cộng phần lịch thanh toán chi phí cố định (Tiền nhà, Điện nước, Tiết kiệm định kỳ), xuất 30 ngày dự báo (`2026-11-25` $\rightarrow$ `2026-12-24`) kèm khoảng tin cậy $95\%$ vào bảng `ai_spending_forecast`.
- **Kiểm thử ngược (Walk-forward Backtest) trên 10 tháng lịch sử đầy đủ (đánh giá 3 tháng gần nhất):**

| Tháng kiểm thử | Chi tiêu thực tế (VND) | Chi tiêu dự báo (VND) | Sai số tuyệt đối (VND) | APE (%) |
| :---: | ---: | ---: | ---: | :---: |
| `2026-08` | 18,528,000 | 18,716,865 | 188,865 | **1.02%** |
| `2026-09` | 22,426,500 | 18,684,667 | 3,741,833 | 16.68% |
| `2026-10` | 20,900,500 | 19,099,066 | 1,801,434 | **8.62%** |
| **Trung bình (MAPE)** | | | | **8.77% (< 15%) ✅** |

- **Kết quả phân tích Burn-Rate (Tháng `2026-11`):**
  - Thu nhập lũy kế tháng: `26,199,000 VND` | Chi tiêu lũy kế: `22,056,100 VND`
  - Tốc độ đốt tiền trung bình: `919,004 VND/ngày`
  - Chi tiêu cuối tháng dự kiến: `25,773,460 VND` $\rightarrow$ **Số dư cuối tháng dự kiến: `425,540 VND`** (Cảnh báo mức `WARNING` do tỷ lệ sử dụng ngân sách cao).

---

## 5. Danh Sách RESTful API Đã Đóng Gói (Swagger UI: `/docs`)

| Method | Endpoint | Chức năng |
| :---: | :--- | :--- |
| `POST` | `/api/v1/ai/classify` | Phân loại 1 chuỗi mô tả chuyển khoản tiếng Việt |
| `POST` | `/api/v1/ai/classify-batch` | Phân loại hàng loạt nhiều giao dịch |
| `POST` | `/api/v1/ai/train-classifier` | Huấn luyện lại & đánh giá mô hình NLP |
| `POST` | `/api/v1/ai/detect-anomalies` | Chạy Isolation Forest + Z-Score & lưu vào `fact_transactions` |
| `POST` | `/api/v1/ai/forecast` | Chạy dự báo 30 ngày SARIMAX & lưu vào `ai_spending_forecast` |
| `GET` | `/api/v1/ai/burn-rate` | Tính Burn-rate & dự phóng số dư cuối tháng |
| `GET` | `/api/v1/ai/evaluation-report` | Xem báo cáo đánh giá JSON mới nhất của toàn tầng AI |
| `GET` | `/api/v1/analytics/kpi-summary` | Trả lời đồng bộ **5 Câu hỏi Nghiệp vụ Cốt lõi** |
