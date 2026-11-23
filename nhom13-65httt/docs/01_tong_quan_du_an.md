# 01. TỔNG QUAN DỰ ÁN VÀ ĐẶC TẢ YÊU CẦU

## 1. Thông Tin Chung Đề Tài
- **Tên đề tài:** Hệ thống Quản lý Tài chính Cá nhân Thông minh tích hợp Thu thập Dữ liệu Tự động, AI phân loại và dự báo, trực quan hóa bằng Apache Superset.
- **Mã nhóm:** `nhom13-65httt`
- **Học phần:** Hệ thống Kinh doanh Thông minh (HTKDTM)
- **Giảng viên hướng dẫn:** ThS. Đỗ Oanh Cường

---

## 2. Bối Cảnh Thực Tế & Xác Định Vấn Đề
### 2.1. Bối cảnh thực tế
Trong kỷ nguyên số và thanh toán không dùng tiền mặt, một cá nhân trung bình tại Việt Nam (đặc biệt là sinh viên và nhân viên văn phòng trẻ) thường sử dụng:
- 2–3 tài khoản ngân hàng (Vietcombank, MB Bank, Techcombank, TPBank,...).
- 2–3 ví điện tử (MoMo, ZaloPay, ShopeePay,...).
- Nhiều nền tảng thương mại điện tử và dịch vụ số (Shopee, Grab, Be, Baemin,...).

Dữ liệu giao dịch phát sinh rời rạc, phân mảnh nghiêm trọng trên các hệ sinh thái đóng, không có cơ chế tập trung dữ liệu một cách an toàn.

### 2.2. Vấn đề cốt lõi
- **Hiện tượng "Mù mờ dòng tiền vi mô" (Micro-spending Blindness):** Người dùng không nhận biết được việc tích tiểu thành đại từ các khoản chi tiêu nhỏ lặp đi lặp lại hàng ngày (cà phê, trà sữa, phí dịch vụ, mua sắm ngẫu hứng - "Hiệu ứng Latte"), làm cạn kiệt nguồn tiền tiết kiệm.
- **Rào cản ghi chép thủ công (Data Entry Friction):** Thói quen nhập tay vào các app chi tiêu (Money Lover, MISA, Notion, Excel) thường nhanh chóng thất bại sau 1–2 tuần vì mất thời gian, dễ quên và gây nản lòng.
- **Rủi ro bảo mật từ các app kết nối ngân hàng bên thứ ba:** Việc cấp quyền đăng nhập tài khoản trực tiếp hoặc ủy quyền mở cho các ứng dụng không rõ nguồn gốc tiềm ẩn nguy cơ lộ lọt dữ liệu tài chính nhạy cảm.
- **Thiếu tính năng BI đa chiều và phân tích dự báo:** Các ứng dụng thông thường chỉ dừng lại ở các biểu đồ tròn/cột tĩnh lịch sử, không có khả năng khoan sâu (drill-down), lọc chéo đa chiều và thiếu cảnh báo dự báo trước dòng tiền trong tương lai.

---

## 3. Năm Câu Hỏi Nghiệp Vụ Cốt Lõi (Core Business Questions)
Hệ thống được thiết kế để giải quyết triệt để 5 bài toán quản trị tài chính cá nhân:
1. **Tỷ lệ tiết kiệm ròng hàng tháng là bao nhiêu?**
   $$\text{Net Savings Rate} = \frac{\text{Tổng Thu Nhập Thực} - \text{Tổng Chi Tiêu Thực}}{\text{Tổng Thu Nhập Thực}} \times 100\%$$
   *(Đã loại bỏ các giao dịch chuyển tiền nội bộ giữa các tài khoản của chính mình).*
2. **Danh mục chi tiêu nào đang vượt trần ngân sách và vượt bao nhiêu phần trăm?**
   - So sánh ngân sách hạn mức của từng danh mục (Ăn uống, Giải trí, Mua sắm,...) so với thực chi lũy kế trong tháng.
3. **Chi tiêu tập trung vào khung giờ và ngày nào trong tuần?**
   - Phân tích Heatmap thời gian chi tiêu để phát hiện "giờ vàng tiêu tiền theo cảm xúc" (ví dụ: khuya muộn mua hàng online, cuối tuần ăn uống quá mức).
4. **Với tốc độ chi tiêu hiện tại, số dư cuối tháng dự kiến là bao nhiêu?**
   - Sử dụng mô hình chuỗi thời gian (Prophet / ARIMA) để tính Burn-rate và dự phóng ngày có thể bị thâm hụt tài khoản.
5. **Tuần qua có giao dịch nào bất thường cần xem lại không?**
   - AI tự động đánh dấu (Anomaly Detection) các khoản trừ tiền đột biến, phí ẩn phát sinh, giao dịch lặp bất thường.

---

## 4. Đánh Giá Phê Phán Các Giải Pháp Hiện Có

| Tiêu chí | Ghi chép truyền thống (Excel / Sheets) | App chi tiêu thủ công (Money Lover, MISA) | App liên kết ngân hàng (Timo, Fintech) | BI doanh nghiệp thuần (PowerBI, Tableau) | **Giải pháp của Nhóm 13 (Đề xuất)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nhập liệu** | Thủ công 100% | Thủ công + quét hóa đơn cơ bản | Tự động đọc SMS / API mở | Nhập thủ công file CSV tĩnh | **Bán tự động đa kênh (Email IMAP, CSV/PDF, Telegram Bot OCR)** |
| **Bảo mật** | Cao (cá nhân tự giữ) | Trung bình (lưu server bên thứ 3) | Thấp (phải cấp tài khoản ngân hàng) | Cao (tự quản lý) | **Tuyệt đối an toàn (Self-hosted, Docker, chỉ đọc thông báo 1 chiều)** |
| **Khả năng làm sạch & Khử trùng** | Thủ công | Không có | Phụ thuộc ngân hàng | Hạn chế (Power Query) | **Pipeline tự động (Jaro-Winkler, Levenshtein, Log_Dedup)** |
| **Phân loại tiếng Việt** | Không có | Luật từ khóa cứng (Rule-based) | Phân loại thô | Không có | **NLP / LLM tiếng Việt nhận thức ngữ cảnh** |
| **Phân tích dự báo** | Không có | Không có | Thống kê cơ bản | Cần viết thêm script rời | **Mô hình chuỗi thời gian Prophet/ARIMA & Isolation Forest** |
| **Trực quan hóa** | Biểu đồ cơ bản | Biểu đồ di động cố định | Thống kê cơ bản | Rất mạnh | **Chuẩn BI doanh nghiệp với Apache Superset (Sankey, Heatmap, Drill-down)** |

---

## 5. Mục Tiêu Dự Án & Bộ Tiêu Chí Đánh Giá (KPIs)

### 5.1. Mục tiêu tổng quát
Xây dựng một hệ thống hoàn chỉnh từ khâu tiếp nhận thông báo giao dịch, tự động chuẩn hóa - làm sạch - khử trùng, phân loại thông minh bằng AI, nạp vào Data Warehouse chuẩn Star Schema và biểu diễn trực quan trên nền tảng Apache Superset.

### 5.2. Bộ chỉ số đo lường chất lượng & KPI

#### A. Tiêu chí Kỹ thuật Dữ liệu (Data Engineering)
- **Tỷ lệ bóc tách thành công (Extraction Success Rate):** $\ge 95\%$ với các định dạng email/sao kê chuẩn của 3 ngân hàng/ví điện tử phổ biến tại Việt Nam.
- **Độ toàn vẹn dữ liệu:** $100\%$ giao dịch trùng lặp (giữa email biến động tức thời và sao kê tải định kỳ) được phát hiện và xử lý ghi nhận vào bảng `log_dedup`.
- **Độ mới dữ liệu (Freshness):** $\le 24$ giờ đối với luồng batch tự động; $\le 1$ phút đối với ảnh biên lai gửi qua Telegram Bot.
- **Độ đầy đủ (Completeness):** $\ge 98\%$ bản ghi có đầy đủ ngày giao dịch, số tiền, tài khoản nguồn/đích.
- **Độ chính xác (Accuracy):** $\ge 98\%$ bản ghi kiểm tra khớp hoàn toàn với sao kê gốc (trên mẫu ngẫu nhiên 50 dòng).
- **Độ tin cậy pipeline:** $\ge 95\%$ lần chạy batch theo lịch thành công không bị gián đoạn.

#### B. Tiêu chí Trí tuệ Nhân tạo (AI/ML Performance)
- **Độ chính xác phân loại danh mục (F1-Score / Accuracy):** $\ge 85\%$ trên tập kiểm thử nội dung chuyển khoản tiếng Việt không dấu, viết tắt.
- **Sai số dự báo dòng tiền (MAPE):** Sai số tổng chi tiêu tháng $\le 15\%$ so với thực tế chi tiêu.
- **Phát hiện bất thường:** Phát hiện chính xác các giao dịch lệch chuẩn vượt ngưỡng $2.5\sigma$ hoặc thuộc nhóm cô lập (Isolation Forest).

#### C. Tiêu chí Trực quan hóa & Trải nghiệm (BI Usability)
- **Tốc độ phản hồi Dashboard:** Thời gian nạp toàn bộ widget biểu đồ và lọc chéo $\le 2$ giây.
- **Giải quyết nghiệp vụ:** Thỏa mãn $5/5$ câu hỏi nghiệp vụ tài chính cốt lõi.

---

## 6. Công Nghệ Áp Dụng (Tech Stack)

| Thành phần | Công nghệ lựa chọn | Mục đích sử dụng |
| :--- | :--- | :--- |
| **Ngôn ngữ cốt lõi** | Python 3.10+ | Lập trình pipeline ETL, AI models, backend API |
| **Backend API** | FastAPI / Uvicorn | Cung cấp RESTful API phân loại, dự báo và tích hợp |
| **Cơ sở dữ liệu & DW** | PostgreSQL 15+ | Lưu trữ Staging và kho dữ liệu phân tích Star Schema |
| **Business Intelligence** | Apache Superset | Nền tảng trực quan hóa đa chiều, phân tích lát cắt |
| **OCR & Thị giác máy** | Tesseract OCR / PaddleOCR | Trích xuất chữ và con số từ ảnh biên lai, hóa đơn |
| **NLP & Học máy** | Scikit-learn, HuggingFace/PhoBERT, Prophet | Phân loại ngữ cảnh tiếng Việt, phát hiện bất thường, dự báo chuỗi thời gian |
| **Thu thập dữ liệu** | Google API Client (Gmail), IMAP, python-telegram-bot | Kết nối hộp thư đến và kênh nhận ảnh biên lai |
| **Điều phối tác vụ** | APScheduler / Python Cronjob | Lập lịch chạy batch ETL hàng ngày/hàng giờ |
| **Đóng gói & Vận hành** | Docker & Docker Compose | Đảm bảo tính nhất quán môi trường triển khai |
