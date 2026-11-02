# PharmaMind AI — MOBILE APP INTEGRATION PLAN

## 1. Mục tiêu

Tài liệu này mô tả kế hoạch tích hợp toàn bộ hệ thống **PharmaMind AI** thành **một ứng dụng mobile duy nhất** cho gia đình.

App mobile sẽ là giao diện trung tâm để người dùng:

- đăng nhập và quản lý tài khoản;
- quản lý gia đình và từng thành viên;
- theo dõi hồ sơ sức khỏe cá nhân hóa;
- quản lý thuốc, đơn thuốc và lịch uống;
- nhập đơn thuốc bằng OCR hoặc Excel;
- nhận nhắc nhở và cảnh báo;
- theo dõi tủ thuốc thông minh;
- sử dụng Digital Twin 3D;
- tương tác với AI Dược sĩ.

Mục tiêu cuối cùng:

> **Một app duy nhất để quản lý sức khỏe, thuốc và tủ thuốc thông minh cho toàn bộ gia đình.**

---

## 2. Kiến trúc tổng thể

```text
Mobile App
   ↓
FastAPI Backend
   ↓
PostgreSQL
   ↓
Health / Medication / Prescription / Schedule / Cabinet Services
   ↓
Hardware Simulator / ESP32
   ↓
AI Service
```

Mobile App không phải source of truth. Business logic, authorization và dữ liệu chính vẫn nằm ở Backend.

---

## 3. Công nghệ mobile đề xuất

Khuyến nghị sử dụng:

```text
Flutter
Dart
```

Lý do:

```text
1 codebase cho Android + iOS
UI mượt
animation tốt
REST / WebSocket dễ tích hợp
camera và file picker tốt
phù hợp Digital Twin mức mobile
phù hợp cấu trúc mobile/ đã thiết kế trước đó
```

State management đề xuất:

```text
Riverpod
```

Networking:

```text
Dio
```

Secure token storage:

```text
Android Keystore
iOS Keychain
```

---

## 4. Phạm vi mobile app

App sẽ tích hợp:

```text
AUTH
FAMILY
MEMBER
HEALTH PROFILE
MEDICATION
PRESCRIPTION
OCR / EXCEL IMPORT
SCHEDULE
REMINDER
SMART CABINET
DIGITAL TWIN
NOTIFICATIONS
AI PHARMACIST
SETTINGS
```

---

## 5. Cấu trúc thư mục mobile

```text
mobile/
│
├── lib/
│   ├── main.dart
│   │
│   ├── app/
│   │   ├── app.dart
│   │   ├── routes.dart
│   │   ├── theme.dart
│   │   └── app_config.dart
│   │
│   ├── core/
│   │   ├── network/
│   │   ├── storage/
│   │   ├── websocket/
│   │   ├── notifications/
│   │   ├── permissions/
│   │   ├── error/
│   │   ├── utils/
│   │   └── widgets/
│   │
│   ├── features/
│   │   ├── auth/
│   │   ├── family/
│   │   ├── member/
│   │   ├── health/
│   │   ├── medication/
│   │   ├── prescription/
│   │   ├── import_prescription/
│   │   ├── schedule/
│   │   ├── reminder/
│   │   ├── cabinet/
│   │   ├── digital_twin/
│   │   ├── notifications/
│   │   ├── ai_chat/
│   │   └── settings/
│   │
│   ├── services/
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   ├── websocket_service.dart
│   │   ├── notification_service.dart
│   │   ├── file_upload_service.dart
│   │   └── ai_service.dart
│   │
│   └── shared/
│       ├── models/
│       ├── enums/
│       └── constants/
│
├── assets/
│   ├── images/
│   ├── icons/
│   └── models/
│
├── test/
├── integration_test/
└── pubspec.yaml
```

---

## 6. Navigation chính

Bottom Navigation đề xuất:

```text
Trang chủ
Gia đình
Lịch thuốc
Tủ thuốc
AI
```

Không nên quá 5 tab.

---

## 7. Home Dashboard

Home phải trả lời nhanh:

```text
Ai cần uống thuốc?
Thuốc gì?
Khi nào?
Thuốc ở đâu?
Có cảnh báo gì?
```

Các card chính:

```text
Liều tiếp theo
Lịch hôm nay
Tình trạng tủ thuốc
Cảnh báo
Quick Actions
```

Ví dụ:

```text
Bà Lan
Amlodipine 5 mg
1 viên
20:00 hôm nay
Ngăn 08
```

CTA:

```text
Xem thuốc
Xem ngăn
```

---

## 8. Family Module

App cho phép:

```text
Tạo Family
Chọn Family
Xem Family
Quản lý quyền
```

Lưu `currentFamily` trong app state để giảm số bước thao tác.

---

## 9. Member Module

Mỗi thành viên hiển thị:

```text
Avatar
Tên
Tuổi
Quan hệ
Thuốc đang dùng
Lịch tiếp theo
Cảnh báo
```

Tabs chi tiết:

```text
Tổng quan
Sức khỏe
Thuốc
Đơn thuốc
Lịch dùng
```

---

## 10. Health Profile Module

Bao gồm:

```text
Thông tin cơ bản
Bệnh nền
Dị ứng
Phản ứng thuốc
Chiều cao
Cân nặng
Nhóm máu
Liên hệ khẩn cấp
```

---

## 11. Medication Module

Mỗi thuốc hiển thị:

```text
Tên thuốc
Hàm lượng
Số lượng
Hạn sử dụng
Ngăn tủ
Trạng thái
```

Medication Detail:

```text
Tên thuốc
Hoạt chất
Hàm lượng
Dạng bào chế
Nhà sản xuất
Số lượng
Hạn sử dụng
Thành viên sử dụng
Đơn thuốc liên quan
Lịch uống
Ngăn tủ
Cảnh báo
```

---

## 12. Prescription Module

Cho phép:

```text
Tạo đơn thủ công
Xem lịch sử đơn
Cập nhật đơn
Import OCR
Import Excel
```

---

## 13. OCR Prescription Import

Flow:

```text
Chọn thành viên
   ↓
Chụp ảnh / chọn ảnh / PDF
   ↓
Upload
   ↓
OCR Processing
   ↓
Review
   ↓
Confirm
   ↓
Commit
```

App không ghi dữ liệu OCR trực tiếp vào database.

---

## 14. Excel Prescription Import

Flow:

```text
Chọn thành viên
   ↓
Chọn .xlsx
   ↓
Upload
   ↓
Parse
   ↓
Review
   ↓
Confirm
   ↓
Commit
```

UI cần có nút:

```text
Tải file mẫu
```

---

## 15. Import Wizard trên mobile

Khuyến nghị 5 bước:

```text
1. Chọn thành viên
2. Chụp / tải đơn thuốc
3. Kiểm tra dữ liệu
4. Kiểm tra lịch uống và thông tin sức khỏe
5. Xác nhận cập nhật
```

---

## 16. Schedule Module

Timeline:

```text
08:00
Bà Lan
Amlodipine
1 viên

12:00
Ông Minh
Vitamin D
1 viên
```

Tabs:

```text
Hôm nay
Ngày mai
Tuần này
```

---

## 17. Reminder Module

App cần hỗ trợ:

```text
Local Notification
Push Notification
In-app Reminder
```

Notification categories:

```text
MEDICATION_REMINDER
MISSED_DOSE
LOW_STOCK
EXPIRATION
CABINET_OFFLINE
SAFETY_WARNING
```

---

## 18. Smart Cabinet Module

Có 2 chế độ:

```text
Simple Mode
Digital Twin Mode
```

### Simple Mode

```text
[01][02][03]
[04][05][06]
[07][08][09]
```

Mỗi ngăn hiển thị:

```text
Tên thuốc
Status
Next Dose
```

Đây là chế độ ưu tiên trên mobile và cho người lớn tuổi.

---

## 19. Digital Twin trên mobile

Hỗ trợ:

```text
Rotate
Zoom
Select drawer
Highlight next dose
Open / close animation
Capsule fly-out
Info bottom sheet
```

Asset phải:

```text
low-poly
compressed
lazy-loaded
```

Nếu máy yếu:

```text
fallback Simple Mode
```

---

## 20. Capsule Reveal Feature

Flow:

```text
Open Drawer
   ↓
Capsule Fly-out
   ↓
Bottom Sheet
   ↓
Medication
Member
Dose
Schedule
Warnings
```

Thông tin chính:

```text
Amlodipine 5 mg
Bà Lan
1 viên
20:00 hôm nay
Còn 20 viên
```

---

## 21. Realtime Cabinet Sync

Mobile kết nối WebSocket để nhận:

```text
CABINET_ONLINE
CABINET_OFFLINE
COMPARTMENT_OPEN
COMPARTMENT_CLOSE
STATE_SYNC
```

Khi app quay lại foreground:

```text
Reconnect WebSocket
Refetch cabinet state
```

---

## 22. AI Pharmacist Module

Chat UI gồm:

```text
Chat bubbles
Input
Suggested prompts
Voice future
```

Prompt ví dụ:

```text
Hôm nay bà uống thuốc gì?
Thuốc nào sắp hết?
Cho tôi xem ngăn 08.
Thành viên nào có cảnh báo dị ứng?
```

AI không query database trực tiếp mà gọi backend tools.

---

## 23. API Layer

Mobile gọi trực tiếp FastAPI hiện tại.

Không cần backend riêng cho mobile ở MVP.

Cần:

```text
Base URL
JWT interceptor
Refresh token handling
Error normalization
Retry
```

---

## 24. Token Security

Access token:

```text
memory / secure session
```

Refresh token:

```text
secure storage
```

Không lưu token plain trong `SharedPreferences`.

---

## 25. Offline Cache

Có thể cache:

```text
Family summary
Member summary
Today's schedule
Medication list
Cabinet last state
```

Cache không phải source of truth.

Nếu mất mạng:

```text
Hiển thị dữ liệu gần nhất
Hiện banner offline
Disable action cần backend
```

---

## 26. Camera / File Permissions

App cần quyền:

```text
Camera
Photo Library
File Picker
Notifications
```

Chỉ xin permission khi cần.

Ví dụ:

```text
Camera → khi chụp đơn
Notification → sau khi user tạo schedule
File → khi import Excel/PDF
```

---

## 27. Push Notification

Khuyến nghị:

```text
Firebase Cloud Messaging
```

Backend gửi push dựa trên schedule/event.

Không hiển thị dữ liệu y tế quá chi tiết trên lock screen mặc định.

Ví dụ tốt:

```text
Đã đến giờ uống thuốc.
```

---

## 28. Multi-user / Multi-device

Một User có thể dùng:

```text
Phone
Tablet
```

Một Family có:

```text
OWNER
ADMIN
CAREGIVER
VIEWER
```

Frontend ẩn action theo role, nhưng backend vẫn enforce quyền cuối cùng.

---

## 29. Elderly Friendly Mode

Setting:

```text
Chế độ dễ đọc
```

Khi bật:

```text
Font lớn hơn
Button lớn hơn
Contrast cao hơn
Giảm animation
Đơn giản hóa card
Ưu tiên Simple Cabinet Mode
```

---

## 30. Accessibility

Hỗ trợ:

```text
Screen reader
Dynamic font size
High contrast
Reduced motion
Large touch targets
```

---

## 31. Mobile Screen List

MVP:

```text
01 Splash
02 Login
03 Register
04 Home
05 Family
06 Member List
07 Member Detail
08 Health Profile
09 Medication List
10 Medication Detail
11 Add Medication
12 Prescription List
13 Prescription Detail
14 Import Prescription
15 OCR Review
16 Excel Review
17 Schedule Timeline
18 Smart Cabinet
19 Digital Twin
20 Compartment Detail
21 Notifications
22 AI Pharmacist
23 Settings
```

---

## 32. User Flow chính

```text
Open App
 ↓
Login
 ↓
Home
 ↓
Next Dose
 ↓
Select Member
 ↓
View Schedule
 ↓
Open Cabinet
 ↓
Open Drawer
 ↓
View Medication
```

---

## 33. OCR Flow

```text
Member
 ↓
Import Prescription
 ↓
Camera / File
 ↓
Upload
 ↓
OCR
 ↓
Review
 ↓
Schedule
 ↓
Confirm
 ↓
Database Updated
```

---

## 34. Cabinet Flow

```text
Home
 ↓
Smart Cabinet
 ↓
Simple / 3D Mode
 ↓
Select Drawer
 ↓
Open
 ↓
Capsule Fly-out
 ↓
Medication / Member / Schedule Info
```

---

## 35. Backend không cần viết lại

Toàn bộ mobile app sử dụng lại:

```text
FastAPI Backend
PostgreSQL
WebSocket
AI Service
Hardware Service
```

Không tạo một backend mới riêng cho mobile.

---

## 36. API Aggregation khuyến nghị

Một số màn hình nên có endpoint tổng hợp:

```text
GET /mobile/home
GET /members/{id}/summary
GET /cabinets/{id}/mobile-state
```

Mục đích:

```text
giảm số request
giảm loading
tối ưu mobile
```

---

## 37. Deep Link

Push notification có thể mở thẳng:

```text
Medication Detail
Schedule Detail
Compartment Detail
Import Review
```

Ví dụ:

```text
pharmamind://schedule/123
pharmamind://cabinet/1/compartment/8
```

---

## 38. App Lifecycle

Khi app resume:

```text
Refresh token nếu cần
Sync current family
Sync today schedule
Sync cabinet state
Reconnect WebSocket
```

---

## 39. Feature Flags

Đề xuất:

```text
enable_ai
enable_3d
enable_ocr
enable_excel_import
enable_hardware
```

để triển khai tuần tự.

---

## 40. Mobile Development Phases

### Phase 1 — Foundation

```text
Flutter project
Theme
Navigation
API client
Secure storage
Auth
```

### Phase 2 — Family & Health

```text
Family
Member
Health Profile
```

### Phase 3 — Medication

```text
Medication
Prescription
Schedule
```

### Phase 4 — Smart Import

```text
OCR
Excel
Review
Commit
```

### Phase 5 — Cabinet

```text
Simple Cabinet
Realtime
WebSocket
```

### Phase 6 — Digital Twin

```text
3D
Drawer animation
Capsule fly-out
```

### Phase 7 — AI & Notifications

```text
AI Pharmacist
Push Notification
Advanced Reminders
```

---

## 41. Sprint đề xuất

```text
Sprint 1  — App Skeleton + Auth
Sprint 2  — Family + Member
Sprint 3  — Health Profile
Sprint 4  — Medication
Sprint 5  — Prescription + Schedule
Sprint 6  — OCR / Excel Import
Sprint 7  — Cabinet Simple Mode
Sprint 8  — Realtime + WebSocket
Sprint 9  — Digital Twin 3D
Sprint 10 — AI + Push Notification
```

---

## 42. Testing

Cần:

```text
Unit Test
Widget Test
Integration Test
API Mock Test
Real Device Test
```

Critical flows:

```text
Login
Refresh Token
Switch Family
Member Data Isolation
OCR Upload
Excel Upload
Schedule Update
Notification
Cabinet Realtime
Drawer Open
Digital Twin
Offline Mode
Reconnect
```

---

## 43. Security

Bắt buộc:

```text
HTTPS
JWT
Secure Storage
Family Authorization
Member Scope
No Sensitive Logs
Protected File Upload
```

Không gửi dữ liệu sức khỏe nhạy cảm vào analytics hoặc crash logs.

---

## 44. Release Environments

```text
DEV
STAGING
PRODUCTION
```

Environment config:

```text
API_BASE_URL
WS_BASE_URL
APP_ENV
FEATURE_FLAGS
```

---

## 45. Acceptance Criteria

- [ ] Flutter project hoạt động Android/iOS.
- [ ] Auth + refresh token hoạt động.
- [ ] Family switch hoạt động.
- [ ] Member detail hoạt động.
- [ ] Health Profile hoạt động.
- [ ] Medication hoạt động.
- [ ] Prescription hoạt động.
- [ ] OCR import hoạt động.
- [ ] Excel import hoạt động.
- [ ] Schedule timeline hoạt động.
- [ ] Notification hoạt động.
- [ ] Smart Cabinet Simple Mode hoạt động.
- [ ] WebSocket realtime hoạt động.
- [ ] Digital Twin hoạt động ở mức mobile.
- [ ] Capsule reveal hoạt động.
- [ ] AI Pharmacist UI hoạt động.
- [ ] Offline state được xử lý.
- [ ] Secure storage được dùng.
- [ ] Role-based UI hoạt động.
- [ ] Accessibility cơ bản hoạt động.
- [ ] Cross-family data không bị leak.
- [ ] Tests pass.

---

## 46. Definition of Done

Mobile App đạt MVP khi demo được:

```text
Open App
 ↓
Login
 ↓
Select Family
 ↓
Select Member
 ↓
View Health Profile
 ↓
Import Prescription by OCR / Excel
 ↓
Confirm Prescription
 ↓
Schedule Updated
 ↓
Receive Reminder
 ↓
Open Smart Cabinet
 ↓
Select Drawer
 ↓
Capsule Fly-out
 ↓
View Medication / Member / Schedule
 ↓
Ask AI Pharmacist
```

---

## 47. Deliverables

```text
docs/mobile/
└── MOBILE_APP_INTEGRATION_PLAN.md

mobile/
├── lib/
│   ├── app/
│   ├── core/
│   ├── features/
│   ├── services/
│   └── shared/
├── assets/
├── test/
├── integration_test/
└── pubspec.yaml
```

---

## 48. Roadmap tổng thể

```text
BACKEND CORE
     ↓
MOBILE FOUNDATION
     ↓
FAMILY / HEALTH
     ↓
MEDICATION / PRESCRIPTION
     ↓
OCR / EXCEL
     ↓
SCHEDULE / REMINDER
     ↓
SMART CABINET
     ↓
DIGITAL TWIN
     ↓
AI PHARMACIST
     ↓
REAL HARDWARE
```

---

## 49. Kết luận

> **PharmaMind AI nên được triển khai thành một app mobile duy nhất bằng Flutter, trong đó toàn bộ dữ liệu và business logic tiếp tục được quản lý bởi FastAPI Backend. App mobile đóng vai trò Family Health Hub: quản lý sức khỏe, thuốc, đơn thuốc, lịch uống, tủ thuốc thông minh, Digital Twin và AI Dược sĩ.**

Nguyên tắc cốt lõi:

```text
One App
One Family Health Hub
One Backend Source of Truth
Mobile-first Experience
Hardware-independent Architecture
AI-ready
```
