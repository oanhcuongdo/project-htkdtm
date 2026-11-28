# Bảng Thuật Ngữ Kỹ Thuật (Glossary)

| Thuật ngữ | Ý nghĩa | Thành phần sử dụng |
|---|---|---|
| **RAG** | *Retrieval-Augmented Generation*: Truy xuất các đoạn ngữ cảnh liên quan từ kho vector trước khi sinh câu trả lời có căn cứ. | `ai/` |
| **Multimodal RAG** | RAG trên dữ liệu đa phương thức (văn bản PDF/DOCX, lời thoại video/audio, hình ảnh OCR). | `ai/`, `worker/` |
| **Intent (bước phân loại ý định)** | Phân loại ý định người dùng (`greeting`, `qa`, `quiz`, `flashcard`, `essay_grading`, `summarize`). | `ai/` |
| **Retriever (bước truy xuất)** | Tìm kiếm các đoạn văn bản liên quan trong cơ sở dữ liệu vector Qdrant theo phạm vi khóa học/bài học/tài liệu. | `ai/` |
| **Grader (bước chấm điểm ngữ cảnh)** | Đánh giá mức độ liên quan của các đoạn văn bản vừa truy xuất được so với câu hỏi. | `ai/` |
| **Generator (bước sinh câu trả lời)** | Tạo câu trả lời hoàn chỉnh kèm trích dẫn nguồn bằng mô hình Gemini đã cấu hình. | `ai/` |
| **Reflection (bước tự kiểm tra)** | Kiểm tra lại chất lượng câu trả lời đối chiếu với ngữ cảnh và có thể kích hoạt sinh lại tối đa 1 lần. | `ai/` |
| **Chunk** | Đoạn văn bản nhỏ (~256–512 token) được cắt ra trong quá trình xử lý nạp tài liệu. | `worker/`, `ai/` |
| **Embedding** | Vector dày đặc (384 chiều từ mô hình `all-MiniLM-L6-v2`) biểu diễn ngữ nghĩa của đoạn văn bản phục vụ tìm kiếm tương đồng. | `worker/`, `ai/`, Qdrant |
| **`document_chunks`** | Tên collection trong Qdrant lưu trữ vector và payload của từng đoạn văn bản (`document_id`, `page_number`, `timestamp`...). | Qdrant |
| **Celery task** | Tác vụ chạy nền bất đồng bộ (ví dụ: `process_document`, `lesson_content`, `quiz`, `essay`, `flashcards`). | `worker/` |
| **Broker / Backend (Redis)** | Redis DB 1 dùng làm hàng đợi phân phối tác vụ (broker) và Redis DB 0 dùng cho bộ nhớ đệm ứng dụng / kết quả Celery. | `worker/`, Redis |
| **SSE streaming** | *Server-Sent Events*: Truyền phát từng token câu trả lời AI theo thời gian thực từ Backend API tới trình duyệt Web. | `backend/`, `frontend/` |
| **JWT** | *JSON Web Token* (Access token / Refresh token) dùng để xác thực và duy trì phiên đăng nhập API. | `backend/`, `frontend/` |
| **MinIO** | Hệ thống lưu trữ đối tượng tương thích chuẩn S3 dùng để chứa tệp tải lên gốc (PDF, video, audio, ảnh). | Hạ tầng dùng chung |
| **Citation (Trích dẫn)** | Thông tin tham chiếu nguồn gốc (mã tài liệu, số trang hoặc mốc thời gian) đính kèm theo câu trả lời AI. | `ai/`, `backend/` |
| **`GraphState`** | Kiểu dữ liệu `TypedDict` lưu trạng thái truyền qua các bước của luồng xử lý AI `asyncio` (`query`, `chunks`, `answer`, `citations`...). | `ai/` |
| **API Gateway** | Dịch vụ `backend/`: Điểm tiếp nhận REST/SSE duy nhất cho client, chuyển tiếp yêu cầu sang AI Service và giao việc cho Worker. | `backend/` |
| **Quiz / Flashcard** | Học liệu luyện tập tương tác (câu hỏi trắc nghiệm và thẻ ghi nhớ 2 mặt) được AI tạo từ ngữ cảnh tài liệu. | `ai/`, `frontend/` |

---

*Xem thêm: [Thiết kế hệ thống](../architecture/system-design.md) · [Quy trình AI Workflow](../architecture/ai-agent-workflow.md) · [Mục lục tài liệu](../README.md)*
