# PharmaMind AI — FRONTEND SPECIFICATION

# 1. Mục tiêu

Tài liệu này mô tả đặc tả frontend cho hệ thống **PharmaMind AI**.

Frontend phải đáp ứng đồng thời 4 yêu cầu:

```text
1. Dễ dùng cho gia đình
2. Thân thiện với người lớn tuổi
3. Phù hợp với kiến trúc backend hiện tại
4. Sẵn sàng tích hợp Digital Twin 3D và AI Pharmacist
```

Mục tiêu tổng thể:

> **Người dùng chỉ cần vài thao tác đơn giản để xem thành viên trong gia đình, thuốc đang dùng, lịch uống, trạng thái tủ thuốc, cảnh báo và thông tin sức khỏe liên quan.**

---

# 2. Định hướng sản phẩm frontend

PharmaMind AI không nên được thiết kế giống một dashboard kỹ thuật.

Frontend phải có cảm giác:

```text
Family Health App
+
Smart Medicine Cabinet
+
AI Pharmacist
```

Ưu tiên:

```text
Đơn giản
Dễ đọc
Ít bước
Ít chữ dài
Icon rõ ràng
Màu sắc dễ hiểu
Thông tin quan trọng nổi bật
```

---

# 3. Nhóm người dùng chính

Frontend phải phục vụ:

```text
1. Người lớn tuổi
2. Người sử dụng thuốc dài hạn
3. Người chăm sóc
4. Thành viên gia đình
5. Chủ gia đình / người quản lý
```

---

# 4. Nguyên tắc UX bắt buộc

## 4.1 Không quá nhiều thông tin trên một màn hình

Một màn hình chỉ nên tập trung vào:

```text
1 nhiệm vụ chính
```

Ví dụ:

```text
Hôm nay cần uống thuốc gì?
```

không nên cùng lúc hiển thị:

```text
20 biểu đồ
10 cảnh báo
toàn bộ lịch sử
```

## 4.2 Ưu tiên hành động quan trọng

Các CTA chính:

```text
Uống thuốc hôm nay
Xem tủ thuốc
Xem thành viên
Thêm thuốc
Hỏi AI
```

phải nổi bật.

## 4.3 Font lớn, dễ đọc

Khuyến nghị:

```text
Body: 16–18 px
Heading: 24–32 px
Primary action: 18–20 px
```

Không dùng font quá mảnh.

## 4.4 Nút bấm lớn

Đặc biệt với người lớn tuổi:

```text
Touch target >= 44px
```

Không dùng icon quá nhỏ.

## 4.5 Không dựa vào màu sắc duy nhất

Ví dụ cảnh báo phải có:

```text
icon + text + màu
```

---

# 5. Design System đề xuất

Phong cách:

```text
Modern Healthcare
Friendly
Clean
Soft
Trustworthy
```

Màu chủ đạo gợi theo concept sản phẩm:

```text
Primary: #2E9C95
Primary Light: #DDF4F1
Background: #F7FAFA
Surface: #FFFFFF
Text Primary: #17343A
Text Secondary: #62767A
Success: #2FA66A
Warning: #E6A83A
Danger: #D9534F
Info: #3A8FD9
```

---

# 6. Typography

Khuyến nghị:

```text
Inter
Roboto
Noto Sans
```

---

# 7. Border Radius

```text
Cards: 16 px
Buttons: 12 px
Inputs: 12 px
Modals: 20 px
```

---

# 8. Responsive Design

Frontend cần hỗ trợ:

```text
Desktop
Tablet
Mobile
```

Ưu tiên:

```text
Mobile First
```

Digital Twin 3D tối ưu đặc biệt cho:

```text
Tablet
Desktop
```

---

# 9. Kiến trúc frontend đề xuất

Khuyến nghị:

```text
React
TypeScript
Vite
React Router
TanStack Query
Zustand
React Hook Form
Zod
Three.js
React Three Fiber
Drei
```

Nếu triển khai mobile app riêng sau này:

```text
React Native
```

---

# 10. Frontend Architecture

```text
UI Layer
  ↓
Feature Layer
  ↓
Application State
  ↓
API Client
  ↓
Backend
```

Không gọi API trực tiếp rải rác trong component.

---

# 11. Cấu trúc thư mục đề xuất

```text
frontend/
│
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   ├── providers.tsx
│   │   └── guards.tsx
│   │
│   ├── pages/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── family/
│   │   ├── members/
│   │   ├── medications/
│   │   ├── prescriptions/
│   │   ├── schedules/
│   │   ├── cabinet/
│   │   ├── digital-twin/
│   │   ├── ai/
│   │   └── settings/
│   │
│   ├── features/
│   │   ├── auth/
│   │   ├── family/
│   │   ├── member/
│   │   ├── medication/
│   │   ├── prescription/
│   │   ├── schedule/
│   │   ├── cabinet/
│   │   ├── digitalTwin/
│   │   └── ai/
│   │
│   ├── components/
│   │   ├── common/
│   │   ├── navigation/
│   │   ├── cards/
│   │   ├── forms/
│   │   ├── feedback/
│   │   └── health/
│   │
│   ├── services/
│   │   ├── apiClient.ts
│   │   ├── authService.ts
│   │   └── websocketClient.ts
│   │
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── familyStore.ts
│   │   └── uiStore.ts
│   │
│   ├── hooks/
│   ├── types/
│   ├── utils/
│   ├── constants/
│   └── assets/
│       ├── images/
│       ├── icons/
│       └── models/
│
├── public/
├── tests/
├── package.json
├── tsconfig.json
└── README.md
```

---

# 12. Navigation Structure

Navigation chính:

```text
Trang chủ
Gia đình
Lịch thuốc
Tủ thuốc
AI Dược sĩ
Tài khoản
```

Trên mobile:

```text
Bottom Navigation
```

Trên desktop:

```text
Left Sidebar
```

---

# 13. Dashboard / Home

Mục tiêu:

```text
Người dùng biết ngay hôm nay cần làm gì.
```

Các khối chính:

```text
Greeting
Today's Medication
Next Dose
Family Overview
Smart Cabinet Status
Alerts
Quick Actions
```

Ví dụ:

```text
Xin chào, Anh A

Liều tiếp theo
Bà Lan
Amlodipine 5 mg
08:00
Ngăn 08

Lịch hôm nay

Tủ thuốc
Online
9 ngăn
1 cảnh báo
```

---

# 14. Next Dose Card

Hiển thị:

```text
Tên thành viên
Tên thuốc
Hàm lượng
Liều dùng
Thời gian
Ngăn tủ
```

CTA:

```text
Xem thuốc
Xem ngăn
```

---

# 15. Family Screen

Mỗi member card:

```text
Ảnh / avatar
Tên
Tuổi
Quan hệ
Số thuốc đang dùng
Lịch tiếp theo
```

---

# 16. Member Detail Screen

Tabs:

```text
Tổng quan
Sức khỏe
Thuốc
Đơn thuốc
Lịch dùng
```

---

# 17. Health Profile UI

Các section:

```text
Thông tin cơ bản
Bệnh nền
Dị ứng
Phản ứng thuốc
Liên hệ khẩn cấp
```

---

# 18. Allergy UI

Hiển thị:

```text
Tên chất / thuốc
Mức độ
Phản ứng
Nguồn
Ngày ghi nhận
```

Nếu severity = SEVERE:

```text
warning card
```

---

# 19. Medication Screen

Card gồm:

```text
Tên thuốc
Hàm lượng
Dạng bào chế
Số lượng
Đơn vị
Hạn sử dụng
Ngăn tủ
Status
```

Status chip:

```text
Đang dùng
Sắp hết
Hết thuốc
Sắp hết hạn
Hết hạn
Đã lưu trữ
```

---

# 20. Medication Detail Screen

Hiển thị:

```text
Thông tin thuốc
Inventory
Expiration
Members
Prescription links
Schedule
Cabinet compartment
Warnings
```

---

# 21. Add Medication Flow

Chia 3 bước:

```text
Step 1
Thông tin thuốc

Step 2
Tồn kho

Step 3
Gán thành viên
```

---

# 22. Prescription Screen

Card:

```text
Tên đơn
Tên thành viên
Ngày bắt đầu
Ngày kết thúc
Số thuốc
Status
```

---

# 23. Schedule Screen

Ưu tiên timeline:

```text
08:00
Bà Lan
Amlodipine 5 mg
1 viên

12:00
Ông Minh
Vitamin D
1 viên

20:00
Bà Lan
Metformin
1 viên
```

Có tab:

```text
Hôm nay
Ngày mai
Tuần này
```

---

# 24. Smart Cabinet Screen

Có 2 chế độ:

```text
Simple Mode
3D Mode
```

---

# 25. Simple Mode

Hiển thị 9 ngăn dạng lưới:

```text
[01][02][03]
[04][05][06]
[07][08][09]
```

Mỗi ô:

```text
Tên thuốc
Status
Next Dose
```

Simple Mode rất quan trọng cho người lớn tuổi.

---

# 26. 3D Mode

Hiển thị Digital Twin 3D theo Task 10:

```text
Rotate
Zoom
Select drawer
Highlight
Realtime open / close
```

---

# 27. Compartment Detail Panel

Khi chọn ngăn:

```text
Tên ngăn
Thuốc
Số lượng
Hạn sử dụng
Người sử dụng
Lịch tiếp theo
Cảnh báo
```

---

# 28. Cabinet Status

Hiển thị:

```text
Online
Offline
Đang đồng bộ
Lỗi kết nối
```

Không dùng thuật ngữ kỹ thuật như:

```text
WS disconnected
MQTT timeout
```

---

# 29. AI Pharmacist Screen

Chuẩn bị UI:

```text
Chat list
Input box
Suggested prompts
Voice button (future)
```

Suggested prompts:

```text
Thuốc của bà hôm nay uống lúc nào?
Thuốc nào sắp hết?
Cho tôi xem thuốc ở ngăn 08
Thành viên nào có cảnh báo dị ứng?
```

Disclaimer:

```text
Thông tin hỗ trợ, không thay thế tư vấn bác sĩ hoặc dược sĩ.
```

---

# 30. Notification Center

Các loại:

```text
Lịch thuốc
Low stock
Expiration
Cabinet offline
Safety warning
```

Priority:

```text
INFO
WARNING
CRITICAL
```

---

# 31. Form UX

Form cần:

```text
Label rõ
Placeholder đơn giản
Validation realtime
Error text dễ hiểu
```

Ví dụ không dùng:

```text
ValidationError field required
```

Mà dùng:

```text
Vui lòng nhập tên thuốc.
```

---

# 32. Loading / Empty / Error State

Loading:

```text
Skeleton
Loading card
Progress indicator
```

Empty:

```text
Chưa có thuốc nào trong gia đình.
[ Thêm thuốc ]
```

Error:

```text
Không thể tải dữ liệu.
Vui lòng kiểm tra kết nối và thử lại.
[ Thử lại ]
```

---

# 33. Offline UX

Nếu mất mạng:

```text
Hiển thị banner nhẹ
Không xóa dữ liệu đang hiển thị
Disable action cần backend
```

---

# 34. Authentication UI

Các màn hình:

```text
Login
Register
Logout
Session Expired
```

Nếu refresh token fail:

```text
Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.
```

---

# 35. Route Guard

Protected routes:

```text
/dashboard
/families
/members
/medications
/prescriptions
/schedules
/cabinet
/digital-twin
/ai
/settings
```

---

# 36. Role-based UI

Frontend có thể ẩn action không có quyền.

Ví dụ Viewer không hiện:

```text
Thêm thuốc
Sửa thuốc
Archive
```

Backend vẫn là nơi enforce cuối cùng.

---

# 37. State Management

Đề xuất:

```text
Server State → TanStack Query
Global Client State → Zustand
Form State → React Hook Form
```

Zustand dùng cho:

```text
currentFamily
selectedMember
theme
sidebar
digitalTwinSelection
```

---

# 38. API Client

Tạo:

```text
services/apiClient.ts
```

Có:

```text
base URL
Authorization header
refresh token interceptor
error normalization
```

---

# 39. WebSocket Client

Tạo:

```text
services/websocketClient.ts
```

Chịu trách nhiệm:

```text
connect
authenticate
reconnect
subscribe
unsubscribe
event dispatch
```

Nếu mất kết nối:

```text
Đang kết nối lại...
```

---

# 40. Realtime Events UI

Các event chính:

```text
CABINET_ONLINE
CABINET_OFFLINE
COMPARTMENT_OPEN
COMPARTMENT_CLOSE
STATE_SYNC
```

phải update UI mà không reload trang.

---

# 41. Accessibility

Frontend phải hỗ trợ:

```text
Keyboard navigation
Focus visible
ARIA labels
Contrast phù hợp
Screen reader basics
```

---

# 42. Elderly Mode

Đề xuất setting:

```text
Chế độ dễ đọc
```

Khi bật:

```text
Font lớn hơn
Button lớn hơn
Giảm animation
Tăng contrast
Đơn giản hóa card
```

---

# 43. Reduced Motion

Tôn trọng:

```text
prefers-reduced-motion
```

Nếu bật:

```text
giảm animation 3D
giảm pulse
giảm slide transition
```

---

# 44. Language

UI mặc định:

```text
Tiếng Việt
```

Chuẩn bị i18n cho:

```text
English
```

---

# 45. Date / Time

Hiển thị thân thiện:

```text
08:00 hôm nay
20:00 tối nay
Ngày 01/11/2026
```

Không hiển thị raw ISO string.

---

# 46. Confirmation Dialog

Dùng cho:

```text
Archive Family
Archive Medication
Remove Member
Unassign Medication
```

Không dùng quá nhiều cho hành động đơn giản.

---

# 47. Toast

Dùng cho:

```text
Đã lưu
Đã cập nhật
Đã gán thuốc
Đã thay đổi lịch
```

---

# 48. Mobile / Desktop Detail Pattern

Mobile:

```text
Bottom Sheet
```

Desktop:

```text
Detail Panel bên phải
```

---

# 49. Home Quick Actions

```text
+ Thêm thuốc
+ Thêm thành viên
Xem lịch hôm nay
Mở tủ thuốc
Hỏi AI
```

---

# 50. Safety Warning UX

Cảnh báo y tế phải:

```text
rõ
không gây hoảng loạn
không khẳng định quá mức
```

Ví dụ tốt:

```text
Hồ sơ có thông tin dị ứng hoặc phản ứng thuốc cần kiểm tra.
```

Không nên:

```text
Thuốc này chắc chắn gây phản vệ.
```

---

# 51. User-friendly Wording

Không dùng:

```text
FamilyMembership
PrescriptionItem
Compartment state
```

trong UI.

Dùng:

```text
Gia đình
Thuốc trong đơn
Ngăn thuốc
```

---

# 52. Frontend Development Phases

## Phase 1

```text
Auth
Layout
Navigation
Family
Member
```

## Phase 2

```text
Medication
Prescription
Schedule
```

## Phase 3

```text
Cabinet Simple Mode
Realtime
```

## Phase 4

```text
Digital Twin 3D
```

## Phase 5

```text
AI Pharmacist
Notifications
Advanced Accessibility
```

---

# 53. API Integration Order

```text
Auth
 ↓
Family
 ↓
Member
 ↓
Medication
 ↓
Prescription
 ↓
Schedule
 ↓
Cabinet
 ↓
Digital Twin
 ↓
AI
```

---

# 54. Screen List MVP

```text
01 Login
02 Register
03 Home Dashboard
04 Family List / Family Detail
05 Member List
06 Member Detail
07 Health Profile
08 Medication List
09 Medication Detail
10 Add Medication
11 Prescription List
12 Prescription Detail
13 Schedule Timeline
14 Smart Cabinet Simple Mode
15 Digital Twin 3D
16 Compartment Detail
17 Notification Center
18 AI Pharmacist
19 Settings
```

---

# 55. User Flow chính

```text
Login
 ↓
Home
 ↓
Select Family
 ↓
View Member
 ↓
View Today Schedule
 ↓
View Medication
 ↓
Open Cabinet
 ↓
Select Compartment
 ↓
View Medication Detail
```

---

# 56. User Flow cho người chăm sóc

```text
Login
 ↓
Family Dashboard
 ↓
Select Member
 ↓
Today's Schedule
 ↓
Check Medication
 ↓
Cabinet Status
 ↓
Warning / Reminder
```

---

# 57. User Flow cho người lớn tuổi

Nên tối giản:

```text
Home
 ↓
Thuốc tiếp theo
 ↓
Xem ngăn
 ↓
Xem hướng dẫn
```

---

# 58. Acceptance Criteria

Frontend tổng thể phải đáp ứng:

- [ ] Người dùng hiểu được màn hình chính trong vài giây.
- [ ] Next Dose nổi bật.
- [ ] Không quá nhiều thông tin trên một screen.
- [ ] Người lớn tuổi vẫn có thể thao tác.
- [ ] Font và nút đủ lớn.
- [ ] Simple Cabinet Mode tồn tại song song với 3D Mode.
- [ ] Digital Twin không bắt buộc để dùng toàn bộ hệ thống.
- [ ] Role không phù hợp thì không hiện action dư thừa.
- [ ] Error message thân thiện.
- [ ] Không hiển thị thuật ngữ kỹ thuật backend cho user.
- [ ] Realtime cabinet update hoạt động.
- [ ] Offline state được xử lý rõ ràng.
- [ ] Allergy / drug reaction warning hiển thị an toàn.
- [ ] Responsive tốt trên desktop/tablet/mobile.
- [ ] Trải nghiệm nhất quán giữa Family, Member, Medication và Cabinet.

---

# 59. Definition of Done — Frontend Foundation

Frontend foundation hoàn thành khi:

- [ ] Có responsive layout.
- [ ] Có design system.
- [ ] Có route guard.
- [ ] Có auth flow.
- [ ] Có current family context.
- [ ] Có navigation mobile + desktop.
- [ ] Có loading state.
- [ ] Có empty state.
- [ ] Có error state.
- [ ] Có toast.
- [ ] Có form validation.
- [ ] Có API client.
- [ ] Có refresh-token handling.
- [ ] Có WebSocket client.
- [ ] Có role-based UI.
- [ ] Có accessibility cơ bản.
- [ ] Có chế độ dễ đọc hoặc chuẩn bị hỗ trợ.

---

# 60. Deliverables

Tài liệu:

```text
docs/frontend/
├── FRONTEND_SPECIFICATION.md
├── DESIGN_SYSTEM.md
├── USER_FLOW.md
├── SCREEN_LIST.md
├── COMPONENT_GUIDE.md
└── API_INTEGRATION.md
```

Code:

```text
frontend/
├── src/
│   ├── app/
│   ├── pages/
│   ├── features/
│   ├── components/
│   ├── services/
│   ├── store/
│   ├── hooks/
│   ├── types/
│   ├── utils/
│   └── assets/
├── tests/
└── package.json
```

---

# 61. Kết luận

> **Frontend PharmaMind AI phải ưu tiên sự dễ hiểu trước sự phức tạp. Hệ thống có thể có backend, AI và Digital Twin rất mạnh, nhưng người dùng cuối chỉ nên cảm nhận một trải nghiệm đơn giản: hôm nay ai cần uống thuốc gì, lúc nào, thuốc nằm ở đâu, còn bao nhiêu và có cảnh báo gì cần lưu ý.**

Nguyên tắc cốt lõi:

```text
Simple First
Family First
Safety First
Accessibility First
Realtime When Useful
3D as Enhancement, not Dependency
```
