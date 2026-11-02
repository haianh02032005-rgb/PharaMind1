# PharmaMind AI — readiness trước khi đưa lên app

## Đã rà soát và xử lý

- Backend FastAPI, frontend React/Vite, PostgreSQL, import đơn thuốc và Digital Twin hiện có.
- CORS đã chuyển từ wildcard sang `CORS_ORIGINS`; production (`DEBUG=false`) từ chối JWT secret yếu và wildcard origin.
- Upload đơn thuốc được giới hạn kích thước khi đọc request, tránh nạp file không giới hạn vào RAM.
- Frontend tải màn hình theo route để trì hoãn phần Digital Twin nặng.
- Trang AI không còn sinh câu trả lời dược lý hard-code. Trang nêu rõ dịch vụ AI chưa sẵn sàng.
- Bộ phân tích OCR không còn biến ảnh/PDF không đọc được thành đơn thuốc Paracetamol/Vitamin C bịa; trường hợp này báo rõ OCR ảnh/PDF chưa kết nối.
- `storage/imports/` chứa tài liệu đơn thuốc đã tải lên, vì vậy được loại khỏi Git. Không xóa dữ liệu hiện có.
- Flutter MVP source nằm trong `mobile/`; chưa có thư mục native Android/iOS do môi trường phát triển chưa cài Flutter SDK.

## Kết quả kiểm tra hiện có

- Backend: `python -m pytest -q` — 73 tests.
- Frontend: `npm run test` — 31 tests.
- Frontend production build: `npm run build`.
- Production config guard: JWT secret yếu bị từ chối khi `DEBUG=false`.

Frontend build hiện có entry chính khoảng 188 KB minified; Digital Twin 3D được tách thành chunk riêng khoảng 653 KB. Build thành công nhưng Vite vẫn cảnh báo chunk 3D lớn.

## Còn chặn phát hành app

1. Cài Flutter SDK và tạo Android/iOS project; build trên Android. iOS build/signing cần macOS + Xcode.
2. Chọn API domain staging/production, HTTPS, `API_BASE_URL` cho app và origins chính xác cho web. Không đưa JWT secret hoặc API keys vào mobile binary.
3. OCR ảnh/PDF thực chưa được kết nối; hiện chỉ xử lý văn bản đọc được/fixture. Cần tích hợp OCR provider và đánh giá chất lượng tiếng Việt.
4. Dịch vụ AI và notification routers còn placeholder. Chỉ bật các tính năng đó sau khi có backend, kiểm tra an toàn và cấu hình nhà cung cấp.
5. Cấu hình lưu file upload bền vững, riêng tư và có backup; thư mục `storage/imports/` hiện là lưu cục bộ.
6. Chốt chính sách phát hành: package/bundle ID, app signing, privacy policy và nội dung xin quyền thiết bị.

## Thứ tự công việc cho task app tiếp theo

1. Tạo platform scaffolds, chạy Flutter app trên emulator/device và kết nối API staging.
2. Hoàn thiện auth/session, gia đình, hồ sơ sức khỏe, thuốc, đơn thuốc/import, lịch và tủ thuốc theo API hiện có.
3. Thêm realtime, offline behavior, notification và AI sau khi backend tương ứng sẵn sàng.
4. Rà soát dữ liệu nhạy cảm, quyền thành viên, accessibility, build/signing và phát hành nội bộ.

App mobile phải dùng backend làm nguồn dữ liệu chuẩn và lưu refresh token trong Keychain/Keystore. API URL phải là HTTPS ngoài môi trường phát triển.
