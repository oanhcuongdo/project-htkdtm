# Prompt giao việc và tiêu chí kiểm thử (Nhóm 03, EduVision BI)

Đi kèm [ke_hoach_hoan_thien_th5.md](ke_hoach_hoan_thien_th5.md). **Mã việc (T1, N2, HU1...) khớp với kế hoạch.** Hạn nộp 30/11/2026 20:34.
Mỗi việc có **prompt** (đưa cho người làm hoặc công cụ hỗ trợ) và **tiêu chí kiểm thử** (người duyệt dùng để quyết định merge). Việc chỉ xong khi đạt **toàn bộ** tiêu chí của nó.

**Hạn:** toàn bộ hoàn thành trước **29/11, 16:00**; đóng băng tính năng **29/11, 12:00**; hạn từng việc (theo mã) xem mục "Lịch hạn" trong [ke_hoach_hoan_thien_th5.md](ke_hoach_hoan_thien_th5.md). Mốc nhanh: P1 xong 26/11, P2 xong 28/11 lúc 18:00, P3 xong 29/11 lúc 12:00. **Số migration:** 0003 đã dùng (bảng bài báo, Tùng); Ngọc Anh dùng 0004.

**Nguồn ngưỡng:** các con số đạt/không đạt lấy từ bảng mức đạt trong đề cương (`docs/De_Cuong_Nhom03.docx`, mục đánh giá): dùng **mức thấp nhất** làm điều kiện bắt buộc, mức cao hơn là mục tiêu. Số nào là đề xuất của nhóm thì ghi rõ "đề xuất". Người làm phải điền **số đo thật** vào PR, không điền số mong muốn. Mô hình không vượt baseline thì báo cáo trung thực kèm phân tích nguyên nhân (đề cương mục 8.2).

| Chỉ số (đề cương) | Mức thấp nhất | Mức mục tiêu |
|---|---|---|
| macro-F1 sentiment (M1) | 0,70 | 0,75 trở lên |
| macro-F1 ABSA, trung bình khía cạnh (M2) | 0,60 | 0,65 trở lên |
| Kappa LLM với nhãn người | 0,50 | 0,60 trở lên |
| Dự báo so baseline (MAE) | Báo cáo trung thực | Tốt hơn baseline |
| Tập vàng | 300 | 500 trở lên (đề cương: khoảng 600) |
| Nhãn LLM sơ bộ cho huấn luyện | 2.000 | 4.000 trở lên |
| Dashboard nhúng vào website | 4 | 6 |
| Chatbot đúng bộ 10 câu mẫu | 6/10 | 8/10 trở lên |
| Pipeline tự chạy liên tục | 3 ngày | 7 ngày trở lên |

---

## A. Quy tắc chung (dán vào cuối mọi prompt)

```text
Quy tắc bắt buộc:
- Chỉ tạo hoặc sửa các tệp thuộc phần việc của mình. Không sửa README.md gốc, .gitignore gốc, _template_nhom/, tệp của người khác.
- Mọi đường dẫn nằm trong nhom03-65httt/.
- Không đưa lên Git: dữ liệu thật (CSV, Excel), .env, khóa API, token, trọng số mô hình, node_modules, dist.
- Dữ liệu thật để ở nhom03-65httt/data/raw/ trên máy mình (đã bị .gitignore chặn). Đường dẫn dữ liệu và khóa lấy từ tham số hoặc biến môi trường, không viết cứng đường dẫn máy cá nhân.
- Không thêm Co-Authored-By hay dòng ghi công công cụ nào vào commit hoặc mô tả PR.
- Thông điệp commit đúng mẫu <loại>(nhom03-65httt): <mô tả không dấu>, một dòng.
- Không git add . ; chỉ git add từng đường dẫn cụ thể.
- Chưa push. Cuối cùng đưa lệnh git add, git commit và kết quả chạy các lệnh kiểm tra trong "Tiêu chí kiểm thử".
- Không bịa số liệu. Chỗ nào chưa làm được thì trả 501 hoặc ghi rõ "chưa làm", không giả vờ đã xong.
- Đọc mục tương ứng trong docs/De_Cuong_Nhom03.docx và src/database/schema/ trước khi viết; không tự đặt tên bảng, khía cạnh, chỉ số ngoài đề cương.
```

## B. Tiêu chí chung cho mọi PR (người duyệt kiểm tra trước)

| # | Tiêu chí | Cách kiểm |
|---|---|---|
| B1 | PR đúng đích: Fork của nhóm trưởng, base `nhom03-65httt` | Đầu trang PR |
| B2 | Mọi tệp trong Files changed bắt đầu bằng `nhom03-65httt/` | Tab Files changed |
| B3 | Không có `.csv`, `.xlsx`, `.env`, `*.pt`, `*.safetensors`, `*.pkl`, `node_modules`, `dist` | `git show --stat --format= HEAD` |
| B4 | Commit đúng mẫu, không `Co-Authored-By` | `git log -1 --format=%B` |
| B5 | Không khóa, mật khẩu, đường dẫn máy cá nhân trong phần thêm | Quét `password`, `api_key`, `secret`, `sk-`, `C:\Users\` trong diff |
| B6 | `pytest` backend vẫn xanh | `cd nhom03-65httt/src/backend && pytest` |
| B7 | Nếu sửa website: `npm run typecheck` và `npm run build` qua | `cd nhom03-65httt/src/frontend` |
| B8 | Nếu thêm migration: chạy lại hai lần không lỗi; `downgrade` một bước rồi `upgrade head` | `alembic upgrade head` |
| B9 | Mô tả PR theo mẫu [review_pull_request.md](review_pull_request.md) | Đọc mô tả |

---

## C0. Gán tay tập vàng (cả nhóm: T0, N0, TA0, HA0, HU0), P1

Tệp gán nhãn thật: `BoGanNhan_EduVision_1200_v2.xlsx` (ngoài Git). Hiện **chưa ai gán** (cả 5 sheet đều 0 dòng có nhãn).

Thông tin đã kiểm tra trong tệp:
- 1.200 mẫu: VUIHOC 250, ELSA Speak 250, DUOLINGO 250, MONKEY 250, HOCMAI 200; trong đó **200 mẫu hai người cùng gán** (cột `is_overlap`), 1.000 mẫu một người gán.
- Mỗi người có sheet riêng (`GN_Tung`, `GN_NgocAnh`, `GN_ThaiAnh`, `GN_HoangAnh`, `GN_HuuHung`) với **280 dòng**. Cột A, B (mã mẫu và văn bản) không sửa; điền cột C đến G.
- Nhãn cảm xúc chung (cột C, bắt buộc): **Tích cực / Trung tính / Tiêu cực / Bỏ qua**.
- Bốn cột khía cạnh (chỉ điền khi đánh giá có nhắc): **Kỹ thuật, Học thuật, CSKH, Giá**, mỗi cột chọn Tích cực, Trung tính, Tiêu cực. Trong kho dữ liệu khía cạnh là Technical, Academic, Customer Service, Pricing, và thêm Other (dành cho mẫu không rơi vào bốn nhóm).
- Số sao bị ẩn ở sheet gán nhãn (nằm ở `Khoa_Master`, không gửi cho người gán).

```text
Việc: mở sheet của mình, đọc sheet Hướng dẫn, gán theo lô 50 dòng. Không sửa cột A, B, không sắp xếp lại, không xóa dòng. Không nhìn nhãn LLM trước khi gán. Trả lại tệp qua kênh riêng của nhóm.
```

**Lệch giữa tệp v2 và đề cương (cần nhóm chốt):** đề cương và `danhsachnhom.md` ghi tập vàng khoảng 600 mẫu, mỗi người khoảng 140 dòng, có lô Quizlet 100 mẫu; tệp v2 là 1.200 mẫu, 280 dòng mỗi người, không có Quizlet. Đề xuất: **mỗi người gán tối thiểu 140 dòng** (đủ vượt mức tối thiểu 300 mẫu của đề cương), cố gắng 280; mẫu hai người cùng gán nên gán trước để tính kappa; sau đó sửa đề cương cho khớp số thật.

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| G1 | Số dòng | Tối thiểu 140 dòng của mình có nhãn cột C (mục tiêu 280) |
| G2 | Giá trị nhãn | Chỉ trong tập quy định (Tích cực, Trung tính, Tiêu cực, Bỏ qua); khía cạnh để trống nếu không nhắc |
| G3 | Cột A, B | Không bị sửa (đối chiếu `item_id` và văn bản với bản gốc) |
| G4 | Mẫu gán đôi | Cả hai người đều có nhãn; tính được Cohen's kappa, ghi số thật (đề cương chỉ đặt ngưỡng kappa cho LLM với người) |
| G5 | Git | Không đưa tệp gán nhãn lên Git |

---

## C1. Tùng

### T1. ETL raw, clean, dw và lịch sử ETL (P1)
Nhánh `nhom03-65httt-tung-etl`. Commit: `feat(nhom03-65httt): etl nap danh gia tu raw qua clean den dw`

```text
Bối cảnh: kho PostgreSQL có schema raw, clean, dw (migration 0001, 0002; đọc src/database/schema/ trước, không bịa tên bảng).
Đầu vào: nhom03-65httt/data/raw/reviews.csv, UTF-8 có BOM, 28.638 dòng, cột: source, product, review_id, author_hash, rating, text, lang_guess, created_at, app_version, thumbs_up, reply_text, crawled_at, platform_group, source_type. Báo chí: data/raw/news/news.csv (platform, origin, title, outlet, link, published_at, collected_at, title_hash).
Việc:
1. src/etl/load_raw.py: nạp nguyên văn vào raw.review_raw.
2. src/etl/transform.py: làm sạch sang clean.review_text (chuẩn hóa khoảng trắng, loại dòng rỗng), loại trùng theo (source, review_id).
3. src/etl/load_dw.py: nạp dim (nền tảng, nguồn, thời gian) và dw.fact_review đúng khóa ngoại; nạp báo chí vào bảng sự kiện nếu schema có.
4. Tham số --input, DSN từ biến môi trường, --truncate (tùy chọn). Chạy lại nhiều lần không sinh trùng.
5. Ghi lịch sử ETL mỗi lần chạy (số dòng đọc, nạp, loại, thời gian, trạng thái) vào bảng lịch sử ETL. Schema 01 và 02 **chưa có** bảng này: dùng bảng do Ngọc Anh thêm ở migration 0004 (N1). Làm N1 trước, hoặc thống nhất tên bảng với Ngọc Anh để cùng làm.
5b. **Việc nối sau khi N1 merge (thuộc Tùng):** sửa `run_etl.py` để ghi từng bước vào bảng lịch sử ETL của N1 (giữ ghi tệp JSONL làm dự phòng khi bảng chưa có hoặc kết nối lỗi); thêm kiểm thử đọc lại bản ghi vừa ghi.
6. Kiểm thử pytest bằng dữ liệu mẫu nhỏ tự tạo, không dùng dữ liệu thật.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| T1.1 | Chạy ETL lần 1 trên `reviews.csv` | `raw.review_raw` đúng **28.638** dòng, không lỗi |
| T1.2 | Chạy lần 2 | Số dòng **không đổi** |
| T1.3 | Đếm theo `source` ở `raw.review_raw` | google_play **23.381**, app_store_vn **3.748**, youtube **1.509**; ở `dw.fact_review` ít hơn đúng số dòng bị loại vì rỗng sau làm sạch (đã đo: 5 dòng, còn 23.378, 3.747, 1.508) |
| T1.4 | Đếm theo `platform_group` ở `raw` | trong_nuoc **13.679**, quoc_te **14.959**; ở `dw.fact_review` còn 13.676 và 14.957 (đã đo) |
| T1.5 | Nền tảng | Đủ **9** nền tảng trong `dw` |
| T1.6 | `rating` | Trong 1 đến 5 (YouTube không có sao: nêu cách xử lý) |
| T1.7 | Khóa | `(source, review_id)` duy nhất ở `clean` |
| T1.8 | Lịch sử ETL | **Hiện tại** mỗi lần chạy ghi một bản ghi vào `data/logs/etl_runs.jsonl` (đã làm, ngoài Git). **Sau khi N1 merge**: `run_etl.py` ghi thêm vào bảng lịch sử ETL, mỗi bước một dòng, có số dòng loại; đây mới là bản đạt tiêu chí |
| T1.9 | Kiểm thử | `pytest` xanh trên dữ liệu mẫu |
| T1.10 | Không lộ dữ liệu | B3 đạt |

### T2. M1 cảm xúc, thí nghiệm E1 và API (P2)
Nhánh `nhom03-65httt-tung-m1`. Commit: `feat(nhom03-65httt): mo hinh cam xuc m1 thi nghiem e1 va api sentiment`

```text
Bối cảnh: M1 phân loại Tích cực, Trung tính, Tiêu cực (đề cương mục 8.1). Huấn luyện trên tập khoảng 4.000 đánh giá do LLM gán nhãn (Hoàng Anh làm, HA1); kiểm định trên tập vàng, không dùng tập vàng để huấn luyện. UIT-VSFC dùng bổ trợ. Baseline TF-IDF kết hợp Logistic Regression (HA1).
Việc:
1. src/ml/sentiment/: fine-tune PhoBERT, seed cố định. Trọng số lưu ở models/ (ngoài Git), cách tải ghi trong models/README.md. Nếu chưa kịp huấn luyện thì dùng mô hình có sẵn làm bản đầu và ghi rõ.
2. Thí nghiệm E1: so TF-IDF+LR, PhoBERT và LLM zero-shot (đối chứng) bằng macro-F1 trên tập kiểm thử và chéo nền tảng (huấn luyện trên nhóm này, kiểm thử trên nhóm kia). Ghi ma trận nhầm lẫn và kappa. Ghi kết quả vào docs/thi_nghiem_e1.md.
3. Chấm điểm toàn bộ dữ liệu, ghi nhãn vào fact_review.
4. src/backend/app/api/sentiment.py: POST /api/v1/predict/sentiment {"text": "..."}. Tải mô hình một lần khi khởi động. Chuyển điểm cuối khỏi predict.py, đăng ký router trong main.py. Có pytest.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| T2.1 | macro-F1 trên tập vàng | **Không dưới 0,70** (mức thấp nhất của đề cương), mục tiêu 0,75; ghi số thật |
| T2.2 | So với baseline | Bảng E1 có đủ 3 mô hình; nếu M1 không vượt baseline phải nêu nguyên nhân |
| T2.3 | Chéo nền tảng | Có kết quả huấn luyện nhóm này, kiểm thử nhóm kia |
| T2.4 | Không rò rỉ | Tập vàng không nằm trong tập huấn luyện |
| T2.5 | Tái tạo | Cùng seed cho chỉ số gần như nhau (nêu sai lệch) |
| T2.6 | API | Câu khen trả `tich_cuc`, câu chê trả `tieu_cuc`, 200 (nhãn chỉ dùng ba giá trị `tich_cuc`, `trung_tinh`, `tieu_cuc` như ràng buộc của schema) |
| T2.7 | Đầu vào sai | `text` rỗng hoặc thiếu: **422**, không 500 |
| T2.8 | Văn bản dài, tiếng Việt có dấu, tiếng Anh | Không sập, kết quả hợp lý |
| T2.9 | Chưa có trọng số | `/health` vẫn 200 và báo rõ chưa nạp mô hình |
| T2.10 | Ghi vào kho | Số dòng có nhãn bằng số dòng ở `clean.review_text` |
| T2.11 | Git | Không trọng số trong Git |

### T3. `fact_platform_period` (P2)
Nhánh `nhom03-65httt-tung-platform-period`. Commit: `feat(nhom03-65httt): tong hop fact platform period`

```text
Việc: tác vụ tổng hợp theo nền tảng và kỳ (số đánh giá, Sentiment Index, tỷ lệ tiêu cực, sao trung bình, tỷ lệ theo khía cạnh...) đúng grain trong đề cương và schema 02. Idempotent: chạy lại ghi đè kỳ cũ, không nhân đôi. Grain trong schema 02 là **một nền tảng x một tháng** (`time_key` = ngày đầu tháng), cột: new_review_count, positive_rate, negative_rate, avg_rating, sentiment_index, bhi, review_share_in_group. Kỳ hai tuần của phát hiện bất thường và KPI-09 **không** lấy từ bảng này (xem N4).
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| T3.1 | Chạy hai lần | Số dòng không đổi |
| T3.2 | Tổng số đánh giá theo nền tảng | Bằng `count(*)` trực tiếp từ `fact_review` |
| T3.3 | Công thức Sentiment Index | Trùng định nghĩa trong `docs/kpi_bhi.md` |
| T3.4 | Kỳ không có dữ liệu | Không sinh dòng giả; ghi nhận trong nhật ký |

### T4. Collector YouTube, báo chí RSS, Google Trends, thông tin ứng dụng (P2)
Nhánh `nhom03-65httt-tung-collectors`. Commit: `feat(nhom03-65httt): collector youtube bao chi google trends va thong tin ung dung`

```text
Bối cảnh: dữ liệu đã thu bằng script ngoài kho; cần mã trong src/etl/collectors/ tái chạy được. Tuân thủ docs/dao_duc_phap_ly.md (API chính thức hoặc RSS, tần suất gọi, không giả trình duyệt, không đổi IP, che thông tin cá nhân). Đọc danh sách nền tảng từ config/platforms.yml.
Việc: bốn collector (youtube, news_rss, google_trends, app_info), cùng giao diện dòng lệnh --only, --out (mặc định ngoài Git), cột đầu ra khớp tệp đã có (reviews: 12 cột chuẩn; news: platform, origin, title, outlet, link, published_at, collected_at, title_hash). Khóa YouTube lấy từ .env. Kiểm thử bằng dữ liệu giả lập, không gọi mạng trong pytest.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| T4.1 | `pytest` | Xanh, không gọi mạng thật |
| T4.2 | Chạy thật `--only "ELSA Speak"` giới hạn nhỏ | CSV đúng cột, UTF-8 có BOM, không trùng khi chạy lại |
| T4.3 | Đạo đức | Không giả trình duyệt, không proxy; có giãn cách giữa các lần gọi |
| T4.4 | Khóa | Không khóa trong mã |
| T4.5 | Git | Không CSV trong PR |

### T5. Docker Compose đủ dịch vụ (P2)
Tiêu chí: `docker compose config` hợp lệ; `up -d --build` lên được postgres (healthy), migrate (Exited 0), api (healthy), và dịch vụ mới (Superset, n8n) khi thêm; mọi cổng chỉ bind `127.0.0.1`; mật khẩu lấy từ `.env`, không có giá trị mặc định yếu trong Git; `docker compose down` sạch.

### T6. Chatbot LLM (P3)
Nhánh `nhom03-65httt-tung-chatbot`. Commit: `feat(nhom03-65httt): chatbot truy van kpi va text-to-sql chi doc`

```text
Bối cảnh: đề cương mục "Tự động hóa và chatbot": chatbot dùng LLM trả lời câu hỏi trên số liệu đã tổng hợp trong kho và giải thích kết quả mô hình, gọi qua API; không tự tạo số liệu không có căn cứ; kiểm thử bằng bộ 10 câu mẫu về chỉ số, nền tảng và cảnh báo.
Việc (hai tầng):
1. Tầng 1: công cụ truy vấn có tham số trên KPI, BHI, cảnh báo có sẵn.
2. Tầng 2: Text-to-SQL chỉ đọc. Migration (hỏi nhóm số trước) tạo vai trò chatbot_ro chỉ SELECT trên view trong schema dw. Kiểm tra SQL bằng pglast: chỉ một câu SELECT, chỉ view cho phép, bắt buộc LIMIT, statement_timeout.
3. LLM chỉ trả lời từ các dòng truy vấn trả về; giải thích kết quả mô hình dựa trên bảng đánh giá mô hình đã lưu. Khóa LLM trong .env.
4. src/backend/app/api/chat.py: POST /api/v1/chat. Bộ 10 câu mẫu kèm đáp án mong đợi trong src/backend/tests/chat_samples.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| T6.1 | Bộ 10 câu mẫu | **Ít nhất 6/10** đúng (mức thấp nhất của đề cương), mục tiêu 8/10 trở lên; ghi số thật |
| T6.2 | `DROP`, `INSERT`, `UPDATE`, nhiều câu nối `;` | Bị từ chối, không thực thi |
| T6.3 | Bảng ngoài danh sách (`raw`, `pg_catalog`) | Bị từ chối |
| T6.4 | Không có `LIMIT` | Tự thêm hoặc từ chối |
| T6.5 | Truy vấn quá lâu | Bị ngắt bởi `statement_timeout` |
| T6.6 | Không có dữ liệu | Trả lời "không có dữ liệu", không bịa số |
| T6.7 | Vai trò `chatbot_ro` | `INSERT` bằng vai trò này bị từ chối |
| T6.8 | Giải thích mô hình | Số F1, MAE nêu ra khớp bảng đánh giá đã lưu |
| T6.9 | Khóa | Chỉ ở `.env`; B5 đạt |

### T7. Khuyến nghị và cảnh báo tự sinh (P3)
Nhánh `nhom03-65httt-tung-canh-bao-tu-sinh`. Commit: `feat(nhom03-65httt): canh bao va khuyen nghi tu sinh`

```text
Bối cảnh: đề cương mục khuyến nghị: mỗi cảnh báo ghi vào fact_alert kèm đề xuất hành động mẫu theo khía cạnh và bộ phận phụ trách, hiển thị trên website và gửi email qua n8n. Cảnh báo sinh từ chỉ số bất thường (Ngọc Anh, N4) và KPI (Hưng).
Việc: dịch vụ sinh cảnh báo từ điểm bất thường và ngưỡng KPI; ghi dw.fact_alert (cột có sẵn: time_key, platform_key, aspect_key, metric_name, metric_value, threshold, detected_at, status). Bảng fact_alert **không có** cột đề xuất hành động hay bộ phận phụ trách: lưu ánh xạ khía cạnh sang đề xuất và bộ phận trong tệp config/ (ví dụ config/khuyen_nghi.yml), API ghép khi trả về; số dẫn chứng là metric_value và threshold. Nếu nhóm muốn lưu thẳng vào bảng thì thêm cột ở migration 0004 trở đi (hỏi Ngọc Anh). Chạy lại không sinh cảnh báo trùng cho cùng sự kiện. API trả cảnh báo thuộc Hưng (HU3), phần này chỉ ghi dữ liệu.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| T7.1 | Điểm bất thường chèn thử | Sinh đúng một cảnh báo có số dẫn chứng |
| T7.2 | Chạy lại | Không sinh trùng |
| T7.3 | Mỗi cảnh báo | Có `metric_name`, `metric_value`, `threshold`, `detected_at`, trạng thái `moi`; khi trả qua API được ghép đề xuất hành động và bộ phận phụ trách từ tệp cấu hình |
| T7.4 | Không bất thường | Không sinh cảnh báo |

### T8a. Bộ lập lịch tự chạy và chỉ tiêu 3 ngày liên tục (P2, bật trước tối 27/11)
Nhánh `nhom03-65httt-tung-lap-lich`. Commit: `feat(nhom03-65httt): lap lich tu chay thu thap va etl hang ngay`

```text
Bối cảnh: đề cương đặt chỉ tiêu "pipeline tự chạy liên tục" tối thiểu 3 ngày, mục tiêu 7 ngày, mở rộng 14 ngày; bằng chứng là lịch sử ETL. Để đủ 3 ngày trước 30/11 phải bật lịch chậm nhất tối 27/11.
Việc:
1. Một lệnh vào duy nhất (ví dụ src/etl/run_pipeline.py) chạy tuần tự: collector (Google Play, App Store, và các nguồn khác trong T4) với --count vừa phải, rồi ETL (T1), rồi chấm điểm cho dòng mới (M1, M2 nếu đã có), rồi cập nhật fact_platform_period, rồi sinh cảnh báo (T7 nếu đã có). Mỗi bước ghi lịch sử ETL (bắt đầu, kết thúc, số dòng, trạng thái); một bước lỗi thì ghi rõ và các bước sau không chạy bậy, vòng sau vẫn chạy được.
2. Không sửa mã collector của người khác. Mỗi vòng thu thập lại đoạn mới nhất; ETL loại trùng theo (source, review_id) nên chạy lại không sinh trùng.
3. Giãn cách và tần suất theo docs/dao_duc_phap_ly.md (không tăng tần suất để lấy nhiều hơn).
4. Lập lịch hằng ngày bằng cách đơn giản trước: Task Scheduler của Windows hoặc dịch vụ cron trong Docker Compose (hoặc n8n nếu đã dựng). Giờ chạy cố định, ghi nhật ký ra tệp ngoài Git.
5. Chạy trên máy luôn bật (tắt chế độ ngủ, bật khởi động lại Docker tự động restart: unless-stopped). Ghi máy nào chạy, từ lúc nào.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| T8a.1 | Chạy tay `run_pipeline.py` một lần | Mọi bước chạy xong, lịch sử ETL có một dòng cho mỗi bước, trạng thái thành công |
| T8a.2 | Chạy hai lần liền | Số dòng ở `dw.fact_review` không tăng thêm khi không có dữ liệu mới |
| T8a.3 | Một bước lỗi (ví dụ tắt mạng) | Bước đó ghi `thất bại` kèm lý do; vòng sau chạy bình thường |
| T8a.4 | Lịch tự chạy | Sau khi bật, mỗi ngày có đúng một vòng tự chạy, không cần ai bấm |
| T8a.5 | Bằng chứng 3 ngày | Truy vấn lịch sử ETL cho thấy **3 ngày liên tiếp** đều có vòng thành công; chụp kết quả vào báo cáo. Nếu chưa đủ, ghi **số ngày thật** |
| T8a.6 | Chạy lại sau khi khởi động máy | Dịch vụ tự dậy lại (Docker restart policy hoặc tác vụ lịch), nêu cách kiểm tra |
| T8a.7 | Tần suất gọi nguồn | Không vượt giới hạn trong `docs/dao_duc_phap_ly.md`; có giãn cách giữa các lần gọi |
| T8a.8 | Git | Không có nhật ký, dữ liệu, khóa trong PR |
| T8a.9 | Dashboard 6 | Hiện được các vòng chạy gần nhất (phối hợp N3) |

### T8b. Workflow n8n gửi email cảnh báo (P3)
Tiêu chí: tệp workflow JSON trong `src/etl/workflows/` nhập vào n8n được; đọc `fact_alert` chưa gửi và gửi email khi vượt ngưỡng, đánh dấu đã gửi để không gửi lặp; thông tin SMTP trong `.env` hoặc kho khóa của n8n, không trong JSON; kiểm thử bằng hộp thư thử (không gửi cho người thật). Nếu nhóm chọn n8n làm bộ lập lịch thì T8a chuyển sang dùng n8n, vẫn giữ nguyên tiêu chí T8a.

### T10. M4 phân cụm và E3 (P3, tùy chọn)
Tiêu chí: BERTopic hoặc embedding kết hợp K-Means trên đánh giá tiêu cực, có silhouette hoặc độ gắn kết chủ đề và diễn giải thủ công; E3 gồm (a), (b), (c) như đề cương mục 8.3, phần (c) ghi rõ chỉ mang tính khám phá. Không làm thì ghi "không thực hiện" trong báo cáo.

### T11. Tích hợp, báo cáo kỹ thuật, nộp (P3, 29 đến 30/11)
Chạy mục D. Báo cáo kỹ thuật có: bài toán BI, thiết kế kho, kết quả E1, E2, E4 (E3 nếu làm), trả lời câu hỏi Q1 đến Q6, mục khuyến nghị hành động, bảng kiểm tra khả thi dữ liệu, hạn chế, ảnh demo. Mỗi con số trong báo cáo phải truy được về một truy vấn hoặc tệp kết quả.

---

## C2. Ngọc Anh

### N1. Bảng kết quả mô hình và nhật ký chất lượng dữ liệu (P1)
Nhánh `nhom03-65httt-ngocanh-bang-ket-qua`. Commit: `feat(nhom03-65httt): migration bang ket qua mo hinh va nhat ky chat luong`

```text
Bối cảnh: schema galaxy 6 fact 7 dim đã có (02). Kết quả M1, M2, M3 ghi vào fact_review, fact_review_aspect, fact_forecast; cảnh báo vào fact_alert (đề cương mục 8.2). KPI-04, 06, 08, 10 cần các bảng này.
Việc:
1. Schema 02 **đã có** dim_aspect, dim_app_version, dim_event, dim_model, fact_review_aspect, fact_platform_period, fact_forecast, fact_news_sentiment, fact_alert. **Chưa có** bảng lịch sử ETL và bảng nhật ký chất lượng dữ liệu: thêm hai bảng này bằng tệp SQL mới (04_...sql) và migration mới. **Số 0003 đã được Tùng dùng** cho bảng bài báo `clean.news_article` (schema/03_schema_news.sql); migration của N1 là **0004**, `down_revision` là `0003`. Nếu cần thêm migration khác thì hỏi nhóm trưởng số kế tiếp. Không sửa tệp đã merge.
2. Bảng lịch sử ETL, thiết kế **khớp với bản ghi mà `src/etl/run_etl.py` (T1) đang ghi ra `data/logs/etl_runs.jsonl`**, một dòng cho mỗi bước của mỗi lần chạy: `run_id` (uuid hoặc bigint, một mã cho cả lần chạy), `step` (`raw`, `clean`, `dw`, có thể thêm `score`, `aggregate`, `alert` cho các bước sau), `started_at`, `finished_at` (timestamptz), `status` (`success`, `failed`, `dry_run`), `input_name` (tên tệp đầu vào, không lưu đường dẫn máy cá nhân), `rows_read`, `rows_inserted`, `rows_dropped` (số nguyên), `error_message` (text, rỗng nếu thành công). Cần chỉ mục theo `started_at` để dashboard 6 và bằng chứng "tự chạy 3 ngày liên tục" (T8a.5) truy vấn nhanh. Bảng nhật ký chất lượng: ngày chạy, nguồn, loại kiểm tra (trùng, thiếu, ngoài miền), số dòng. Truy vấn cho dashboard 6.
3. Dữ liệu khởi tạo (seed) cho các chiều tĩnh, nếu chưa có: dw.dim_time (sinh ngày từ 2020 đến hết 2027), dw.dim_aspect (đúng 5 giá trị: Technical, Academic, Customer Service, Pricing, Other), dw.dim_platform (9 nền tảng từ config/platforms.yml), dw.dim_source (google_play, app_store_vn, youtube, báo chí), dw.dim_model (M1, M2, M3 hai mục tiêu, baseline). Viết thành tệp SQL hoặc script chạy lại được (ON CONFLICT DO NOTHING), nằm ở src/database/seed/. Đây là điều kiện để ETL của Tùng (T1) nạp được fact; chỉ chứa dữ liệu cấu hình tự tạo, không có dữ liệu thật.
4. Script kiểm tra chất lượng dữ liệu src/etl/quality/check_quality.py: chạy các kiểm tra (trùng khóa, thiếu văn bản, sao ngoài 1 đến 5, ngày ngoài miền, mồ côi khóa ngoại) trên raw, clean, dw và ghi kết quả vào bảng nhật ký chất lượng.
5. View chỉ đọc trong schema dw cho dashboard và chatbot (ví dụ dw.v_review_enriched, dw.v_platform_month, dw.v_alert_open): ghép sẵn tên nền tảng, khía cạnh, nhãn, tháng, không lộ cột nhạy cảm. Chatbot (T6) chỉ được truy vấn các view này nên cần chốt tên view cùng Tùng.
6. IF NOT EXISTS (hoặc CREATE OR REPLACE VIEW), COMMENT ON TABLE tiếng Việt, cập nhật docs/erd.md.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| N1.1 | `alembic upgrade head` hai lần | Không lỗi |
| N1.2 | `downgrade -1` rồi `upgrade head` | Không lỗi |
| N1.3 | `/health/db` | Báo đúng phiên bản mới |
| N1.4 | Bảng mới | Khóa ngoại đúng, có comment, `snake_case`, đúng schema |
| N1.5 | Bảng mới | Có bảng lịch sử ETL với các cột nêu ở mục 2 và bảng nhật ký chất lượng; sau khi PR merge, Tùng nối `run_etl.py` ghi vào bảng (T1.8) và `SELECT` thấy lần chạy gần nhất |
| N1.6 | ERD | Khớp SQL |
| N1.7 | Số phiên bản | Không trùng PR khác |
| N1.8 | Nhật ký chất lượng | Sau khi chạy ETL có dòng cho từng nguồn |
| N1.9 | Seed chiều | Chạy hai lần không trùng; `dim_aspect` đúng 5 dòng; `dim_platform` đủ 9 nền tảng; `dim_time` phủ mọi ngày của dữ liệu (kiểm tra bằng `min` và `max` của `created_at`) |
| N1.10 | Script chất lượng | Chạy trên dữ liệu mẫu có lỗi cố tình chèn (sao 7, trùng khóa, văn bản rỗng): mỗi lỗi bị ghi vào nhật ký đúng loại và đúng số dòng |
| N1.11 | View | `SELECT` được bằng vai trò chỉ đọc; không có cột tên thật hoặc hồ sơ tác giả; số dòng khớp bảng gốc |

### N2. M3 dự báo, thí nghiệm E4 và API (P2)
Nhánh `nhom03-65httt-ngocanh-du-bao`. Commit: `feat(nhom03-65httt): mo hinh du bao m3 thi nghiem e4 va api forecast`

```text
Bối cảnh (đề cương mục 8.1, 8.3): M3 dự báo Sentiment Index và tỷ lệ tiêu cực của từng nền tảng cho tháng kế tiếp. Đặc trưng: giá trị các tháng trước, số đánh giá, tỷ lệ theo khía cạnh, sự kiện (cập nhật, mùa thi, khuyến mãi), cảm xúc báo chí, mức quan tâm Google Trends. Phương pháp: LightGBM hoặc hồi quy có điều chuẩn, một mô hình chung cho các nền tảng. Baseline: "kỳ sau giống kỳ này" và trung bình trượt.
Việc:
1. Huấn luyện M3 và hai baseline; chia theo thời gian (walk-forward), không xáo trộn.
2. Đánh giá bằng MAE, RMSE và tỷ lệ dự báo đúng chiều; ghi vào docs/thi_nghiem_e4.md.
3. Thí nghiệm E4: so mô hình có và không có đặc trưng cảm xúc và đặc trưng sự kiện, cùng baseline.
4. Ghi dự báo vào dw.fact_forecast (khóa: nền tảng, tháng, model_key; chỉ có một cột forecast_value). Hai mục tiêu (Sentiment Index và tỷ lệ tiêu cực) ghi bằng **hai dòng dim_model riêng** (ví dụ M3_sentiment_index và M3_negative_rate) để không đổi schema. Số thực tế điền vào actual_value khi có. Giá trị thực lấy từ dw.fact_platform_period (sentiment_index, negative_rate). API src/backend/app/api/forecast.py cho một nền tảng và số kỳ. Có pytest.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| N2.1 | Walk-forward | Tập kiểm định luôn nằm sau tập huấn luyện |
| N2.2 | Chỉ số | Có MAE, RMSE, tỷ lệ đúng chiều cho M3 và cả hai baseline |
| N2.3 | So baseline | Mức thấp nhất: **báo cáo trung thực** (nếu M3 không hơn baseline, nêu nguyên nhân); mục tiêu: tốt hơn baseline |
| N2.4 | E4 | Bảng 4 cấu hình: có và không cảm xúc, có và không sự kiện, kèm baseline |
| N2.5 | API | Nền tảng hợp lệ trả 200 và đủ số kỳ; không tồn tại 404; tham số sai 422 |
| N2.6 | Miền giá trị | Tỷ lệ tiêu cực trong 0 đến 1 (đúng ràng buộc của `negative_rate`), Sentiment Index trong miền định nghĩa ở `docs/kpi_bhi.md`; `ci_lower` không lớn hơn `ci_upper` |
| N2.7 | Ghi kho | `fact_forecast` có dòng cho mỗi nền tảng chính và kỳ, cho cả hai mô hình mục tiêu; ghi lại không vi phạm khóa chính |
| N2.8 | Dữ liệu ít | Nền tảng ít điểm dữ liệu được ghi chú, không báo lỗi |

### N3. Dashboard Superset số 5 và 6 (P2)
Nhánh `nhom03-65httt-ngocanh-superset`. Commit: `feat(nhom03-65httt): superset dashboard du bao va suc khoe pipeline`

```text
Bối cảnh: Superset kết nối trực tiếp schema dw của PostgreSQL và truy vấn bằng SQL (đề cương mục 9). Dashboard 5: Dự báo và khuyến nghị. Dashboard 6: Sức khỏe pipeline và chất lượng dữ liệu. Hưng làm dashboard 1 đến 4 trên cùng hạ tầng; thống nhất cấu hình với Tùng (T5) để chỉ có một dịch vụ Superset.
Việc:
1. Thêm dịch vụ Superset vào docker-compose.yml (cùng Tùng), kết nối chỉ đọc tới dw; tài khoản quản trị và khóa bí mật lấy từ .env, không có giá trị mặc định trong Git. Cổng chỉ bind 127.0.0.1.
2. Dataset từ truy vấn nằm trong src/bi/superset/queries/, mỗi tệp một chỉ số, có chú thích định nghĩa và đơn vị, dùng biến lọc thời gian của Superset.
3. Mọi dashboard có bộ lọc (thời gian, nhóm nền tảng, nền tảng) và **drill-down** (ví dụ từ nhóm trong nước hoặc quốc tế xuống từng nền tảng, từ tháng xuống ngày, từ khía cạnh xuống từng đánh giá) theo yêu cầu mục 13 của đề cương.
4. Dashboard 5: dự báo theo nền tảng kèm giá trị thực tế khi có (fact_forecast.actual_value), khoảng tin cậy, danh sách khuyến nghị từ fact_alert. Dashboard 6: lịch sử ETL, nhật ký chất lượng theo ngày và nguồn, thời điểm cập nhật gần nhất, số dòng theo lớp raw, clean, dw.
5. Xuất định nghĩa dashboard (zip hoặc JSON) vào src/bi/superset/dashboards/ để người khác nhập lại; kiểm tra không lộ mật khẩu hay chuỗi kết nối có mật khẩu trong tệp xuất.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| N3.1 | `docker compose up -d` | Superset lên được, đăng nhập bằng tài khoản trong `.env` |
| N3.2 | Kết nối dw | Truy vấn thử trả số dòng khớp `psql` |
| N3.3 | Dashboard 5 | Có biểu đồ dự báo từng nền tảng; nền tảng chưa có dự báo hiện trạng thái trống, không lỗi |
| N3.4 | Dashboard 6 | Hiện lần chạy ETL gần nhất, số dòng loại, lỗi chất lượng theo nguồn |
| N3.5 | Bộ lọc thời gian | Đổi khoảng ngày thì số liệu đổi đúng |
| N3.6 | Nhập lại | Máy sạch nhập tệp dashboard xong thấy đủ 2 dashboard có dữ liệu |
| N3.7 | Nhúng | Dashboard nhúng được vào website qua guest token (phối hợp HA5) |
| N3.8 | Lộ khóa | Quét B5 không thấy mật khẩu trong tệp xuất |
| N3.9 | Drill-down | Mỗi dashboard có ít nhất một đường khoan sâu hoạt động (bấm vào nhóm hoặc nền tảng thì xuống mức chi tiết); tổng ở mức chi tiết bằng số ở mức trên |
| N3.10 | Bộ lọc | Bộ lọc nền tảng và nhóm nền tảng tác động đúng đến mọi biểu đồ cùng dashboard |

### N4. Phát hiện bất thường và API (P3)
Nhánh `nhom03-65httt-ngocanh-bat-thuong`. Commit: `feat(nhom03-65httt): phat hien bat thuong va api anomaly`

```text
Bối cảnh (đề cương M4 phần phát hiện bất thường): quy tắc thống kê, không huấn luyện: đường cơ sở là trung bình 8 kỳ (kỳ hai tuần) gần nhất cộng 2 độ lệch chuẩn, đối chiếu với các sự kiện đã biết trong dim_event.
Việc: hàm tính bất thường theo nền tảng và **kỳ hai tuần tính từ dw.fact_review** (fact_platform_period chỉ có theo tháng nên không dùng được cho đường cơ sở 8 kỳ hai tuần); ghi cảnh báo vào dw.fact_alert qua quy trình của Tùng (T7); gắn sự kiện trùng thời gian; ghi kết quả; API src/backend/app/api/anomaly.py; pytest bằng chuỗi mẫu có điểm đột biến cố tình chèn.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| N4.1 | Chuỗi có đột biến chèn | Bị phát hiện đúng kỳ |
| N4.2 | Chuỗi phẳng hoặc dao động nhỏ | Không báo bất thường |
| N4.3 | Ít hơn 8 kỳ | Không tính, trả thông báo rõ, không lỗi |
| N4.4 | Sự kiện đã biết | Bất thường trùng sự kiện được gắn nhãn sự kiện |
| N4.5 | API | 200, 404 nền tảng lạ, 422 tham số sai |

### N5. Hai phần mở rộng (P3)
Nhánh `nhom03-65httt-ngocanh-mo-rong`. Commit: `feat(nhom03-65httt): phan tich theo phien ban ung dung va ty le danh gia trung`

```text
Bối cảnh (danhsachnhom.md, phần mở rộng làm sau khi lõi chạy): (a) cảm xúc theo phiên bản ứng dụng và cảnh báo bản phát hành bị đánh giá thấp; (b) tỷ lệ đánh giá trùng nội dung. Dùng dw.dim_app_version (phiên bản, ngày phát hành) và cột app_version của đánh giá.
Việc:
1. (a) Nối đánh giá với dim_app_version, tính Sentiment Index và tỷ lệ tiêu cực theo phiên bản; so với phiên bản liền trước; cảnh báo khi một phiên bản thấp hơn ngưỡng và có đủ số đánh giá tối thiểu (ngưỡng và số tối thiểu đặt trong config/, ghi lý do chọn). Ghi cảnh báo qua quy trình của Tùng (T7, fact_alert).
2. (b) Định nghĩa đánh giá trùng: chuẩn hóa văn bản (chữ thường, bỏ dấu câu và khoảng trắng thừa) rồi so khớp; tính tỷ lệ theo nền tảng và theo kỳ; đưa kết quả vào nhật ký chất lượng và dashboard 6.
3. Truy vấn và kiểm thử trên dữ liệu mẫu nhỏ có phiên bản và bản trùng cố tình chèn.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| N5.1 | Phiên bản ít đánh giá | Không bị cảnh báo (dưới số tối thiểu) |
| N5.2 | Phiên bản thấp rõ rệt, đủ đánh giá | Bị cảnh báo đúng một lần; chạy lại không sinh trùng |
| N5.3 | Đánh giá không có `app_version` | Gom vào nhóm riêng, không báo lỗi |
| N5.4 | Bản trùng chèn thử | Tỷ lệ trùng tính đúng so với đếm tay |
| N5.5 | Dữ liệu thật | Có ít nhất một ví dụ minh họa cho (a) và số tỷ lệ trùng thật cho (b), ghi trong PR |
| N5.6 | Không bịa | Phần nào dữ liệu thật chưa đủ thì ghi rõ, không điền số |

### N6. OLAP trên kho dữ liệu: roll-up, drill-down, slice, dice, pivot (P2)
Nhánh `nhom03-65httt-ngocanh-olap`. Commit: `docs(nhom03-65httt): tai lieu va truy van olap tren dw`

```text
Bối cảnh: đề cương (mục tiêu cụ thể số 3) yêu cầu kho dữ liệu galaxy schema hỗ trợ OLAP gồm roll-up, drill-down, slice, dice, pivot. Ngọc Anh là chủ kho nên có trách nhiệm chứng minh kho trả lời được các phép này.
Việc:
1. docs/olap.md: nêu phân cấp của từng chiều có trong schema (thời gian: ngày, tháng, quý, năm; nền tảng: nhóm trong nước hoặc quốc tế, nền tảng; khía cạnh; phiên bản ứng dụng) và nói mỗi phép OLAP áp vào chiều nào. Chỉ dùng cột thật có trong dim_time, dim_platform, dim_aspect, dim_app_version (đọc schema, không bịa cột).
2. src/bi/olap/olap_queries.sql: năm truy vấn mẫu trên schema dw (dùng view của N1 nếu có), mỗi truy vấn có chú thích tên phép, chiều và ý nghĩa nghiệp vụ:
   - Roll-up: tổng số đánh giá và Sentiment Index từ tháng lên quý lên năm (GROUP BY ROLLUP hoặc UNION các mức).
   - Drill-down: từ nhóm nền tảng (trong nước, quốc tế) xuống từng nền tảng rồi xuống khía cạnh.
   - Slice: cố định một chiều (ví dụ một nền tảng, hoặc một tháng).
   - Dice: lọc nhiều chiều cùng lúc (ví dụ ba nền tảng, một khoảng thời gian, một khía cạnh).
   - Pivot: nền tảng ở hàng, cảm xúc hoặc khía cạnh ở cột (FILTER hoặc crosstab).
3. Mỗi truy vấn chạy được trên dữ liệu thật sau ETL và trên dữ liệu mẫu nhỏ trong src/database/seed/.
4. Có tệp kiểm thử (pytest hoặc script SQL) so tổng giữa các mức: tổng roll-up bằng tổng chi tiết.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| N6.1 | Chạy năm truy vấn trên dw | Không lỗi, mỗi truy vấn ra ít nhất một dòng trên dữ liệu thật |
| N6.2 | Roll-up | Tổng ở mức quý bằng tổng các tháng của quý đó; tổng năm bằng tổng các quý |
| N6.3 | Drill-down | Tổng các nền tảng bằng số của nhóm; tổng các khía cạnh khớp số đánh giá có khía cạnh |
| N6.4 | Slice, dice | Số dòng khớp đếm tay bằng một truy vấn thuần trên `fact_review` |
| N6.5 | Pivot | Tổng hàng khớp số đánh giá của nền tảng; không mất giá trị `NULL` âm thầm |
| N6.6 | Chú thích | Mỗi truy vấn nêu tên phép, chiều và ý nghĩa nghiệp vụ |
| N6.7 | Tài liệu | `docs/olap.md` mô tả đúng phân cấp theo schema thật, không có cột không tồn tại |
| N6.8 | Dữ liệu | Không có dữ liệu thật trong tệp seed hay tài liệu |

---

## C3. Thái Anh

### TA1. Thu thập sâu Google Play, App Store (P1)
Nhánh `nhom03-65httt-thaianh-thu-thap-sau`. Commit: `feat(nhom03-65httt): thu thap sau app store va google play`

```text
Bối cảnh: collector ở src/etl/collectors/ (App Store chỉ RSS và iTunes Lookup, theo docs/dao_duc_phap_ly.md; cấm giả trình duyệt, đổi IP, proxy). Số dòng App Store đang mỏng cho Khan Academy (174), HOCMAI (169), VUIHOC (428).
Việc: thu thập sâu bổ sung có kiểm soát (sleep không dưới 2 giây, backoff khi 429 hoặc 5xx), kết quả ra thư mục ngoài Git, không trùng với dữ liệu đã có. Kiểm thử bằng dữ liệu giả lập.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| TA1.1 | `pytest` collector | Xanh, không gọi mạng thật |
| TA1.2 | Chạy thật `--only "<nền tảng>" --count 20` | CSV đúng 12 cột chuẩn, UTF-8 BOM, không trùng |
| TA1.3 | Đạo đức | Không giả trình duyệt, proxy, đổi IP; `--sleep` nhỏ hơn 2 bị từ chối |
| TA1.4 | Dữ liệu cá nhân | Chỉ `author_hash`, không tên thật, ảnh, hồ sơ |
| TA1.5 | Git | Không CSV |

### TA2. Bảng sự kiện `dim_event` (P1)
Nhánh `nhom03-65httt-thaianh-dim-event`. Commit: `docs(nhom03-65httt): ra soat dim event cac dong can kiem tra`

```text
Bối cảnh: dim_event khởi tạo từ tệp dim_event_seed.csv (ngoài Git), cột needs_review trong dw.dim_event đánh dấu dòng cần kiểm tra, một số dòng đánh dấu "cần kiểm tra". Sự kiện dùng cho E2, M3 (đặc trưng sự kiện) và gắn nhãn bất thường.
Việc: rà từng dòng "cần kiểm tra" với nguồn công khai (ghi nguồn), quyết định giữ, sửa hoặc bỏ; ghi quyết định vào docs/ra_soat_dim_event.md (không đưa dữ liệu thô vào Git). Cung cấp tệp hoặc script nạp dim_event cho ETL.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| TA2.1 | Mỗi dòng "cần kiểm tra" | Có quyết định và nguồn trong tài liệu |
| TA2.2 | Sự kiện | `event_type` thuộc `cap_nhat`, `khuyen_mai`, `mua_thi`, `su_co`; có `start_date`, `end_date` hợp lệ (end không trước start); `platform_key` rỗng chỉ với sự kiện chung như mùa thi; dòng đã rà thì `needs_review = false` |
| TA2.3 | Nạp vào kho | `dim_event` có dòng, khóa ngoại đúng, nạp lại không trùng |
| TA2.4 | Git | Không đưa tệp seed thật nếu chứa nội dung từ nguồn bên ngoài chưa cho phép |

### TA3. M2 khía cạnh, thí nghiệm E2 và API (P2)
Nhánh `nhom03-65httt-thaianh-m2`. Commit: `feat(nhom03-65httt): mo hinh khia canh m2 thi nghiem e2 va api aspects`

```text
Bối cảnh (đề cương mục 8.1, 8.3): M2 phân loại đa nhãn bốn khía cạnh Technical, Academic, Customer Service, Pricing (schema dim_aspect còn thêm Other cho mẫu không thuộc bốn nhóm; tệp gán nhãn dùng tên Kỹ thuật, Học thuật, CSKH, Giá), sau đó xác định cảm xúc theo từng khía cạnh. Nhãn khía cạnh sơ bộ từ LLM (HA1), kiểm định trên tập vàng. Baseline: luật từ khóa.
Việc:
1. Baseline luật từ khóa, rồi M2 (ABSA). Seed cố định.
2. Đánh giá trên tập vàng: F1 theo từng khía cạnh và trung bình, so với baseline. Ghi vào docs/ket_qua_m2.md.
3. Thí nghiệm E2: quanh các sự kiện đã biết (dim_event), so độ trễ phát hiện và biên độ biến động của số sao trung bình với Sentiment Index; thống kê tỷ lệ lệch pha và nội dung các ca lệch pha. Ghi docs/thi_nghiem_e2.md.
4. Ghi vào fact_review_aspect. API src/backend/app/api/aspects.py: POST /api/v1/predict/aspects {"text": "..."} trả khía cạnh kèm cảm xúc. Có pytest.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| TA3.1 | F1 trung bình trên tập vàng | **Không dưới 0,60** (mức thấp nhất), mục tiêu 0,65; ghi F1 từng khía cạnh |
| TA3.2 | So baseline | Có bảng so sánh với baseline từ khóa |
| TA3.3 | Khía cạnh | Chỉ dùng năm giá trị của `dim_aspect` (bốn khía cạnh và Other); nhãn cảm xúc là `tich_cuc`, `trung_tinh`, `tieu_cuc`; điểm trong -1 đến 1, độ tin cậy trong 0 đến 1 |
| TA3.4 | API | "Giảng viên dạy hay nhưng ứng dụng lag" trả ít nhất hai khía cạnh với cảm xúc trái ngược |
| TA3.5 | Câu không chứa khía cạnh | Danh sách rỗng, không bịa |
| TA3.6 | Đầu vào sai | 422 |
| TA3.7 | E2 | Có ít nhất một ca sự kiện cụ thể với số liệu độ trễ và biên độ; tỷ lệ lệch pha nêu rõ; ca lệch pha có trích nội dung (đã che thông tin cá nhân) |
| TA3.8 | Ghi kho | `fact_review_aspect` có dòng, khóa ngoại đúng |

### TA4. Chấm cảm xúc báo chí vào `fact_news_sentiment` (P3)
Nhánh `nhom03-65httt-thaianh-cam-xuc-bao-chi`. Commit: `feat(nhom03-65httt): cham cam xuc bao chi vao fact news sentiment`

```text
Bối cảnh: schema 02 có dw.fact_news_sentiment (khóa: source_key, article_id, platform_key; cột time_key, sentiment_score từ -1 đến 1, sentiment_label, confidence, mention_count). Đề cương dùng cảm xúc báo chí làm đặc trưng của M3, cho KPI-07 (độ lệch báo chí và người học) và E3 phần (c). Dữ liệu: data/raw/news/news.csv (413 bài; cột platform, origin, title, outlet, link, published_at, collected_at, title_hash). Chỉ có tiêu đề, không có nội dung bài; nhiều bài không liên quan đến chất lượng nền tảng (ví dụ đề thi); đề cương ghi khoảng 123 bài liên quan. Báo chí quốc tế gần như không có (4 bài), nên phần này chủ yếu cho nhóm trong nước.
Việc:
1. src/ml/news/score_news.py: lọc bài liên quan (tiêu đề nhắc đúng tên nền tảng hoặc sản phẩm, bỏ tin thuần đề thi hoặc đáp án không nói về nền tảng; ghi quy tắc lọc rõ ràng) và ghi số bài giữ, bỏ vào báo cáo.
2. Chấm cảm xúc tiêu đề bằng mô hình M1 của Tùng (T2) khi có, hoặc dùng mô hình cảm xúc có sẵn nếu M1 chưa xong; ghi tên mô hình vào dw.dim_model.
3. Ghi vào dw.fact_news_sentiment: article_id lấy từ title_hash, time_key theo ngày đăng (published_at), sentiment_score, sentiment_label (tich_cuc, trung_tinh, tieu_cuc), confidence, mention_count. Chạy lại không sinh dòng trùng.
4. Mô tả hạn chế trong docs/cam_xuc_bao_chi.md: chỉ có tiêu đề, mẫu nhỏ, lệch phân bố giữa các nền tảng; chỉ dùng cho phân tích khám phá.
5. Kiểm thử bằng vài tiêu đề mẫu tự tạo (khen, chê, trung tính, không liên quan).
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| TA4.1 | Lọc bài liên quan | Số bài giữ và bỏ được ghi; số bài giữ gần mức khoảng 123 của đề cương (nêu lý do nếu khác nhiều) |
| TA4.2 | Tiêu đề mẫu | Tiêu đề khen trả `tich_cuc`, chê trả `tieu_cuc`; tiêu đề không liên quan bị bỏ, không ghi vào bảng |
| TA4.3 | Miền giá trị | `sentiment_score` trong -1 đến 1, `confidence` trong 0 đến 1, nhãn đúng ba giá trị |
| TA4.4 | Chạy lại | Số dòng không đổi; khóa `(source_key, article_id, platform_key)` không trùng |
| TA4.5 | Ghi kho | Mỗi nền tảng có bài báo chí đều có dòng; `time_key` tồn tại trong `dim_time` |
| TA4.6 | KPI-07 | Truy vấn `kpi_07_lech_bao_chi_nguoi_hoc.sql` chạy được trên dữ liệu thật và ra số trong -100 đến 100 |
| TA4.7 | Hạn chế | Có tài liệu nêu rõ chỉ tiêu đề, mẫu nhỏ, báo chí quốc tế gần như không có |
| TA4.8 | Dữ liệu | Không đưa `news.csv` lên Git (B3) |

---

---

## C4. Hoàng Anh

### HA1. LLM gán nhãn, đo độ khớp, mô hình nền TF-IDF (P1)
Nhánh `nhom03-65httt-hoanganh-baseline`. Commit: `feat(nhom03-65httt): llm gan nhan, do kappa va mo hinh nen tf-idf`

```text
Bối cảnh (đề cương mục 8.1): tập huấn luyện khoảng 4.000 đánh giá do LLM gán nhãn cảm xúc và khía cạnh sơ bộ; đo độ khớp giữa LLM và nhãn người trên tập vàng (Cohen's kappa); bổ trợ UIT-VSFC. Baseline: TF-IDF và Logistic Regression.
Việc:
1. src/ml/labeling/llm_label.py: gán nhãn cảm xúc (tich_cuc, trung_tinh, tieu_cuc) và bốn khía cạnh Technical, Academic, Customer Service, Pricing (kèm Other) cho mẫu chia tầng theo nền tảng, nguồn, sao; ghi kết quả ra tệp ngoài Git, có cache để chạy lại không gọi lại LLM cho dòng đã có. Khóa LLM trong .env.
2. src/ml/labeling/llm_agreement.py: accuracy và kappa giữa nhãn LLM và nhãn người trên tập vàng.
3. src/ml/baseline/tfidf.py: TF-IDF kết hợp Logistic Regression, seed cố định, in macro-F1, accuracy, ma trận nhầm lẫn.
4. Đường dẫn tập vàng và tệp nhãn truyền bằng tham số.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| HA1.1 | Số nhãn LLM | **Ít nhất 2.000** (mức thấp nhất), mục tiêu 4.000 |
| HA1.2 | Kappa LLM với người | **Không dưới 0,50** (mức thấp nhất), mục tiêu 0,60; ghi số thật. Dưới 0,50 thì nêu nguyên nhân và đổi lời nhắc LLM |
| HA1.3 | Chạy lại | Có cache, không gọi lại LLM cho dòng đã gán; cùng seed cho cùng kết quả baseline |
| HA1.4 | Không rò rỉ | Tập vàng không lẫn trong tập huấn luyện |
| HA1.5 | Baseline | In đủ macro-F1, accuracy, ma trận nhầm lẫn |
| HA1.6 | Chi phí và khóa | Khóa chỉ ở `.env`; có giới hạn số lần gọi; B5 đạt |
| HA1.7 | Nhãn sai định dạng | Dòng LLM trả sai tập nhãn bị loại và đếm, không làm sập |

### HA2. Website nối API thật và API tìm kiếm đánh giá (P2)
Nhánh `nhom03-65httt-hoanganh-ket-noi-api`. Commit: `feat(nhom03-65httt): website goi api that thay du lieu mau`

```text
Bối cảnh: website dùng src/frontend/src/services/mock-data.ts. Đọc docs/quy_uoc_ma_nguon.md mục 6.
Việc:
1. Thay lớp services bằng lời gọi API thật (URL từ biến Vite VITE_API_URL), giữ giao diện. Không viết fetch rải rác trong trang.
2. API lỗi hoặc không có dữ liệu: hiện trạng thái trống hoặc thông báo tiếng Việt, không trắng trang.
3. src/backend/app/api/reviews.py: tìm kiếm và lọc đánh giá (nền tảng, khoảng ngày, cảm xúc, khía cạnh, từ khóa), phân trang; trả nhãn AI và cờ lệch pha nếu có.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| HA2.1 | `npm run typecheck`, `npm run build` | Qua |
| HA2.2 | Có API chạy | Tổng quan, So sánh, Khía cạnh, Review Explorer hiển thị số từ API, không còn dữ liệu mẫu |
| HA2.3 | Tắt API | Báo lỗi rõ, không trắng trang, không lỗi console |
| HA2.4 | Review Explorer | Lọc đúng số dòng theo nền tảng, ngày, cảm xúc; phân trang đúng, trang cuối đúng |
| HA2.5 | Đầu vào API | Ngày sai định dạng 422; trang vượt quá trả danh sách rỗng, không 500 |
| HA2.6 | Che dữ liệu | Không trả tên thật hay hồ sơ tác giả |

### HA3. JWT và phân quyền (P2)
Nhánh `nhom03-65httt-hoanganh-jwt`. Commit: `feat(nhom03-65httt): api xac thuc jwt va phan quyen`

```text
Việc: src/backend/app/api/auth.py: POST /api/v1/auth/login trả JWT có hạn; hai vai trò Admin, Viewer; dependency bảo vệ điểm cuối (đọc cho Viewer, quản trị cho Admin); bí mật ký và mật khẩu tài khoản khởi tạo lấy từ .env; mật khẩu băm. Website: trang đăng nhập gọi API, giữ vai trò, trang quản trị chỉ Admin.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| HA3.1 | Sai mật khẩu | **401** |
| HA3.2 | Viewer gọi điểm cuối Admin | **403** |
| HA3.3 | Không token hoặc hết hạn | **401** |
| HA3.4 | Mật khẩu | Lưu băm; không tài khoản hay mật khẩu viết cứng trong mã |
| HA3.5 | Bí mật ký | Chỉ ở `.env` |
| HA3.6 | Website | Trang quản trị chỉ Admin vào được |
| HA3.7 | pytest | Có bài cho 401, 403, 200 |

### HA4. Cập nhật dữ liệu, quản lý nguồn và sự kiện (P3)
Nhánh `nhom03-65httt-hoanganh-nguon-cap-nhat`. Commit: `feat(nhom03-65httt): api cap nhat du lieu va quan ly nguon`

```text
Việc: refresh.py: POST /api/v1/refresh (chỉ Admin) kích hoạt ETL hoặc workflow n8n, trả mã công việc và trạng thái; sources.py: thêm, sửa, xóa nguồn dữ liệu và bảng sự kiện (dim_event), kiểm tra dữ liệu vào bằng Pydantic. Ghi nhận vào lịch sử ETL.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| HA4.1 | Viewer gọi | 403 |
| HA4.2 | Admin bấm cập nhật | Có công việc chạy; bấm lại khi đang chạy không sinh công việc thứ hai |
| HA4.3 | Cập nhật xong | Dữ liệu không trùng |
| HA4.4 | Thêm, sửa, xóa nguồn và sự kiện | Đúng, có xác nhận khi xóa, dữ liệu sai trả 422 |
| HA4.5 | Có lịch sử | Mỗi lần cập nhật ghi vào lịch sử ETL |

### HA5. Nhúng Superset, guest token, kiểm thử người dùng (P3)
Nhánh `nhom03-65httt-hoanganh-nhung-superset`. Commit: `feat(nhom03-65httt): nhung superset va guest token`

```text
Việc: embed.py: điểm cuối cấp guest token Superset chỉ cho người đã đăng nhập, hạn ngắn, giới hạn theo dashboard; website nhúng dashboard bằng SDK nhúng của Superset trong khung /dashboard, mỗi dashboard một tab. Kiểm thử người dùng: ít nhất 3 người thử theo kịch bản, ghi lại lỗi và cách sửa vào docs/kiem_thu_nguoi_dung.md.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| HA5.1 | Chưa đăng nhập xin token | 401 |
| HA5.2 | Dashboard nhúng | **Ít nhất 4** (mức thấp nhất), mục tiêu cả 6 và có phân quyền |
| HA5.3 | Token hết hạn | Website báo và làm mới, không trắng khung |
| HA5.4 | Phân quyền | Viewer chỉ xem; không có quyền sửa dashboard |
| HA5.5 | Kiểm thử người dùng | Có ít nhất 3 người, có bảng lỗi và xử lý |
| HA5.6 | Khóa | Tài khoản dịch vụ Superset trong `.env`, B5 đạt |

---

## C5. Hưng

### HU1. Sửa tồn đọng KPI (P1)
Nhánh `nhom03-65httt-hung-kpi-fix`. Commit: `fix(nhom03-65httt): sua decimal bhi, from dttm va ky hai tuan kpi 09`

```text
Bối cảnh: bản kiểm tra nhánh nhom03-65httt phát hiện 3 điểm.
Việc:
1. src/bi/bhi.py: compute_bhi nhận cả Decimal và float (PostgreSQL trả Decimal); chuyển sang float trước khi kiểm tra; vẫn từ chối chuỗi, None, bool.
2. src/bi/superset/queries/: kpi_04, 06, 07, 08, 09, 10 thêm bộ lọc thời gian của Superset (from_dttm, to_dttm) theo cách các KPI khác đang dùng.
3. KPI-09: đề cương dùng kỳ hai tuần (đường cơ sở 8 kỳ hai tuần). Sửa SQL (hiện nhóm theo tuần bằng date_trunc('week')) cho khớp kỳ hai tuần, hoặc nếu giữ theo tuần thì sửa cả đề cương và docs/kpi_bhi.md; ghi lý do. Ưu tiên sửa SQL theo đề cương.
4. Bổ sung kiểm thử cho Decimal.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| HU1.1 | `compute_bhi(Decimal("20"), Decimal("4.1"), 100)` | `{"bhi": 67.0, "flags": []}`, không `ValueError` |
| HU1.2 | Chuỗi `"20"`, `None`, `True` | Vẫn bị từ chối |
| HU1.3 | `pytest src/bi` | Xanh (trước đó 17 qua, nay thêm bài mới) |
| HU1.4 | Truy vấn KPI cần lọc thời gian | Đều có `from_dttm`, không còn ngày viết cứng |
| HU1.5 | KPI-09 | SQL, `docs/kpi_bhi.md` và đề cương cùng một định nghĩa kỳ |

### HU2. API KPI, BHI và dashboard 1 đến 4 (P2)
Nhánh `nhom03-65httt-hung-kpi-api`. Commit: `feat(nhom03-65httt): api kpi bhi va dashboard 1 den 4`

```text
Bối cảnh: 10 KPI và BHI đã định nghĩa trong docs/kpi_bhi.md; SQL ở src/bi/superset/queries/. BHI = 0,6 x (50 + SI/2) + 0,4 x ((R-1)/4 x 100).
Việc:
1. src/backend/app/api/kpi.py: GET /api/v1/kpi (nền tảng, khoảng ngày) và /api/v1/bhi, đọc từ dw.
2. KPI phụ thuộc bảng chưa có thì trả 501 kèm lý do, không bịa số.
3. Dashboard Superset số 1 đến 4 từ truy vấn có sẵn, có bộ lọc và **drill-down** (nhóm nền tảng xuống nền tảng, tháng xuống ngày, khía cạnh xuống từng đánh giá); xuất định nghĩa vào src/bi/superset/dashboards/.
4. pytest cho từng điểm cuối.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| HU2.1 | SQL khớp Python | BHI từ SQL bằng `compute_bhi` trên cùng dữ liệu mẫu (sai số làm tròn nhỏ) |
| HU2.2 | Miền giá trị | BHI trong 0 đến 100 |
| HU2.3 | Đầu vào | Nền tảng lạ 404; ngày sai 422 |
| HU2.4 | Số thật | Sau ETL, tổng đánh giá theo nền tảng khớp đếm tay |
| HU2.5 | Điểm cuối chưa làm được | 501 có lý do |
| HU2.6 | Dashboard 1 đến 4 | Mở được, có dữ liệu thật, lọc thời gian chạy |
| HU2.7 | Đủ 10 KPI | Mỗi KPI hoặc có số hoặc có 501 ghi lý do, không để trống |
| HU2.8 | Drill-down | Mỗi dashboard 1 đến 4 có ít nhất một đường khoan sâu hoạt động; tổng ở mức chi tiết bằng số ở mức trên |
| HU2.9 | Bộ lọc | Bộ lọc thời gian, nhóm nền tảng và nền tảng tác động đúng đến mọi biểu đồ cùng dashboard |

### HU3. API cảnh báo (P2)
Nhánh `nhom03-65httt-hung-alerts-api`. Commit: `feat(nhom03-65httt): api xem canh bao va danh dau da xu ly`

```text
Việc: alerts.py: GET /api/v1/alerts (lọc nền tảng, mức độ, trạng thái, phân trang) và POST /api/v1/alerts/{id}/resolve; đọc fact_alert; chỉ Admin được đánh dấu.
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| HU3.1 | Đánh dấu đã xử lý | `status` chuyển `moi` hoặc `dang_xu_ly` thành `da_xu_ly` (đúng ràng buộc schema); lần gọi sau không còn trong danh sách chưa xử lý |
| HU3.2 | Gọi lặp | Không lỗi |
| HU3.3 | Cảnh báo không tồn tại | 404 |
| HU3.4 | Viewer đánh dấu | 403 (khi JWT xong; trước đó ghi chú) |
| HU3.5 | Mỗi cảnh báo trả về | Có `metric_name`, `metric_value`, `threshold`, nền tảng, khía cạnh (nếu có), đề xuất hành động và bộ phận phụ trách (ghép từ cấu hình của T7) |

### HU4. Mục khuyến nghị hành động trên website (P3)
Tiêu chí: trang hoặc khối hiển thị khuyến nghị lấy từ `fact_alert` qua API; mỗi khuyến nghị có dẫn chứng số liệu; không khuyến nghị khi không có cảnh báo; `typecheck` và `build` qua.

### HU5. Sentiment Index có trọng số lượt hữu ích (P3)
Tiêu chí: công thức ghi rõ trong `docs/kpi_bhi.md`; có truy vấn SQL và hàm Python cho kết quả giống nhau trên dữ liệu mẫu; so với Sentiment Index thường trên dữ liệu thật và nêu khác biệt; xử lý `thumbs_up` thiếu hoặc bằng 0 (không chia cho 0).

### HU6. Kịch bản demo và slide (P3)
Tiêu chí: kịch bản chạy trọn vẹn trên máy sạch đúng thời lượng; chỉ nói điều hệ thống thật sự làm (không nói "đã có mô hình" khi chưa); có phương án khi mạng hoặc Docker lỗi; slide khớp báo cáo kỹ thuật, mỗi con số truy được nguồn.

### HU7. Bộ công cụ kiểm tra cho nhóm (P3, chuyển từ Tùng)
Nhánh `nhom03-65httt-hung-cong-cu-kiem-tra`. Commit: `feat(nhom03-65httt): script kiem tra truoc khi tao pr`

```text
Bối cảnh: CONTRIBUTING.md và docs/review_pull_request.md đã có quy tắc; cần một script để mỗi người tự kiểm tra trước khi tạo PR, giảm lỗi lặp (tệp ngoài nhom03-65httt/, tệp cấm, commit sai mẫu, co-author).
Việc: tools/check_pr.py (hoặc .sh, chạy được trên Windows qua Git Bash) so nhánh hiện tại với origin/nhom03-65httt và kiểm tra: (1) mọi tệp thay đổi bắt đầu bằng nhom03-65httt/; (2) không có .csv, .xlsx, .env, *.pt, *.safetensors, *.pkl, node_modules, dist, tệp nén; (3) mọi commit khớp <loại>(nhom03-65httt): <mô tả không dấu>, một dòng; (4) không có Co-Authored-By hay dòng ghi công công cụ; (5) không có chuỗi giống khóa hoặc mật khẩu trong phần thêm; (6) nhắc chạy pytest, typecheck, build. In kết quả từng mục (đạt, không đạt, cách sửa) và thoát mã khác 0 khi có mục không đạt. Thêm hướng dẫn dùng vào CONTRIBUTING.md (phần nhỏ, không đổi quy tắc cũ).
```

| # | Tiêu chí | Kết quả mong đợi |
|---|---|---|
| HU7.1 | Nhánh sạch | Script báo đạt tất cả, thoát mã 0 |
| HU7.2 | Thêm tệp `.csv` hoặc `.env` giả vào commit thử | Báo không đạt đúng mục 2 |
| HU7.3 | Tệp nằm ngoài `nhom03-65httt/` | Báo không đạt mục 1 |
| HU7.4 | Commit sai mẫu (có dấu, hai dòng, thiếu phạm vi) | Báo không đạt mục 3 kèm gợi ý sửa |
| HU7.5 | Commit có `Co-Authored-By` | Báo không đạt mục 4 |
| HU7.6 | Chuỗi giống khóa (ví dụ `api_key = "..."`) trong diff | Báo không đạt mục 5 |
| HU7.7 | Windows | Chạy được từ Git Bash hoặc PowerShell theo hướng dẫn; không phụ thuộc thư viện ngoài ngoài Python chuẩn |
| HU7.8 | Không sửa tệp | Script chỉ đọc, không tự `git add` hay sửa lịch sử |

---

---

## D. Kiểm thử tích hợp trên máy sạch (Tùng, 30/11)

Chạy trên một bản clone mới của `nhom03-65httt`, theo README, **không dùng môi trường cũ**.

| # | Bước | Kết quả mong đợi |
|---|---|---|
| D1 | `git clone`, checkout nhánh mới nhất | Có đủ tệp, không có dữ liệu thật |
| D2 | Sao `.env.example` thành `.env`, điền mật khẩu | Phần lõi không cần khóa nào khác |
| D3 | `docker compose up -d --build` | `postgres` healthy, `migrate` Exited 0, `api` healthy (và Superset, n8n nếu đã thêm) |
| D4 | `GET /health/db` | Có `raw`, `clean`, `dw` và phiên bản migration mới nhất |
| D5 | Đặt `data/raw/`, chạy ETL | Đủ 28.638 dòng; chạy lại không đổi |
| D6 | `GET /api/v1/kpi`, `/bhi` | Số thật, không 500 |
| D7 | `POST /api/v1/predict/sentiment`, `/aspects`; `GET /api/v1/forecast`, `/anomaly` | 200 với dữ liệu mẫu |
| D8 | `npm ci`, `npm run typecheck`, `npm run build` | Qua |
| D9 | `npm run dev`, mở mọi trang | Số thật; không lỗi console đỏ |
| D10 | `pytest` backend, `src/bi`, collectors, ETL | Tất cả xanh |
| D11 | Đăng nhập Admin và Viewer | Phân quyền đúng |
| D12 | Chatbot 10 câu mẫu | Đạt như T6.1 đến T6.9 |
| D13 | Dashboard Superset nhúng trong website | Ít nhất 4, mục tiêu 6; có dữ liệu; lọc thời gian chạy |
| D14 | Cảnh báo | Có ít nhất một cảnh báo sinh ra, hiện trên website; email thử gửi qua n8n |
| D15 | Quét Git: B3, B5 | Sạch |
| D16 | README | Người chưa biết dự án làm theo được từ D1 đến D9 |
| D17 | Báo cáo kỹ thuật | Có E1, E2, E4, Q1 đến Q6; mọi số truy được nguồn |
| D18 | `docker compose down` | Không lỗi |

Phần nào không đạt tại D1 đến D18 thì ghi rõ vào README mục "Hạn chế", không nộp như thể đã xong.

## E. Quy trình duyệt PR (nhóm trưởng)

1. Kiểm B1 đến B9.
2. Tự chạy lại lệnh trong "Cách kiểm tra" của PR ít nhất một lần.
3. Đối chiếu bảng tiêu chí của đúng việc đó ở mục C.
4. Đạt: squash merge với tiêu đề đúng mẫu, mô tả để trống. Chưa đạt: ghi góp ý, đánh dấu "bắt buộc" hoặc "nên làm".
