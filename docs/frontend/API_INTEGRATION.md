# PharmaMind AI — API & Realtime Integration Guide

## 1. Cấu hình Base URL
- **REST API**: `VITE_API_BASE_URL` (mặc định `http://localhost:8000`)
- **WebSocket**: `VITE_WS_BASE_URL` (mặc định `ws://localhost:8000`)

## 2. Xác thực (Authentication)
- `POST /auth/register`: Đăng ký tài khoản
- `POST /auth/login`: Nhận `access_token` và `refresh_token`
- `POST /auth/refresh`: Làm mới token tự động khi nhận `401 Unauthorized`
- `GET /users/me`: Lấy thông tin người dùng hiện tại

## 3. Gia đình & Thành viên (Family & Members)
- `GET /families`, `POST /families`: Danh sách & tạo gia đình
- `GET /families/{family_id}/members`, `POST /families/{family_id}/members`: Danh sách & thêm thành viên
- `GET /families/{family_id}/members/{member_id}/health-profile`: Hồ sơ sức khỏe tổng hợp
- `GET/POST /families/{family_id}/members/{member_id}/conditions`: Bệnh nền
- `GET/POST /families/{family_id}/members/{member_id}/allergies`: Dị ứng
- `GET/POST /families/{family_id}/members/{member_id}/drug-reactions`: Tiền sử phản ứng thuốc
- `GET/POST /families/{family_id}/members/{member_id}/emergency-contacts`: Liên hệ khẩn cấp

## 4. Thuốc, Đơn thuốc & Lịch uống (Medications, Prescriptions, Schedules)
- `GET/POST /families/{family_id}/medications`: Kho thuốc gia đình
- `POST /families/{family_id}/medications/{medication_id}/members`: Gán thuốc cho thành viên
- `GET/POST /families/{family_id}/prescriptions`: Quản lý đơn thuốc
- `POST /families/{family_id}/prescriptions/{prescription_id}/items`: Thêm thuốc vào đơn
- `GET/POST /families/{family_id}/schedules`: Quản lý lịch uống thuốc
- `GET /families/{family_id}/schedules/daily?date=YYYY-MM-DD`: Lịch uống trong ngày
- `GET /families/{family_id}/members/{member_id}/next-dose`: Liều uống tiếp theo của thành viên

## 5. Tủ thuốc thông minh & Digital Twin 3D
- `GET /families/{family_id}/cabinets`: Danh sách tủ thuốc của gia đình
- `POST /families/{family_id}/cabinets`: Tạo tủ thuốc 9 ngăn
- `GET /families/{family_id}/cabinets/{cabinet_id}/digital-twin`: Dữ liệu tổng hợp cho Digital Twin 3D
- `PUT /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/medication`: Gán thuốc vào ngăn
- `DELETE /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/medication`: Gỡ thuốc khỏi ngăn
- `POST /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/open`: Mở ngăn
- `POST /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/close`: Đóng ngăn
- `POST /families/{family_id}/cabinets/{cabinet_id}/simulator/online`: Đưa tủ lên ONLINE
- `POST /families/{family_id}/cabinets/{cabinet_id}/simulator/offline`: Đưa tủ về OFFLINE
- `WebSocket /ws/families/{family_id}/cabinets/{cabinet_id}?token={access_token}`: Nhận sự kiện `CABINET_ONLINE`, `CABINET_OFFLINE`, `COMPARTMENT_OPEN`, `COMPARTMENT_CLOSE`, `CABINET_STATE_SYNC`.

