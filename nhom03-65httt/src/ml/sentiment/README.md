# M1: phân tích cảm xúc 3 lớp (T2)

Phân loại đánh giá thành **tích cực, trung tính, tiêu cực** bằng PhoBERT tinh chỉnh, kèm mô hình nền TF-IDF + Logistic Regression để so sánh (thí nghiệm E1).
Kết quả chấm điểm ghi vào `dw.fact_review_sentiment` (mỗi đánh giá một dòng) và là đầu vào của `fact_platform_period` (T3), KPI, dự báo M3 và cảnh báo.

## Cách chạy (từ thư mục `nhom03-65httt`)

```powershell
pip install -r src/ml/sentiment/requirements.txt
python src/ml/sentiment/train_baseline.py --save models/m1_tfidf_lr/model.joblib    # mô hình nền, vài phút
python src/ml/sentiment/train_phobert.py --epochs 4                                 # PhoBERT, khoảng 35 đến 40 phút trên CPU
python src/ml/sentiment/score_all.py --dry-run --limit 500                          # thử chấm điểm, hoàn tác
python src/ml/sentiment/score_all.py                                                # chấm các đánh giá CHƯA có nhãn M1
python src/etl/build_platform_period.py --sentiment-source model                    # cập nhật fact_platform_period theo nhãn M1
```

`score_all.py` cần migration 0004 (bảng `dw.fact_review_sentiment`, `dw.etl_run_log`, dòng `M1_phobert` trong `dw.dim_model`). Ghi theo lô và commit từng lô nên dừng giữa chừng rồi chạy lại sẽ tiếp tục.
`--rescore` chấm lại tất cả (sau khi huấn luyện lại); `--lang vi` chỉ chấm văn bản nhận dạng là tiếng Việt.

## Các tệp

| Tệp | Vai trò |
|---|---|
| `sentiment_common.py` | Đọc dữ liệu gán nhãn, chia train/validation/test (phân tầng, hạt cố định), đo macro-F1 |
| `train_baseline.py` | E1, mô hình nền TF-IDF (từ và ký tự) + Logistic Regression; chọn C trên tập validation |
| `phobert_model.py` | Tách từ (underthesea), gom lô theo độ dài, dự đoán xác suất |
| `train_phobert.py` | Tinh chỉnh `vinai/phobert-base-v2`, chọn epoch theo validation, đo test và tập vàng một lần ở cuối |
| `score_all.py` | Chấm điểm vào `dw.fact_review_sentiment` (upsert), ghi `dw.etl_run_log` bước `score` |
| `tests/test_m1.py` | Kiểm thử không cần tải PhoBERT; các ca CSDL tự bỏ qua nếu chưa có migration 0004 |

## Dữ liệu và mô hình (đều NGOÀI Git)

- Dữ liệu huấn luyện: `data/raw/labeling/training_sample_4000.csv` và `llm_labels_train.csv` (3.775 đánh giá tiếng Việt sau khi bỏ nhãn `bo_qua`), tập vàng LLM `gold_texts_1200.csv` và `llm_labels_gold.csv` (1.169 đánh giá). Chia 80/10/10 phân tầng theo nhãn, hạt ngẫu nhiên 42.
- Trọng số: `models/m1_phobert_sentiment/` (`.gitignore` đã chặn). Lấy từ thư mục chung của nhóm theo `models/README.md`.
- Kết quả đo: `data/ml/e1_tfidf_lr.json`, `data/ml/e1_phobert.json`.

## Kết quả E1 hiện có (26/11/2026)

| Mô hình | macro-F1 test (378) | macro-F1 vàng LLM (1.169) | F1 lớp trung tính (test / vàng) |
|---|---|---|---|
| TF-IDF + Logistic Regression | 0,788 | 0,791 | 0,659 / 0,604 |
| **PhoBERT** (epoch 3, validation 0,854) | **0,894** | **0,860** | 0,821 / 0,698 |

TF-IDF chéo nền tảng: huấn luyện nhóm trong nước, kiểm thử nhóm quốc tế 0,744; chiều ngược lại 0,787.

## Giới hạn (đọc trước khi dùng số liệu)

- **Nhãn là nhãn LLM** (`claude-sonnet-5-5` theo rubric của nhóm), không phải nhãn người. "Tập vàng LLM" chỉ đo mức khớp với LLM đã gán, **chưa phải độ chính xác so với người**. Độ nhất quán giữa hai lần LLM gán độc lập: kappa 0,912 trên 200 dòng. Cần đo lại bằng tập vàng người khi nhóm gán xong.
- **Chưa làm:** cánh LLM zero-shot của E1, PhoBERT chéo nền tảng, đo trên tập vàng người, API `/api/v1/predict/sentiment` (hiện là khung trả 501).
- **Phạm vi ngôn ngữ:** mẫu huấn luyện chỉ gồm văn bản tiếng Việt (`lang_guess = vi`). Khoảng 32% đánh giá trong kho được nhận dạng là `other` (bình luận rất ngắn, tiếng Anh, emoji); mô hình vẫn chấm nhưng độ tin cậy trên nhóm này chưa được đo.
- **Lớp trung tính khó nhất** (ít mẫu, ranh giới mờ): F1 thấp hơn rõ so với hai lớp còn lại.
- Chạy trên CPU, không có GPU; chưa thử nghiệm siêu tham số ngoài cấu hình mặc định (lr 3e-5, 4 epoch, batch 32, độ dài tối đa 128).
