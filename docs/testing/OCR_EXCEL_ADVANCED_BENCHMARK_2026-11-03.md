# Báo cáo benchmark nâng cao OCR và Excel

Ngày chạy: 03/11/2026  
Phạm vi: adapter trích xuất và pipeline chuẩn hóa hiện tại  
Dữ liệu: đơn thuốc giả, không chứa dữ liệu bệnh nhân thật

## Cách chấm

Benchmark đối chiếu giá trị sau khi chạy qua adapter và các bước chuẩn hóa hiện
tại với bộ giá trị chuẩn. Mỗi trường có trọng số bằng nhau và chỉ được tính đúng
khi khớp chính xác (chuỗi không phân biệt hoa thường và khoảng trắng thừa).

Các tình huống khó gồm:

- đơn bốn thuốc với viên nén, thuốc xịt, thuốc nhỏ mắt, liều `0.5`, nhiều giờ uống,
  số lượng và nhiều đường dùng;
- văn bản OCR nhiễu với lỗi `0/O`, mất dấu và số thứ tự La Mã;
- tài liệu bị cắt mất danh sách thuốc để kiểm tra nguy cơ tự sinh dữ liệu;
- XLSX 26 cột, cột bị đảo thứ tự, tên cột khác kiểu chữ, ô trống xen kẽ;
- CSV có BOM, dấu phẩy nằm trong dữ liệu và chuỗi được đặt trong dấu nháy;
- ngày Excel lưu dưới dạng số serial;
- hàng tiêu đề lặp lại giữa dữ liệu, CSV dùng dấu chấm phẩy, thiếu cột bắt buộc
  và tệp XLSX hỏng.

Chạy lại bằng lệnh:

```powershell
.\.venv\Scripts\python.exe -m backend.tests.advanced_import_extraction_benchmark
```

## Kết quả

| Nhóm | Trường đúng | Tổng trường | Độ chính xác exact-match |
|---|---:|---:|---:|
| Văn bản OCR đã đọc được | 45 | 49 | 91,84% |
| Excel/CSV | 52 | 56 | 92,86% |
| Tổng hợp | 97 | 105 | 92,38% |

| Tình huống | Kết quả |
|---|---:|
| OCR văn bản phức tạp | 100,00% |
| OCR nhiễu, số thứ tự La Mã | 50,00% |
| OCR tài liệu bị cắt, kiểm tra không bịa thuốc | 100,00% |
| XLSX phức tạp đúng template | 100,00% |
| XLSX đảo thứ tự và ô thưa | 100,00% |
| CSV BOM và dấu phẩy trong dữ liệu | 100,00% |
| Ngày Excel dạng serial | 40,00% |
| Tiêu đề lặp giữa dữ liệu | 0,00% |

Engine Tesseract đã được kết nối và kiểm tra bằng ảnh PNG tiếng Việt cùng PDF quét
được tạo raster. Cả hai đi qua pipeline ảnh/PDF thật, không dùng JSON passthrough.
Ảnh không có đủ văn bản được từ chối an toàn.

## Hạn chế phát hiện

### P0 — đã xử lý

1. Ảnh PNG/JPEG/TIFF và PDF quét được OCR cục bộ bằng Tesseract; PDF có lớp chữ
   được đọc trực tiếp trước để tránh OCR lại không cần thiết.
2. Đã xóa hành vi tự sinh `Paracetamol 500mg`. Khi không tìm thấy thuốc, danh sách
   để trống và validation chặn việc lưu.
3. Liều, đơn vị và đường dùng không xác định không còn mặc định thành `1 viên uống`.
4. Người dùng phải đánh dấu đã đối chiếu tên thuốc, hàm lượng, liều, đường dùng và
   tần suất với đơn gốc trước khi API chấp nhận commit.

### P1 — còn cần dữ liệu thực tế để hiệu chỉnh

1. Văn bản bị mất dấu không được tự thêm lại dấu tiếng Việt vì làm vậy có thể đổi
   tên người hoặc tên thuốc. Người dùng phải đối chiếu và sửa trên màn hình review.
2. Lỗi ký tự trong tên thuốc như `Metf0rmin` chưa được tự đổi thành `Metformin`;
   đây là lựa chọn an toàn cho đến khi có đối chiếu danh mục thuốc đáng tin cậy.
3. Chữ viết tay, ảnh nghiêng mạnh, lóa, nền phức tạp, bảng nhiều cột và con dấu đè
   chữ chưa được đánh giá trên tập dữ liệu thực tế.
4. Confidence Tesseract là độ tin cậy nhận dạng ký tự, không phải xác suất thông
   tin y khoa chính xác; review của người dùng vẫn là bắt buộc.

### P2 — độ bền của Excel/CSV

1. Ngày lưu đúng kiểu Date của Excel được trả về dưới dạng số serial và sau chuẩn
   hóa trở thành `null`.
2. Hàng tiêu đề lặp trong nội dung bị coi là một thuốc mới, tạo ra bản ghi rác.
3. CSV dùng dấu chấm phẩy theo thiết lập vùng bị từ chối.
4. Mọi dòng Excel được gán confidence `1.0`, kể cả giá trị hợp lệ về cú pháp nhưng
   bất thường về nghiệp vụ; confidence hiện không phản ánh chất lượng dữ liệu.
5. Metadata đơn thuốc lấy từ dòng dữ liệu đầu tiên; benchmark chưa thấy cơ chế báo
   lỗi nếu các dòng sau thuộc bệnh nhân hoặc đơn thuốc khác.

## Điểm đang hoạt động tốt

- XLSX đúng template giữ chính xác tiếng Việt, số thập phân, thuốc nhiều dạng và
  lịch dùng thuốc.
- Đảo thứ tự cột, viết hoa tên cột và ô trống xen kẽ không làm lệch dữ liệu.
- CSV UTF-8 BOM và dữ liệu có dấu phẩy được đọc đúng khi dùng quy tắc CSV chuẩn.
- Tệp thiếu cột bắt buộc và XLSX hỏng được từ chối đúng.
- Ảnh và PDF quét được OCR cục bộ, không gửi dữ liệu sức khỏe sang dịch vụ bên thứ ba.
- Ảnh không đọc được bị từ chối và tài liệu bị cắt không tạo thuốc giả.
- Parser đọc đúng ca benchmark phức tạp gồm liều `0.5`, thuốc xịt, thuốc nhỏ mắt,
  số lượng, ngày điều trị và lịch nhiều giờ.

## Ngưỡng đề xuất trước pilot

- benchmark trên tập đơn thuốc thật đã khử định danh ở nhiều mức nhiễu;
- đạt tối thiểu 95% cho tên thuốc, hàm lượng, liều, đơn vị, đường dùng và tần suất
  trên tập kiểm thử đại diện trước pilot;
- các trường nguy cơ cao không chắc chắn phải để trống và bắt buộc người dùng xác
  nhận, không dùng giá trị mặc định;
- Excel phải xử lý ngày serial và bỏ qua hoặc báo lỗi hàng tiêu đề lặp;
- chạy thêm kiểm tra precision/recall ở cấp dòng thuốc sau khi có OCR engine.

Điểm số này là chỉ báo kỹ thuật trên bộ dữ liệu giả nhỏ. Nó không chứng minh độ an
toàn lâm sàng và không nên được dùng làm căn cứ tự động kê đơn hoặc thay đổi lịch
dùng thuốc.
