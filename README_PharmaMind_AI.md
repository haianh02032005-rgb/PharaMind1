# PharmaMind AI

## Family Health Management & Smart Medicine Cabinet Platform

> **Một chạm thông minh – Cả nhà an bình**

**PharmaMind AI** là nền tảng quản lý sức khỏe gia đình kết hợp:

- Ứng dụng quản lý sức khỏe.
- Hồ sơ sức khỏe cho từng thành viên.
- Tủ thuốc thông minh IoT.
- **Digital Twin – mô hình tủ thuốc 3D trong ứng dụng.**
- Quản lý thuốc và đơn thuốc.
- Theo dõi lịch sử sử dụng thuốc.
- Theo dõi các chỉ số sức khỏe.
- Trợ lý Dược sĩ AI.
- Cảnh báo cho người thân/người chăm sóc.

Mục tiêu của PharmaMind AI không chỉ là tạo một ứng dụng nhắc uống thuốc hoặc một tủ thuốc thông minh đơn lẻ.

Hệ thống hướng tới xây dựng một:

> **Family Health Hub – Trung tâm dữ liệu và chăm sóc sức khỏe số dành cho gia đình.**

---

# 1. Bài toán

Trong một gia đình thường tồn tại nhiều vấn đề liên quan đến thuốc và chăm sóc sức khỏe:

- Người cao tuổi quên uống thuốc.
- Uống thuốc không đúng thời gian.
- Nhầm thuốc giữa các thành viên.
- Một người phải sử dụng nhiều loại thuốc.
- Không biết trong nhà còn bao nhiêu thuốc.
- Không theo dõi được hạn sử dụng.
- Người thân không biết người lớn tuổi đã lấy thuốc hay chưa.
- Không nhớ thuốc được đặt ở vị trí nào.
- Đơn thuốc và lịch sử sử dụng thuốc bị phân tán.
- Hồ sơ khám bệnh và kết quả xét nghiệm nằm ở nhiều nơi.
- Các chỉ số sức khỏe không được theo dõi liên tục.
- Thông tin dị ứng thuốc hoặc tiền sử phản ứng thuốc dễ bị bỏ sót.
- Người chăm sóc khó quản lý đồng thời nhiều thành viên.

PharmaMind AI giải quyết các vấn đề trên bằng việc kết nối:

```text
CON NGƯỜI
    +
DỮ LIỆU SỨC KHỎE
    +
THUỐC
    +
TỦ THUỐC IoT
    +
DIGITAL TWIN 3D
    +
AI
```

---

# 2. Tầm nhìn hệ thống

```text
                    PHARMAMIND AI
                          │
                 FAMILY HEALTH CLOUD
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   Mobile App       AI Assistant       Smart Cabinet
        │                 │                 │
        │                 │               IoT
        │                 │                 │
        └────────── Digital Twin 3D ────────┘
                          │
                Family Health Database
                          │
          ┌───────────────┼───────────────┐
          │               │               │
         Bà              Bố              Con
          │               │               │
       Hồ sơ           Hồ sơ           Hồ sơ
       Thuốc           Thuốc           Thuốc
       Lịch            Lịch            Lịch
       Chỉ số          Chỉ số          Chỉ số
```

Mỗi thành viên được quản lý bằng một `HealthProfile` riêng.

Tất cả thành viên được liên kết trong một:

```text
Family Workspace
```

---

# 3. Các module chính

PharmaMind AI gồm 7 module chính:

```text
01. Family Management
02. Health Profile
03. Medication Management
04. Smart Medicine Cabinet IoT
05. Smart Cabinet Digital Twin 3D
06. AI Pharmacist
07. Family Care & Notification
```

---

# 4. Quản lý gia đình

Một tài khoản có thể tạo một hoặc nhiều hồ sơ thành viên.

Ví dụ:

```text
Gia đình Nguyễn Văn A
│
├── Bà Lan
│   ├── 72 tuổi
│   ├── Thuốc: 5 loại
│   ├── Huyết áp
│   └── Người chăm sóc: Nguyễn Văn A
│
├── Nguyễn Văn A
│   ├── 45 tuổi
│   └── Thuốc: 2 loại
│
├── Trần Thị B
│   ├── 42 tuổi
│   └── Thuốc: 1 loại
│
└── Nguyễn Minh C
    └── 15 tuổi
```

Mỗi thành viên có dữ liệu độc lập nhưng người được cấp quyền chăm sóc có thể xem dữ liệu cần thiết của thành viên đó.

---

# 5. Hồ sơ sức khỏe cá nhân

Mỗi `HealthProfile` lưu các nhóm dữ liệu sau.

## Thông tin cơ bản

```text
Họ tên
Ngày sinh
Giới tính
Chiều cao
Cân nặng
Nhóm máu
Ảnh đại diện
Người liên hệ khẩn cấp
```

## Tiền sử sức khỏe

```text
Bệnh nền
Tiền sử bệnh
Tiền sử phẫu thuật
Dị ứng
Dị ứng thuốc
Tiền sử phản ứng thuốc
Thuốc đang sử dụng
```

## Hồ sơ y tế

```text
Đơn thuốc
Kết quả xét nghiệm
Phiếu khám
Lịch hẹn
Tài liệu y tế
Ghi chú chăm sóc
```

---

# 6. Theo dõi chỉ số sức khỏe

Hệ thống hỗ trợ:

```text
Huyết áp
Nhịp tim
SpO2
Đường huyết
Cân nặng
BMI
Nhiệt độ
Giấc ngủ
Số bước chân
```

Nguồn dữ liệu:

```text
Manual Input
Medical Device
Wearable
Imported Record
```

Dữ liệu được lưu theo thời gian để xây dựng:

- biểu đồ ngày;
- tuần;
- tháng;
- xu hướng;
- cảnh báo theo ngưỡng;
- báo cáo sức khỏe.

---

# 7. Quản lý thuốc

Mỗi thuốc được quản lý bằng entity:

```text
Medication
```

Các thông tin chính:

```text
Tên thuốc
Hoạt chất
Hàm lượng
Dạng bào chế
Nhà sản xuất
Số lượng
Đơn vị
Hạn sử dụng
Ngày mở hộp
Người sử dụng
Liều sử dụng
Lịch sử dụng
Ngăn tủ
Ảnh bao bì
Thông tin cơ bản
Nguồn dữ liệu
```

---

# 8. Quét thuốc

Người dùng có thể sử dụng camera để:

```text
Camera
   ↓
OCR / QR / Barcode
   ↓
Nhận diện thông tin
   ↓
Tra cứu dữ liệu
   ↓
Người dùng xác nhận
   ↓
Lưu Medication
```

Thông tin quan trọng không nên tự động trở thành dữ liệu chính thức nếu người dùng chưa xác nhận.

---

# 9. Tủ thuốc thông minh

Phiên bản MVP dự kiến gồm:

```text
9 ngăn thuốc
Màn hình cảm ứng
ESP32
RTC
Wi-Fi / BLE
Cảm biến trạng thái ngăn
LED
Loa
Cơ cấu khóa/mở
Nguồn điện
Pin dự phòng
```

Ví dụ:

```text
Ngăn 01 → Paracetamol
Ngăn 02 → Vitamin C
Ngăn 03 → Vitamin D3

Ngăn 04 → Cetirizine
Ngăn 05 → Omeprazole
Ngăn 06 → Calcium

Ngăn 07 → Metformin
Ngăn 08 → Amlodipine
Ngăn 09 → Kẽm
```

---

# 10. Digital Twin 3D – Mô hình tủ thuốc 3D

Đây là một chức năng trọng tâm của ứng dụng PharmaMind AI.

Ứng dụng hiển thị một **mô hình 3D tương tác của tủ thuốc vật lý**.

Mô hình này đóng vai trò như:

> **Digital Twin thu gọn của Smart Medicine Cabinet.**

Người dùng có thể:

- xoay tủ;
- phóng to/thu nhỏ;
- quan sát từng ngăn;
- nhấn vào ngăn;
- xem thuốc đang chứa;
- xem số lượng;
- xem người đang sử dụng;
- xem lịch uống;
- xem cảnh báo;
- xem trạng thái ngăn;
- xem mô hình viên thuốc minh họa.

---

# 11. Giao diện tủ thuốc 3D

Ví dụ:

```text
                    SMART CABINET

                 ╔═══════╗
                 ║SCREEN ║
                 ╚═══════╝

        ┌────────┬────────┬────────┐
        │   01   │   02   │   03   │
        │   💊   │   💊   │   💊   │
        ├────────┼────────┼────────┤
        │   04   │   05   │   06   │
        │   💊   │   💊   │   💊   │
        ├────────┼────────┼────────┤
        │   07   │   08   │   09   │
        │   💊   │   💊   │   💊   │
        └────────┴────────┴────────┘
```

Trạng thái từng ngăn được đồng bộ với tủ thật.

---

# 12. Tương tác với mô hình 3D

Người dùng có thể thực hiện:

```text
Rotate
Zoom
Pan
Select Compartment
Open Animation
Close Animation
Inspect Medication
```

Luồng:

```text
3D Cabinet
     ↓
User chọn Ngăn 08
     ↓
Highlight Ngăn 08
     ↓
Animation mở ngăn
     ↓
Hiển thị thuốc 3D
     ↓
Hiển thị Medication Detail Panel
```

---

# 13. Mô hình viên thuốc 3D

Khi người dùng chọn một ngăn, ứng dụng hiển thị một hoặc nhiều mô hình viên thuốc 3D.

Mô hình có thể sử dụng các dạng cơ bản:

```text
Round Tablet
Oval Tablet
Capsule
Softgel
Powder Sachet
Bottle
Box
```

## Nguyên tắc quan trọng

Mô hình viên thuốc **không nhằm tái tạo chính xác thuốc ngoài đời thực**.

Mục đích:

> Giúp người dùng dễ quan sát và hình dung thuốc đang được lưu trong ngăn.

Ứng dụng phải hiển thị chú thích:

> **“Hình ảnh 3D chỉ mang tính minh họa, không sử dụng để nhận dạng thuốc.”**

Không sử dụng màu sắc/hình dạng 3D để xác nhận danh tính thuốc.

Danh tính thuốc phải dựa trên:

```text
Medication ID
Barcode
QR
OCR
Database
User Confirmation
```

---

# 14. Medication Detail Panel

Khi người dùng chọn một ngăn, một bảng thông tin xuất hiện.

Ví dụ:

```text
┌──────────────────────────────────┐
│ AMLODIPINE 5 mg                  │
│                                  │
│ Ngăn: 08                         │
│                                  │
│ Số lượng                         │
│ 18 viên                          │
│                                  │
│ Người sử dụng                    │
│ 👵 Bà Lan                        │
│                                  │
│ Lịch tiếp theo                   │
│ 08:00 – 02/11/2026               │
│                                  │
│ Liều theo lịch                   │
│ 1 viên                           │
│                                  │
│ Còn khoảng                       │
│ 18 ngày                          │
│                                  │
│ Hạn sử dụng                      │
│ 05/2027                          │
│                                  │
│ ⚠ CẢNH BÁO                      │
│ Kiểm tra hồ sơ dị ứng            │
│                                  │
│ [Xem chi tiết]   [Xem lịch]      │
└──────────────────────────────────┘
```

---

# 15. Thông tin hiển thị khi chọn ngăn

## Thông tin ngăn

```text
Compartment ID
Trạng thái cửa
Trạng thái khóa
Lần mở gần nhất
Trạng thái kết nối
```

## Thông tin thuốc

```text
Tên thuốc
Hoạt chất
Hàm lượng
Dạng thuốc
Số lượng
Hạn sử dụng
Mô tả ngắn
Ảnh bao bì
```

## Thông tin sử dụng

```text
Thành viên sử dụng
Liều theo lịch
Lịch uống hôm nay
Lịch tiếp theo
Thời gian bắt đầu
Thời gian kết thúc
```

## Cảnh báo

```text
Dị ứng
Tiền sử phản ứng thuốc
Thuốc sắp hết
Thuốc sắp hết hạn
Lịch bị bỏ lỡ
Thông tin cần xác minh
```

---

# 16. Tồn kho trực quan 3D

Số lượng viên thuốc hiển thị trong 3D không nhất thiết tương ứng 1:1 với số viên thực.

Ví dụ:

```text
1–5 viên        → hiển thị 1–5 viên
6–15 viên       → hiển thị 6 viên
16–30 viên      → hiển thị 10 viên
31–60 viên      → hiển thị 14 viên
>60 viên        → hiển thị 18 viên
```

Đồng thời vẫn hiển thị số lượng thực tế.

---

# 17. Mức tồn kho

Mỗi ngăn có thể có trạng thái:

```text
NORMAL
LOW
CRITICAL
EMPTY
```

Ngăn 3D có thể sử dụng viền, biểu tượng và nhãn trạng thái.

Không nên chỉ phụ thuộc vào màu sắc.

---

# 18. Lịch uống thuốc theo từng thành viên

Một thuốc có thể liên kết với một hoặc nhiều thành viên.

Ví dụ:

```text
Amlodipine
Ngăn 08

Bà Lan
├── 08:00
├── 1 viên
├── Hằng ngày
└── 01/11/2026 → 30/11/2026
```

Nếu nhiều thành viên cùng sử dụng một thuốc, hệ thống luôn hiển thị rõ:

```text
MEMBER
MEDICATION
DOSAGE
TIME
```

---

# 19. Cảnh báo dị ứng và phản ứng thuốc

Hồ sơ thành viên có:

```text
AllergyProfile
```

bao gồm:

```text
Dị nguyên
Thuốc từng gây phản ứng
Hoạt chất liên quan
Mức độ
Triệu chứng từng ghi nhận
Ngày ghi nhận
Nguồn thông tin
Xác nhận bởi người dùng
```

---

# 20. Kiểm tra an toàn khi chọn thuốc

```text
User chọn ngăn
        ↓
Medication
        ↓
Active Ingredient
        ↓
Member sử dụng
        ↓
Allergy Profile
        ↓
Safety Check
        ↓
Medication Detail
```

---

# 21. Mức cảnh báo an toàn

```text
INFO
CAUTION
WARNING
CRITICAL
```

Ứng dụng không tự kết luận một thuốc chắc chắn gây phản vệ.

Thay vào đó có thể hiển thị:

> **Hồ sơ của thành viên có thông tin dị ứng hoặc phản ứng thuốc cần kiểm tra.**

Các cảnh báo nghiêm trọng cần khuyến nghị người dùng tham khảo bác sĩ/dược sĩ.

---

# 22. Trạng thái trực quan của ngăn 3D

```text
AVAILABLE
DOSE_DUE
LOW_STOCK
EXPIRING
EMPTY
WARNING
OFFLINE
```

---

# 23. Đồng bộ Digital Twin với tủ thật

```text
Physical Cabinet
       │
       │ Sensor Event
       ▼
     ESP32
       │
       │ MQTT
       ▼
  IoT Backend
       │
       ▼
    Database
       │
       ▼
 WebSocket / API
       │
       ▼
 Digital Twin 3D
```

---

# 24. Real-time synchronization

Các event:

```text
CABINET_ONLINE
CABINET_OFFLINE
COMPARTMENT_OPEN
COMPARTMENT_CLOSE
LOCK_OPEN
LOCK_CLOSE
MEDICATION_REMOVED
INVENTORY_UPDATED
REMINDER_TRIGGERED
```

Ứng dụng có thể nhận event bằng:

```text
WebSocket
```

Backend giao tiếp với thiết bị bằng:

```text
MQTT
```

---

# 25. Quy trình uống thuốc hoàn chỉnh

```text
Đến giờ uống thuốc
        ↓
Notification
        ↓
App mở Digital Twin
        ↓
Ngăn cần lấy được Highlight
        ↓
Người dùng chọn ngăn
        ↓
Hiển thị:
- Thuốc
- Thành viên
- Liều
- Cảnh báo
        ↓
Người dùng xác nhận
        ↓
Tủ mở ngăn
        ↓
Cảm biến ghi nhận
        ↓
Medication Event
        ↓
Cập nhật tồn kho
        ↓
Digital Twin cập nhật
        ↓
Family Dashboard cập nhật
```

---

# 26. Medication Event

Không nên coi việc mở ngăn là đã uống thuốc.

Luồng trạng thái:

```text
SCHEDULED
    ↓
REMINDER_SENT
    ↓
CABINET_OPENED
    ↓
MEDICATION_RETRIEVED
    ↓
USER_CONFIRMED
```

Các trạng thái khác:

```text
MISSED
SKIPPED
SNOOZED
UNKNOWN
```

---

# 27. Chế độ người chăm sóc

Người thân có thể theo dõi:

```text
BÀ LAN

Medication adherence
92%

Tủ thuốc
● Online

Thuốc sáng
✓ Đã xác nhận

Thuốc trưa
⚠ Chưa ghi nhận

Amlodipine
5 viên còn lại

Vitamin D3
⚠ Sắp hết hạn
```

---

# 28. Nhật ký sức khỏe

```text
01/11/2026

07:30
Tủ PharmaMind AI kết nối

07:55
Huyết áp: 128/82

08:00
Nhắc Amlodipine

08:03
Ngăn 08 mở

08:04
Xác nhận sử dụng thuốc

08:04
Tồn kho Amlodipine:
19 → 18 viên
```

---

# 29. AI Pharmacist

AI có thể trả lời các câu hỏi dựa trên dữ liệu đã lưu.

Ví dụ:

```text
Người dùng:
Thuốc huyết áp của bà ở đâu?

AI:
Theo dữ liệu đã xác nhận,
Amlodipine của bà Lan được lưu ở Ngăn 08.
```

---

# 30. AI và Digital Twin

AI có thể hỗ trợ điều hướng mô hình 3D.

Ví dụ:

```text
User:
Cho tôi xem thuốc huyết áp của bà.
```

Pipeline:

```text
Voice/Text
    ↓
AI
    ↓
Identify Member
    ↓
Identify Medication
    ↓
Find Compartment
    ↓
Digital Twin Command
    ↓
Focus Compartment 08
```

---

# 31. Nguyên tắc AI

Dữ liệu được phân biệt:

```text
CONFIRMED DATA
DEVICE DATA
AI INFERENCE
```

AI không tự thay đổi:

- đơn thuốc;
- liều;
- lịch uống quan trọng;
- thông tin dị ứng;
- tình trạng bệnh;

nếu không có xác nhận phù hợp.

---

# 32. Kiến trúc AI

```text
User
 │
 ▼
AI Gateway
 │
 ▼
Intent Detection
 │
 ├── Family Database
 ├── Medication Database
 ├── Cabinet Database
 ├── Allergy Profile
 ├── Health Metrics
 └── Medical Knowledge Base
 │
 ▼
RAG
 │
 ▼
LLM
 │
 ▼
Safety Layer
 │
 ▼
Answer / App Action
```

---

# 33. Kiến trúc Digital Twin

```text
                    FLUTTER APP
                         │
                ┌────────┴────────┐
                │                 │
           UI Layer          3D Engine
                │                 │
                │          Cabinet Model
                │                 │
                │          Medication Model
                │                 │
                └────────┬────────┘
                         │
                    State Manager
                         │
                         ▼
                       API
                         │
               ┌─────────┼──────────┐
               │         │          │
          Medication   Family      IoT
           Service     Service   Service
               │         │          │
               └─────────┼──────────┘
                         │
                      Database
```

---

# 34. Công nghệ 3D đề xuất

Nếu ứng dụng sử dụng Flutter:

```text
Flutter
  +
glTF / GLB Models
  +
Three-dimensional Viewer
```

Định dạng mô hình ưu tiên:

```text
.glb
.gltf
```

Lý do:

- nhẹ;
- phổ biến;
- dễ tối ưu;
- hỗ trợ animation;
- phù hợp Web/Mobile;
- dễ tạo từ Blender.

---

# 35. Asset 3D

```text
assets/
└── models/
    ├── cabinet/
    │   └── pharmamind_cabinet.glb
    │
    ├── compartments/
    │   └── drawer.glb
    │
    └── medication/
        ├── tablet_round.glb
        ├── tablet_oval.glb
        ├── capsule.glb
        ├── softgel.glb
        ├── bottle.glb
        └── medicine_box.glb
```

Không cần tạo mô hình riêng cho hàng nghìn thuốc.

Chỉ cần thư viện 5–10 mẫu 3D cơ bản và thay đổi:

```text
Scale
Material
Label
Quantity Representation
```

---

# 36. Tối ưu mô hình 3D

Đối với mobile:

```text
Low Poly
Compressed Texture
Small GLB
LOD
Object Pooling
Lazy Loading
```

Không render số lượng viên thuốc thực theo tỷ lệ 1:1 nếu tồn kho lớn.

---

# 37. Cấu trúc dữ liệu Digital Twin

## Cabinet

```text
Cabinet
id
family_id
name
status
firmware_version
last_seen
```

## Compartment

```text
Compartment
id
cabinet_id
index
medication_id
quantity
lock_status
door_status
last_opened_at
```

## Medication3DProfile

```text
Medication3DProfile
id
medication_id
model_type
model_asset
scale
display_count
```

## AllergyProfile

```text
AllergyProfile
id
member_id
substance
reaction
severity
status
source
confirmed_at
notes
```

## Prescription

```text
Prescription
id
member_id
doctor
facility
issued_at
start_date
end_date
document_url
```

## PrescriptionItem

```text
PrescriptionItem
id
prescription_id
medication_id
dosage
frequency
route
instructions
```

## MedicationSchedule

```text
MedicationSchedule
id
member_id
medication_id
prescription_item_id
dosage
time
frequency
start_date
end_date
status
```

## MedicationEvent

```text
MedicationEvent
id
member_id
medication_id
schedule_id
compartment_id
scheduled_at
cabinet_opened_at
confirmed_at
quantity_before
quantity_after
status
source
```

---

# 38. API cho Digital Twin

## Cabinet

```http
GET /cabinets/{cabinetId}
```

## Compartments

```http
GET /cabinets/{cabinetId}/compartments
```

## Detail ngăn

```http
GET /cabinets/{cabinetId}/compartments/{compartmentId}
```

Ví dụ response:

```json
{
  "compartment": 8,
  "status": "CLOSED",
  "quantity": 18,
  "medication": {
    "id": "MED008",
    "name": "Amlodipine",
    "strength": "5 mg",
    "modelType": "round_tablet"
  },
  "members": [
    {
      "id": "M001",
      "name": "Bà Lan",
      "nextDose": "08:00",
      "dosage": "1 viên"
    }
  ],
  "alerts": []
}
```

## Lịch thuốc theo ngăn

```http
GET /cabinets/{cabinetId}/compartments/{id}/schedules
```

## Cảnh báo

```http
GET /cabinets/{cabinetId}/compartments/{id}/alerts
```

## Mở ngăn

```http
POST /cabinets/{cabinetId}/compartments/{id}/open
```

Backend cần kiểm tra:

```text
Authentication
       ↓
Authorization
       ↓
Cabinet Online?
       ↓
Correct Medication?
       ↓
Correct Member?
       ↓
Safety Check
       ↓
Send MQTT command
```

---

# 39. MQTT

```text
pharmamind/{cabinetId}/status
pharmamind/{cabinetId}/compartment/{id}/open
pharmamind/{cabinetId}/compartment/{id}/close
pharmamind/{cabinetId}/sensor
pharmamind/{cabinetId}/command
```

Ví dụ event:

```json
{
  "cabinet_id": "CAB001",
  "compartment": 8,
  "event": "OPEN",
  "timestamp": "2026-11-01T08:03:12+07:00"
}
```

---

# 40. Notification Engine

```text
MEDICATION_REMINDER
MEDICATION_MISSED
MEDICATION_LOW_STOCK
MEDICATION_EMPTY
MEDICATION_EXPIRING
MEDICATION_EXPIRED
ALLERGY_PROFILE_WARNING
CABINET_OFFLINE
HEALTH_METRIC_ALERT
APPOINTMENT_REMINDER
CAREGIVER_ALERT
```

---

# 41. Kiến trúc tổng thể

```text
                         Mobile App
                            │
               ┌────────────┼────────────┐
               │            │            │
           Dashboard    Digital Twin   AI Chat
               │            │            │
               └────────────┼────────────┘
                            │
                        API Gateway
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
       Family           Medication           Health
       Module             Module             Module
          │                 │                  │
          └─────────────────┼──────────────────┘
                            │
                       PostgreSQL
                            │
             ┌──────────────┼──────────────┐
             │                             │
             ▼                             ▼
        AI Service                     IoT Service
             │                             │
         LLM + RAG                      MQTT
                                           │
                                           ▼
                                  PharmaMind Cabinet
```

---

# 42. Tech Stack

## Mobile

```text
Flutter
Dart
```

## 3D

```text
GLB / glTF
Blender
Flutter-compatible 3D engine/viewer
```

## Backend

```text
FastAPI
Python
```

## Database

```text
PostgreSQL
pgvector
```

## Cache / Queue

```text
Redis
```

## IoT

```text
ESP32
MQTT
Wi-Fi / BLE
```

## MQTT Broker

```text
EMQX
```

hoặc:

```text
Mosquitto
```

## AI

```text
Python
LLM
RAG
OCR
Speech-to-Text
Text-to-Speech
```

---

# 43. Repository Structure

```text
pharmamind-ai/
│
├── apps/
│   ├── mobile/
│   ├── web-admin/
│   └── cabinet-display/
│
├── assets/
│   └── 3d/
│       ├── cabinet/
│       ├── compartment/
│       └── medications/
│
├── services/
│   ├── auth/
│   ├── family/
│   ├── health/
│   ├── medication/
│   ├── prescription/
│   ├── allergy/
│   ├── notification/
│   ├── cabinet/
│   └── ai/
│
├── iot/
│   ├── esp32/
│   ├── sensors/
│   └── firmware/
│
├── ai/
│   ├── rag/
│   ├── medication/
│   ├── health-analysis/
│   ├── ocr/
│   └── safety/
│
├── database/
│   ├── migrations/
│   ├── schemas/
│   └── seed/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   ├── hardware/
│   ├── digital-twin/
│   └── ui-ux/
│
├── tests/
├── docker-compose.yml
└── README.md
```

---

# 44. Các màn hình ứng dụng

```text
01. Login / Register
02. Family Dashboard
03. Member Profile
04. Health Dashboard
05. Medication Schedule
06. Smart Cabinet
07. Smart Cabinet 3D
08. Compartment Detail
09. Medication Detail
10. Scan Medication
11. Prescription
12. Allergy Profile
13. Health Metrics
14. Health Timeline
15. AI Pharmacist
16. Family Care
17. Notifications
18. Medical Documents
19. Settings
```

---

# 45. Smart Cabinet 3D Screen

```text
┌──────────────────────────────────────────────┐
│ ← Tủ thuốc gia đình              ● Online  │
│                                              │
│                [3D MODEL]                    │
│                                              │
│          ↻ Kéo để xoay                       │
│          ⤢ Chụm để phóng to                  │
│                                              │
├──────────────────────────────────────────────┤
│ Ngăn 08                                      │
│                                              │
│ Amlodipine 5 mg                 18 viên      │
│                                              │
│ 👵 Bà Lan                                    │
│ Lịch tiếp theo: 08:00                        │
│                                              │
│ [Thông tin] [Lịch uống] [Lịch sử]            │
└──────────────────────────────────────────────┘
```

---

# 46. UX cho người cao tuổi

Không nên yêu cầu người cao tuổi thao tác 3D phức tạp.

Ứng dụng cần hỗ trợ cả:

```text
3D Mode
```

và:

```text
Simple Mode
```

Simple Mode:

```text
┌────────┬────────┬────────┐
│   01   │   02   │   03   │
├────────┼────────┼────────┤
│   04   │   05   │   06   │
├────────┼────────┼────────┤
│   07   │   08   │   09   │
└────────┴────────┴────────┘
```

---

# 47. MVP Digital Twin

## MVP 3D V1

```text
✓ Hiển thị tủ
✓ Rotate
✓ Zoom
✓ Chọn 9 ngăn
✓ Animation mở ngăn
✓ Mô hình thuốc cơ bản
✓ Hiển thị số lượng
✓ Hiển thị tên thuốc
✓ Hiển thị thành viên
✓ Hiển thị lịch tiếp theo
```

## V2

```text
✓ Đồng bộ real-time
✓ Tồn kho
✓ Lịch thuốc
✓ Cảnh báo hạn dùng
✓ Allergy Profile
✓ Medication history
```

## V3

```text
✓ AI điều hướng Digital Twin
✓ Voice Control
✓ Smart Search
✓ Predictive Refill
✓ Advanced Visualization
```

---

# 48. MVP toàn hệ thống

## Phase 1

```text
Family
Member
Medication
Prescription
Medication Schedule
```

## Phase 2

```text
Smart Cabinet
ESP32
MQTT
9 Compartments
```

## Phase 3

```text
Digital Twin 3D
Real-time synchronization
Medication visualization
```

## Phase 4

```text
Health Tracking
Family Care
Notifications
```

## Phase 5

```text
AI Pharmacist
RAG
Voice
Health Summary
```

---

# 49. User Stories

## US01

> Là thành viên gia đình, tôi muốn nhìn thấy mô hình 3D của tủ thuốc để biết thuốc đang được đặt ở ngăn nào.

## US02

> Là người sử dụng thuốc, tôi muốn chọn một ngăn và xem thuốc đang có trong đó.

## US03

> Là người chăm sóc, tôi muốn biết trong ngăn còn bao nhiêu thuốc để chủ động bổ sung.

## US04

> Là người chăm sóc, tôi muốn xem thành viên nào đang sử dụng thuốc và lịch uống theo đơn.

## US05

> Là người dùng, tôi muốn hệ thống cảnh báo nếu hồ sơ thành viên có thông tin dị ứng hoặc phản ứng thuốc cần chú ý.

## US06

> Là người cao tuổi, tôi muốn ứng dụng chỉ cho tôi đúng ngăn cần lấy thuốc vào đúng thời điểm.

## US07

> Là người chăm sóc từ xa, tôi muốn thấy trạng thái tủ thuốc và lịch sử mở ngăn của người thân.

---

# 50. Luồng trải nghiệm quan trọng nhất

```text
HOME
 │
 ▼
SMART CABINET
 │
 ▼
3D DIGITAL TWIN
 │
 ▼
SELECT COMPARTMENT
 │
 ├── Medication 3D
 │
 ├── Quantity
 │
 ├── Member
 │
 ├── Prescription
 │
 ├── Schedule
 │
 ├── Expiration
 │
 └── Safety Alert
 │
 ▼
USER ACTION
 │
 ▼
PHYSICAL CABINET
 │
 ▼
MEDICATION EVENT
 │
 ▼
FAMILY HEALTH DATABASE
```

---

# 51. Giá trị khác biệt

PharmaMind AI không chỉ là:

```text
Medication Reminder App
```

cũng không chỉ là:

```text
Smart Pill Box
```

Mà là:

```text
FAMILY HEALTH PLATFORM
          +
SMART MEDICINE CABINET
          +
DIGITAL TWIN 3D
          +
AI PHARMACIST
```

---

# 52. Điểm cốt lõi

```text
                   PharmaMind AI

                         ●
                         │
                   FAMILY HEALTH
                         │
        ┌────────────────┼────────────────┐
        │                │                │
      HEALTH          MEDICINE           AI
        │                │                │
        └────────────────┼────────────────┘
                         │
                  DIGITAL TWIN 3D
                         │
                         ▼
                  SMART CABINET
                         │
                         ▼
                       FAMILY
```

**Tủ thuốc là thiết bị vật lý.**

**Digital Twin là cầu nối trực quan.**

**Dữ liệu sức khỏe gia đình mới là trung tâm của PharmaMind AI.**

---

# 53. Nguyên tắc thiết kế

## Simple

Người cao tuổi vẫn sử dụng được.

## Visual

Thông tin thuốc và tủ thuốc được trực quan hóa.

## Safe

Không sử dụng mô hình 3D để nhận dạng thuốc hoặc tự đưa ra quyết định y tế.

## Family-first

Thiết kế cho cả gia đình.

## Human-in-the-loop

Thông tin quan trọng cần người dùng xác nhận.

## Explainable

AI cần giải thích nguồn dữ liệu khi phù hợp.

## Privacy-first

Người dùng kiểm soát dữ liệu sức khỏe.

---

# 54. Mục tiêu MVP

MVP thành công khi chứng minh được chuỗi:

```text
TẠO GIA ĐÌNH
      ↓
TẠO THÀNH VIÊN
      ↓
THÊM ĐƠN THUỐC
      ↓
THÊM THUỐC
      ↓
ĐƯA THUỐC VÀO NGĂN
      ↓
HIỂN THỊ TRONG DIGITAL TWIN
      ↓
TẠO LỊCH UỐNG
      ↓
NHẮC THUỐC
      ↓
HIGHLIGHT ĐÚNG NGĂN 3D
      ↓
HIỂN THỊ THUỐC + LIỀU + CẢNH BÁO
      ↓
MỞ NGĂN THẬT
      ↓
CẢM BIẾN GHI NHẬN
      ↓
CẬP NHẬT TỒN KHO
      ↓
ĐỒNG BỘ DIGITAL TWIN
      ↓
NGƯỜI THÂN THEO DÕI
      ↓
AI TỔNG HỢP
```

---

# 55. Định nghĩa sản phẩm

> **PharmaMind AI là nền tảng quản lý sức khỏe gia đình kết hợp hồ sơ sức khỏe số, tủ thuốc thông minh IoT, Digital Twin 3D và Trợ lý Dược sĩ AI, giúp các thành viên quản lý thuốc, theo dõi lịch sử sức khỏe và chăm sóc người thân trong một hệ sinh thái thống nhất.**

---

# 56. Mission

> **Biến việc quản lý thuốc và chăm sóc sức khỏe tại nhà từ hoạt động ghi nhớ thủ công thành một hệ thống thông minh, trực quan, chủ động và có dữ liệu.**

---

# 57. Slogan

> **Một chạm thông minh – Cả nhà an bình.**

---

## Project Status

```text
Project: PharmaMind AI

Category:
Digital Health
AI
IoT
Digital Twin
Family Care

Status:
Prototype / MVP Development

Version:
0.2.0
```

---

## Disclaimer

PharmaMind AI là công cụ hỗ trợ quản lý thông tin, thuốc và theo dõi dữ liệu sức khỏe.

Mô hình thuốc 3D trong ứng dụng **chỉ nhằm mục đích trực quan hóa và không được sử dụng để nhận dạng thuốc thực tế**.

Các cảnh báo liên quan tới dị ứng, phản ứng thuốc hoặc tương tác thuốc là thông tin hỗ trợ và phải được phân biệt với chẩn đoán y tế.

Hệ thống không thay thế việc chẩn đoán, kê đơn hoặc quyết định điều trị của bác sĩ, dược sĩ và các chuyên gia y tế có chuyên môn.
