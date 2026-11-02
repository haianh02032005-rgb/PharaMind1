# PharmaMind AI — FEATURE SPECIFICATION

# FEATURE — Drawer Open Capsule Fly-out & Medication Info Reveal

## 1. Mục tiêu

Tài liệu này mô tả đặc tả tính năng:

> **Khi mở một ngăn trong tủ thuốc thông minh, một hình ảnh hoặc mô hình viên thuốc dạng con nhộng sẽ bay ra theo hiệu ứng trực quan, đồng thời hiển thị thông tin về thuốc, người cần uống thuốc và lịch uống thuốc.**

Tính năng này phải:

```text
1. Phù hợp với kiến trúc hệ thống PharmaMind AI
2. Tương thích với Smart Cabinet Mock / Hardware Simulator
3. Tương thích với Digital Twin 3D
4. Thân thiện với người dùng, đặc biệt là người lớn tuổi
5. Không gây rối mắt, không làm chậm hệ thống
```

Mục tiêu trải nghiệm:

> **Người dùng vừa nhìn thấy trực quan “thuốc nào cần lấy”, vừa ngay lập tức hiểu “ai uống, uống lúc nào, uống bao nhiêu”, mà không cần đọc quá nhiều hoặc tìm nhiều màn hình khác nhau.**

---

# 2. Bối cảnh hệ thống

Tính năng này được xây dựng trên các thành phần đã có trong hệ thống:

```text
Task 06 — Medication Management
Task 07 — Prescription Management
Task 08 — Medication Schedule
Task 09 — Smart Cabinet Mock / Hardware Simulator
Task 10 — Digital Twin 3D
Frontend Specification
```

Nguồn dữ liệu chính:

```text
Cabinet
Compartment
FamilyMedication
FamilyMember
PrescriptionItem
MedicationSchedule
Next Dose
Allergy / Drug Reaction Data
WebSocket Cabinet Event
```

---

# 3. Ý tưởng tổng quan

Khi user mở một ngăn thuốc trong giao diện tủ thuốc:

```text
1. Ngăn được mở bằng animation
2. Một viên thuốc dạng con nhộng minh họa bay ra phía trước hoặc nổi lên
3. Một thẻ thông tin hoặc panel thông tin xuất hiện
4. Panel hiển thị:
   - Tên thuốc
   - Số lượng còn lại
   - Người cần uống thuốc
   - Lịch uống gần nhất hoặc tiếp theo
   - Liều dùng
   - Cảnh báo dị ứng hoặc phản vệ nếu có
```

Mục tiêu là tạo ra cảm giác:

```text
trực quan
thông minh
dễ hiểu
nhẹ nhàng
không gây áp lực
```

---

# 4. Phạm vi tính năng

Tính năng bao gồm:

```text
1. Drawer Open Trigger
2. Capsule Fly-out Animation
3. Medication Info Reveal
4. Member + Schedule Summary
5. Safety Warning Display
6. Realtime Sync with Cabinet State
7. Reduced Motion / Accessibility Support
8. Fallback Simple Mode
9. State Management
10. Error / Empty / Offline handling
```

Tính năng này không bao gồm:

```text
Xác nhận đã uống thuốc
Tự động trừ tồn kho
Tự động kết luận y khoa
Animation vật lý phức tạp
AR / VR
```

---

# 5. Mục tiêu UX

Tính năng phải giải quyết được 4 câu hỏi ngay tại thời điểm mở ngăn:

```text
Đây là thuốc gì?
Ai cần uống thuốc này?
Uống lúc nào?
Còn bao nhiêu?
```

Nếu có rủi ro an toàn thì trả lời thêm:

```text
Có cảnh báo gì cần chú ý không?
```

---

# 6. Nguyên tắc thiết kế UX

## 6.1 Hiệu ứng phải hỗ trợ hiểu thông tin, không chỉ để trang trí

Capsule fly-out không được chỉ mang tính trình diễn.

Hiệu ứng phải giúp user hiểu:

```text
đây là thuốc trong ngăn vừa mở
```

## 6.2 Thông tin xuất hiện đúng thời điểm

Thông tin chỉ hiện khi:

```text
user mở ngăn
hoặc
user chọn ngăn
```

Không hiện quá nhiều panel cùng lúc.

## 6.3 Ưu tiên thân thiện với người lớn tuổi

Tức là:

```text
animation vừa phải
chữ đủ lớn
nội dung ngắn gọn
thông tin chính lên trước
```

## 6.4 Không gây choáng ngợp

Hiệu ứng phải:

```text
mượt
ngắn
không quá nhanh
không quá nhiều vật thể bay
không phát sáng chói
không rung lắc mạnh
```

---

# 7. Trigger của tính năng

Tính năng có thể được kích hoạt bởi 2 loại sự kiện:

## 7.1 User-triggered

Ví dụ:

```text
Người dùng click hoặc tap vào ngăn
Người dùng nhấn nút “Mở ngăn”
```

## 7.2 System-triggered

Ví dụ:

```text
Cabinet simulator gửi event COMPARTMENT_OPEN
Cabinet phần cứng thật gửi event open
```

Trong cả hai trường hợp, frontend đều phải có thể hiển thị cùng một trải nghiệm.

---

# 8. Kịch bản sử dụng chính

## Kịch bản 1 — Người dùng tự mở ngăn

```text
User xem tủ thuốc
 ↓
User chọn ngăn 08
 ↓
User nhấn Mở ngăn
 ↓
Animation mở ngăn
 ↓
Viên thuốc con nhộng bay ra
 ↓
Panel thông tin hiện ra
```

## Kịch bản 2 — Tủ mở theo lịch nhắc thuốc

```text
Hệ thống biết next dose thuộc ngăn 03
 ↓
Cabinet hoặc simulator mở ngăn 03
 ↓
Frontend nhận event realtime
 ↓
Ngăn 03 mở trong 3D hoặc Simple Mode
 ↓
Viên thuốc bay ra
 ↓
Hiện thông tin cho đúng người cần uống
```

---

# 9. Mô tả hiệu ứng capsule fly-out

## 9.1 Hình thức

Hiệu ứng sử dụng:

```text
mô hình viên thuốc minh họa dạng con nhộng
```

Không yêu cầu chính xác về màu hay hình dạng thật của thuốc thực tế.

Mục tiêu:

```text
người dùng dễ quan sát và hình dung
```

## 9.2 Hướng chuyển động

Viên thuốc có thể:

```text
bay ra phía trước từ ngăn
hoặc
nổi lên nhẹ phía trước ngăn
```

Khuyến nghị:

> **Bay ra một quãng ngắn, nhẹ nhàng, rồi dừng ở vị trí nổi phía trước drawer để user nhìn rõ.**

## 9.3 Thời lượng

Khuyến nghị:

```text
300–700 ms
```

Ưu tiên:

```text
ngắn
mượt
không kéo dài quá lâu
```

## 9.4 Số lượng capsule hiển thị

MVP chỉ nên hiển thị:

```text
1 capsule chính
```

Không nên cho bay ra nhiều viên cùng lúc vì dễ rối mắt.

---

# 10. Panel thông tin đi kèm

Ngay sau hoặc đồng thời với hiệu ứng capsule, phải hiện thông tin.

Thông tin nên được hiển thị theo cấu trúc:

```text
A. Thông tin thuốc
B. Người cần uống
C. Lịch uống
D. Cảnh báo
```

---

# 11. Nội dung bắt buộc phải hiển thị

## 11.1 Thông tin thuốc

```text
Tên thuốc
Hoạt chất nếu có
Hàm lượng
Dạng bào chế
Số lượng còn lại
Đơn vị
Hạn sử dụng
```

## 11.2 Thông tin người cần uống

```text
Tên thành viên
Quan hệ nếu cần
Avatar nếu có
```

## 11.3 Thông tin lịch uống

```text
Liều dùng
Thời gian uống tiếp theo
Lịch hôm nay hoặc lịch gần nhất
```

## 11.4 Cảnh báo an toàn

```text
Dị ứng
Tiền sử phản ứng thuốc
Cảnh báo cần kiểm tra trước khi dùng
```

---

# 12. Cấu trúc panel hiển thị đề xuất

Panel nên hiển thị như sau:

```text
[ Viên thuốc hoặc tên thuốc ]

Amlodipine 5 mg
Còn lại: 20 viên
Hạn dùng: 05/2027

Người cần uống:
Bà Lan

Liều dùng:
1 viên

Lịch uống:
20:00 hôm nay

Cảnh báo:
Không có cảnh báo
```

Nếu có cảnh báo:

```text
⚠ Bà Lan có tiền sử phản ứng với thuốc cùng nhóm. Vui lòng kiểm tra trước khi dùng.
```

---

# 13. Hiển thị cho nhiều người dùng cùng một thuốc

Nếu một thuốc đang được dùng bởi nhiều thành viên, panel phải hiển thị danh sách ngắn gọn.

Ví dụ:

```text
Người cần uống:
- Bà Lan — 08:00 — 1 viên
- Ông Minh — 20:00 — 1 viên
```

Khuyến nghị:

```text
ưu tiên người có lịch gần nhất lên đầu
```

---

# 14. Ưu tiên next dose

Nếu drawer được mở do logic `next dose`, panel nên highlight rõ:

```text
Lần uống tiếp theo
```

Ví dụ:

```text
Tiếp theo: 20:00 hôm nay
```

hoặc:

```text
Đến giờ uống thuốc
```

---

# 15. Cảnh báo dị ứng hoặc phản vệ

Cảnh báo phải hiển thị mềm, cẩn trọng.

Được phép hiển thị:

```text
Có hồ sơ dị ứng hoặc phản ứng thuốc cần kiểm tra.
```

Không nên hiển thị:

```text
Thuốc này chắc chắn gây phản vệ.
```

Nếu backend có dữ liệu trực tiếp đủ rõ, có thể hiển thị:

```text
⚠ Thành viên Bà Lan có tiền sử phản ứng với Amoxicillin.
```

---

# 16. Phù hợp với Simple Mode và 3D Mode

Tính năng phải hoạt động trong cả:

```text
Simple Cabinet Mode
3D Digital Twin Mode
```

## 16.1 Trong 3D Mode

```text
Drawer mở ra
Capsule 3D bay ra
Panel, tooltip hoặc side panel hiện thông tin
```

## 16.2 Trong Simple Mode

Không bắt buộc mô hình 3D phức tạp.

Có thể dùng:

```text
icon viên thuốc hoặc ảnh capsule minh họa bay ra hoặc pop-out
```

để vẫn tạo cảm giác trực quan.

---

# 17. Animation trong 3D Mode

Các bước animation gợi ý:

```text
1. Drawer open
2. Capsule spawn from compartment
3. Capsule move outward
4. Capsule float hoặc hover nhẹ
5. Info panel fade in
```

Khi drawer đóng:

```text
1. Info panel fade out
2. Capsule fade hoặc shrink hoặc move back
3. Drawer close
```

---

# 18. Animation trong Simple Mode

Các bước gợi ý:

```text
1. Ô ngăn thuốc được highlight
2. Icon capsule pop-out nhẹ
3. Thẻ thông tin slide lên hoặc fade in
```

---

# 19. Accessibility / Reduced Motion

Phải có chế độ giảm chuyển động.

Nếu user bật:

```text
Chế độ dễ đọc
hoặc
prefers-reduced-motion
```

thì thay vì hiệu ứng bay ra đầy đủ, dùng:

```text
Capsule xuất hiện nhẹ hoặc fade in
Không bay xa
Không floating animation kéo dài
```

Tức là:

```text
giảm chuyển động nhưng vẫn giữ ý nghĩa
```

---

# 20. Elderly-friendly rules

Để thân thiện với người lớn tuổi:

```text
1. Capsule đủ lớn để dễ nhìn
2. Panel chữ lớn
3. Không dùng hiệu ứng quá nhanh
4. Không ẩn nội dung quan trọng sau quá nhiều click
5. Thông tin chính hiển thị ngay
```

---

# 21. Trạng thái dữ liệu

Tính năng cần xử lý tốt các trạng thái sau:

```text
1. Drawer có thuốc và có lịch uống
2. Drawer có thuốc nhưng chưa gán lịch
3. Drawer trống
4. Drawer có thuốc nhưng cabinet offline
5. Drawer có thuốc nhưng thiếu dữ liệu member
6. Drawer có thuốc và có cảnh báo dị ứng
```

---

# 22. Empty State

Nếu ngăn trống:

```text
Không hiển thị capsule bay ra
```

Thay vào đó hiển thị:

```text
Ngăn này hiện chưa có thuốc.
```

Có thể có CTA:

```text
Gán thuốc cho ngăn
```

nếu user có quyền.

---

# 23. No Schedule State

Nếu ngăn có thuốc nhưng chưa có lịch cụ thể:

```text
vẫn hiển thị capsule và thông tin thuốc
```

Phần lịch hiển thị:

```text
Chưa có lịch uống cụ thể.
```

---

# 24. Offline State

Nếu cabinet offline nhưng user mở thông tin ngăn ở chế độ xem dữ liệu hiện có:

```text
Có thể vẫn hiển thị panel thông tin từ cache hoặc state hiện tại
```

Kèm thông báo:

```text
Thiết bị hiện không kết nối. Dữ liệu có thể chưa được cập nhật mới nhất.
```

Không nên phát animation mở ngăn thực nếu drawer chưa thật sự mở.

---

# 25. Realtime Sync

Khi hệ thống nhận các event:

```text
COMPARTMENT_OPEN
COMPARTMENT_CLOSE
COMPARTMENT_ASSIGN_MEDICATION
COMPARTMENT_UNASSIGN_MEDICATION
STATE_SYNC
CABINET_OFFLINE
CABINET_ONLINE
```

UI phải cập nhật đúng.

Nếu drawer đang được chọn và mở bằng event realtime:

```text
hiệu ứng capsule + panel có thể tự xuất hiện
```

nếu điều đó phù hợp với bối cảnh.

---

# 26. Điều kiện hiển thị tự động panel

Panel thông tin tự động bật khi:

```text
A. User chủ động mở ngăn
B. System mở ngăn cho next dose
```

Nếu drawer mở do đồng bộ state nền mà user không tương tác trực tiếp, có thể cân nhắc:

```text
chỉ highlight drawer
không bật panel full-size ngay
```

để tránh làm phiền.

---

# 27. Logic ưu tiên ngữ cảnh

## Khi user chủ động mở ngăn

```text
Mở panel đầy đủ
```

## Khi system mở ngăn do đến giờ uống

```text
Hiển thị panel với emphasis “Đến giờ uống thuốc”
```

## Khi chỉ sync trạng thái nền

```text
Cập nhật trạng thái drawer
Không nhất thiết bật full panel
```

---

# 28. Data contract cần thiết

Frontend cần lấy dữ liệu tối thiểu sau để hiển thị tính năng:

```text
cabinet_id
compartment.position
compartment.status
compartment.is_open
medication.id
medication.name
medication.active_ingredient
medication.strength
medication.dosage_form
medication.quantity
medication.unit
medication.expiration_date
members[]
schedule_summary[]
warnings[]
next_dose
```

---

# 29. API đề xuất dùng

Tính năng có thể dùng các API hiện có và hoặc API tổng hợp.

API hiện có:

```http
GET /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}
GET /families/{family_id}/cabinets/{cabinet_id}/state
GET /families/{family_id}/members/{member_id}/next-dose
GET /families/{family_id}/members/{member_id}/schedule-day
```

WebSocket:

```text
/ws/families/{family_id}/cabinets/{cabinet_id}
```

---

# 30. API tổng hợp khuyến nghị

Để frontend đơn giản hơn, nên có endpoint tổng hợp:

```http
GET /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/reveal
```

Response ví dụ:

```json
{
  "position": 8,
  "status": "AVAILABLE",
  "is_open": true,
  "medication": {
    "id": 10,
    "name": "Amlodipine",
    "active_ingredient": "Amlodipine",
    "strength": "5 mg",
    "dosage_form": "TABLET",
    "quantity": 20,
    "unit": "TABLET",
    "expiration_date": "2027-05-31"
  },
  "members": [
    {
      "id": 3,
      "full_name": "Nguyen Thi Lan",
      "relationship_label": "Bà",
      "dose_amount": 1,
      "dose_unit": "TABLET",
      "next_schedule": "2026-11-01T20:00:00+07:00"
    }
  ],
  "warnings": [
    {
      "type": "ALLERGY_WARNING",
      "message": "Có hồ sơ dị ứng hoặc phản ứng thuốc cần kiểm tra."
    }
  ]
}
```

---

# 31. Frontend state đề xuất

```ts
type DrawerRevealState = {
  selectedPosition: number | null
  isPanelOpen: boolean
  isAnimating: boolean
  animationMode: "FULL" | "REDUCED"
  revealData: DrawerRevealData | null
  openedBy: "USER" | "SYSTEM" | null
}
```

---

# 32. Thành phần UI đề xuất

## 32.1 3D Mode

```text
CabinetCanvas
CabinetModel
CapsuleFlyout
DrawerInfoPanel
DrawerWarningBadge
```

## 32.2 Simple Mode

```text
CabinetGrid
CompartmentCard
CapsulePopout
MedicationRevealCard
```

---

# 33. Component trách nhiệm

## CapsuleFlyout

Phụ trách:

```text
render capsule
spawn animation
move / fade / hover
reduced motion handling
```

## DrawerInfoPanel

Phụ trách:

```text
render medication info
render member list
render schedule summary
render warnings
```

---

# 34. Visual hierarchy trong panel

Thứ tự thông tin nên là:

```text
1. Tên thuốc
2. Người cần uống và lịch tiếp theo
3. Liều dùng
4. Số lượng còn lại
5. Hạn sử dụng
6. Cảnh báo
```

Không nên để:

```text
thông tin kỹ thuật ít quan trọng lên đầu
```

---

# 35. Nội dung ưu tiên ngắn gọn

Ví dụ tốt:

```text
Amlodipine 5 mg
Bà Lan — 20:00 hôm nay
Liều: 1 viên
Còn lại: 20 viên
```

Sau đó user có thể bấm:

```text
Xem thêm
```

nếu cần nhiều dữ liệu hơn.

---

# 36. CTA trong panel

Có thể có các nút:

```text
Xem chi tiết thuốc
Xem lịch hôm nay
Đóng
```

Nếu có quyền:

```text
Chỉnh sửa thuốc
```

nhưng không nên làm CTA này quá nổi bật so với thông tin chính.

---

# 37. Safety-first wording

Thông điệp cảnh báo nên viết theo hướng hỗ trợ:

Ví dụ:

```text
⚠ Vui lòng kiểm tra thông tin dị ứng trước khi dùng thuốc.
```

hoặc:

```text
⚠ Hệ thống ghi nhận hồ sơ phản ứng thuốc liên quan. Nên kiểm tra lại trước khi sử dụng.
```

---

# 38. Tránh thông điệp gây lo lắng quá mức

Không dùng:

```text
Nguy hiểm! Thuốc này có thể gây sốc phản vệ nghiêm trọng!
```

trừ khi backend thật sự có mức cảnh báo khẩn cấp rất rõ ràng và được kiểm chứng.

---

# 39. Performance requirements

Hiệu ứng phải đủ nhẹ để chạy mượt trên:

```text
Desktop phổ thông
Tablet
Mobile tầm trung
```

Khuyến nghị:

```text
1 capsule object reuse
animation đơn giản
không dùng particle quá nặng
không spawn nhiều object
```

---

# 40. Caching & preload

Để animation mượt:

```text
preload capsule asset
preload drawer info panel styles
cache reveal data ngắn hạn nếu phù hợp
```

---

# 41. Error handling

Nếu lấy dữ liệu reveal thất bại:

```text
vẫn có thể mở drawer animation
```

nhưng panel hiển thị:

```text
Không thể tải thông tin thuốc lúc này.
[ Thử lại ]
```

Nếu asset capsule load lỗi:

```text
fallback sang icon capsule 2D
```

---

# 42. Logging & analytics

Có thể log các event UI sau:

```text
drawer_reveal_opened
drawer_reveal_closed
capsule_animation_played
drawer_reveal_failed
warning_panel_viewed
```

Mục đích:

```text
theo dõi mức sử dụng
tối ưu UX sau này
```

---

# 43. Test scenarios

## 43.1 Happy path

```text
Drawer có thuốc
Có member
Có schedule
Open drawer
Capsule bay ra
Panel hiển thị đúng
```

## 43.2 Empty compartment

```text
Ngăn trống
Không hiển thị capsule
Hiển thị empty state
```

## 43.3 Multiple members

```text
Một thuốc cho 2 thành viên
Panel hiển thị đúng danh sách
```

## 43.4 Warning present

```text
Có allergy hoặc drug reaction
Hiển thị warning đúng
```

## 43.5 Reduced motion

```text
Bật reduced motion
Animation nhẹ hơn
Vẫn hiểu được luồng
```

## 43.6 Offline cabinet

```text
Cabinet offline
User vẫn xem được data hiện có nếu đã tải
Hiển thị cảnh báo trạng thái
```

## 43.7 Realtime open event

```text
System gửi COMPARTMENT_OPEN
UI update đúng
```

---

# 44. Acceptance Criteria

Tính năng được chấp nhận khi:

- [ ] Khi mở ngăn có hiệu ứng viên thuốc con nhộng bay ra hoặc xuất hiện minh họa rõ ràng.
- [ ] Hiệu ứng không quá nhanh, không gây rối mắt.
- [ ] Có hiển thị tên thuốc.
- [ ] Có hiển thị số lượng thuốc còn lại.
- [ ] Có hiển thị người cần uống thuốc.
- [ ] Có hiển thị lịch uống hoặc thời gian uống gần nhất hoặc tiếp theo.
- [ ] Có hiển thị liều dùng cơ bản.
- [ ] Có hiển thị cảnh báo dị ứng hoặc phản ứng thuốc nếu có.
- [ ] Tính năng hoạt động cả ở Simple Mode và 3D Mode.
- [ ] Có hỗ trợ reduced motion hoặc accessibility.
- [ ] Có xử lý ngăn trống.
- [ ] Có xử lý drawer có thuốc nhưng chưa có lịch.
- [ ] Có xử lý cabinet offline.
- [ ] Có thể nhận update từ WebSocket.
- [ ] Không tự động trừ tồn kho.
- [ ] Không tự động xác nhận đã uống thuốc.
- [ ] Dữ liệu hiển thị đúng với state backend.
- [ ] Trải nghiệm thân thiện với người dùng, đặc biệt người lớn tuổi.

---

# 45. Definition of Done

Tính năng được xem là hoàn thành khi demo được chuỗi sau:

```text
User mở Cabinet hoặc Digital Twin
 ↓
Chọn ngăn 08
 ↓
Ngăn mở ra
 ↓
Capsule bay ra nhẹ nhàng
 ↓
Panel hiện:
- Amlodipine 5 mg
- Còn lại 20 viên
- Bà Lan
- Liều 1 viên
- 20:00 hôm nay
 ↓
Nếu có warning thì hiển thị warning
 ↓
User đóng panel hoặc đóng ngăn
```

và toàn bộ luồng hoạt động tốt ở cả:

```text
Simple Mode
3D Mode
Realtime mode
Reduced motion mode
```

---

# 46. Deliverables

Sau khi hoàn thiện đặc tả này, nên có:

```text
docs/frontend/
└── FEATURE_DRAWER_OPEN_CAPSULE_REVEAL.md
```

Code gợi ý:

```text
frontend/src/features/cabinet/
├── reveal/
│   ├── types.ts
│   ├── hooks.ts
│   ├── animation.ts
│   ├── api.ts
│   └── selectors.ts
│
frontend/src/components/cabinet/
├── CapsuleFlyout.tsx
├── DrawerInfoPanel.tsx
├── CapsulePopout.tsx
├── MedicationRevealCard.tsx
└── DrawerWarningBadge.tsx
```

---

# 47. Kết luận

> **Tính năng “mở ngăn → viên thuốc con nhộng bay ra → hiện thông tin thuốc và người dùng thuốc” là một điểm nhấn trải nghiệm rất tốt cho PharmaMind AI. Nếu được thiết kế đúng cách, nó vừa trực quan, hiện đại, vừa thực sự hữu ích cho người dùng trong gia đình, đặc biệt là người lớn tuổi và người chăm sóc.**

Nguyên tắc cốt lõi:

```text
Visual for clarity
Animation with purpose
Simple before flashy
Safety before decoration
Accessible for all users
```
