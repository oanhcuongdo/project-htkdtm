# Quy Trình AI Agent & RAG

AI Service (`src/ai/`) là một ứng dụng FastAPI độc lập chạy tại cổng `8001`. Backend API Gateway (`src/backend/`) gọi sang AI Service qua giao thức HTTP với header xác thực `X-Internal-API-Key`; Celery Worker (`src/worker/`) cũng gọi trực tiếp các endpoint công cụ học tập trên AI Service. Tệp `src/ai/src/workflows/graph.py` hiện tại triển khai quy trình xử lý hội thoại trực tiếp bằng `asyncio` và `TypedDict` (`GraphState`), **không** import hay thực thi gói `langgraph`.

## Luồng Xử Lý Chat (RAG Pipeline)

1. **Phân loại ý định (giới hạn 10 giây):** Xác định ý định câu hỏi (`classify_intent`). Các lời chào hỏi (`greeting`) trả lời trực tiếp ngay mà không cần truy xuất tài liệu.
2. **Truy xuất ngữ cảnh (giới hạn 60 giây):** Với các yêu cầu hỏi đáp (`qa`) và tóm tắt (`summarize`), truy xuất các đoạn văn bản (`chunks`) từ Qdrant theo phạm vi bài học (`lesson_id`), khóa học (`course_id`) hoặc danh sách tài liệu cá nhân (`document_ids` / `user_id` lọc mềm).
3. **Chấm điểm mức độ liên quan (giới hạn 15 giây):** Đánh giá các chunk truy xuất được (`grade_chunks`). Nếu bước chấm điểm gặp lỗi hoặc timeout, luồng xử lý có thể dùng các chunk thô đạt ngưỡng lọc làm phương án dự phòng (`fallback`) để vẫn giữ được trích dẫn nguồn.
4. **Sinh câu trả lời & trích dẫn (giới hạn 60 giây):** Tổng hợp câu trả lời kèm trích dẫn nguồn (`citations`) theo phong cách gia sư (`tutor_mode`) và lịch sử hội thoại.
5. **Tự kiểm tra & phản chiếu (giới hạn 15 giây):** Khi có các chunk liên quan hợp lệ, hệ thống thực hiện kiểm tra chất lượng câu trả lời (`reflect`) và cho phép thử sinh lại tối đa 1 lần nếu cần thiết.
6. **Trả kết quả:** Trả về câu trả lời cuối cùng, danh sách trích dẫn (`citations`) và thông tin ý định (`intent`) về API Gateway (hoặc truyền phát từng token qua `/chat/ask/stream` SSE).

Các tác vụ công cụ học tập khác (sinh trắc nghiệm `quiz`, thẻ ghi nhớ `flashcards`, chấm bài tự luận `essay`, sơ đồ tư duy `mindmap`) gọi thẳng nhánh sinh nội dung tương ứng trong AI Service. Dịch vụ sử dụng **Google Gemini** cho tác vụ sinh nội dung chất lượng cao và **Groq** cho bước phân loại, chấm điểm và phản chiếu tốc độ cao. Mã mô hình được cấu hình trong `src/ai/src/core/config.py` và có thể ghi đè qua biến môi trường. Mô hình nhúng (`sentence-transformers/all-MiniLM-L6-v2`) được nạp lười (lazy-loading / khởi động nền) để giữ các probe `/health` nhanh, còn Qdrant lưu trữ toàn bộ vector phục vụ tìm kiếm.

API Gateway nắm quyền xác thực người dùng và quản lý các route công khai. AI Service không truy cập trực tiếp vào cơ sở dữ liệu ứng dụng; Worker chịu trách nhiệm nạp tài liệu và xử lý nền qua Redis/Celery.

---

## Xem Thêm

- [Thiết kế tổng thể hệ thống](./system-design.md)
- [Giao tiếp liên dịch vụ & Hợp đồng API](./service-communication.md)
- [Lược đồ cơ sở dữ liệu](./database-schema.md)
- [Lưu trữ, bộ nhớ đệm & bền vững dữ liệu](./storage-and-cache.md)
- [Đặc tả API Chat & Multimodal RAG](../api/chat-and-rag.md)
