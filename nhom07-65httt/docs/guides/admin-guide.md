# Cẩm Nang Hướng Dẫn Vận Hành Dành Cho Quản Trị Viên (Admin Guide)
> Phiên bản: 2.0 | Cập nhật: 14/09/2026 | Tác giả: Đội ngũ Quản trị & Vận hành Đào tạo | Trạng thái: Chính thức (Active)

---

## Mục Lục Tài Liệu

1. [Tổng Quan Vai Trò Quản Trị Viên Tối Cao (Super Admin)](#1-tổng-quan-vai-trò-quản-trị-viên-tối-cao-super-admin)
2. [Bảng Điều Khiển Quản Trị Trung Tâm (Admin Dashboard)](#2-bảng-điều-khiển-quản-trị-trung-tâm-admin-dashboard)
3. [Bảng Giám Sát Sức Khỏe 6 Dịch Vụ Kỹ Thuật (System Health Checks)](#3-bảng-giám-sát-sức-khỏe-6-dịch-vụ-kỹ-thuật-system-health-checks)
4. [Quản Lý Người Dùng & Phân Quyền Hệ Thống (User Management & RBAC)](#4-quản-lý-người-dùng--phân-quyền-hệ-thống-user-management--rbac)
5. [Kiểm Duyệt & Quản Trị Khóa Học Toàn Sàn (Course Moderation)](#5-kiểm-duyệt--quản-trị-khóa-học-toàn-sàn-course-moderation)
6. [Quản Trị Cây Danh Mục Đào Tạo Đa Cấp (Category Hierarchy Management)](#6-quản-trị-cây-danh-mục-đào-tạo-đa-cấp-category-hierarchy-management)
7. [Két Sắt Quản Lý Khóa AI & Cơ Chế Xoay Vòng Thông Minh (AI Key Vault)](#7-két-sắt-quản-lý-khóa-ai--cơ-chế-xoay-vòng-thông-minh-ai-key-vault)
8. [Cài Đặt Toàn Hệ Thống & Quản Trị Định Mức (System Settings & Quotas)](#8-cài-đặt-toàn-hệ-thống--quản-trị-định-mức-system-settings--quotas)
9. [Quy Trình Xử Lý Sự Cố Vận Hành Thực Tế (Operational Incident Playbooks)](#9-quy-trình-xử-lý-sự-cố-vận-hành-thực-tế-operational-incident-playbooks)
10. [Danh Mục Kiểm Tra Định Kỳ Mỗi Buổi Sáng (Daily Morning Checklist)](#10-danh-mục-kiểm-tra-định-kỳ-mỗi-buổi-sáng-daily-morning-checklist)

---

## 1. Tổng Quan Vai Trò Quản Trị Viên Tối Cao (Super Admin)

Trong hệ sinh thái đào tạo thông minh **Multimodal AI Learning Hub**, tài khoản với vai trò **Quản trị viên (Admin)** nắm giữ quyền hạn tối cao và toàn diện đối với toàn bộ hạ tầng công nghệ, cơ sở dữ liệu người dùng, nội dung học liệu và chi phí vận hành dịch vụ Trí tuệ nhân tạo (AI).

### 1.1 Trách Nhiệm Vận Hành Cốt Lõi

| Hạng mục | Trách nhiệm của Quản trị viên | Mục tiêu cam kết chất lượng (SLA) |
|---|---|---|
| **Giám sát Sẵn sàng (High Availability)** | Theo dõi liên tục trạng thái sống còn của 6 cụm dịch vụ kỹ thuật (API Gateway, AI LangGraph, Cơ sở dữ liệu PostgreSQL, Bộ đệm Redis, Kho vector Qdrant, Lưu trữ đối tượng MinIO/R2, Hàng đợi Celery Worker). | Đảm bảo tính khả dụng của nền tảng đạt tối thiểu **99.9%** thời gian hoạt động. |
| **Kiểm duyệt & An toàn Nội dung** | Thanh tra toàn diện các khóa học, tài liệu tải lên; gỡ bỏ ngay lập tức các nội dung độc hại, sai lệch tôn giáo chính trị hoặc vi phạm nghiêm trọng bản quyền sở hữu trí tuệ. | Thời gian phản hồi và xử lý khiếu nại bản quyền hoặc nội dung xấu dưới **2 giờ**. |
| **Quản trị Tài khoản & Phân quyền** | Khởi tạo tài khoản giảng viên, điều chỉnh định mức lưu trữ và token AI cho các tài khoản VIP, vô hiệu hóa kịp thời các tài khoản có hành vi phá hoại hoặc gian lận. | Tuyệt đối không để xảy ra tình trạng lộ lọt thông tin cá nhân hoặc cấp quyền sai lệch. |
| **Điều phối Gemini** | Quản lý Gemini API keys, model đang dùng và cơ chế xoay vòng/dự phòng khi gặp giới hạn. | Quản trị viên thay key hoặc model mà không cần cập nhật biến môi trường. |

### 1.2 Cơ Chế Bảo Vệ Quản Trị Viên Tối Hậu (Last-Admin Safeguards)

Để ngăn chặn các sơ suất vận hành dẫn đến tê liệt hệ thống hoặc mất quyền kiểm soát toàn sàn, tầng Backend API áp dụng 2 quy tắc an toàn bất biến:

1. **Từ chối Tự Xóa Tài Khoản (Self-Deletion Denial):** Quản trị viên đang đăng nhập không thể tự xóa tài khoản của chính mình (Hệ thống sẽ trả về mã lỗi `HTTP 400 Bad Request: Cannot delete yourself`). Thao tác xóa một quản trị viên chỉ có thể được thực hiện bởi một quản trị viên khác.
2. **Bảo vệ Quản Trị Viên Cuối Cùng (Last-Admin Protection):** Nếu hệ thống chỉ còn duy nhất **1 Quản trị viên hoạt động**, mọi thao tác hạ quyền (Demote sang Lecturer/Student), vô hiệu hóa (Deactivate), hoặc xóa tài khoản này đều bị khóa cứng tuyệt đối (Hệ thống trả về mã lỗi `HTTP 400 Bad Request: Cannot demote or deactivate the last active administrator`). Điều này đảm bảo nền tảng không bao giờ rơi vào trạng thái "vô chủ" (Orphaned Platform).

---

## 2. Bảng Điều Khiển Quản Trị Trung Tâm (Admin Dashboard)

Sau khi đăng nhập bằng tài khoản có vai trò Quản trị (role `admin`), hệ thống sẽ tự động điều hướng bạn đến **Bảng Điều Khiển Quản Trị Trung Tâm** tại đường dẫn `/app/admin`.

```
+---------------------------------------------------------------------------------------------------------+
|                                    BẢNG ĐIỀU KHIỂN QUẢN TRỊ TRUNG TÂM                                   |
+--------------------------+--------------------------+--------------------------+--------------------------+
|      TỔNG NGƯỜI DÙNG     |       TỔNG TÀI LIỆU      |    TÀI LIỆU SẴN SÀNG     |       ĐANG XỬ LÝ         |
|           154            |           482            |           468            |            14            |
| (Tăng 12% so với tháng)  | (Bao gồm PDF, Video, Web)| (Đã nạp Vector DB thành) | (Đang bóc tách OCR/audio)|
+--------------------------+--------------------------+--------------------------+--------------------------+
```

### 2.1 Bốn Thẻ Chỉ Số Toàn Sàn (Global Statistics)

1. **Tổng người dùng (Total Users):** Toàn bộ số lượng tài khoản đã đăng ký trên hệ thống (bao gồm cả Học viên, Giảng viên và Quản trị viên).
2. **Tổng tài liệu (Total Documents):** Tổng số tệp học liệu (PDF, Word, Video, Audio, Liên kết Web) đã được tải lên kho dữ liệu chung của nền tảng.
3. **Tài liệu sẵn sàng (Documents Ready):** Số lượng tài liệu đã trải qua chu trình trích xuất nội dung, nhận diện chữ quang học (OCR), bóc tách âm thanh (Whisper) và được nhúng vector thành công vào cơ sở dữ liệu Qdrant. Các tài liệu này sẵn sàng phục vụ tính năng Hỏi đáp AI RAG và Sinh bài trắc nghiệm tự động.
4. **Đang xử lý (Documents Processing):** Số lượng tệp đang nằm trong hàng đợi tác vụ của Celery Worker. Chỉ số này phản ánh tải làm việc tức thời của máy chủ xử lý dữ liệu.

### 2.2 Danh Bạ Người Dùng Nhanh Trên Dashboard

Ngay phía dưới các thẻ sức khỏe hệ thống, Dashboard cung cấp bảng tra cứu nhanh danh bạ người dùng với tính năng tìm kiếm tức thì theo Tên hoặc Email. Mỗi dòng hiển thị:
- Ảnh đại diện, Tên hiển thị và Địa chỉ Email.
- Huy hiệu vai trò: **Admin** (Tím), **Lecturer** (Xanh dương), hoặc **Student** (Xanh lá).
- Huy hiệu trạng thái: **Hoạt động** (Xanh lục) hoặc **Đã khóa** (Đỏ).
- Ngày tạo tài khoản định dạng chuẩn Việt Nam.
- Các nút chuyển trang (Phân trang 5 người dùng/trang) và đường dẫn chuyển nhanh sang trang Quản lý chuyên sâu (`/app/admin/users`).

---

## 3. Bảng Giám Sát Sức Khỏe 6 Dịch Vụ Kỹ Thuật (System Health Checks)

Đây là tính năng mang lại giá trị vận hành cao nhất cho Quản trị viên không chuyên sâu về kỹ thuật (Non-Tech Admins). Thay vì phải sử dụng các dòng lệnh Linux phức tạp trong máy chủ, bạn chỉ cần quan sát đèn tín hiệu màu sắc trực quan:
- **Đèn Xanh Lục (Healthy):** Dịch vụ hoạt động hoàn hảo, tốc độ phản hồi nhanh.
- **Đèn Đỏ (Degraded / Unhealthy):** Dịch vụ bị ngắt quãng, nghẽn mạng hoặc gặp sự cố cần kiểm tra ngay.

```
+---------------------------------------------------------------------------------------------------------+
|                                    GIÁM SÁT SỨC KHỎE HẠ TẦNG DỊCH VỤ                                    |
+------------------------------------+------------------------------------+-------------------------------+
| [XANH] Cơ sở dữ liệu (PostgreSQL)  | [XANH] Dịch vụ AI (LangGraph)      | [XANH] Bộ đệm (Redis Upstash) |
| Trạng thái: Hoạt động bình thường  | Trạng thái: Sẵn sàng xử lý RAG     | Trạng thái: Kết nối ổn định   |
+------------------------------------+------------------------------------+-------------------------------+
| [XANH] Lưu trữ (Cloudflare R2/S3)  | [XANH] Vector DB (Qdrant)          | [XANH] Xử lý ngầm (Celery)    |
| Trạng thái: Đọc/Ghi tệp mượt mà    | Trạng thái: Tìm kiếm ngữ nghĩa OK  | Trạng thái: Đang tiêu thụ task|
+------------------------------------+------------------------------------+-------------------------------+
```

### Chi tiết chức năng và cảnh báo của 6 dịch vụ:

1. **Cơ sở dữ liệu quan hệ (PostgreSQL - Database):**
   - *Vai trò:* Lưu trữ toàn bộ thông tin đăng nhập, hồ sơ người dùng, thông tin khóa học, kết quả điểm thi, giao dịch thanh toán và các khóa API đã mã hóa.
   - *Hiện tượng khi báo đèn đỏ:* Người dùng không thể đăng nhập, không thể lưu bài học hoặc không thể ghi nhận điểm số.
2. **Dịch vụ AI Đa tác tử (LangGraph AI Service):**
   - *Vai trò:* Điều phối luồng xử lý thông minh (Intelligent Agent Graph): phân tích câu hỏi của sinh viên, tìm kiếm tài liệu đối sánh, chấm điểm bài luận và soạn bài giảng tự động cho giảng viên.
   - *Hiện tượng khi báo đèn đỏ:* Học viên chat với AI không phản hồi, tính năng tự động tạo câu hỏi trắc nghiệm báo lỗi.
3. **Bộ nhớ đệm & Hàng đợi thông điệp (Redis Upstash - Cache & Message Broker):**
   - *Vai trò:* Lưu trữ tạm thời phiên đăng nhập của người dùng, lưu bộ nhớ đệm cây danh mục khóa học để tải trang nhanh dưới 50ms, và làm cầu nối truyền tải nhiệm vụ cho Celery Worker.
   - *Hiện tượng khi báo đèn đỏ:* Tốc độ tải trang web bị chậm rõ rệt, tác vụ tải tài liệu không được đưa vào xử lý.
4. **Kho lưu trữ tệp đối tượng (Cloudflare R2 / MinIO Storage):**
   - *Vai trò:* Lưu trữ an toàn các tệp video bài giảng chất lượng cao, hình ảnh bìa (Thumbnail), tệp giáo trình PDF, slide thuyết trình và bài tập học viên nộp.
   - *Hiện tượng khi báo đèn đỏ:* Không thể tải video lên, học viên không bấm nghe hoặc tải tài liệu đính kèm về được.
5. **Cơ sở dữ liệu Vector (Qdrant Vector Database):**
   - *Vai trò:* Chứa hàng triệu vector nhúng ngữ nghĩa của tài liệu. Cho phép trợ lý AI tìm chính xác đoạn văn liên quan nhất chỉ trong vài mili-giây.
   - *Hiện tượng khi báo đèn đỏ:* Tính năng hỏi đáp tài liệu thông minh (RAG) không trích dẫn được nguồn gốc trang sách.
6. **Công nhân xử lý ngầm (Celery Worker):**
   - *Vai trò:* Động cơ chạy nền liên tục thực hiện các tác vụ nặng: bóc tách chữ từ tệp PDF hàng trăm trang, chạy mô hình Whisper để biến giọng nói video thành văn bản, tự động chấm điểm bài tập tự luận.
   - *Hiện tượng khi báo đèn đỏ:* Tài liệu tải lên bị kẹt vĩnh viễn ở trạng thái "Đang xử lý (Processing)".

---

## 4. Quản Lý Người Dùng & Phân Quyền Hệ Thống (User Management & RBAC)

Trang **Quản lý Người Dùng** tại đường dẫn `/app/admin/users` cung cấp bức tranh toàn cảnh về cộng đồng học tập trên sàn.

### 4.1 Bảng Danh Sách & Bộ Lọc Nâng Cao

- **Tìm kiếm:** Gõ từ khóa bất kỳ để tìm theo Tên, Email hoặc Mã định danh người dùng.
- **Lọc theo Vai trò (Role Filter):**
  - *Tất cả vai trò:* Hiển thị toàn bộ tài khoản.
  - *Quản trị viên (Admin):* Xem danh sách các cán bộ quản trị cấp cao.
  - *Giảng viên (Lecturer):* Xem danh sách các thầy cô giáo có quyền tạo khóa học và mở lớp.
  - *Học viên (Student):* Xem toàn bộ người học đăng ký trên nền tảng.
- **Chỉ số tổng hợp theo thời gian thực:** Hiển thị tức thì tổng số người dùng, số Quản trị viên, số Giảng viên và số Học viên hiện có.

---

### 4.2 Thao Tác Tạo Mới Người Dùng (Direct User Provisioning)

Trong các trường hợp cần cấp tài khoản chính thức cho giảng viên của đối tác liên kết, hoặc tạo tài khoản cho cán bộ quản lý mới mà không yêu cầu họ tự đăng ký:

```
[ Bấm nút "Thêm người dùng" (Nút tím góc phải) ]
                     │
                     ▼
[ Điền Form: Họ tên, Email, Mật khẩu khởi tạo, Vai trò ]
                     │
                     ▼
[ Bấm "Tạo người dùng" ]
                     │
                     ▼
[ Hệ thống tự động cấp hạn mức VIP: 10GB Lưu trữ + 2.000.000 Token AI ]
```

1. Bấm nút **Thêm người dùng** ở góc trên cùng bên phải.
2. Điền đầy đủ thông tin:
   - **Họ và tên:** Nhập tên đầy đủ (Ví dụ: *TS. Nguyễn Văn Hùng*).
   - **Địa chỉ Email:** Email công vụ hoặc email cá nhân hợp lệ (Ví dụ: *hung.nguyen@daihoc.edu.vn*).
   - **Mật khẩu khởi tạo:** Mật khẩu tạm thời có độ phức tạp cao (Tối thiểu 8 ký tự, có chữ hoa, số và ký tự đặc biệt). Quản trị viên bàn giao mật khẩu này cho người dùng và yêu cầu họ đổi mật khẩu ở lần đăng nhập đầu tiên.
   - **Chọn vai trò:** Lựa chọn `Học viên`, `Giảng viên`, hoặc `Quản trị viên`.
3. Bấm **Tạo người dùng**.
4. **Cơ chế đặc quyền tự động:** Tài khoản được tạo trực tiếp từ bảng điều khiển quản trị sẽ được tự động thiết lập hạn ngạch cao cấp (Enterprise Quota: 10 GB dung lượng lưu trữ đám mây, 50 lượt tải video và 2.000.000 Token AI hàng tháng).

---

### 4.3 Thay Đổi Vai Trò & Thăng/Hạ Cấp Quyền Hạn (Role Modification)

Khi một học viên hoàn thành khóa đào tạo chứng chỉ giảng dạy và được bổ nhiệm làm Giảng viên của hệ thống:
1. Tìm tài khoản của người đó trong bảng danh sách.
2. Bấm vào nút **Chỉnh sửa** (Biểu tượng chiếc bút) ở cột Thao tác.
3. Trong hộp thoại hiện ra, tại mục **Vai trò người dùng**, bấm chọn **Giảng viên (Lecturer)**.
4. Bấm **Lưu thay đổi**. Ngay lập tức, khi người dùng đó tải lại trang web, thanh menu bên trái của họ sẽ xuất hiện toàn bộ các công cụ giảng dạy: *Tạo khóa học, Soạn bài giảng, Chấm bài tập và Thống kê doanh thu*.

---

### 4.4 Khóa Tài Khoản (Ban/Deactivate) & Kích Hoạt Lại

Khi phát hiện một tài khoản có hành vi phát ngôn vi phạm chuẩn mực văn hóa, nghi vấn gian lận bài thi hoặc chia sẻ tài khoản cho nhiều người:
1. Tìm người dùng cần xử lý trong bảng.
2. Tại cột **Trạng thái**, nhấp chuột trực tiếp vào nút công tắc gạt (Toggle Switch).
3. Nếu tài khoản đang màu xanh lá (Hoạt động), bấm gạt sang màu xám (Đã khóa):
   - Ngay lập tức, phiên đăng nhập của người dùng đó sẽ bị thu hồi. Người đó không thể truy cập vào bất kỳ bài học hoặc dịch vụ nào trên sàn.
4. Khi giải quyết xong khiếu nại, Quản trị viên chỉ cần bấm gạt công tắc trở lại màu xanh lá để kích hoạt tài khoản bình thường.

---

### 4.5 Xóa Vĩnh Viễn Người Dùng (User Deletion)

Thao tác xóa vĩnh viễn là thao tác không thể phục hồi:
1. Bấm nút **Xóa** (Biểu tượng thùng rác màu đỏ) tại dòng người dùng tương ứng.
2. Hộp thoại cảnh báo bảo mật nghiêm ngặt sẽ hiển thị: *"Hành động này sẽ xóa vĩnh viễn toàn bộ dữ liệu, lịch sử học tập và tài liệu của người dùng này khỏi cơ sở dữ liệu"*.
3. Bấm **Xác nhận xóa**.
4. *Lưu ý an toàn:* Nếu bạn vô tình bấm xóa chính tài khoản Quản trị viên đang đăng nhập, hoặc xóa Quản trị viên duy nhất còn lại của hệ thống, hệ thống sẽ tự động chặn lại và hiển thị thông báo lỗi bảo vệ.

---

## 5. Kiểm Duyệt & Quản Trị Khóa Học Toàn Sàn (Course Moderation)

Trang **Quản lý Khóa Học** tại đường dẫn `/app/admin/courses` cho phép Quản trị viên kiểm soát chất lượng học thuật và bản quyền của toàn bộ các khóa đào tạo trên nền tảng.

### 5.1 Danh Sách Khóa Học Tập Trung Toàn Hệ Thống

Không giống như giao diện Giảng viên chỉ xem được khóa học của chính mình, Quản trị viên nhìn thấy toàn bộ khóa học của tất cả các giảng viên trên hệ thống:
- Cột thông tin hiển thị rõ: Ảnh Thumbnail, Tên khóa học, Giảng viên sở hữu, Học phí (VNĐ hoặc Miễn phí), Số học viên đã ghi danh, và Huy hiệu trạng thái:
  - **Bản nháp (Draft - Màu vàng):** Giảng viên đang biên soạn, chưa công bố ra ngoài.
  - **Đã xuất bản (Published - Màu xanh lá):** Khóa học đang hiển thị công khai trên danh mục để học viên đăng ký.
  - **Đã lưu trữ (Archived - Màu xám):** Khóa học tạm dừng tuyển sinh mới.

---

### 5.2 Thanh Tra Chi Tiết Khóa Học & Danh Sách Học Viên

1. Bấm vào nút **Xem chi tiết** (Biểu tượng con mắt) ở cột Thao tác của bất kỳ khóa học nào.
2. Cửa sổ thanh tra chuyên sâu sẽ hiển thị toàn diện các thông tin:
   - **Thông tin học thuật:** Mô tả chi tiết, Danh mục cha/con, Trình độ (Cơ bản/Trung cấp/Nâng cao), Ngôn ngữ giảng dạy.
   - **Tài chính khóa học:** Doanh thu ước tính mà khóa học đã tạo ra và giá niêm yết.
   - **Danh sách học viên đã ghi danh:** Quản trị viên có thể xem danh sách tất cả học viên trong khóa: Họ và tên, Ngày đăng ký học, Số tiền đã thanh toán (VNĐ), và Tỷ lệ hoàn thành khóa học (%).

---

### 5.3 Quyền Can Thiệp Khẩn Cấp: Gỡ Bỏ Hoặc Xóa Khóa Học Vi Phạm

Khi nhận được phản ánh về một khóa học vi phạm bản quyền video hoặc chứa nội dung sai lệch:
1. **Chuyển trạng thái về Bản nháp / Lưu trữ:**
   - Quản trị viên bấm nút **Đổi trạng thái**.
   - Chọn chuyển khóa học từ `Published` về `Draft` hoặc `Archived`.
   - Ngay lập tức, khóa học bị gỡ khỏi trang chủ và trang tìm kiếm công khai, ngăn chặn học viên mới tiếp tục mua khóa học vi phạm.
2. **Xóa vĩnh viễn khóa học rác:**
   - Đối với các khóa học rác do người dùng thử nghiệm tạo bừa bãi, Quản trị viên bấm biểu tượng thùng rác màu đỏ.
   - Xác nhận xóa trong hộp thoại. Toàn bộ các chương, bài học và tài liệu liên quan sẽ được xóa sạch khỏi cơ sở dữ liệu.

---

## 6. Quản Trị Cây Danh Mục Đào Tạo Đa Cấp (Category Hierarchy Management)

Để các khóa học trên trang chủ được phân loại khoa học giúp học viên dễ dàng tìm kiếm theo chuyên ngành, Quản trị viên thiết lập hệ thống **Cây Danh Mục Đào Tạo (Category Taxonomy Tree)** tại mục Cài đặt (`/app/admin/settings` hoặc `/api/v1/categories`).

```
[ CÔNG NGHỆ THÔNG TIN ] (Danh mục gốc - Slug: cong-nghe-thong-tin)
         │
         ├──▶ [ Trí Tuệ Nhân Tạo ] (Danh mục con cấp 1 - Slug: tri-tue-nhan-tao)
         │           │
         │           ├──▶ [ Học Máy & Học Sâu ] (Danh mục con cấp 2)
         │           └──▶ [ Xử Lý Ngôn Ngữ Tự Nhiên - NLP ] (Danh mục con cấp 2)
         │
         └──▶ [ Lập Trình Web ] (Danh mục con cấp 1)
                     │
                     ├──▶ [ Frontend (React, Vue) ]
                     └──▶ [ Backend (Python, Node.js) ]
```

### 6.1 Các Khái Niệm Quan Trọng

- **Danh mục gốc (Top-level / Parent Category):** Nhóm ngành đào tạo lớn (Ví dụ: *Công nghệ thông tin, Ngoại ngữ, Quản trị kinh doanh, Thiết kế đồ họa*). Danh mục này có `parent_id` là rỗng (null).
- **Danh mục con đa cấp (Sub-categories):** Các chuyên ngành hẹp thuộc danh mục lớn. Hệ thống hỗ trợ lồng ghép phân cấp không giới hạn tầng sâu.
- **Mã đường dẫn tĩnh (Slug):** Đoạn chữ không dấu, viết thường, nối nhau bởi dấu gạch ngang (Ví dụ: `tri-tue-nhan-tao`), dùng để tạo đường dẫn URL thân thiện cho công cụ tìm kiếm Google (SEO).

### 6.2 Thao Tác Tạo Mới & Sắp Xếp Danh Mục

1. Bấm nút **Thêm danh mục mới**.
2. Nhập **Tên danh mục:** Ví dụ: *Thị Giác Máy Tính (Computer Vision)*.
3. **Mã Slug tự động:** Hệ thống tự động chuyển đổi tên tiếng Việt thành mã slug chuẩn `thi-giac-may-tinh`. Quản trị viên có thể chỉnh sửa lại nếu muốn.
4. Nhập **Mô tả ngắn** về chuyên ngành này.
5. **Chọn Danh mục cha (Parent Category):**
   - Nếu đây là ngành lớn mới, chọn: *Là danh mục gốc*.
   - Nếu là chuyên ngành nhánh, bấm chọn danh mục cha tương ứng (ví dụ: chọn cha là *Trí Tuệ Nhân Tạo*).
6. Bấm **Lưu danh mục**.
7. **Cơ chế tối ưu hóa tốc độ (Redis Caching):** Ngay sau khi bạn tạo hoặc chỉnh sửa danh mục, hệ thống sẽ tự động làm mới bộ đệm trong Redis Upstash. Hàng vạn học viên truy cập trang chủ sẽ nhìn thấy ngay danh mục mới mà không làm tăng tải cho cơ sở dữ liệu PostgreSQL.

---

## 7. Két Sắt Quản Lý Khóa AI & Cơ Chế Xoay Vòng Thông Minh (AI Key Vault)

Đây là tính năng độc quyền mang tính đột phá về công nghệ, giúp vận hành hạ tầng Trí tuệ nhân tạo một cách ổn định, tiết kiệm và an toàn tuyệt đối. Quản trị viên truy cập tại tab **Khóa AI (AI Key Vault)** trong mục Cài đặt (`/app/admin/settings` hoặc `/app/admin/ai-keys`).

### 7.1 Bốn Thẻ Chỉ Số Vận Hành AI Toàn Nền Tảng

```
+--------------------------+--------------------------+--------------------------+--------------------------+
|      TỔNG SỐ KHÓA AI     |    KHÓA ĐANG HOẠT ĐỘNG   |    NHÀ CUNG CẤP AI       |     TỔNG LƯỢT GỌI AI     |
|          8               |            6             |            4             |          84.210          |
| (Các key Gemini trong database) | (Sẵn sàng trong Pool) | (Gemini Developer API) | (Đã phục vụ học viên) |
+--------------------------+--------------------------+--------------------------+--------------------------+
```

### 7.2 Cơ Chế Bảo Mật Tuyệt Đối (Zero-Leakage Encryption)

Gemini API key là thông tin bí mật. Hệ thống mã hóa key trước khi ghi vào database và không trả lại giá trị đầy đủ sau khi lưu:

1. **Mã hóa đối xứng Fernet (AES-128 CBC kết hợp HMAC SHA-256):** Khi Quản trị viên nhập khóa mới, mã khóa lập tức được mã hóa ngay trước khi ghi vào cơ sở dữ liệu. Ngay cả kỹ sư quản trị máy chủ mở trực tiếp bảng cơ sở dữ liệu cũng chỉ nhìn thấy một chuỗi ký tự mã hóa vô nghĩa.
2. **Che mờ giao diện (Masked Rendering):** Sau khi lưu, key đầy đủ không được trả lại cho trình duyệt; giao diện chỉ hiển thị dấu chấm và trạng thái đã bảo vệ.

---

### 7.3 Quản Lý Gemini Key Và Model

```
[ Mở Admin → Khóa API & AI ]
          │
          ▼
[ Thêm Gemini API Key và đặt tên gợi nhớ ]
          │
          ▼
[ Chọn model, mặc định gemini-3.5-flash-lite ]
          │
          ▼
[ Lưu — key được mã hóa và đồng bộ tới AI service ]
```

1. Mở mục **Khóa API & AI** trong trang quản trị.
2. Thêm Gemini API key, đặt tên gợi nhớ rồi lưu. Key đầy đủ chỉ xuất hiện trong lúc nhập; sau đó hệ thống mã hóa trong database và chỉ hiển thị trạng thái đã bảo vệ.
3. Chọn model ID Gemini và bấm **Lưu model**. Giá trị mặc định là `gemini-3.5-flash-lite`; thay đổi áp dụng cho chatbot và phiên âm audio.
4. Các key đang bật được AI service dùng luân phiên. Worker gửi audio qua AI service nên không cần lưu Gemini key riêng.

Heroku không cần `GEMINI_API_KEY` hoặc `GEMINI_MODEL`. Giữ `AI_KEY_ENCRYPTION_KEY` ổn định; nếu đổi khóa mã hóa, các Gemini API key đã lưu sẽ không giải mã được.

---

### 7.4 Cơ Chế Xoay Vòng Thông Minh (Round-Robin) & Tự Động Chuyển Lỗi (Auto-Failover)

Đây là cơ chế vận hành ngầm thông minh nhất của nền tảng:

```
                          YÊU CẦU CỦA HỌC VIÊN
                   (Hỏi đáp tài liệu / Tạo trắc nghiệm)
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │    BỘ ĐIỀU PHỐI AI POOL THÔNG MINH   │
                 └──────────────────┬───────────────────┘
                                    │
               ┌────────────────────┴───────────────────┐
               ▼                                        ▼
    [ Chìa khóa Gemini 1 ]                   [ Chìa khóa Gemini 2 ]
    (Trạng thái: Đang gọi)                   (Trạng thái: Chờ sẵn sàng)
               │
      Gặp lỗi HTTP 429!
 (Hết lượt gọi hoặc hết quota)
               │
               ▼
   TỰ ĐỘNG CHUYỂN LẬP TỨC
 (Tự động Failover trong 0.1s) ──────────────▶   TIẾP NHẬN YÊU CẦU THÀNH CÔNG!
                                                 (Học viên không hề bị gián đoạn)
```

- **Xoay vòng tải (Round-Robin):** Khi có nhiều học viên đồng thời sử dụng các tính năng AI, hệ thống sẽ phân bổ tuần tự các yêu cầu qua các chìa khóa đang hoạt động trong Pool. Nhờ vậy, không có chìa khóa nào bị quá tải đơn độc.
- **Tự động chuyển lỗi (Auto-Failover on HTTP 429):** Khi một chìa khóa bị cạn tiền hoặc vượt quá số lượt gọi cho phép trong 1 phút của nhà cung cấp (mã lỗi `HTTP 429 Too Many Requests`), dịch vụ AI Backend sẽ lập tức tự động chuyển yêu cầu sang chìa khóa tiếp theo trong Pool. Học viên hoàn toàn không thấy màn hình báo lỗi và việc học diễn ra liền mạch 100%!

### 7.5 Bật / Tắt Khóa Tức Thì & Giám Sát Lượt Dùng

- **Công tắc Bật/Tắt (Toggle Active):** Khi bạn muốn nạp tiền hoặc bảo trì một tài khoản bên Google, bạn không cần phải xóa chìa khóa. Chỉ cần bấm nút công tắc gạt sang màu xám. Hệ thống sẽ ngay lập tức loại chìa khóa đó ra khỏi Pool quay vòng. Sau khi nạp tiền xong, gạt bật lại màu xanh để sử dụng tiếp.
- **Theo dõi số lượt gọi (Usage Counter):** Mỗi dòng chìa khóa đều hiển thị tổng số lượt gọi thành công và thời gian lần cuối cùng chìa khóa được sử dụng. Giúp Quản trị viên đối soát hóa đơn hàng tháng với các hãng công nghệ AI một cách minh bạch.

---

## 8. Cài Đặt Toàn Hệ Thống & Quản Trị Định Mức (System Settings & Quotas)

Tại trang **Cài Đặt Hệ Thống** (`/app/admin/settings`), Quản trị viên theo dõi các thông số nền tảng và thiết lập hạn mức tài nguyên.

### 8.1 Thông Tin Nền Tảng Kỹ Thuật (Platform Metadata)
- **Phiên bản hệ thống:** `2.0.0 (4-Service Microservices Architecture)`.
- **Giao diện người dùng (Frontend):** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS.
- **Cổng giao tiếp dữ liệu (API Gateway):** FastAPI, Uvicorn, Python 3.11.
- **Lõi trí tuệ nhân tạo (AI Core):** FastAPI + AsyncIO Multi-Step RAG Workflow (`GraphState`) và Gemini LLM.
- **Cơ sở dữ liệu Vector:** Qdrant Vector Engine.

### 8.2 Bảng Định Mức Tài Nguyên Mặc Định (Default Quotas)

Khi một người dùng tự đăng ký tài khoản mới trên trang web, hệ thống tự động gán định mức mặc định theo bảng sau:

| Loại tài khoản | Dung lượng lưu trữ tối đa | Số lượng video tối đa | Số Token AI hàng tháng |
|---|---|---|---|
| **Học viên Tiêu chuẩn (Student)** | 500 MB | 5 video | 100.000 Tokens |
| **Giảng viên (Lecturer)** | 5.0 GB | 25 video | 1.000.000 Tokens |
| **Tài khoản Doanh nghiệp / Quản trị** | 10.0 GB | 50 video | 2.000.000 Tokens |

*Ghi chú:* Để nâng hạn mức cho một giảng viên đặc biệt cần tải lên các khóa học đồ sộ nhiều gigabyte, Quản trị viên vào trang Quản lý người dùng (`/app/admin/users`), chọn tài khoản và cập nhật hạn mức riêng biệt.

---

## 9. Quy Trình Xử Lý Sự Cố Vận Hành Thực Tế (Operational Incident Playbooks)

Khi tiếp nhận phản hồi sự cố từ đội ngũ hỗ trợ khách hàng hoặc giảng viên, Quản trị viên xử lý theo 4 kịch bản quy chuẩn sau:

### Kịch Bản 1: Giảng viên hoặc Học viên báo lỗi "Hệ thống AI không phản hồi" hoặc "Có lỗi xảy ra khi tạo trắc nghiệm"

- **Bước 1:** Truy cập ngay vào Bảng điều khiển Quản trị (`/app/admin`).
- **Bước 2:** Nhìn vào đèn chỉ số **Dịch vụ AI (LangGraph)**. Nếu đèn báo Đỏ, liên hệ ngay đội ngũ hạ tầng DevOps kiểm tra máy chủ AI.
- **Bước 3:** Nếu đèn AI vẫn Xanh, truy cập ngay vào tab **Khóa AI (AI Key Vault)** (`/app/admin/ai-keys` hoặc `/app/admin/settings`).
- **Bước 4:** Kiểm tra danh sách khóa:
  - Có bao nhiêu Gemini key đang ở trạng thái **Hoạt động (Active)**? Nếu tất cả key đều đang tắt hoặc số lượt gọi tăng vọt, có thể tài khoản Google đã hết quota hoặc chạm hạn ngạch.
- **Bước 5 - Khắc phục:** Thêm một Gemini API key còn hạn ngạch trong Admin → Khóa API & AI, rồi bật key. AI service nhận cấu hình mới qua đồng bộ nội bộ.

---

### Kịch Bản 2: Tài liệu PDF hoặc Video tải lên bị kẹt vĩnh viễn ở trạng thái "Đang xử lý (Processing)"

- **Bước 1:** Tại Dashboard, kiểm tra thẻ chỉ số **Đang xử lý (Documents Processing)** xem số lượng tệp tồn đọng có lớn bất thường không (trên 20 tệp).
- **Bước 2:** Kiểm tra đèn **Xử lý ngầm (Celery Worker)**:
  - Nếu đèn báo Đỏ: Worker xử lý ngầm đang bị dừng hoặc mất kết nối với Redis. Cần khởi động lại tiến trình Celery trên máy chủ.
- **Bước 3:** Kiểm tra đèn **Lưu trữ (Cloudflare R2 / MinIO)**:
  - Đảm bảo máy chủ lưu trữ tệp vẫn hoạt động bình thường, không bị đầy dung lượng ổ cứng.
- **Bước 4:** Hướng dẫn người dùng kiểm tra kích thước tệp:
  - Tệp tải lên có vượt quá giới hạn cho phép **100 MB** hay không.
  - Tệp PDF có bị đặt mật khẩu bảo vệ hay không (Hệ thống không thể bóc tách chữ từ các file PDF bị khóa mật khẩu).

---

### Kịch Bản 3: Học viên phản hồi "Đã thanh toán học phí qua Ngân hàng / Ví điện tử nhưng chưa vào học được"

- **Nguyên nhân thường gặp:** Đường truyền giữa cổng thanh toán (VNPay / MoMo) và hệ sinh thái bị trễ mạng cục bộ, dẫn đến tín hiệu Webhook chưa kịp kích hoạt trạng thái ghi danh.
- **Quy trình xử lý khẩn cấp bảo vệ quyền lợi học viên:**
  1. Yêu cầu bộ phận hỗ trợ xin học viên: *Ảnh chụp màn hình biên lai trừ tiền thành công* (có mã giao dịch ngân hàng) và *Địa chỉ Email tài khoản*.
  2. Quản trị viên truy cập vào **Quản lý Khóa Học** (`/app/admin/courses`).
  3. Bấm vào khóa học mà học viên đã đăng ký mua -> Bấm **Xem chi tiết**.
  4. Mở danh sách học viên ghi danh của khóa học. Kiểm tra xem email của học viên đã có trong danh sách hay chưa.
  5. Nếu trạng thái đang là `pending` (Chờ xử lý), Quản trị viên bấm nút **Kích hoạt thủ công (Confirm Enrollment)** cho học viên.
  6. Khóa học sẽ lập tức chuyển sang trạng thái đã thanh toán thành công và mở quyền vào học trọn đời cho học viên.

---

### Kịch Bản 4: Giảng viên báo không tìm thấy nút Xuất Bản Khóa Học hoặc Khóa Học bị lỗi

- **Bước 1:** Quản trị viên vào **Quản lý Khóa Học** (`/app/admin/courses`).
- **Bước 2:** Tìm khóa học của giảng viên đó và bấm **Xem chi tiết**.
- **Bước 3:** Kiểm tra xem khóa học đã có ít nhất một Chương (Section) và một Bài học (Lesson) hoàn chỉnh hay chưa. Hệ thống có cơ chế kiểm tra chất lượng: nếu khóa học hoàn toàn rỗng chưa có nội dung bài giảng, hệ thống sẽ không cho phép xuất bản để tránh ảnh hưởng đến trải nghiệm học tập của sinh viên.
- **Bước 4:** Thông báo cho giảng viên bổ sung đầy đủ nội dung bài học trước khi tiến hành xuất bản.

---

## 10. Danh Mục Kiểm Tra Định Kỳ Mỗi Buổi Sáng (Daily Morning Checklist)

Để đảm bảo toàn bộ hệ thống luôn vận hành với độ ổn định cao nhất, cán bộ quản trị trực ban nên dành ra **3 phút đầu mỗi buổi sáng** để thực hiện bảng kiểm tra 5 bước sau:

```
[ BẢNG KIỂM TRA ĐỊNH KỲ MỖI BUỔI SÁNG - DAILY 3-MINUTE HEALTH CHECK ]

[ ] Bước 1: Đăng nhập vào https://learninghubs.tech bằng tài khoản Quản trị viên.
[ ] Bước 2: Quan sát Bảng Giám Sát Sức Khỏe trên Dashboard:
            - PostgreSQL: Đèn Xanh Lục
            - LangGraph AI: Đèn Xanh Lục
            - Redis Upstash: Đèn Xanh Lục
            - MinIO / R2 Storage: Đèn Xanh Lục
            - Qdrant Vector DB: Đèn Xanh Lục
            - Celery Worker: Đèn Xanh Lục
[ ] Bước 3: Kiểm tra chỉ số "Đang xử lý (Documents Processing)": Đảm bảo không có hàng chục tài liệu bị ứ đọng từ hôm trước.
[ ] Bước 4: Kiểm tra Admin → Khóa API & AI: bảo đảm có ít nhất một Gemini API key đang hoạt động và model đã chọn hợp lệ.
[ ] Bước 5: Kiểm tra mục Quản lý người dùng: Đảm bảo không có tài khoản bất thường gửi lượng yêu cầu đột biến.
```

Thực hiện chuẩn xác quy trình trên sẽ giúp nền tảng vận hành trơn tru, không xảy ra sự cố bất ngờ trong các khung giờ học viên và giảng viên truy cập cao điểm!

---

*Xem thêm các tài liệu liên quan:*
- [Cẩm nang Dành Cho Giảng Viên (Lecturer Guide)](./lecturer-guide.md)
- [Quy Trình Hoạt Động Từ Đầu Đến Cuối Toàn Hệ Thống](./end-to-end-workflows.md)
- [Đặc Tả Kỹ Thuật API Quản Trị & Phân Quyền RBAC](../api/admin.md)
- [Tài Khoản Mẫu & Tham Chiếu Phân Quyền](./demo-accounts.md)
- [Mục Lục Tài Liệu Hệ Thống](../README.md)
