# PharmaMind AI — TASK 10 SPECIFICATION

# TASK 10 — Digital Twin 3D

## 1. Mục tiêu

Task 10 xây dựng lớp **Digital Twin 3D** cho PharmaMind AI.

Sau Task 09, hệ thống đã có:

```text
User
Authentication
Family
Family Member
Medication
Prescription
Medication Schedule
Smart Cabinet Mock / Hardware Simulator
Cabinet
9 Compartments
Cabinet Events
Realtime WebSocket
```

Task 10 sẽ bổ sung lớp hiển thị và đồng bộ mô hình 3D của tủ thuốc thông minh trong App/Web.

Hệ thống sẽ có thể:

```text
Hiển thị mô hình 3D của tủ thuốc
Hiển thị đúng 9 ngăn thuốc
Hiển thị trạng thái mở / đóng của từng ngăn
Hiển thị thuốc đang được gán trong từng ngăn
Hiển thị chi tiết thuốc khi chọn ngăn
Highlight ngăn cần lấy thuốc tiếp theo
Đồng bộ trạng thái realtime từ Backend / WebSocket
Mô phỏng drawer open animation
Tạo nền tảng để kết nối mô hình 3D với phần cứng thật sau này
```

Mục tiêu cuối cùng:

> **Người dùng có thể quan sát tủ thuốc số hóa (Digital Twin) một cách trực quan, dễ hiểu, đồng bộ với trạng thái Cabinet ngoài đời thực hoặc Cabinet Simulator, và có thể tương tác để xem thông tin thuốc trong từng ngăn.**

---

# 2. Điều kiện tiên quyết

Chỉ bắt đầu Task 10 khi Task 09 đã hoàn thành.

Phải test được chuỗi:

```text
MedicationSchedule
   ↓
Next Dose
   ↓
Cabinet
   ↓
Compartment
   ↓
Medication Assignment
   ↓
Cabinet Event
   ↓
Realtime WebSocket
```

---

# 3. Phạm vi Task 10

Task 10 bao gồm:

```text
1. Digital Twin UI Architecture
2. Cabinet 3D Asset Specification
3. Compartment Object Mapping
4. 3D Viewer Integration
5. Cabinet Scene State
6. Compartment Selection
7. Drawer Open / Close Animation
8. Medication Visual Placeholder 3D
9. Compartment Information Panel
10. Highlight Next Dose
11. Realtime State Sync qua WebSocket
12. Fallback Polling State Sync
13. 3D Interaction Rules
14. Responsive Layout
15. Performance Optimization
16. Error / Offline States
17. Family-scoped Frontend Authorization Integration
18. Test Scenarios
19. Deliverable Contract cho 3D Asset
20. UI / API Integration Contract
```

Task 10 không bao gồm:

```text
Tạo firmware ESP32 thật
Điều khiển motor thật
AR / VR
Physics simulation phức tạp
Photorealistic manufacturing CAD
Medication taken confirmation
Inventory deduction
AI Pharmacist
```

---

# 4. Ý tưởng tổng quan của Digital Twin

Digital Twin là bản sao số của tủ thuốc thông minh.

Nó phải phản ánh:

```text
Trạng thái tủ
Trạng thái từng ngăn
Thuốc gán vào từng ngăn
Ngăn nào đang mở
Ngăn nào sắp đến giờ dùng
Ngăn nào đang được nhắc lấy thuốc
```

Digital Twin **không phải** nơi tự tạo business data mới.

Digital Twin chỉ:

```text
Render
Display
Animate
Reflect current state
```

State phải lấy từ:

```text
Cabinet API
Compartment API
Medication API
Schedule / Next Dose API
WebSocket Event
```

---

# 5. Mô hình thực tế cần tham chiếu

Hình ảnh tham chiếu thực tế cho Task 10 là concept tủ thuốc như ảnh bạn đã cung cấp.

Các đặc điểm trực quan cần giữ làm chuẩn tham chiếu:

```text
1. Kiểu dáng hộp tủ thuốc gia đình nhỏ gọn
2. Thân tủ bo góc mềm
3. Màu sắc chủ đạo trắng + xanh mint / xanh ngọc nhạt
4. Có tay xách / quai phía trên
5. Phía trên có màn hình hiển thị ngang
6. Có 9 ngăn thuốc bố trí dạng lưới 3 × 3
7. Mỗi ngăn có cửa trong suốt hoặc bán trong suốt
8. Mỗi ngăn có nhãn thuốc hiển thị phía dưới
9. Tổng thể thân thiện, hiện đại, dễ dùng trong gia đình
```

---

# 6. Yêu cầu về độ giống hình ảnh tham chiếu

Task 10 không yêu cầu tái tạo chính xác 100% về công nghiệp / CAD.

Nhưng mô hình 3D phải **gợi đúng cảm giác sản phẩm thực tế** như ảnh tham chiếu:

```text
Tủ thuốc gia đình hiện đại
9 ngăn trực quan
Màn hình điều khiển phía trên
Thiết kế gọn, thân thiện
```

Tức là:

```text
ưu tiên đúng concept sản phẩm,
không bắt buộc đúng đến từng mm hoặc từng chi tiết cơ khí.
```

---

# 7. Mục tiêu hiển thị của mô hình 3D

Mô hình 3D phục vụ:

```text
Người dùng dễ hình dung tủ thuốc thật
Dễ biết thuốc nằm ở ngăn nào
Dễ thấy ngăn nào đang mở
Dễ thấy ngăn nào cần lấy tiếp theo
Dễ click / tap để xem chi tiết thuốc
```

Không phải phục vụ:

```text
thiết kế cơ khí chính xác
mô phỏng nội lực
mô phỏng sản xuất
```

---

# 8. Thành phần chính của Task 10

Task 10 gồm 4 phần logic:

```text
A. 3D Asset
B. 3D Viewer
C. State Mapping
D. Realtime Sync
```

---

# 9. A. 3D Asset

Cần chuẩn bị mô hình 3D của Cabinet gồm:

```text
Cabinet body
Top screen block
Handle
9 drawer / compartment objects
Mỗi drawer có object độc lập
```

Định dạng khuyến nghị:

```text
glTF / GLB
```

---

# 10. B. 3D Viewer

Trong frontend cần có viewer 3D để:

```text
render model
rotate
zoom
pan (nếu cần)
click object
highlight object
play simple open/close animation
```

---

# 11. C. State Mapping

Frontend phải map dữ liệu backend vào mô hình 3D:

```text
Compartment position 1 → drawer_01
Compartment position 2 → drawer_02
...
Compartment position 9 → drawer_09
```

---

# 12. D. Realtime Sync

Khi Backend gửi WebSocket event:

```text
COMPARTMENT_OPEN
COMPARTMENT_CLOSE
CABINET_ONLINE
CABINET_OFFLINE
STATE_SYNC
```

UI phải update gần realtime.

---

# 13. Kiến trúc tổng quát

```text
Backend Cabinet API
     ↓
Frontend State Store
     ↓
3D Scene Controller
     ↓
3D Viewer / Model
     ↓
Interaction Layer
     ↓
Info Panel / Status Panel
```

---

# 14. Kiến trúc dữ liệu UI

Frontend nên tách state:

```text
cabinetState
compartmentStateMap
selectedCompartment
nextDoseInfo
connectionState
viewerState
```

---

# 15. Công nghệ frontend khuyến nghị

Nếu dùng web app:

```text
React
TypeScript
Three.js
@react-three/fiber
@react-three/drei
Zustand hoặc Redux Toolkit
```

Nếu dùng mobile app:

```text
React Native
```

thì 3D phức tạp hơn.

Giai đoạn MVP Task 10 khuyến nghị:

> **Ưu tiên Web Digital Twin trước**, sau đó nhúng hoặc tối ưu lại cho mobile sau.

---

# 16. Vì sao nên làm Web trước?

Bởi vì:

```text
3D trên web dễ debug hơn
Three.js hệ sinh thái mạnh
Dễ kiểm tra object mapping
Dễ test realtime
Dễ trình diễn demo cho cuộc thi / startup
```

---

# 17. Yêu cầu về Asset 3D

Phải có:

```text
Một file GLB chính
tên ví dụ: pharmamind_cabinet.glb
```

Model phải chứa object names ổn định:

```text
cabinet_body
top_screen
handle
drawer_01
drawer_02
drawer_03
drawer_04
drawer_05
drawer_06
drawer_07
drawer_08
drawer_09
```

Nếu có object text / icon riêng thì nên đặt tên rõ ràng.

---

# 18. Object Naming Contract

Đây là hợp đồng bắt buộc giữa 3D asset và frontend code.

Frontend sẽ dựa vào tên object.

Do đó phải thống nhất:

```text
drawer_01
drawer_02
...
drawer_09
```

Không dùng tên ngẫu nhiên như:

```text
Cube.001
Mesh_34
Object_17
```

---

# 19. Drawer Coordinate Mapping

Mỗi drawer cần có:

```text
position index
display label
3D object name
```

Ví dụ:

```text
1 → "Ngăn 01" → drawer_01
2 → "Ngăn 02" → drawer_02
...
9 → "Ngăn 09" → drawer_09
```

---

# 20. Mô tả visual của cabinet 3D

Cabinet 3D nên có:

```text
Thân tủ màu trắng hoặc trắng ngà
Viền xanh mint / xanh ngọc nhạt
Tay xách phía trên
Màn hình ngang ở phía trên mặt trước
9 ngăn thuốc hình chữ nhật nhỏ
Cửa ngăn hơi trong suốt
Góc bo mềm
Phong cách hiện đại, tối giản, thân thiện
```

---

# 21. Mô tả visual của drawer / compartment

Mỗi ngăn nên:

```text
Dễ phân biệt
Có mặt trước rõ ràng
Có thể mở ra trước hoặc kéo ra ngắn
Có vùng hiển thị trạng thái
Có thể highlight khi selected / next dose
```

---

# 22. Không cần mô hình viên thuốc quá chính xác

Bên trong ngăn có thể có mô hình thuốc 3D dạng minh họa:

```text
vỉ thuốc
lọ thuốc
hộp thuốc nhỏ
viên nang đơn giản
```

Không cần:

```text
đúng màu thực tế
đúng shape y khoa 100%
đúng packaging thật
```

Chỉ cần:

```text
người dùng dễ quan sát và hình dung.
```

---

# 23. Medication Visual Placeholder

Khuyến nghị tạo các visual template theo dosage form:

```text
TABLET      → viên nén / vỉ thuốc đơn giản
CAPSULE     → viên nang đơn giản
SYRUP       → chai nhỏ
SACHET      → gói thuốc nhỏ
CREAM/GEL   → tuýp nhỏ
PATCH       → miếng dán nhỏ
INJECTION   → lọ / ống nhỏ
OTHER       → hộp thuốc generic
```

---

# 24. Mô hình viên thuốc không phải source of truth

3D placeholder chỉ để minh họa.

Thông tin thật phải lấy từ data:

```text
Medication name
Quantity
Unit
Expiration date
Schedule
```

Không suy ngược dữ liệu từ 3D model.

---

# 25. UI Layout đề xuất

Trang Digital Twin nên gồm:

```text
A. 3D Viewer (trái / giữa)
B. Information Panel (phải)
C. Status Bar / Summary (trên)
D. Event / Connection indicator
```

---

# 26. Status Bar

Status bar có thể hiển thị:

```text
Cabinet Name
Connection status: Online / Offline
Last sync time
Next dose summary
Selected family member (nếu có)
```

---

# 27. Information Panel

Khi chưa chọn ngăn:

```text
Hiển thị overview của cabinet
Số ngăn đang có thuốc
Ngăn đang mở
Ngăn sắp đến giờ dùng
```

Khi chọn ngăn:

```text
Thông tin chi tiết ngăn
Thông tin thuốc trong ngăn
Lịch dùng gần nhất
Số lượng còn lại
Hạn sử dụng
Cảnh báo nếu có
```

---

# 28. Thông tin khi chọn ngăn

Khi click / tap vào một ngăn, panel nên hiển thị:

```text
Tên ngăn: Ngăn 01
Tên thuốc
Hoạt chất
Hàm lượng
Dạng bào chế
Số lượng còn lại
Đơn vị
Hạn sử dụng
Trạng thái ngăn
Trạng thái mở / đóng
Thành viên sử dụng
Lần dùng tiếp theo
Liều dùng
```

---

# 29. Liên kết với yêu cầu ban đầu của ứng dụng

Task 10 phải hỗ trợ đúng ý tưởng người dùng đã nêu:

```text
Khi ấn vào từng ngăn thuốc sẽ có mô hình viên thuốc 3D minh họa
Khi ấn vào ngăn sẽ hiện thông tin:
- số lượng thuốc còn trong ngăn
- lịch trình uống thuốc đó theo đơn của từng thành viên trong gia đình
- thông tin cơ bản về thuốc
- cảnh báo phản vệ nếu có của thành viên trong gia đình
```

---

# 30. Thông tin lịch trình theo từng thành viên

Nếu một thuốc gắn với nhiều FamilyMember, panel phải hiển thị theo dạng danh sách:

```text
Bà Lan
- 08:00 mỗi ngày
- liều: 1 viên

Ông Minh
- 20:00 mỗi ngày
- liều: 1 viên
```

---

# 31. Cảnh báo phản vệ / dị ứng

Khi selected compartment chứa medication liên kết với member có:

```text
AllergyProfile
DrugReactionHistory
```

UI có thể hiển thị cảnh báo mềm:

```text
Cảnh báo: Thành viên A có tiền sử phản ứng với hoạt chất / thuốc liên quan
```

Lưu ý:

Task 10 chỉ hiển thị dữ liệu đã có.
Không tự suy luận y khoa mới.

---

# 32. Giao diện cảnh báo

Cảnh báo nên dùng:

```text
icon warning
màu vàng / cam / đỏ
text ngắn gọn
```

Ví dụ:

```text
⚠ Thành viên Bà Lan có tiền sử phản ứng với Amoxicillin.
```

Hoặc:

```text
⚠ Có hồ sơ dị ứng thuốc cần kiểm tra trước khi dùng.
```

---

# 33. 3D Interaction Rules

Người dùng cần có thể:

```text
Rotate model
Zoom in / out
Select drawer
Reset camera
```

Có thể cân nhắc:

```text
Double click drawer → focus
Click outside → clear selection
```

---

# 34. Camera mặc định

Camera ban đầu nên đặt ở góc:

```text
front perspective hơi chếch
```

để nhìn rõ:

```text
màn hình trên
9 ngăn
tổng thể hình khối
```

Không nên để camera chính diện quá phẳng hoặc quá từ trên xuống.

---

# 35. Selection Behavior

Khi chọn ngăn:

```text
drawer được highlight
camera có thể focus nhẹ
panel cập nhật theo ngăn
nếu ngăn đang open thì animation hiển thị đúng
```

---

# 36. Drawer Open Animation

Animation đơn giản là đủ.

Ví dụ:

```text
drawer trượt ra phía trước 10–20%
```

hoặc:

```text
cửa ngăn bật mở
```

Không cần animation cơ khí quá phức tạp.

---

# 37. Animation Source

Animation có thể:

```text
A. baked trong GLB
hoặc
B. code-driven trong frontend
```

Khuyến nghị MVP:

> **Code-driven animation** để dễ điều khiển từ WebSocket state.

---

# 38. Compartment State → 3D Visual Mapping

Ví dụ:

```text
EMPTY      → màu trung tính
AVAILABLE  → màu bình thường
OPEN       → drawer mở
WARNING    → highlight vàng/cam
DOSE_DUE   → highlight xanh / nhấp nháy nhẹ
OFFLINE    → dim / xám
```

---

# 39. Next Dose Highlight

Frontend cần gọi:

```text
GET /families/{family_id}/members/{member_id}/next-dose
```

hoặc API tổng hợp phù hợp.

Ngăn tương ứng với medication của `next dose` nên được:

```text
highlight
pulse nhẹ
badge “Tiếp theo”
```

---

# 40. Nhiều thành viên trong gia đình

Nếu một cabinet phục vụ nhiều thành viên, UI cần có cách lọc:

```text
All members
Theo từng member
```

Ví dụ dropdown:

```text
Tất cả
Bà Lan
Ông Minh
Nguyễn Văn A
```

---

# 41. Cabinet Scene State

Frontend nên có kiểu dữ liệu state như:

```ts
type CabinetSceneState = {
  cabinetId: number
  cabinetStatus: "ONLINE" | "OFFLINE" | "ERROR" | "ARCHIVED"
  compartments: Record<number, CompartmentSceneState>
  selectedPosition: number | null
  nextDosePosition: number | null
  connectionState: "CONNECTED" | "DISCONNECTED" | "RECONNECTING"
  lastSyncAt: string | null
}
```

---

# 42. Compartment Scene State

Ví dụ:

```ts
type CompartmentSceneState = {
  position: number
  isOpen: boolean
  status: string
  medication: {
    id: number
    name: string
    strength?: string
    dosageForm?: string
    quantity?: number
    unit?: string
    expirationDate?: string | null
  } | null
}
```

---

# 43. State Initialization

Khi mở trang Digital Twin:

```text
Load cabinet detail
Load cabinet state
Load compartments
Load next-dose summary
Render initial model state
Connect WebSocket
```

---

# 44. Realtime Sync Strategy

Thứ tự khởi tạo khuyến nghị:

```text
1. REST API for initial state
2. WebSocket for realtime updates
3. Polling fallback nếu WebSocket lỗi
```

---

# 45. Fallback Polling

Nếu WebSocket mất kết nối:

```text
poll cabinet state mỗi 10–30 giây
```

cho đến khi reconnect.

---

# 46. WebSocket Events cần hỗ trợ ở frontend

Ít nhất gồm:

```text
CABINET_ONLINE
CABINET_OFFLINE
COMPARTMENT_OPEN
COMPARTMENT_CLOSE
COMPARTMENT_ASSIGN_MEDICATION
COMPARTMENT_UNASSIGN_MEDICATION
STATE_SYNC
DEVICE_ERROR
```

---

# 47. Event Handling Rules

Ví dụ:

## CABINET_ONLINE

```text
cabinet status → ONLINE
connection indicator → online
last_sync_at update
```

## COMPARTMENT_OPEN

```text
compartment.isOpen = true
compartment.status = OPEN
play drawer open animation
```

## COMPARTMENT_CLOSE

```text
compartment.isOpen = false
restore visual status
```

---

# 48. Offline UI State

Nếu cabinet offline:

```text
Hiển thị badge OFFLINE
Disable thao tác open/close từ UI (nếu có)
Model có thể làm xám nhẹ
Panel hiện thông báo “Thiết bị hiện không kết nối”
```

---

# 49. Error UI State

Nếu device error:

```text
Hiển thị banner warning
Cho phép xem thông tin ngăn nhưng cảnh báo trạng thái
```

---

# 50. Responsive Design

Task 10 nên hỗ trợ tối thiểu:

```text
Desktop / Laptop
Tablet
```

Mobile có thể hỗ trợ sau, hoặc hỗ trợ ở mức:

```text
xem / xoay / chọn ngăn cơ bản
```

Desktop vẫn là ưu tiên để demo.

---

# 51. Performance Budget

Mô hình GLB phải tối ưu vừa phải.

Khuyến nghị:

```text
1 model GLB duy nhất
polycount vừa phải
texture tối ưu
không quá nhiều object rời không cần thiết
```

Mục tiêu:

```text
Load nhanh
Render mượt trên laptop phổ thông
```

---

# 52. Không over-engineer visual

MVP Task 10 không cần:

```text
bóng đổ siêu thực
PBR quá nặng
hiệu ứng vật lý phức tạp
animation nhiều lớp
```

Ưu tiên:

```text
ổn định
dễ dùng
đúng trạng thái
dễ demo
```

---

# 53. Data Contract giữa Backend và Frontend

Frontend cần ít nhất các field:

```text
cabinet_id
cabinet_status
compartment.position
compartment.is_open
compartment.status
compartment.medication
medication.name
medication.strength
medication.dosage_form
medication.quantity
medication.unit
medication.expiration_date
next_dose
member schedule summaries
warning flags
```

---

# 54. Endpoint frontend sẽ dùng

Task 10 phụ thuộc các API từ các task trước:

```http
GET /families/{family_id}/cabinets/{cabinet_id}
GET /families/{family_id}/cabinets/{cabinet_id}/state
GET /families/{family_id}/cabinets/{cabinet_id}/compartments
GET /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}
GET /families/{family_id}/cabinets/{cabinet_id}/events

GET /families/{family_id}/members/{member_id}/next-dose
GET /families/{family_id}/members/{member_id}/schedule-day
```

WebSocket:

```text
/ws/families/{family_id}/cabinets/{cabinet_id}
```

---

# 55. Nếu cần API tổng hợp riêng

Có thể thêm API frontend-friendly:

```http
GET /families/{family_id}/cabinets/{cabinet_id}/digital-twin
```

Response tổng hợp:

```text
cabinet state
compartments
medication summaries
next dose
warning summaries
```

Điều này rất hữu ích cho frontend.

---

# 56. Digital Twin Summary API

Response đề xuất:

```json
{
  "cabinet": {
    "id": 1,
    "name": "Tủ thuốc gia đình",
    "status": "ONLINE",
    "hardware_mode": "SIMULATOR"
  },
  "compartments": [
    {
      "position": 1,
      "status": "AVAILABLE",
      "is_open": false,
      "medication": {
        "id": 10,
        "name": "Amlodipine",
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
          "next_schedule": "2026-11-01T20:00:00+07:00"
        }
      ],
      "warnings": [
        "LOW_STOCK"
      ]
    }
  ]
}
```

---

# 57. Frontend Folder Structure đề xuất

```text
frontend/
│
├── src/
│   ├── app/
│   ├── pages/
│   │   └── digital-twin/
│   │       ├── DigitalTwinPage.tsx
│   │       ├── DigitalTwinLayout.tsx
│   │       ├── CabinetCanvas.tsx
│   │       ├── CabinetModel.tsx
│   │       ├── CompartmentMesh.tsx
│   │       ├── InfoPanel.tsx
│   │       ├── StatusBar.tsx
│   │       └── hooks.ts
│   │
│   ├── components/
│   │   ├── cabinet/
│   │   ├── common/
│   │   └── medication/
│   │
│   ├── features/
│   │   ├── digitalTwin/
│   │   │   ├── api.ts
│   │   │   ├── store.ts
│   │   │   ├── selectors.ts
│   │   │   ├── types.ts
│   │   │   └── websocket.ts
│   │   │
│   │   └── cabinet/
│   │       └── ...
│   │
│   ├── assets/
│   │   └── models/
│   │       └── pharmamind_cabinet.glb
│   │
│   └── utils/
│       └── ...
```

---

# 58. Asset Folder Structure đề xuất

```text
assets/
└── models/
    ├── pharmamind_cabinet.glb
    ├── medication/
    │   ├── tablet_placeholder.glb
    │   ├── bottle_placeholder.glb
    │   ├── blister_placeholder.glb
    │   └── generic_box_placeholder.glb
    └── textures/
```

---

# 59. 3D Controller Layer

Nên có lớp controller để map state vào scene:

```text
updateCabinetStatus()
updateCompartmentOpen()
updateCompartmentMedication()
highlightNextDose()
clearSelection()
focusDrawer()
resetView()
```

---

# 60. Scene Controller Rule

Không để UI component lẫn quá nhiều business logic.

Nên tách:

```text
API fetching
State store
Scene controller
Presentation component
```

---

# 61. Bảo mật / Authorization phía frontend

Frontend không tự tin rằng user được phép truy cập.

Mỗi trang Digital Twin phải phụ thuộc:

```text
JWT auth
Family membership
Cabinet fetch success
```

Nếu backend trả unauthorized / not found:

```text
redirect / show access denied
```

---

# 62. Error Handling

Cần xử lý:

```text
Model load fail
API fail
WebSocket disconnect
Cabinet not found
Cabinet offline
Compartment without medication
Missing next dose
```

---

# 63. Empty State

Nếu compartment trống:

```text
Hiển thị trạng thái Empty
Panel ghi “Chưa gán thuốc cho ngăn này”
Có thể hiển thị placeholder object mờ hoặc không hiển thị thuốc
```

---

# 64. Demo Flow mong muốn

Demo lý tưởng:

```text
User mở Digital Twin
  ↓
Thấy mô hình 3D của tủ thuốc
  ↓
Ngăn 08 được highlight do là lần dùng tiếp theo
  ↓
User click ngăn 08
  ↓
Panel hiện:
- Amlodipine 5 mg
- Còn 20 viên
- Uống 20:00 hôm nay
- Thành viên: Bà Lan
  ↓
Từ simulator / hardware mock gửi event mở ngăn
  ↓
Ngăn 08 mở ra trên mô hình 3D
  ↓
UI cập nhật realtime
```

---

# 65. Test Scenarios — Frontend Logic

Cần test:

```text
Load initial state
Map 9 drawers đúng
Select drawer
Open animation
Close animation
WebSocket event updates state
Offline state UI
Next dose highlight
Compartment panel detail
```

---

# 66. Test — Drawer Mapping

Phải đảm bảo:

```text
position 1 → drawer_01
...
position 9 → drawer_09
```

không bị lệch.

---

# 67. Test — Selected Compartment Panel

Khi chọn ngăn 03:

```text
panel phải hiện đúng thông tin ngăn 03
không lấy nhầm ngăn khác
```

---

# 68. Test — WebSocket Open Event

Nhận event:

```json
{
  "type": "COMPARTMENT_OPEN",
  "cabinet_id": 1,
  "compartment": {
    "position": 8
  }
}
```

Expected:

```text
drawer_08 mở animation
state update
panel update nếu đang selected
```

---

# 69. Test — Next Dose Highlight

Nếu next dose thuộc ngăn 02:

```text
drawer_02 được highlight
```

Nếu user đã chọn ngăn 05:

```text
drawer_05 vẫn selected
drawer_02 vẫn có secondary indicator
```

---

# 70. Test — Offline Transition

Event:

```text
CABINET_OFFLINE
```

Expected:

```text
status bar update
visual dim
interaction hạn chế phù hợp
```

---

# 71. Test — Empty Compartment

Chọn ngăn trống:

```text
panel hiển thị empty state
không crash
```

---

# 72. Test — Missing Model Asset

Nếu GLB load lỗi:

```text
show fallback placeholder UI
show error message
không làm toàn trang bị trắng
```

---

# 73. Test — Reconnect

Nếu WebSocket reconnect:

```text
UI phải resync state
```

Có thể:

```text
refetch cabinet state sau reconnect
```

---

# 74. Tích hợp với hình ảnh thật

Ảnh tủ thuốc thực tế mà bạn gửi sẽ được dùng như tài liệu chuẩn khi:

```text
Thiết kế GLB model
Xác định silhouette / shape
Xác định bố cục 9 ngăn
Xác định vị trí màn hình phía trên
Xác định cảm giác thẩm mỹ sản phẩm
```

Task 10 phải ghi rõ điều này trong tài liệu dự án.

---

# 75. Không cần copy nguyên xi mọi chi tiết

Mô hình 3D nên:

```text
bám sát concept
giữ tinh thần thiết kế
giữ nhận diện sản phẩm
```

Không cần:

```text
sao chép ảnh 2D một cách cứng nhắc
```

---

# 76. Asset Deliverable Contract

Team 3D hoặc người dựng model cần giao:

```text
1. File GLB chính
2. Danh sách object name
3. Screenshot preview các góc
4. Tài liệu mapping drawer positions
5. Quy ước animation hoặc pivot points
```

---

# 77. Pivot / Origin Rules

Mỗi drawer nên có pivot / origin hợp lý để mở kéo ra dễ dàng.

Ví dụ:

```text
origin của drawer đặt gần tâm hoặc phía sau ngăn
```

Nếu open animation là translate thì cần axis thống nhất.

---

# 78. Chế độ hiển thị đơn giản

Có thể hỗ trợ:

```text
Simple 2D-like mode / Minimal mode
```

cho máy yếu hoặc demo nhanh:

```text
không animation phức tạp
không medication placeholder chi tiết
```

Nhưng đây chỉ là nice-to-have.

---

# 79. Logging / Analytics

Có thể log frontend analytics cơ bản:

```text
drawer_selected
camera_reset
websocket_reconnected
panel_opened
```

Không bắt buộc trong Task 10.

---

# 80. API / Frontend Integration Contract

Task 10 cần chốt rõ:

```text
field names
status enums
event types
drawer mapping
```

để tránh mismatch giữa frontend 3D và backend cabinet service.

---

# 81. Acceptance Criteria

Task 10 chỉ hoàn thành khi:

- [ ] Có đặc tả đầy đủ cho mô hình 3D Cabinet.
- [ ] Có quy ước object names cho 9 drawers.
- [ ] Có mapping position → drawer object rõ ràng.
- [ ] Có thiết kế UI layout cho Digital Twin page.
- [ ] Có cơ chế load state ban đầu từ API.
- [ ] Có cơ chế WebSocket realtime update.
- [ ] Có cơ chế fallback polling khi mất WebSocket.
- [ ] Có selection cho từng compartment.
- [ ] Có drawer open/close animation logic.
- [ ] Có panel hiển thị thông tin thuốc trong ngăn.
- [ ] Có hiển thị số lượng còn lại.
- [ ] Có hiển thị lịch dùng theo từng thành viên.
- [ ] Có hiển thị thông tin cơ bản của thuốc.
- [ ] Có hiển thị cảnh báo phản vệ / dị ứng nếu có.
- [ ] Có highlight ngăn của next dose.
- [ ] Có xử lý offline / error state.
- [ ] Có tối ưu performance ở mức MVP.
- [ ] Có data contract rõ giữa backend và frontend.
- [ ] Có test scenarios rõ ràng.
- [ ] Có chỉ rõ mô hình 3D tham chiếu theo hình ảnh tủ thuốc thực tế.
```

---

# 82. Definition of Done

Task 10 được đánh dấu:

```text
DONE
```

khi demo được chuỗi:

```text
Open Digital Twin Page
  ↓
Load Cabinet 3D
  ↓
Load initial state
  ↓
Highlight next dose drawer
  ↓
Select a drawer
  ↓
Show medication / schedule / warning info
  ↓
Receive websocket open event
  ↓
Drawer opens in 3D
  ↓
Close event updates 3D again
```

và trải nghiệm đủ ổn định cho demo sản phẩm.

---

# 83. Deliverables

Sau Task 10 cần có:

```text
docs/tasks/
└── TASK_10_DIGITAL_TWIN_3D.md

frontend/src/pages/digital-twin/
├── DigitalTwinPage.tsx
├── DigitalTwinLayout.tsx
├── CabinetCanvas.tsx
├── CabinetModel.tsx
├── CompartmentMesh.tsx
├── InfoPanel.tsx
├── StatusBar.tsx
└── hooks.ts

frontend/src/features/digitalTwin/
├── api.ts
├── store.ts
├── selectors.ts
├── types.ts
└── websocket.ts

frontend/src/assets/models/
└── pharmamind_cabinet.glb

assets/models/
├── pharmamind_cabinet.glb
└── medication/
    ├── tablet_placeholder.glb
    ├── bottle_placeholder.glb
    ├── blister_placeholder.glb
    └── generic_box_placeholder.glb
```

---

# 84. Không thực hiện trong Task 10

Không làm:

```text
AR / VR
Game engine phức tạp
ESP32 firmware
MQTT broker production
Taken confirmation
Inventory deduction
Adherence scoring
AI interpretation
OCR
```

---

# 85. Gợi ý Task tiếp theo sau Task 10

Sau Task 10, roadmap có thể mở rộng theo các nhánh:

```text
TASK 11 — Medication Event & Taken Confirmation
TASK 12 — Reminder / Notification Engine
TASK 13 — MQTT / ESP32 Hardware Integration
TASK 14 — AI Pharmacist & Drug Knowledge Layer
TASK 15 — OCR / Smart Ingestion
```

---

# 86. Roadmap hiện tại

```text
TASK 01
Project Initialization
        ↓
TASK 02
Database Foundation
        ↓
TASK 03
Authentication & User
        ↓
TASK 04
Family Management
        ↓
TASK 05
Family Member & Health Profile
        ↓
TASK 06
Medication Management
        ↓
TASK 07
Prescription Management
        ↓
TASK 08
Medication Schedule
        ↓
TASK 09
Smart Cabinet Mock / Hardware Simulator
        ↓
TASK 10
Digital Twin 3D
```

---

# 87. Nguyên tắc chuyển sang giai đoạn tiếp theo

Không chuyển sang Task 11 hoặc tích hợp phần cứng thật nếu chưa chứng minh được:

```text
CABINET API
  ↓
DRAWER MAPPING
  ↓
3D VIEWER
  ↓
INITIAL STATE LOAD
  ↓
WEBSOCKET UPDATE
  ↓
NEXT DOSE HIGHLIGHT
  ↓
INFO PANEL
```

---

# 88. Kết luận

> **Task 10 là lớp trực quan hóa và trải nghiệm người dùng cao cấp của PharmaMind AI. Nó biến dữ liệu cabinet, medication và schedule thành một tủ thuốc số hóa dễ hiểu, dễ trình diễn, và đủ linh hoạt để sau này đồng bộ với phần cứng thật. Hình ảnh tủ thuốc thực tế tham chiếu phải bám theo concept sản phẩm đã cung cấp: màn hình phía trên, 9 ngăn rõ ràng, phong cách gia đình hiện đại, thân thiện và dễ quan sát.**
