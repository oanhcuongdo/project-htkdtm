# Checklist hồ sơ và bàn giao

Đối chiếu với [README của học phần](https://github.com/oanhcuongdo/project-htkdtm/blob/main/README.md). Việc có thư mục hoặc tài liệu khung không đồng nghĩa đã triển khai xong ứng dụng hoặc hoàn thành mọi yêu cầu nghiệm thu.

## 1. Hồ sơ ở giai đoạn đề cương

- [x] Thư mục nhóm `nhom14-65httt/` và nhánh làm việc cùng tên.
- [x] Đề cương nằm tại `docs/De_cuong_Vi_Viet.docx`.
- [x] Có `danhsachnhom.md` trực tiếp trong thư mục nhóm, theo các mục của mẫu.
- [ ] Bổ sung đầy đủ 3 mã sinh viên hiện mới ghi `23511065`.
- [ ] Xác nhận lớp sinh hoạt từng người, mã lớp học phần, nhóm trưởng, email, phân công và tỷ lệ đóng góp.
- [x] Có README của nhóm và tài liệu nguồn dữ liệu, kế hoạch thực hiện.
- [x] Có vị trí `src/backend/`, `src/frontend/`, `src/database/` với README định hướng.

## 2. Nội dung đề cương TH4 cần nhóm rà soát

- [ ] Mục 1 xác định vấn đề, đối tượng, phạm vi, mục tiêu và câu hỏi nghiên cứu.
- [ ] Mục 2 có nguyên nhân, hậu quả, yếu tố ảnh hưởng và cách kiểm chứng.
- [ ] Mục 3 đánh giá các giải pháp, ưu điểm, hạn chế và cơ sở lựa chọn.
- [ ] Mục 4–6 nêu giải pháp, nghiệp vụ, dữ liệu, cơ chế AI và BI với luận cứ phù hợp.
- [ ] Mục 7–8 có cách đo, ngưỡng mục tiêu, mốc thời gian và sản phẩm bàn giao.

Các ô trên để nhóm xác nhận sau khi duyệt bản Word; không phải kết luận rằng nội dung tương ứng đang thiếu.

## 3. Các mục hoàn thiện khi có mã nguồn

- [ ] Backend/frontend và cơ sở dữ liệu chạy được theo hướng dẫn.
- [ ] Ghi phiên bản runtime, gói phụ thuộc, tệp cấu hình mẫu không chứa bí mật và lệnh khởi chạy đã kiểm tra.
- [ ] Có migration, dữ liệu mẫu hợp lệ và mô tả nguồn dữ liệu.
- [ ] Có mô hình gợi ý, đối chứng và kết quả đánh giá thực tế.
- [ ] Có ghi sự kiện, dashboard BI và kết quả đối soát.
- [ ] Có báo cáo kiểm thử, hạn chế, hướng dẫn cài đặt và demo.

## 4. Kiểm tra thay đổi trước commit và PR

- [ ] Thay đổi chỉ nằm trong `nhom14-65httt/`; không sửa README, `.gitignore`, mẫu của kho hoặc thư mục nhóm khác.
- [ ] Không đưa `.env`, khóa API, thư viện cài đặt, tệp biên dịch hoặc tệp nén lớn vào commit.
- [ ] Kiểm tra `git status` và phần thay đổi đã stage; chỉ dùng `git add nhom14-65httt/`.
- [ ] Push lên `origin/nhom14-65httt`.
- [ ] Khi nộp PR, kiểm tra base là `oanhcuongdo/project-htkdtm:main`, head là `DucEvil/project-htkdtm:nhom14-65httt` và mọi đường dẫn thay đổi thuộc thư mục nhóm.
- [ ] Chờ giảng viên kiểm duyệt theo quy định; nhóm không tự bỏ qua yêu cầu review để gộp vào nhánh chung.

