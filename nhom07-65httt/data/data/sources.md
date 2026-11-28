# Danh mục nguồn dữ liệu

## Udemy

- Trang chính: <https://www.udemy.com/>
- Quy tắc robots: <https://www.udemy.com/robots.txt>
- Điều khoản sử dụng: <https://www.udemy.com/terms/terms-of-use/>
- Sitemap được khai báo trong robots: <https://www.udemy.com/sitemap.xml>
- Dữ liệu hiện có: `data/udemy_courses.csv`, gồm 3.001 bản ghi được thu thập ngày 18/11/2026.
- Các trường có trong CSV: tiêu đề, URL/slug khóa học, điểm đánh giá, số lượt đánh giá, thời lượng, số bài giảng/chương, URL ảnh và thời điểm thu thập.
- Trạng thái: **tạm dừng thu thập tự động cho đến khi có văn bản cho phép**. Nội dung Điều khoản sử dụng Udemy được lập chỉ mục hiện nêu rằng không cho phép scraping hoặc truy cập tự động. Robots có khai báo sitemap và cho phép một số mẫu URL, nhưng điều đó không thay thế sự cho phép trong điều khoản. Chưa có thông tin API hoặc văn bản chấp thuận.
- Cách nhập CSV hiện có: nhập dữ liệu cũ ngoại tuyến; pipeline này không tải trang Udemy.
- Hạn chế: không lưu HTML/JSON gốc; giá, giảng viên, danh mục, ngôn ngữ, cấp độ, mô tả và kỹ năng thiếu ở toàn bộ hoặc gần như toàn bộ bản ghi.

## khoahocre.com

- Trang chính: <https://khoahocre.com/>
- Trạng thái: **chưa đánh giá, không sử dụng**. Chưa xác minh được robots hiện tại và chưa có điều khoản hoặc văn bản cho phép; nguồn này không được crawl hay đưa vào dataset.

## Nguồn bổ sung

Chưa thêm nguồn nào khác. Trước khi tích hợp, cần rà soát robots, điều khoản và phương thức lấy metadata được cho phép.

## Tài liệu tham khảo vận hành

- Robots của Udemy hiện khai báo sitemap, chặn phần lớn URL có query và cho phép một số đường dẫn. Đây chỉ là hướng dẫn URL, không phải giấy phép crawl.
- Nội dung Điều khoản Udemy được lập chỉ mục nêu hạn chế scraping/spidering tự động. Cần kiểm tra lại điều khoản chính thức và có văn bản cho phép hoặc API được phê duyệt trước khi bật thu thập.
- Thời điểm kiểm tra và trạng thái nguồn được ghi trong manifest/báo cáo của mỗi lần chạy pipeline.
