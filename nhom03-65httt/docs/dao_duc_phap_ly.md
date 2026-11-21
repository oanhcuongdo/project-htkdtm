# Ghi chú đạo đức và giới hạn pháp lý của việc thu thập dữ liệu

Đồ án EduVision BI (Nhóm 03, lớp 65HTTT) chỉ phục vụ **học tập và nghiên cứu**, không dùng cho mục đích thương mại.
Tài liệu này ghi lại những gì nhóm đã làm để thu thập dữ liệu có trách nhiệm, và những giới hạn nhóm cần nêu trung thực.
Đây là ghi chú của sinh viên, **không phải tư vấn pháp lý**. Điều khoản của các nền tảng thay đổi theo thời gian,
nên trước khi nộp bài và trước khi công bố bất cứ thứ gì, nhóm cần đối chiếu lại bản điều khoản hiện hành.

## 1. Nguyên tắc chung đã áp dụng

- Chỉ lấy dữ liệu **công khai**, không cần đăng nhập. Không thu thập từ Facebook, TikTok, nhóm kín hay nội dung cần đăng nhập.
- Giãn cách giữa các lần gọi (tối thiểu 2 giây), có thử lại với độ trễ tăng dần khi gặp lỗi 429/5xx.
- **Không vượt cơ chế chống bot.** Khi một nguồn chặn (ví dụ Google News từng trả "Sorry... automated queries" và mã 503), nhóm **dừng lại**, không đổi IP, không dùng proxy, không giả trình duyệt, và chờ rồi chạy lại với số yêu cầu ít hơn.
- Không lưu tên người dùng, ảnh đại diện, đường dẫn trang cá nhân hay thông tin liên hệ. Chỉ lưu `author_hash` (SHA-256 của tên hiển thị, cắt 12 ký tự).
- Khóa API chỉ nằm trong biến môi trường hoặc file `.env` (đã được `.gitignore` chặn), không ghi vào mã, log hay tài liệu.
- Mỗi nguồn có đánh giá khả thi và phương án dự phòng (nhập CSV/Excel); nếu nguồn không đủ thì ghi nhận là hạn chế, không cố vượt.

## 2. Từng nguồn dữ liệu

| Nguồn | Cách lấy | Điều cần lưu ý | Việc nhóm cần làm |
|---|---|---|---|
| **Google Play** | Thư viện `google-play-scraper` đọc trang công khai của cửa hàng (không phải API chính thức) | Google không cung cấp API công khai để đọc đánh giá của ứng dụng người khác. Điều khoản dịch vụ của Google hạn chế truy cập tự động ngoài các giao diện được cung cấp. Đây là vùng rủi ro cao nhất về điều khoản. | Giữ lượng thu thập thấp, chỉ một lần cho mỗi đợt; đọc lại điều khoản trước khi nộp; ghi rõ trong báo cáo đây là thu thập từ trang công khai bằng thư viện bên thứ ba. |
| **App Store** | Nguồn cấp RSS đánh giá khách hàng công khai của Apple (`itunes.apple.com/.../customerreviews`) và iTunes Lookup/Search API | Nguồn cấp này công khai nhưng chỉ trả tối đa khoảng 500 đánh giá gần nhất cho mỗi nền tảng, nên dữ liệu là một mẫu, không đầy đủ. | Ghi rõ giới hạn mẫu; không dùng cho kết luận về toàn bộ người dùng. |
| **YouTube** | YouTube Data API v3 với khóa API của nhóm | Chịu **YouTube API Services Terms of Service** và **Developer Policies**; có hạn mức quota (mặc định 10.000 đơn vị/ngày). Chính sách có quy định về lưu trữ và làm mới dữ liệu lấy từ API; nhóm chưa đối chiếu chi tiết bản hiện hành. | Đối chiếu Developer Policies hiện hành về thời hạn lưu trữ và xóa dữ liệu trước khi nộp; không công bố bình luận gốc; không dùng quá hạn mức. |
| **Tin báo chí** | Google News RSS và RSS chuyên mục giáo dục của các báo | Chỉ lưu tiêu đề, tên báo, đường dẫn, ngày đăng; **không lưu toàn văn** để tránh vi phạm bản quyền. Google News có cơ chế chặn truy vấn tự động. | Giữ cửa sổ thời gian rộng, ít yêu cầu; chỉ trích dẫn tiêu đề kèm nguồn. |
| **Google Trends** | Thư viện `pytrends` (không chính thức) | Không phải API chính thức, dễ bị giới hạn (429). Dữ liệu là mẫu và được chuẩn hóa 0-100 cho từng từ khóa. | Chạy ít lần, chốt một lần chạy cho mô hình; ghi rõ cách chuẩn hóa. |
| **UIT-VSFC** | Bộ dữ liệu công khai trên Hugging Face (`uitnlp/vietnamese_students_feedback`) | Có giấy phép và điều kiện sử dụng riêng do nhóm tác giả đặt ra; phải trích dẫn nguồn. | Đọc thẻ bộ dữ liệu (dataset card) để xác nhận giấy phép; trích dẫn trong báo cáo; chỉ dùng để huấn luyện, không trộn vào số liệu phân tích. |

## 3. Quyền riêng tư và dữ liệu cá nhân

- Nội dung đánh giá và bình luận là văn bản tự do do người dùng viết; **có thể chứa thông tin cá nhân** (số điện thoại, tên, email) hoặc quảng cáo. Nhóm đã gặp bình luận chứa số điện thoại.
- `author_hash` chỉ là **giả danh hóa (pseudonymization)**, không phải ẩn danh tuyệt đối: người có danh sách tên có thể băm lại để đối chiếu.
- Việc cần làm: lọc hoặc che số điện thoại/email trong bước làm sạch; không công bố bình luận gốc kèm `author_hash`; trong báo cáo và slide chỉ dùng số liệu tổng hợp và vài trích dẫn ngắn, đã che thông tin nhạy cảm.
- Nếu gửi văn bản đánh giá cho dịch vụ LLM bên ngoài để gán nhãn thì nội dung đó rời khỏi máy nhóm; chỉ gửi văn bản công khai, đã bỏ thông tin cá nhân, và ghi rõ trong báo cáo.

## 4. Quy tắc với repo công khai

- **Không commit dữ liệu thô hay đã làm sạch** (CSV các loại) và **không commit trọng số mô hình**; đã có `.gitignore` của nhóm chặn `data/`, `*.csv` và các đuôi trọng số. Chia sẻ qua kênh riêng của nhóm.
- Không commit khóa API, `.env`, token. Chỉ commit `.env.example` với giá trị rỗng.
- Chỉ đưa lên repo: mã nguồn, cấu hình, lược đồ cơ sở dữ liệu, tài liệu, và dữ liệu mẫu nhỏ tự tạo (không phải đánh giá thật).
- Nếu từng lỡ commit dữ liệu hay khóa thì **xóa khỏi lịch sử Git** (không chỉ xóa file) và tạo lại khóa.

## 5. Giới hạn cần nêu trong báo cáo

- Dữ liệu là **mẫu**, không đại diện toàn bộ người dùng: kho ứng dụng giới hạn số đánh giá gần nhất; YouTube và báo chí lệch về vài nền tảng; Monkey Junior không có dữ liệu YouTube.
- Bình luận YouTube chứa nhiều nội dung lạc đề; tin báo chí có thể là bài quảng cáo trả tiền.
- Hệ thống chỉ phục vụ học tập; kết quả mô hình không phải căn cứ ra quyết định thật.
