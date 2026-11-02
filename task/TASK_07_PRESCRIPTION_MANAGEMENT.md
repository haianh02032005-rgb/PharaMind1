# PharmaMind AI — TASK 07 SPECIFICATION

# TASK 07 — Prescription Management

## 1. Mục tiêu

Task 07 xây dựng nền tảng **Prescription Management** cho PharmaMind AI.

Sau Task 06, hệ thống đã có:

```text
User
Authentication
Family
Family Membership
Family Member
Health Profile
Medication Catalog
Family Medication
Member ↔ Medication Link
Inventory
Expiration
```

Task 07 sẽ bổ sung:

```text
Prescription
Prescription Item
Doctor / Facility Information
Dosage
Frequency
Route
Instructions
Start Date
End Date
Prescription History
```

Mục tiêu cuối cùng:

> **Mỗi thành viên trong gia đình có thể có một hoặc nhiều đơn thuốc, trong đó từng thuốc được liên kết rõ với FamilyMedication, liều dùng, tần suất, đường dùng và thời gian điều trị.**

Task 07 là nền móng trực tiếp cho:

```text
TASK 08 — Medication Schedule
```

---

# 2. Điều kiện tiên quyết

Chỉ bắt đầu Task 07 khi Task 06 đã hoàn thành.

Phải test được:

```text
Family
  ↓
FamilyMember
  ↓
FamilyMedication
  ↓
MemberMedication Link
  ↓
Inventory
  ↓
Family Authorization
```

---

# 3. Phạm vi Task 07

Task 07 bao gồm:

```text
1. Prescription Model
2. PrescriptionItem Model
3. Prescription Status
4. Medication Route Enum
5. Frequency Representation
6. Create Prescription
7. Add Prescription Items
8. List Prescriptions
9. Get Prescription Detail
10. Update Prescription
11. Update Prescription Item
12. Archive Prescription
13. Restore Prescription
14. Prescription History
15. Prescription ↔ Member
16. Prescription ↔ FamilyMedication
17. Validation
18. Family-scoped Authorization
19. Alembic Migration
20. Tests
```

Task 07 không bao gồm:

```text
Medication Schedule
Reminder
Medication Event
Adherence
Cabinet
Compartment
Digital Twin
AI Pharmacist
OCR Prescription
Doctor Account
Hospital Integration
Electronic Signature
```

---

# 4. Kiến trúc tổng quát

```text
Family
  │
  └── FamilyMember
        │
        └── Prescription
               │
               └── PrescriptionItem
                      │
                      └── FamilyMedication
```

---

# 5. Phân biệt Prescription và Medication Schedule

Đây là nguyên tắc quan trọng.

## Prescription

Đơn thuốc lưu:

```text
thuốc gì
liều bao nhiêu
bao nhiêu lần/ngày
đường dùng
bắt đầu từ khi nào
kết thúc khi nào
hướng dẫn của bác sĩ
```

## Medication Schedule

Lịch uống sẽ lưu:

```text
08:00
12:00
20:00
```

Task 07 chưa tạo lịch theo giờ.

Ví dụ:

```text
Prescription:
Amlodipine 5 mg
1 viên
1 lần/ngày
```

Task 08 mới chuyển thành:

```text
08:00 mỗi ngày
```

---

# 6. Prescription Model

Tạo:

```text
backend/app/models/prescription.py
```

Đề xuất:

```python
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    family_id: Mapped[int] = mapped_column(
        ForeignKey(
            "families.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    member_id: Mapped[int] = mapped_column(
        ForeignKey(
            "family_members.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    doctor_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    facility_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    issued_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE",
        nullable=False,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

---

# 7. Prescription Status

Đề xuất:

```text
DRAFT
ACTIVE
COMPLETED
ARCHIVED
```

Ý nghĩa:

```text
DRAFT      → chưa hoàn thiện
ACTIVE     → đang sử dụng
COMPLETED  → đã kết thúc điều trị
ARCHIVED   → lưu lịch sử
```

---

# 8. PrescriptionItem Model

Tạo:

```text
backend/app/models/prescription_item.py
```

Đề xuất:

```python
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    prescription_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prescriptions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    family_medication_id: Mapped[int] = mapped_column(
        ForeignKey(
            "family_medications.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    dose_amount: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    dose_unit: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    frequency_per_day: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    frequency_text: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    route: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

---

# 9. Dose Amount

Ví dụ:

```text
1 viên
0.5 viên
5 ml
10 ml
2 viên
```

Lưu:

```text
dose_amount
dose_unit
```

Ví dụ:

```text
dose_amount = 1
dose_unit = TABLET
```

---

# 10. Dose Unit

Có thể dùng lại `MedicationUnit`.

Ví dụ:

```text
TABLET
CAPSULE
ML
SACHET
DROP
PUFF
PATCH
OTHER
```

---

# 11. Frequency

Không nên chỉ lưu:

```text
1 lần/ngày
```

dưới dạng text duy nhất.

Đề xuất lưu:

```text
frequency_per_day
```

và:

```text
frequency_text
```

Ví dụ:

```text
frequency_per_day = 2
frequency_text = "2 lần/ngày"
```

hoặc:

```text
frequency_per_day = null
frequency_text = "Khi đau"
```

---

# 12. Tại sao cần frequency_text?

Có những chỉ định không thể biểu diễn đơn giản bằng số:

```text
Khi cần
Cách ngày
Mỗi 8 giờ
3 lần/tuần
Theo triệu chứng
```

Do đó cần cả:

```text
structured field
+
free text
```

---

# 13. Route

Đề xuất Enum:

```text
ORAL
TOPICAL
INHALATION
INJECTION
EYE
EAR
NASAL
RECTAL
SUBLINGUAL
TRANSDERMAL
OTHER
```

---

# 14. PrescriptionCreateRequest

Ví dụ:

```json
{
  "member_id": 3,
  "title": "Đơn thuốc huyết áp",
  "doctor_name": "BS. Nguyen Van B",
  "facility_name": "Bệnh viện A",
  "issued_at": "2026-10-20",
  "start_date": "2026-10-20",
  "end_date": "2026-11-20",
  "notes": "Theo dõi huyết áp tại nhà"
}
```

---

# 15. Create Prescription API

Endpoint:

```http
POST /families/{family_id}/prescriptions
```

Quyền:

```text
OWNER
ADMIN
CAREGIVER
```

VIEWER:

```text
không được tạo
```

---

# 16. Create Prescription Flow

```text
Authenticated User
      ↓
Family Authorization
      ↓
Validate Member
      ↓
Create Prescription
      ↓
Commit
      ↓
Return Prescription
```

Member phải thuộc đúng:

```text
family_id
```

---

# 17. Add Prescription Item API

Endpoint:

```http
POST /families/{family_id}/prescriptions/{prescription_id}/items
```

Request:

```json
{
  "family_medication_id": 10,
  "dose_amount": 1,
  "dose_unit": "TABLET",
  "frequency_per_day": 1,
  "frequency_text": "1 lần/ngày",
  "route": "ORAL",
  "instructions": "Uống sau ăn sáng"
}
```

---

# 18. Prescription Item Flow

```text
Get Prescription
      ↓
Check Family Scope
      ↓
Get FamilyMedication
      ↓
Check same family
      ↓
Check medication linked to member?
      ↓
Create PrescriptionItem
```

---

# 19. Có bắt buộc Medication đã link với Member không?

Khuyến nghị:

```text
Có
```

Nếu `FamilyMedication` chưa liên kết với `FamilyMember`:

Task 07 có thể:

```text
Option A: reject
```

hoặc:

```text
Option B: auto-create MemberMedication link
```

Đề xuất dùng:

> **Option A — reject**

Lý do:

- rõ ràng;
- tránh logic ẩn;
- buộc dữ liệu nhất quán;
- dễ audit.

---

# 20. Prescription Item Family Scope

Phải đảm bảo:

```text
Prescription.family_id
==
FamilyMedication.family_id
==
FamilyMember.family_id
```

Nếu không:

```text
reject
```

---

# 21. Prescription Item Duplicate

Một prescription có thể chứa cùng medication nhiều lần không?

MVP đề xuất:

```text
không cho duplicate cùng FamilyMedication trong cùng Prescription
```

Thêm Unique Constraint:

```text
(prescription_id, family_medication_id)
```

---

# 22. Unique Constraint

Trong model:

```python
__table_args__ = (
    UniqueConstraint(
        "prescription_id",
        "family_medication_id",
        name="uq_prescription_item_medication",
    ),
)
```

---

# 23. Date Validation

Rule:

```text
start_date <= end_date
```

nếu cả hai tồn tại.

Không cho:

```text
start_date = 20/11
end_date = 10/11
```

---

# 24. issued_at

`issued_at` có thể:

```text
null
```

nếu người dùng nhập đơn thủ công mà không biết ngày kê.

---

# 25. Start Date mặc định

Nếu không có:

```text
start_date
```

Task 07 không tự suy đoán.

Có thể để null.

Task 08 khi tạo schedule sẽ yêu cầu thời gian rõ hơn.

---

# 26. List Prescriptions

Endpoint:

```http
GET /families/{family_id}/prescriptions
```

Query:

```http
?member_id=3
?status=ACTIVE
?include_archived=true
```

---

# 27. List Prescriptions by Member

Có thể hỗ trợ:

```http
GET /families/{family_id}/members/{member_id}/prescriptions
```

Đây là endpoint tiện dụng.

---

# 28. Get Prescription Detail

Endpoint:

```http
GET /families/{family_id}/prescriptions/{prescription_id}
```

Response:

```json
{
  "id": 5,
  "member": {
    "id": 3,
    "full_name": "Nguyen Thi Lan"
  },
  "title": "Đơn thuốc huyết áp",
  "doctor_name": "BS. Nguyen Van B",
  "facility_name": "Bệnh viện A",
  "issued_at": "2026-10-20",
  "start_date": "2026-10-20",
  "end_date": "2026-11-20",
  "status": "ACTIVE",
  "items": [
    {
      "id": 11,
      "medication": {
        "id": 10,
        "name": "Amlodipine",
        "strength": "5 mg"
      },
      "dose_amount": 1,
      "dose_unit": "TABLET",
      "frequency_per_day": 1,
      "frequency_text": "1 lần/ngày",
      "route": "ORAL",
      "instructions": "Uống sau ăn sáng"
    }
  ]
}
```

---

# 29. Update Prescription

Endpoint:

```http
PATCH /families/{family_id}/prescriptions/{prescription_id}
```

Cho cập nhật:

```text
title
doctor_name
facility_name
issued_at
start_date
end_date
notes
status
```

Không cho:

```text
family_id
member_id
```

ở MVP.

Nếu cần đổi Member, tạo Prescription mới.

---

# 30. Update Prescription Item

Endpoint:

```http
PATCH /families/{family_id}/prescriptions/{prescription_id}/items/{item_id}
```

Cho cập nhật:

```text
dose_amount
dose_unit
frequency_per_day
frequency_text
route
instructions
```

Không đổi medication trực tiếp.

Nếu sai medication:

```text
delete item
create item mới
```

---

# 31. Delete Prescription Item

Endpoint:

```http
DELETE /families/{family_id}/prescriptions/{prescription_id}/items/{item_id}
```

Cho phép:

```text
OWNER
ADMIN
CAREGIVER
```

Nếu Prescription đã có Schedule ở Task 08, rule sẽ chặt hơn.

Task 07 chưa có Schedule nên cho phép delete.

---

# 32. Archive Prescription

Endpoint:

```http
POST /families/{family_id}/prescriptions/{prescription_id}/archive
```

Quyền:

```text
OWNER
ADMIN
```

CAREGIVER:

```text
không archive
```

---

# 33. Restore Prescription

Endpoint:

```http
POST /families/{family_id}/prescriptions/{prescription_id}/restore
```

Quyền:

```text
OWNER
ADMIN
```

---

# 34. Complete Prescription

Có thể hỗ trợ:

```http
POST /families/{family_id}/prescriptions/{prescription_id}/complete
```

Chuyển:

```text
ACTIVE
  ↓
COMPLETED
```

CAREGIVER có thể được phép nếu bạn muốn.

Đề xuất MVP:

```text
OWNER
ADMIN
CAREGIVER
```

đều có thể complete.

---

# 35. Archived Prescription Rule

Nếu:

```text
ARCHIVED
```

không cho:

```text
add item
update item
update prescription
```

Chỉ cho:

```text
view
restore
```

---

# 36. Completed Prescription Rule

Nếu:

```text
COMPLETED
```

MVP đề xuất:

```text
view only
```

Nếu cần sửa:

```text
reactivate
```

có thể làm task sau.

---

# 37. Authorization Matrix

| Action | OWNER | ADMIN | CAREGIVER | VIEWER |
|---|---:|---:|---:|---:|
| View prescriptions | ✓ | ✓ | ✓ | ✓ |
| Create prescription | ✓ | ✓ | ✓ | ✗ |
| Update prescription | ✓ | ✓ | ✓ | ✗ |
| Add item | ✓ | ✓ | ✓ | ✗ |
| Update item | ✓ | ✓ | ✓ | ✗ |
| Delete item | ✓ | ✓ | ✓ | ✗ |
| Complete prescription | ✓ | ✓ | ✓ | ✗ |
| Archive prescription | ✓ | ✓ | ✗ | ✗ |
| Restore prescription | ✓ | ✓ | ✗ | ✗ |

---

# 38. Family Scope Rule

Mọi query phải scope theo:

```text
family_id
```

Đúng:

```python
get_prescription(
    family_id=family_id,
    prescription_id=prescription_id,
)
```

Không dùng:

```python
get_prescription(prescription_id)
```

rồi kiểm tra sau.

---

# 39. Prescription Item Scope Rule

Khi lấy item:

```text
prescription_id
family_id
item_id
```

phải cùng khớp.

Không query item chỉ bằng:

```text
item_id
```

---

# 40. Cross-Family Attack Protection

Ví dụ:

```text
Prescription 7 → Family A
```

User thuộc Family B gọi:

```http
GET /families/B/prescriptions/7
```

Expected:

```text
404
```

---

# 41. Cross-Family Medication Attack

Prescription Family A nhưng truyền:

```text
family_medication_id
```

của Family B.

Expected:

```text
reject
```

---

# 42. Cross-Member Medication Rule

Nếu:

```text
Prescription → Member A
Medication → linked only Member B
```

Task 07 nên reject item.

Lý do:

```text
Medication chưa được gán cho Member A
```

---

# 43. Cấu trúc thư mục sau Task 07

```text
backend/
│
├── app/
│   ├── models/
│   │   ├── prescription.py
│   │   ├── prescription_item.py
│   │   └── __init__.py
│   │
│   └── modules/
│       └── prescriptions/
│           ├── router.py
│           ├── service.py
│           ├── repository.py
│           ├── schema.py
│           ├── dependencies.py
│           ├── enums.py
│           └── exceptions.py
│
├── alembic/
│   └── versions/
│       └── xxxx_create_prescription_tables.py
│
└── tests/
    ├── test_prescription_create.py
    ├── test_prescription_item.py
    ├── test_prescription_update.py
    ├── test_prescription_authorization.py
    └── test_prescription_validation.py
```

---

# 44. Repository Layer

Tạo:

```text
backend/app/modules/prescriptions/repository.py
```

Nhiệm vụ:

```text
create_prescription()
get_prescription()
list_prescriptions()
update_prescription()

create_item()
get_item()
update_item()
delete_item()

archive_prescription()
restore_prescription()
complete_prescription()
```

---

# 45. Service Layer

Tạo:

```text
backend/app/modules/prescriptions/service.py
```

Service chịu trách nhiệm:

```text
family authorization
member validation
medication validation
date validation
status rules
duplicate item prevention
transaction
```

---

# 46. Schema Layer

Tạo:

```text
backend/app/modules/prescriptions/schema.py
```

Các schema:

```text
PrescriptionCreateRequest
PrescriptionUpdateRequest
PrescriptionResponse
PrescriptionListResponse

PrescriptionItemCreateRequest
PrescriptionItemUpdateRequest
PrescriptionItemResponse
```

---

# 47. Enums

Tạo:

```text
backend/app/modules/prescriptions/enums.py
```

Bao gồm:

```text
PrescriptionStatus
MedicationRoute
```

---

# 48. Model Registry

Cập nhật:

```text
backend/app/models/__init__.py
```

Import:

```python
from backend.app.models.prescription import Prescription
from backend.app.models.prescription_item import PrescriptionItem
```

---

# 49. Alembic Migration

Tạo migration:

```bash
alembic revision --autogenerate -m "create prescription tables"
```

Review.

Sau đó:

```bash
alembic upgrade head
```

---

# 50. Migration phải tạo

```text
prescriptions
prescription_items
```

với:

```text
Foreign Keys
Indexes
Unique Constraint
Not Null
```

---

# 51. Test — Create Prescription

OWNER tạo Prescription cho Member cùng Family.

Expected:

```text
201
```

---

# 52. Test — Cross-Family Member

Prescription Family A nhưng member Family B.

Expected:

```text
404
```

---

# 53. Test — Add Prescription Item

Medication thuộc đúng Family và đã link Member.

Expected:

```text
201
```

---

# 54. Test — Medication chưa link Member

Expected:

```text
reject
```

---

# 55. Test — Duplicate Medication Item

Thêm cùng medication lần 2 vào cùng Prescription.

Expected:

```text
409
```

---

# 56. Test — Date Validation

```text
start_date > end_date
```

Expected:

```text
422
```

---

# 57. Test — Invalid Dose

Ví dụ:

```text
dose_amount = -1
```

Expected:

```text
422
```

---

# 58. Test — Frequency

```text
frequency_per_day = -2
```

Expected:

```text
422
```

Cho phép:

```text
null
```

nếu dùng:

```text
frequency_text = "Khi cần"
```

---

# 59. Test — Archive Prescription

OWNER:

```text
success
```

CAREGIVER:

```text
reject
```

---

# 60. Test — Completed Prescription

Complete:

```text
ACTIVE → COMPLETED
```

Sau đó update item:

```text
reject
```

---

# 61. Test — Archived Prescription

Add item:

```text
reject
```

---

# 62. Test — Cross-Family Read

User Family B đọc Prescription Family A.

Expected:

```text
404
```

---

# 63. API Summary sau Task 07

Bổ sung:

```http
POST /families/{family_id}/prescriptions
GET  /families/{family_id}/prescriptions

GET /families/{family_id}/members/{member_id}/prescriptions

GET   /families/{family_id}/prescriptions/{prescription_id}
PATCH /families/{family_id}/prescriptions/{prescription_id}

POST /families/{family_id}/prescriptions/{prescription_id}/complete
POST /families/{family_id}/prescriptions/{prescription_id}/archive
POST /families/{family_id}/prescriptions/{prescription_id}/restore

POST   /families/{family_id}/prescriptions/{prescription_id}/items
PATCH  /families/{family_id}/prescriptions/{prescription_id}/items/{item_id}
DELETE /families/{family_id}/prescriptions/{prescription_id}/items/{item_id}
```

---

# 64. Example Full Flow

```text
Login
 ↓
Select Family
 ↓
Select Member
 ↓
Create Prescription
 ↓
Doctor / Facility
 ↓
Start Date / End Date
 ↓
Add Amlodipine
 ↓
Dose = 1 TABLET
 ↓
Frequency = 1 lần/ngày
 ↓
Route = ORAL
 ↓
Instructions = sau ăn sáng
 ↓
Prescription ACTIVE
```

---

# 65. Dữ liệu chuẩn bị cho Task 08

Task 07 phải tạo được dữ liệu:

```text
Prescription
  ↓
PrescriptionItem
  ↓
Medication
  ↓
Dose
  ↓
Frequency
  ↓
Start Date / End Date
```

Task 08 sẽ chuyển những dữ liệu này thành:

```text
MedicationSchedule
```

Ví dụ:

```text
1 lần/ngày
```

sẽ được người dùng cấu hình thành:

```text
08:00
```

---

# 66. Không tự tạo Schedule ở Task 07

Không tự động:

```text
1 lần/ngày
→ 08:00
```

vì giờ uống cần user xác nhận.

Task 07 chỉ lưu chỉ định.

---

# 67. Không tự diễn giải y khoa

Nếu Prescription ghi:

```text
Khi đau
```

backend không tự chuyển thành:

```text
3 lần/ngày
```

Không dùng AI để suy luận.

---

# 68. Dữ liệu nhạy cảm

Prescription là dữ liệu sức khỏe.

Không log:

```text
full prescription
doctor notes
instructions
member medical details
```

nếu không cần.

Có thể log:

```text
PRESCRIPTION_CREATED
prescription_id
member_id
user_id
timestamp
```

---

# 69. Acceptance Criteria

Task 07 chỉ hoàn thành khi:

- [ ] `prescriptions` table tồn tại.
- [ ] `prescription_items` table tồn tại.
- [ ] Prescription thuộc đúng Family.
- [ ] Prescription thuộc đúng FamilyMember.
- [ ] PrescriptionItem tham chiếu FamilyMedication.
- [ ] Cross-family member bị chặn.
- [ ] Cross-family medication bị chặn.
- [ ] Medication phải link với Member trước khi thêm vào Prescription.
- [ ] Duplicate medication item bị chặn.
- [ ] Date validation hoạt động.
- [ ] Dose validation hoạt động.
- [ ] Frequency validation hoạt động.
- [ ] Create Prescription hoạt động.
- [ ] List Prescription hoạt động.
- [ ] Get Detail hoạt động.
- [ ] Update Prescription hoạt động.
- [ ] Add Item hoạt động.
- [ ] Update Item hoạt động.
- [ ] Delete Item hoạt động.
- [ ] Complete Prescription hoạt động.
- [ ] Archive/Restore hoạt động.
- [ ] Completed Prescription không cho edit.
- [ ] Archived Prescription không cho edit.
- [ ] Family authorization hoạt động.
- [ ] Alembic migration pass.
- [ ] Tests pass.

---

# 70. Definition of Done

Task 07 được đánh dấu:

```text
DONE
```

khi demo được chuỗi:

```text
Login
 ↓
Select Family
 ↓
Select Member
 ↓
Create Prescription
 ↓
Add Medication
 ↓
Set Dose
 ↓
Set Frequency
 ↓
Set Route
 ↓
Set Instructions
 ↓
View Prescription
 ↓
Complete / Archive
```

và User từ Family khác không truy cập được dữ liệu.

---

# 71. Deliverables

Sau Task 07 cần có:

```text
backend/app/models/
├── prescription.py
├── prescription_item.py
└── __init__.py

backend/app/modules/prescriptions/
├── router.py
├── service.py
├── repository.py
├── schema.py
├── dependencies.py
├── enums.py
└── exceptions.py

backend/alembic/versions/
└── xxxx_create_prescription_tables.py

backend/tests/
├── test_prescription_create.py
├── test_prescription_item.py
├── test_prescription_update.py
├── test_prescription_authorization.py
└── test_prescription_validation.py

docs/tasks/
└── TASK_07_PRESCRIPTION_MANAGEMENT.md
```

---

# 72. Không thực hiện trong Task 07

Không làm:

```text
Medication Schedule
Reminder
Notification
Medication Event
Adherence
Automatic Inventory Deduction

Cabinet
Compartment
Digital Twin

OCR Prescription
AI Pharmacist
Drug Interaction
Automatic Dose Interpretation
```

---

# 73. Task tiếp theo

Sau Task 07:

```text
TASK 08 — Medication Schedule Management
```

Task 08 dự kiến xây:

```text
MedicationSchedule
Schedule Time
Recurring Rule
Start / End Date
Reminder Preparation
Schedule Status
PrescriptionItem ↔ Schedule

Daily Timeline
Next Dose
Missed Dose foundation
Schedule CRUD
Family-scoped Authorization
Migration
Tests
```

---

# 74. Roadmap hiện tại

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
Smart Cabinet Mock
        ↓
TASK 10
Digital Twin 3D
```

---

# 75. Nguyên tắc chuyển Task

Không chuyển sang Task 08 nếu chưa chứng minh được:

```text
FAMILY
  ↓
MEMBER
  ↓
PRESCRIPTION
  ↓
PRESCRIPTION ITEM
  ↓
MEDICATION
  ↓
DOSE / FREQUENCY
```

và chưa test đầy đủ Family scope + Prescription status rules.

> **Task 07 là cầu nối giữa dữ liệu thuốc và lịch uống. Task 08 chỉ được xây trên PrescriptionItem đã hợp lệ, thay vì tạo lịch uống độc lập không có nguồn gốc rõ ràng.**
