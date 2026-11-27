# Nguồn dữ liệu và kế hoạch chuẩn bị

> **Người phụ trách:** Nguyễn Mạnh Đức (2351106511) – Nhóm 14, 65HTTT  
> **Dự án:** Vị Việt – Website đặt món trực tuyến tích hợp trí tuệ nhân tạo gợi ý ẩm thực Việt Nam  
> **Học phần:** Hệ thống kinh doanh thông minh (TS. Đỗ Oanh Cường)

Tài liệu này ghi nguồn đã chọn và công việc chuẩn bị dữ liệu cho Vị Việt. Chưa có bản dữ liệu đã làm sạch hoặc kết quả đánh giá mô hình trong thư mục nhóm.

---

## 1. Nguồn chính ViFoodRec

- **Repository:** [A New Dataset and Empirical Evaluation for Vietnamese Food Recommendation System](https://github.com/QuocAn55/A-New-Dataset-and-Empirical-Evaluation-for-Vietnamese-Food-Recommendation-System).
- **Bài báo:** [ACL Anthology](https://aclanthology.org/2024.paclic-1.4/).
- **Phiên bản nguồn đã đối chiếu cấu trúc:** commit `126caa3a8b58708a09b2b2e119ff4923b6f06d82`, ngày 11/11/2026.

Các đường dẫn dưới đây được đối chiếu từ cây tệp của repository nguồn, chưa phải dữ liệu đã nhập vào Vị Việt:

| Tệp trong nguồn | Vai trò dự kiến |
| :--- | :--- |
| `Data/Clean Dataset/foods.csv` | Đầu vào chính để kiểm tra đặc trưng và tuyển chọn món |
| `Data/Clean Dataset/ratings.csv` | Tham khảo thử nghiệm gợi ý; cần kiểm tra cách xử lý/điền thiếu trước khi dùng làm nhãn đánh giá |
| `Data/Raw Dataset/food_dataset_cookyweb.csv` | Đối chiếu dữ liệu món gốc khi cần |
| `Data/Raw Dataset/food_dataset_mnmnweb.csv` | Đối chiếu dữ liệu món gốc khi cần |

Ưu tiên dùng đặc trưng món kết hợp khẩu vị tự khai báo. Không tự coi mọi đánh giá trong tệp đã xử lý là phản hồi người thật độc lập; không dùng đánh giá đã suy diễn làm nhãn kiểm tra mà chưa xác định nguồn gốc. Người dùng trong dataset không phải tài khoản hoặc lịch sử đặt món của khách trên website.

Khi tải và xử lý, ghi ngày tải, commit nguồn, tên tệp, số bản ghi trước/sau làm sạch, hàm băm tệp và phép biến đổi. Kiểm tra điều kiện sử dụng và khả năng tái phân phối trước khi chép dữ liệu hoặc ảnh nguồn vào repository; hiện tài liệu này chỉ lưu liên kết tham chiếu.

---

## 2. Nguồn bổ sung khi cần

[vietnamese_recipe_dataset của PTIT-KLTN](https://github.com/PTIT-KLTN/vietnamese_recipe_dataset) chỉ được xem xét nếu ViFoodRec chưa đủ thông tin cho một chức năng cụ thể, ví dụ chuẩn hóa nguyên liệu hoặc hướng dẫn tự nấu ở giai đoạn mở rộng.

Không hợp nhất hai nguồn ngay từ đầu. Khi bổ sung, lập bảng ánh xạ theo tên, nguyên liệu và cách chế biến; giữ mã gốc của mỗi nguồn, kiểm tra thủ công các trường hợp nghi trùng. Không nối dữ liệu chỉ vì tên món giống nhau.

---

## 3. Nguồn nghiệp vụ của Vị Việt

| Nhóm dữ liệu | Nguồn và giới hạn |
| :--- | :--- |
| Hồ sơ quán, tọa độ, giờ mở và phạm vi phục vụ | Quán tham gia cung cấp hoặc dữ liệu được phép sử dụng; tọa độ cần xác minh |
| Thực đơn, nguyên liệu, giá và trạng thái món | Quán xác nhận cho từng món thực bán; không sao chép nguyên liệu từ công thức chuẩn rồi coi là thành phần thực tế |
| Khẩu vị và tương tác | Người thử đồng ý tham gia; ghi riêng sự kiện hiển thị, nhấp, lưu, đặt và phản hồi |
| Đơn kiểm thử | Dữ liệu mô phỏng có đánh dấu, chỉ kiểm tra nghiệp vụ và đối soát BI |
| Vị trí người dùng | Người dùng chủ động cấp quyền hoặc nhập địa chỉ; không công khai địa chỉ chi tiết trên dashboard |

Google Maps hỗ trợ vị trí, hiển thị quán và chỉ đường. Nếu bổ sung tìm địa điểm qua Places API, một quán được tìm thấy chưa trở thành quán nhận đơn trên Vị Việt. Không mặc định dữ liệu bản đồ có thực đơn và nguyên liệu đầy đủ.

---

## 4. Quy trình làm sạch dự kiến

1. Tải bản nguồn cố định và lập bản ghi nguồn; giữ nguyên bản gốc để đối chiếu.
2. Kiểm tra cấu trúc cột, mã định danh, kiểu dữ liệu, dữ liệu thiếu và ký tự tiếng Việt; lập từ điển dữ liệu theo tệp thực tế.
3. Tuyển chọn ban đầu khoảng 100 món thuộc phạm vi ẩm thực Việt Nam; đây là mục tiêu của nhóm, không phải số bản ghi của toàn bộ dataset.
4. Chuẩn hóa tên và đơn vị khi có đủ căn cứ; đối chiếu trùng bằng nhiều đặc trưng, giữ các biến thể món khi có khác biệt đáng kể.
5. Chuẩn hóa nguyên liệu và bổ sung nhãn vùng miền (`region`), mức cay (`spiciness_level`), cách chế biến khi kiểm tra được; trường chưa rõ để thiếu, không gán nhãn đoán.
6. Tách `CanonicalDish` là món chuẩn khỏi `MenuItem` là món thực bán tại một quán; ánh xạ món thực đơn về món chuẩn để dùng đặc trưng chung.
7. Kiểm tra khả dụng, tọa độ và nguyên liệu tại quán. Khi khách loại trừ nguyên liệu mà dữ liệu thành phần chưa rõ, loại ứng viên theo điều kiện đó.
8. Lưu báo cáo chất lượng: số đầu vào/đầu ra, bản ghi trùng/thiếu/loại, lý do và nguồn nhãn bổ sung.
9. Tách dữ liệu phát triển khỏi tập đánh giá; không dùng phản hồi tương lai để tạo hồ sơ hoặc chọn tham số trước đánh giá.

---

## 5. Mục tiêu quy mô theo đề cương & Cờ mô phỏng (`is_simulated`)

| Hạng mục | Mục tiêu dự kiến | Mục đích |
| :--- | :--- | :--- |
| Món chuẩn (`CanonicalDish`) | Khoảng 100 | Làm sạch và thử gợi ý theo nội dung (nguồn ViFoodRec) |
| Hồ sơ quán (`Restaurant`) | 20 | Thử luồng quản lý quán và phạm vi phục vụ (`is_simulated = true`) |
| Mục thực đơn (`MenuItem`) | 200 | Ánh xạ món chuẩn và kiểm tra khả dụng (`is_simulated = true`) |
| Người dùng thử (`User`) | 30 | Đánh giá khẩu vị và trải nghiệm thực tế |
| Đơn kiểm thử (`Order`) | 100 | Kiểm thử nghiệp vụ và đối soát BI (`is_simulated = true`) |

> [!IMPORTANT]
> **Quy định cờ mô phỏng:** Mọi bản ghi quán ăn, thực đơn, đơn hàng tạo ra bằng seed script bắt buộc phải đánh dấu `is_simulated = TRUE` để đảm bảo tính minh bạch học thuật, tuyệt đối không bịa đặt đối tác thương mại hoặc doanh thu thực tế.

---

## 6. Cấu trúc thư mục lưu trữ dữ liệu (`src/database/`)

```
src/database/
├── seed/
│   ├── README.md                 # Hướng dẫn nạp và định dạng dữ liệu seed
│   ├── canonical_dishes.json     # 100 món chuẩn đã làm sạch và gán nhãn
│   ├── ingredients.json          # Từ điển nguyên liệu và dị nguyên
│   ├── regions_and_labels.json   # Danh mục nhãn vùng miền, mức cay
│   ├── sample_restaurants.json   # 20 quán ăn thử nghiệm (is_simulated = true)
│   ├── sample_menu_items.json    # 200 món bán tại các quán
│   ├── sample_users.json         # Danh sách tài khoản thử nghiệm
│   └── sample_orders.json        # 100 đơn hàng mẫu phục vụ test ETL/BI
└── vifoodrec/
    ├── README.md                 # Quy trình trích xuất từ ViFoodRec
    └── mapping.json              # Bảng ánh xạ ID ViFoodRec sang CanonicalDish ID
```
