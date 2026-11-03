# OCR đơn thuốc ảnh và PDF

PharmaMind chạy OCR cục bộ bằng Tesseract 5 với mô hình tiếng Việt và tiếng Anh.
Ảnh đơn thuốc không được gửi đến dịch vụ OCR bên thứ ba. PDF có lớp chữ được đọc
trực tiếp; trang PDF quét được kết xuất ở 300 DPI rồi OCR.

Pipeline hỗ trợ PNG, JPEG, TIFF và PDF. Giới hạn upload vẫn là 10 MB cho ảnh và
20 MB cho PDF. PDF mặc định tối đa 10 trang, mỗi trang có timeout 45 giây và ảnh
được giới hạn 30 triệu pixel.

## Docker và hosting

Dockerfile của dự án đã cài:

- `tesseract-ocr`, `tesseract-ocr-vie`, `tesseract-ocr-eng`;
- `poppler-utils` để kết xuất PDF quét;
- Pillow, pytesseract, pypdf và pdf2image.

Sau khi deploy image mới, giữ các biến mặc định sau hoặc đặt rõ trong secrets của
dịch vụ:

```dotenv
OCR_ENABLED=true
OCR_LANGUAGES=vie+eng
OCR_TIMEOUT_SECONDS=45
OCR_PDF_MAX_PAGES=10
OCR_RENDER_DPI=300
OCR_MAX_IMAGE_PIXELS=30000000
```

`OCR_TESSERACT_CMD`, `OCR_TESSDATA_DIR` và `OCR_POPPLER_PATH` thường để trống
trong Linux/Docker vì các binary và language data nằm trên PATH hệ thống.

## Chạy local trên Windows

1. Cài Tesseract 5 và bảo đảm có `vie.traineddata` cùng `eng.traineddata`.
2. Cài Poppler nếu cần xử lý PDF quét.
3. Nếu các chương trình chưa nằm trên PATH, đặt đường dẫn tuyệt đối trong `.env`:

```dotenv
OCR_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_TESSDATA_DIR=C:\ocr-data\tessdata
OCR_POPPLER_PATH=C:\poppler\Library\bin
```

Thư mục `OCR_TESSDATA_DIR` không được chứa khoảng trắng vì cách Tesseract nhận
tham số trên Windows. Các tệp language data dùng cho local test có thể đặt trong
`.tessdata/`; thư mục này đã được gitignore.

## Luồng an toàn dữ liệu

1. Hệ thống kiểm tra kích thước và định dạng trước khi OCR.
2. Tesseract trả về văn bản và confidence theo từng từ; pipeline tính confidence
   tổng hợp và theo trường.
3. Parser chỉ điền trường có bằng chứng trong văn bản. Nó không mặc định thuốc,
   liều, đơn vị hay đường dùng khi không đọc được.
4. Validation chặn danh sách thuốc rỗng, liều/đơn vị/tần suất/đường dùng còn thiếu.
5. Giao diện bắt buộc người dùng xác nhận đã đối chiếu các trường quan trọng với
   đơn gốc trước khi commit. API cũng kiểm tra xác nhận này.
6. Tệp nguồn chỉ được lưu vào local volume hoặc object storage sau khi parse thành
   công; tệp lỗi không tạo object mồ côi.

OCR không thay thế việc đọc đơn gốc. Confidence nhận dạng cao không bảo đảm thông
tin y khoa đúng. Không tự sửa lỗi tên thuốc kiểu `Metf0rmin → Metformin`; người
dùng phải xác nhận trên màn hình review.

## Hướng dẫn chụp

- đặt toàn bộ đơn thuốc trong khung hình, không cắt mất danh sách thuốc;
- chụp thẳng, đủ sáng, tránh bóng và phản chiếu;
- giữ chữ lớn, nét; ưu tiên ảnh gốc thay vì ảnh gửi lại nhiều lần;
- với PDF, ưu tiên bản xuất trực tiếp từ bệnh viện có lớp chữ;
- đơn viết tay cần nhập và kiểm tra thủ công vì chưa có bảo đảm chất lượng.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_ocr_real_pipeline.py -q
.\.venv\Scripts\python.exe -m backend.tests.advanced_import_extraction_benchmark
```

Bộ test hiện bao gồm ảnh PNG tiếng Việt, PDF quét, bốn loại thuốc/đường dùng,
liều thập phân, nhiều mốc giờ, văn bản nhiễu và tài liệu bị cắt. Kết quả benchmark
được ghi tại [báo cáo OCR/Excel nâng cao](../testing/OCR_EXCEL_ADVANCED_BENCHMARK_2026-11-03.md).

Trước pilot, cần bổ sung một tập đơn thuốc thật đã khử định danh và đo riêng
precision/recall cho tên thuốc, hàm lượng, liều, đơn vị, đường dùng và tần suất.

Tham khảo: [Tesseract quality guidance](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html),
[pytesseract usage](https://github.com/madmaze/pytesseract/blob/master/README.rst).
