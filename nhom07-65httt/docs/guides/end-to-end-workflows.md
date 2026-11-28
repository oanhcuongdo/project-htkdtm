# Các Luồng Vận Hành Thực Tế Từ A Đến Z

> Phiên bản: 2.0 | Cập nhật: 14/09/2026 | Tác giả: Đội ngũ Trải nghiệm & Vận hành | Trạng thái: Chính thức (Active)

Tài liệu này dẫn bạn đi trọn vẹn 4 hành trình sử dụng Multimodal AI Learning Hub ngoài đời thực — từ cú nhấp chuột đầu tiên trên màn hình cho tới những gì hệ thống tự động làm phía sau. Bạn không cần biết lập trình. Mỗi khi gặp thuật ngữ kỹ thuật, chúng tôi giải thích ngay bằng ví dụ đời thường.

**Cách đọc tài liệu này:**

- Mỗi kịch bản có cùng một cấu trúc 5 phần: Người thực hiện -> Mục tiêu -> Thao tác trên giao diện từng bước -> Điều gì xảy ra ngầm bên dưới -> Kết quả nhìn thấy.
- Phần "Điều gì xảy ra ngầm bên dưới" được viết như chuyện hậu trường: bạn hình dung có một đội ngũ nhân viên vô hình (máy chủ, kho chứa, trợ lý AI) đang phối hợp với nhau.
- Nếu bạn là người mới, hãy đọc Kịch bản 1 trước, sau đó nhảy tới kịch bản đúng vai trò của mình (học viên: 1 và 3, giảng viên: 2, quản trị viên: 4).

**Bản đồ nhanh 4 kịch bản:**

| Kịch bản | Nhân vật | Câu hỏi được trả lời |
|---|---|---|
| 1. Ôn thi từ PDF 100 trang | Học viên | Tải tài liệu lên rồi để AI ra đề cho tôi như thế nào? |
| 2. Mở khóa học và bán | Giảng viên + Học viên | Đăng khóa học, thu học phí và mở khóa tự động ra sao? |
| 3. Gia sư AI trong phòng học Focus Mode | Học viên | Học sâu với AI gợi mở, bản đồ tư duy và podcast ra sao? |
| 4. Xử lý sự cố và vận hành định kỳ | Quản trị viên | Mỗi sáng admin kiểm tra sức khỏe hệ thống thế nào? |

---

## Kịch bản 1: Học viên tải tài liệu học tập (PDF 100 trang) lên ôn thi

**Người thực hiện:** Minh Anh, sinh viên năm 2, đang ôn thi môn Kinh tế vi mô. Minh Anh không rành công nghệ, chỉ quen dùng trình duyệt web.

**Mục tiêu:** Biến cuốn giáo trình PDF 100 trang thành bộ 10 câu trắc nghiệm có đáp án và lời giải, làm bài ngay trên web và biết mình yếu ở đâu.

**Điều kiện cần trước khi bắt đầu:**

- Đã có tài khoản học viên và đã đăng nhập.
- File PDF dưới 100MB, không đặt mật khẩu mở file.
- Dùng trình duyệt Chrome, Edge hoặc Safari bản mới.

### Bước 1 — Mở Document Hub và tải file lên

1. Minh Anh bấm mục **Tài liệu (Document Hub)** trên thanh menu bên trái.
2. Màn hình hiện ô tải lên có dòng chữ "Kéo thả file vào đây hoặc bấm để chọn file".
3. Minh Anh kéo file `Giao-trinh-Kinh-te-vi-mo.pdf` từ máy tính thả vào ô. Thanh tiến trình chạy từ 0% lên 100%, sau đó file xuất hiện trong danh sách với nhãn màu vàng **"Đang xử lý"**.
4. Minh Anh có thể tắt máy đi uống nước — không cần ngồi chờ, vì việc xử lý nặng diễn ra ở hậu trường.

### Bước 2 — Điều gì xảy ra ngầm bên dưới (chuyện hậu trường)

Hãy tưởng tượng phía sau màn hình có một dây chuyền nhà máy mini gồm 5 trạm:

1. **Cổng tiếp nhận (API Gateway):** Nhận file từ trình duyệt, kiểm tra nhanh "file có phải PDF không, có vượt dung lượng không, có virus không". Nếu đạt, chuyển tiếp.
2. **Kho chứa file (MinIO):** Giống như nhà kho chứa đồ. File gốc được cất nguyên vẹn vào kho để sau này tải lại hoặc xem trước.
3. **Sổ ghi chép (Postgres):** Giống cuốn sổ cái của kế toán. Hệ thống ghi một dòng: "Minh Anh vừa nộp 1 file, lúc 20h05, trạng thái: đang xử lý". Nhờ cuốn sổ này mà sau này không bị mất dấu file.
4. **Hàng đợi việc (Redis):** Giống khay đựng phiếu việc trong quán ăn. Hệ thống đặt một phiếu "Cần xử lý file số 123" lên khay.
5. **Nhân viên hậu trường (Celery Worker):** Người đầu bếp nhận phiếu và làm toàn bộ việc nặng mà Minh Anh không nhìn thấy:
   - **Bóc chữ từng trang (PyMuPDF):** Mở PDF và sao chép toàn bộ chữ, trang nào ra trang đó, giữ nguyên số trang để sau này trích dẫn.
   - **Nhận diện chữ trong ảnh (Tesseract OCR):** Nếu có trang là ảnh chụp (ví dụ slide chụp từ bảng), máy sẽ "đọc" chữ trong ảnh giống như mắt người nhìn ảnh rồi gõ lại thành chữ.
   - **Cắt nhỏ thông minh (Chunking):** Cắt cuốn sách thành từng mẩu khoảng 800 ký tự (tầm nửa trang giấy), mỗi mẩu gối lên mẩu trước 150 ký tự để không bị đứt ý giữa chừng. Cách cắt này giống như cắt giò lụa mà mỗi lát hơi chồng lên nhau để không rơi nhân.
   - **Đánh mã ý nghĩa (Embedding 384 chiều):** Mỗi mẩu được AI chấm một dãy 384 con số, giống như tọa độ GPS nhưng cho ý nghĩa. Hai mẩu nói về cùng một khái niệm sẽ có tọa độ gần nhau, nhờ đó AI tìm kiếm theo ý hiểu chứ không chỉ theo từ khóa.
   - **Cất vào tủ trí nhớ (Qdrant):** Toàn bộ các mẩu kèm tọa độ được xếp vào tủ trí nhớ thông minh. Từ giờ, mỗi câu hỏi của Minh Anh sẽ được đối chiếu với tủ này.
   - Cuối cùng, nhân viên hậu trường báo về cuốn sổ cái: đổi trạng thái file từ "Đang xử lý" sang **"Sẵn sàng"**.

### Bước 3 — Tạo trắc nghiệm AI và làm bài

1. Minh Anh thấy nhãn file chuyển sang màu xanh **"Sẵn sàng"**, bấm nút **"Tạo trắc nghiệm AI"**.
2. Hộp thoại hiện ra: Minh Anh chọn **10 câu**, độ khó **Trung bình**, phạm vi **Toàn bộ tài liệu**, rồi bấm **Bắt đầu tạo**. Màn hình hiện hiệu ứng "AI đang soạn đề..." khoảng 30–60 giây.
3. Ngầm bên dưới, hệ thống làm 3 việc: (a) vào tủ trí nhớ tìm các đoạn trọng tâm hay ra thi nhất, (b) gửi các đoạn đó kèm yêu cầu ra đề cho mô hình ngôn ngữ Gemini, (c) Gemini soạn 10 câu, mỗi câu 4 đáp án, chỉ 1 đáp án đúng, kèm lời giải và số trang tham chiếu.
4. Đề thi hiện ra. Minh Anh làm bài, bấm **Nộp bài**. Hệ thống chấm tức thì, hiện điểm 7/10, tô xanh câu đúng, tô đỏ câu sai.
5. Minh Anh bấm vào từng câu sai để xem **lời giải chi tiết** và **đoạn trích gốc trong tài liệu**. Cuối bài có dòng **"Điểm yếu của bạn: Chương 3 — Độ co giãn của cầu"**, gợi ý ôn lại đúng chỗ hổng.

**Kết quả nhìn thấy:** Từ 1 file PDF nặng nề, Minh Anh có ngay phòng thi thử cá nhân: đề đúng trọng tâm giáo trình, chấm điểm tức thì, biết mình yếu ở đâu. File gốc vẫn nằm trong Document Hub để xem lại hoặc tạo thêm flashcard, bản tóm tắt bất cứ lúc nào.

**Nếu gặp trục trặc:**

- File kẹt ở "Đang xử lý" quá 10 phút: thường do PDF là ảnh scan mờ. Hãy thử tải lại bản PDF rõ nét hơn, hoặc chia file 100 trang thành 2 file 50 trang.
- Đề thi ra lan man: hãy thu hẹp phạm vi (chọn 1 chương thay vì toàn bộ tài liệu) rồi tạo lại.

---

## Kịch bản 2: Giảng viên mở khóa học và bán cho học viên

**Người thực hiện:** Thầy Hoàng Nam, giảng viên marketing, muốn bán khóa học online 299.000đ. Học viên: bạn Thu Hà, người mua khóa học.

**Mục tiêu:** Từ khóa học chưa có gì thành khóa học hoàn chỉnh có video, slide, tóm tắt AI, bài kiểm tra, mở bán và thu tiền tự động.

### Bước 1 — Tạo khóa học mới

1. Thầy Nam vào **Dashboard Giảng viên**, bấm **Tạo khóa học mới**.
2. Điền tên khóa học "Marketing căn bản cho người mới bắt đầu", chọn danh mục Kinh doanh, nhập học phí **299.000đ**, tải ảnh bìa, viết 3 dòng giới thiệu. Bấm **Lưu nháp**.

### Bước 2 — Dựng nội dung: Chương, Bài học, Video và Slide

1. Trong khóa học nháp, thầy bấm **Thêm chương** -> đặt tên "Chương 1: Tổng quan Marketing".
2. Trong Chương 1, bấm **Thêm bài học** -> đặt tên "Bài 1: Marketing là gì?".
3. Ở trang bài học, thầy bấm **Tải video lên**, chọn file `bai-1-marketing-la-gi.mp4`. Thanh tiến trình chạy, video được mã hóa để phát mượt trên cả điện thoại yếu mạng.
4. Thầy bấm **Đính kèm tài liệu**, tải file `slide-bai-1.pdf` lên. Slide này cũng đi qua dây chuyền xử lý giống Kịch bản 1 nên sau này học viên có thể hỏi AI ngay trên nội dung slide.

### Bước 3 — Nhờ AI soạn phụ giảng (nút AI Assist)

1. Thầy bấm nút **AI Assist** trong trang bài học.
2. Khoảng một phút sau, hệ thống trả về 3 món quà: **tóm tắt bài giảng 5 gạch đầu dòng**, **dàn ý chi tiết theo mốc thời gian video** (ví dụ phút 02:30 nói về 4P), và **5 từ khóa trọng tâm**.
3. Thầy đọc lướt, sửa 2 chỗ diễn đạt cho đúng giọng của mình, bấm **Áp dụng**. Tóm tắt này sau đó hiện ngay dưới video cho học viên đọc trước khi xem.

Ngầm bên dưới, AI đã đọc toàn bộ chữ bóc ra từ video (lời thoại chuyển thành văn bản) và slide PDF, rồi viết lại thành bản tóm tắt ngắn gọn.

### Bước 4 — Tạo bài kiểm tra cuối bài bằng AI

1. Thầy bấm **Tạo trắc nghiệm AI**, chọn **5 câu**, độ khó **Dễ**, bấm **Tạo**.
2. Hệ thống soạn 5 câu hỏi bám sát nội dung Bài 1, thầy xem trước, đổi đáp án 1 câu cho hóc búa hơn, bấm **Lưu**.

### Bước 5 — Xuất bản khóa học

1. Thầy bấm **Xuất bản khóa học**. Hệ thống kiểm tra nhanh: đã có ít nhất 1 bài học, đã có giá bán, đã có ảnh bìa chưa. Nếu thiếu, nút xuất bản sẽ báo rõ "còn thiếu gì".
2. Khóa học chuyển trạng thái thành **Đang mở bán** và xuất hiện trên trang **Khám phá (Explore)** cho mọi người thấy.

### Bước 6 — Học viên mua khóa học và được mở khóa tự động

1. Thu Hà lướt trang Khám phá, thấy khóa học của thầy Nam, bấm **Xem chi tiết**, đọc đề cương và đánh giá, bấm **Mua khóa học – 299.000đ**.
2. Màn hình thanh toán hiện 2 lựa chọn **MoMo** và **VNPay**. Thu Hà chọn MoMo, mã QR hiện ra, Thu Hà mở điện thoại quét và xác nhận.
3. Khoảnh khắc Thu Hà thanh toán xong, cổng thanh toán gọi ngược về hệ thống một tín hiệu tự động gọi là **Webhook** — giống như tiếng chuông cửa báo "tiền đã về". Hệ thống đối chiếu mã đơn hàng, xác nhận thành công.
4. Ngay lập tức (không cần chờ ai duyệt tay), tài khoản Thu Hà được **mở khóa toàn bộ Chương 1**, nút "Mua" biến thành nút **"Vào học ngay"**. Thu Hà nhận email biên nhận.
5. Bên phía thầy Nam, mở trang **Analytics (Thống kê doanh thu)**: số dư tăng thêm 299.000đ (trừ phí cổng thanh toán nếu có), biểu đồ số học viên tăng từ 0 lên 1, danh sách học viên có tên Thu Hà.

**Kết quả nhìn thấy:** Giảng viên chỉ làm việc soạn nội dung một lần, mọi khâu bán hàng – thu tiền – mở khóa đều tự động. Học viên quét mã xong là học được ngay, không phải chờ kích hoạt thủ công.

**Nếu gặp trục trặc:**

- Học viên đã trả tiền nhưng chưa thấy mở khóa: bảo học viên tải lại trang sau 1–2 phút (Webhook đôi khi đến chậm vài giây). Nếu quá 5 phút vẫn chưa mở, giảng viên hoặc admin vào mục Đơn hàng bấm **Đối soát thủ công**.
- Video tải lên báo lỗi: kiểm tra file dưới 2GB và đúng định dạng MP4.

---

## Kịch bản 3: Học viên sử dụng Gia sư AI Socratic và Bản đồ tư duy trong phòng học Focus Mode

**Người thực hiện:** Bạn Quốc Bảo, học viên khóa "Python cho người mới", đang học bài "Vòng lặp và biến".

**Mục tiêu:** Hiểu sâu một đoạn code khó thay vì chép đáp án, đồng thời có sơ đồ ôn bài và bản audio nghe lại trước khi ngủ.

**Điều kiện cần:** Đã mua (hoặc được mở miễn phí) khóa học nên mới vào được phòng học.

### Bước 1 — Vào phòng học Focus Mode

1. Quốc Bảo mở khóa học, bấm **Vào học**. Màn hình chuyển sang phòng học đặc biệt gọi là **Focus Mode** ở địa chỉ `/learn`: video bài giảng ở giữa, danh sách bài học ở bên trái, 3 tab phụ trợ ở bên phải gồm **Trợ lý AI**, **Bản đồ tư duy**, **Bản tin Podcast**.
2. Focus Mode tự ẩn các thông báo gây xao nhãng để Bảo tập trung. Tiến độ xem video được lưu tự động — tắt máy mở lại vẫn nhớ đang xem tới phút mấy.

### Bước 2 — Dừng video ở đoạn khó hiểu và hỏi Gia sư AI

1. Bảo xem tới phút 12, thầy giảng đoạn vòng lặp `for` bị lỗi mà Bảo chưa hiểu. Bảo bấm **tạm dừng video**, mở khung **Trợ lý AI** bên phải.
2. Ở đầu khung chat có nút chọn chế độ. Bảo chọn chế độ **"Gợi mở Socratic"** (thay vì chế độ "Trả lời trực tiếp").
3. Bảo gõ câu hỏi: *"Tại sao đoạn code này bị lỗi?"* kèm đoạn code copy từ bài giảng.

### Bước 3 — AI dạy theo kiểu gợi mở thay vì cho đáp án

1. AI **không** đưa ngay code sửa đúng. Thay vào đó, AI hỏi ngược lại: *"Bạn hãy nhìn vào dòng số 5. Biến X đã được khai báo trước khi dùng chưa? Giá trị của nó khi vòng lặp chạy lần đầu là gì?"*
2. Bảo suy nghĩ, trả lời: *"À, em chưa gán giá trị ban đầu cho X"*. AI xác nhận: *"Chính xác. Vậy theo bạn nên sửa dòng nào đầu tiên?"*
3. Sau 2–3 lượt hỏi đáp như vậy, Bảo tự tay sửa được lỗi. AI mới tóm tắt lại nguyên nhân gốc rễ và dặn cách tránh lỗi tương tự.

Ngầm bên dưới, Gia sư AI đã làm 3 việc trong tích tắc: (a) lấy lời thoại video quanh phút 12 và nội dung slide liên quan từ tủ trí nhớ, (b) hiểu rằng Bảo đang ở chế độ Socratic nên phải đặt câu hỏi dẫn dắt thay vì đọc đáp án, (c) ghi nhớ lịch sử hội thoại để câu hỏi sau nối tiếp câu hỏi trước, đồng thời ghi lại "Bảo hay quên khởi tạo biến" vào hồ sơ điểm yếu để sau này ra đề ôn đúng chỗ đó.

### Bước 4 — Mở tab Bản đồ tư duy để ghi nhớ lâu

1. Bảo bấm sang tab **Bản đồ tư duy**. Màn hình hiện sơ đồ cây: ở giữa là nút "Vòng lặp và biến", tỏa ra các nhánh "Biến đếm", "Điều kiện dừng", "Lỗi thường gặp", "Ví dụ thực tế".
2. Bảo bấm vào từng nhánh để bung ra chi tiết. Nhánh "Lỗi thường gặp" có đúng lỗi Bảo vừa mắc phải, giúp khắc sâu trí nhớ.
3. Bảo bấm **Tải ảnh sơ đồ** để lưu về máy, dán vào sổ ôn thi.

### Bước 5 — Nghe Bản tin Podcast 2 phút trước khi đi ngủ

1. Bảo bấm sang tab **Bản tin Podcast**. Hệ thống đã chuẩn bị sẵn một bản audio giọng đọc AI dài khoảng 2 phút, tóm tắt toàn bộ bài học hôm nay.
2. Bảo bấm **Phát**, vừa nằm vừa nghe lại: "Hôm nay bạn đã học 3 ý chính... lỗi cần tránh là... ngày mai bạn sẽ học...".
3. Ngầm bên dưới, hệ thống đã nhờ AI viết kịch bản tóm tắt rồi dùng công nghệ chuyển văn bản thành giọng nói để tạo file audio, đính kèm ngay dưới bài học nên không cần mở ứng dụng khác.

**Kết quả nhìn thấy:** Bảo không chỉ xem video một chiều mà được AI kèm cặp như gia sư riêng: hỏi sâu thì được gợi mở để tự nghĩ, học xong có sơ đồ để nhớ, tối có podcast để ôn. Toàn bộ diễn ra trong cùng một phòng học, không phải chuyển qua lại nhiều ứng dụng.

---

## Kịch bản 4: Quản trị viên xử lý sự cố và vận hành định kỳ

**Người thực hiện:** Chị Phương Thảo, quản trị viên vận hành, kiểm tra hệ thống mỗi sáng.

**Mục tiêu:** Đảm bảo 6 dịch vụ đều chạy ổn định, xử lý kịp thời khi chìa khóa AI hết hạn mức, và khóa tài khoản vi phạm một cách an toàn.

### Bước 1 — Nhìn bảng đèn tín hiệu lúc 8h sáng

1. Chị Thảo đăng nhập tài khoản admin, mở **Dashboard Quản trị**.
2. Đầu trang là **bảng đèn tín hiệu sức khỏe 6 service** (Cổng API, Dịch vụ AI, Nhân viên xử lý file, Kho dữ liệu, Hàng đợi, Kho file). Mỗi service có một chấm tròn xanh/đỏ kèm dòng chữ "Đang chạy" hoặc "Gặp sự cố".
3. Sáng nay cả 6 chấm đều **xanh**. Chị Thảo lướt nhanh 3 con số tổng quan: số người đang online, số file đang chờ xử lý, tỷ lệ trả lời thành công của AI (đều trong ngưỡng bình thường).

### Bước 2 — Phát hiện chìa khóa AI hết hạn mức trong AI Key Vault

1. Chị Thảo kéo xuống khu vực **AI Key Vault** — nơi cất các chìa khóa dùng để gọi dịch vụ AI Gemini. Mỗi chìa khóa được ví như một thẻ điện thoại trả trước: gọi nhiều quá sẽ hết hạn mức (Quota Limit).
2. Chìa khóa số 1 hiện thẻ đỏ **"Hết hạn mức — Lỗi 429"**, kèm ghi chú "đã gọi 1.450/1.500 lượt miễn phí hôm nay". Các chìa khóa số 2 và 3 vẫn xanh.

Ngầm bên dưới, hệ thống đã tự động làm một việc quan trọng trước cả khi chị Thảo mở mắt: khi thấy chìa khóa số 1 báo hết hạn mức, bộ **xoay vòng khóa thông minh** lập tức chuyển toàn bộ yêu cầu AI mới sang chìa khóa số 2. Nhờ đó, học viên đang hỏi bài lúc 7h59 không hề bị gián đoạn — các em chỉ thấy câu trả lời chậm hơn bình thường khoảng 1–2 giây.

### Bước 3 — Gạt tắt khóa hỏng và thêm khóa dự phòng

1. Chị Thảo bấm nút gạt trên chìa khóa số 1 từ **Bật** sang **Tắt** để hệ thống không cố dùng nó nữa.
2. Chị bấm **Thêm chìa khóa**, dán chìa khóa dự phòng mới (được cấp từ tài khoản Google AI Studio), đặt tên "Key dự phòng tháng 9", bấm **Kiểm tra và Lưu**. Hệ thống gọi thử một câu hỏi kiểm tra "xin chào" tới Gemini: nếu trả lời được tức là khóa sống, đèn chuyển xanh.
3. Chị Thảo bấm **Kích hoạt**. Từ giờ hệ thống có 3 chìa khóa khỏe mạnh để xoay vòng. Chiều mai khi hạn mức ngày được reset, chị có thể bật lại chìa khóa số 1.

**Kết quả nhìn thấy:** Toàn bộ thao tác chỉ mất 2 phút trên giao diện, không cần chạm vào máy chủ hay gõ lệnh. Học viên không cảm nhận được sự cố vì lớp dự phòng tự động đã gánh giúp.

### Bước 4 — Xử lý tài khoản bị báo cáo vi phạm

1. Chị Thảo vào mục **Quản lý người dùng**, mở tab **Báo cáo vi phạm**. Có 1 tài khoản bị 3 học viên tố đăng link lừa đảo trong phần bình luận khóa học.
2. Chị bấm vào hồ sơ, xem lịch sử bình luận để xác minh đúng là spam. Sau đó bấm nút **Khóa tài khoản**, chọn lý do "Spam / lừa đảo", chọn thời hạn "Khóa 7 ngày", bấm **Xác nhận**.
3. Ngầm bên dưới, hệ thống thu hồi ngay phiên đăng nhập của tài khoản đó trên mọi thiết bị, chặn không cho đăng nhập lại trong 7 ngày, nhưng **giữ nguyên toàn bộ dữ liệu** (bài học đã mua, điểm số) để nếu kháng cáo thành công thì mở lại không mất gì. Người bị khóa nhận được email nêu rõ lý do và cách gửi khiếu nại.

**Kết quả nhìn thấy:** Cộng đồng học tập được bảo vệ kịp thời, thao tác khóa/mở rõ ràng có biên bản, tránh khóa nhầm gây mất dữ liệu.

**Lịch vận hành gợi ý cho admin mới:**

- Mỗi sáng (2 phút): nhìn bảng đèn 6 service, kiểm tra AI Key Vault.
- Mỗi chiều (5 phút): duyệt báo cáo vi phạm, kiểm tra danh sách file kẹt ở "Đang xử lý".
- Mỗi tuần (15 phút): xem biểu đồ doanh thu và tỷ lệ hoàn thành khóa học, bổ sung khóa dự phòng nếu chìa khóa AI thường xuyên chạm trần.

---

## Tổng kết nhanh: So sánh 4 luồng

| Tiêu chí | Kịch bản 1 (Tải PDF) | Kịch bản 2 (Bán khóa học) | Kịch bản 3 (Gia sư AI) | Kịch bản 4 (Vận hành) |
|---|---|---|---|---|
| Ai bấm nút? | Học viên | Giảng viên + học viên | Học viên | Quản trị viên |
| Chờ lâu nhất ở đâu? | 3–10 phút xử lý file lần đầu | Vài giây xác nhận thanh toán | 5–15 giây AI trả lời | Gần như tức thì |
| AI giúp gì? | Ra đề, chấm bài, chỉ điểm yếu | Tóm tắt bài, ra đề mẫu | Gợi mở Socratic, vẽ sơ đồ, đọc podcast | Xoay khóa dự phòng tự động |
| Dấu hiệu thành công | Nhãn file xanh "Sẵn sàng" | Đơn "Thành công" + mở khóa ngay | Tự sửa được lỗi + có sơ đồ | 6 đèn xanh + khóa mới hoạt động |

*Ghi nhớ một câu cho người non-tech: bạn chỉ cần bấm nút trên màn hình; mọi việc nặng như đọc 100 trang sách, soạn đề thi, thu tiền hay đổi chìa khóa đều đã có đội ngũ tự động phía sau lo.*

---
*Xem thêm: [Mục lục tài liệu](../README.md) | [Cẩm nang học viên](./student-guide.md) | [Cẩm nang giảng viên](./lecturer-guide.md) | [Cẩm nang quản trị viên](./admin-guide.md) | [Giải thích công nghệ bằng ngôn ngữ đơn giản](./tech-and-methods-explained.md) | [Bảng thuật ngữ](./glossary.md)*
