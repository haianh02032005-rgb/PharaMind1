# PharmaMind AI — TASK 06 SPECIFICATION

# TASK 06 — Medication Management Foundation

## 1. Mục tiêu

Task 06 xây dựng nền tảng **Medication Management** cho PharmaMind AI.

Sau Task 05, hệ thống đã có:

```text
User
Authentication
Family
Family Membership
Family Role
Family Member
Health Profile
Medical Condition
Allergy Profile
Drug Reaction History
Emergency Contact
```

Task 06 sẽ bổ sung lớp dữ liệu thuốc, nhằm quản lý:

```text
Thuốc nào đang tồn tại trong gia đình
Thuốc có tên gì
Hoạt chất gì
Hàm lượng bao nhiêu
Dạng bào chế gì
Nhà sản xuất nào
Hạn sử dụng
Số lượng
Đơn vị
Thuốc thuộc Family nào
Thuốc có thể được dùng cho Member nào
```

Task này tạo nền móng cho:

```text
TASK 07 — Prescription
TASK 08 — Medication Schedule
TASK 09 — Smart Cabinet Mock
TASK 10 — Digital Twin 3D
```

Mục tiêu cuối cùng:

> **PharmaMind AI có thể quản lý danh mục thuốc trong từng Family một cách độc lập, có tồn kho cơ bản, có liên kết với thành viên sử dụng và sẵn sàng cho đơn thuốc, lịch uống và tủ thuốc ở các task tiếp theo.**

---

# 2. Điều kiện tiên quyết

Chỉ bắt đầu Task 06 khi Task 05 đã hoàn thành.

Phải test được:

```text
Family
  ↓
FamilyMember
  ↓
HealthProfile
  ↓
Allergy / Drug Reaction
  ↓
Family Authorization
```

và cross-family access đã bị chặn.

---

# 3. Phạm vi Task 06

Task 06 bao gồm:

```text
1. MedicationCatalog Model
2. FamilyMedication Model
3. MemberMedicationLink Model
4. Medication Batch / Inventory Foundation
5. Dosage Form Enum
6. Medication Unit Enum
7. Medication Status
8. Create Medication
9. List Family Medications
10. Get Medication Detail
11. Update Medication
12. Archive Medication
13. Restore Medication
14. Link Medication với FamilyMember
15. Unlink Medication khỏi FamilyMember
16. Update Quantity
17. Expiration Date
18. Low-stock foundation
19. Medication Search trong Family
20. Family-scoped Authorization
21. Alembic Migration
22. Tests
```

Task 06 không bao gồm:

```text
Prescription
Dosage Instruction
Medication Schedule
Reminder
Medication Event
Cabinet
Compartment
Digital Twin
AI Pharmacist
OCR
Barcode Lookup
External Drug Database
Drug Interaction Engine
Automatic Allergy Inference
```

---

# 4. Nguyên tắc kiến trúc quan trọng

Task 06 cần phân biệt:

```text
Medication Catalog
```

và:

```text
Family Medication
```

---

# 5. Medication Catalog là gì?

`MedicationCatalog` lưu thông tin nhận dạng chung của một loại thuốc.

Ví dụ:

```text
Tên: Amlodipine
Hoạt chất: Amlodipine
Hàm lượng: 5 mg
Dạng: Tablet
Nhà sản xuất: ...
```

Catalog không chứa:

```text
số lượng trong nhà
hạn sử dụng lô thuốc
người sử dụng
ngăn tủ
```

---

# 6. Family Medication là gì?

`FamilyMedication` đại diện cho một thuốc cụ thể đang được quản lý trong một Family.

Ví dụ:

```text
Gia đình A
  ↓
Amlodipine 5 mg
  ↓
Còn 20 viên
Hạn dùng: 05/2027
```

Nó chứa dữ liệu inventory:

```text
quantity
unit
expiration_date
status
notes
```

---

# 7. Tại sao cần tách Catalog và Family Medication?

Nếu không tách:

```text
Amlodipine 5 mg
```

sẽ bị lặp lại hàng trăm lần ở nhiều Family.

Tách thành:

```text
MedicationCatalog
        ↓
FamilyMedication
```

giúp:

- giảm trùng lặp;
- dễ chuẩn hóa;
- chuẩn bị cho OCR/barcode;
- chuẩn bị cho drug database;
- dễ gắn nhiều lô thuốc sau này;
- dễ dùng cho Prescription.

---

# 8. Mô hình dữ liệu tổng quát

```text
MedicationCatalog
      │
      └── FamilyMedication
              │
              ├── Family
              │
              └── MemberMedicationLink
                        │
                        └── FamilyMember
```

---

# 9. Cấu trúc bảng

```text
medication_catalogs
family_medications
member_medications
```

---

# 10. MedicationCatalog Model

Tạo:

```text
backend/app/models/medication_catalog.py
```

Đề xuất:

```python
from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class MedicationCatalog(Base):
    __tablename__ = "medication_catalogs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    active_ingredient: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )

    strength: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    dosage_form: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
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

# 11. MedicationCatalog scope

Task 06 chưa xây global drug database chính thức.

Catalog hiện tại có thể chứa:

```text
User-entered medication
Admin-seeded medication
Imported medication
```

Field:

```text
source
```

có thể nhận:

```text
USER_ENTERED
SEEDED
IMPORTED
UNKNOWN
```

---

# 12. Không coi Catalog là nguồn y tế chính thức

Thông tin trong `MedicationCatalog` ở Task 06 chỉ phục vụ:

```text
quản lý dữ liệu
hiển thị
mapping
```

Không được coi:

```text
MedicationCatalog == nguồn tư vấn y khoa chính thức
```

Các thông tin y khoa xác thực sẽ cần nguồn riêng ở task AI/RAG sau.

---

# 13. FamilyMedication Model

Tạo:

```text
backend/app/models/family_medication.py
```

Đề xuất:

```python
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class FamilyMedication(Base):
    __tablename__ = "family_medications"

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

    catalog_id: Mapped[int] = mapped_column(
        ForeignKey(
            "medication_catalogs.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    quantity: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    expiration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    opened_at: Mapped[date | None] = mapped_column(
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

# 14. Medication Status

Đề xuất:

```text
ACTIVE
ARCHIVED
DEPLETED
EXPIRED
```

Trong Task 06:

- `ACTIVE`: đang quản lý;
- `ARCHIVED`: không còn dùng nhưng giữ lịch sử;
- `DEPLETED`: số lượng bằng 0;
- `EXPIRED`: đã quá hạn.

Task 06 chưa cần scheduler tự đổi status.

Có thể tính trạng thái động khi response hoặc update thủ công bằng service logic.

---

# 15. Medication Unit

Đề xuất Enum:

```text
TABLET
CAPSULE
ML
BOTTLE
BOX
SACHET
VIAL
AMPULE
PATCH
OTHER
```

Lưu ý:

`unit` là đơn vị tồn kho.

Ví dụ:

```text
20 TABLET
100 ML
2 BOTTLE
```

---

# 16. Dosage Form

Đề xuất:

```text
TABLET
CAPSULE
SOFTGEL
SYRUP
SOLUTION
SUSPENSION
CREAM
OINTMENT
GEL
INJECTION
DROPS
SPRAY
PATCH
POWDER
SACHET
OTHER
```

Dùng để:

- hiển thị;
- mapping 3D;
- chuẩn bị Digital Twin.

---

# 17. MemberMedicationLink Model

Một thuốc có thể được gắn với một hoặc nhiều FamilyMember.

Tạo:

```text
backend/app/models/member_medication.py
```

Đề xuất:

```python
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class MemberMedication(Base):
    __tablename__ = "member_medications"

    __table_args__ = (
        UniqueConstraint(
            "member_id",
            "family_medication_id",
            name="uq_member_medication",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    member_id: Mapped[int] = mapped_column(
        ForeignKey(
            "family_members.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    family_medication_id: Mapped[int] = mapped_column(
        ForeignKey(
            "family_medications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

---

# 18. MemberMedication không lưu liều dùng

Task 06 chỉ lưu:

```text
Member A sử dụng Medication X
```

Không lưu:

```text
1 viên lúc 8h
2 lần/ngày
```

Các thông tin này thuộc:

```text
TASK 07 — Prescription
TASK 08 — Schedule
```

---

# 19. Family scope bắt buộc

Một `FamilyMedication` phải thuộc đúng một:

```text
family_id
```

Một `MemberMedication` chỉ hợp lệ nếu:

```text
member.family_id
==
family_medication.family_id
```

Service phải enforce rule này.

---

# 20. Cross-Family Link bị cấm

Ví dụ:

```text
Member A → Family 1
Medication B → Family 2
```

Không được tạo:

```text
MemberMedication(A, B)
```

Phải reject.

---

# 21. Cấu trúc thư mục sau Task 06

```text
backend/
│
├── app/
│   ├── models/
│   │   ├── medication_catalog.py
│   │   ├── family_medication.py
│   │   ├── member_medication.py
│   │   └── __init__.py
│   │
│   └── modules/
│       └── medications/
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
│       └── xxxx_create_medication_tables.py
│
└── tests/
    ├── test_medication_create.py
    ├── test_medication_list.py
    ├── test_medication_update.py
    ├── test_medication_member_link.py
    ├── test_medication_inventory.py
    └── test_medication_authorization.py
```

---

# 22. MedicationCreateRequest

Đề xuất:

```json
{
  "name": "Amlodipine",
  "active_ingredient": "Amlodipine",
  "strength": "5 mg",
  "dosage_form": "TABLET",
  "manufacturer": "Example Pharma",
  "quantity": 30,
  "unit": "TABLET",
  "expiration_date": "2027-05-31",
  "opened_at": null,
  "notes": "Thuốc dùng trong gia đình"
}
```

---

# 23. Create Medication API

Endpoint:

```http
POST /families/{family_id}/medications
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

# 24. Create Flow

```text
Authenticated User
      ↓
Family Authorization
      ↓
Validate Request
      ↓
Find Existing Catalog Match
      ↓
If not found → Create Catalog
      ↓
Create FamilyMedication
      ↓
Commit
      ↓
Return Medication
```

---

# 25. Catalog Matching

Task 06 có thể dùng matching đơn giản:

```text
normalized name
active ingredient
strength
dosage form
manufacturer
```

Không cần fuzzy matching.

Không cần AI.

Không cần external API.

---

# 26. Name Normalization

Ví dụ:

```text
"  Amlodipine  "
```

→

```text
"Amlodipine"
```

Không bắt buộc lowercase khi hiển thị.

Có thể lưu thêm normalized field sau này.

---

# 27. Create Response

Ví dụ:

```json
{
  "id": 10,
  "family_id": 1,
  "catalog": {
    "id": 5,
    "name": "Amlodipine",
    "active_ingredient": "Amlodipine",
    "strength": "5 mg",
    "dosage_form": "TABLET",
    "manufacturer": "Example Pharma"
  },
  "quantity": 30,
  "unit": "TABLET",
  "expiration_date": "2027-05-31",
  "status": "ACTIVE"
}
```

---

# 28. List Family Medications

Endpoint:

```http
GET /families/{family_id}/medications
```

Mặc định trả:

```text
ACTIVE
DEPLETED
EXPIRED
```

Không trả:

```text
ARCHIVED
```

nếu không yêu cầu.

---

# 29. Query Parameters

Có thể hỗ trợ:

```http
GET /families/{family_id}/medications?status=ACTIVE
GET /families/{family_id}/medications?search=amlodipine
GET /families/{family_id}/medications?include_archived=true
```

---

# 30. Search Medication

Search theo:

```text
name
active ingredient
manufacturer
```

Task 06 chỉ cần:

```text
ILIKE
```

hoặc tương đương.

Không cần Elasticsearch.

---

# 31. Get Medication Detail

Endpoint:

```http
GET /families/{family_id}/medications/{medication_id}
```

Response có thể gồm:

```json
{
  "id": 10,
  "family_id": 1,
  "catalog": {
    "name": "Amlodipine",
    "active_ingredient": "Amlodipine",
    "strength": "5 mg",
    "dosage_form": "TABLET",
    "manufacturer": "Example Pharma"
  },
  "quantity": 30,
  "unit": "TABLET",
  "expiration_date": "2027-05-31",
  "status": "ACTIVE",
  "members": [
    {
      "id": 3,
      "full_name": "Nguyen Thi Lan"
    }
  ]
}
```

---

# 32. Update Medication

Endpoint:

```http
PATCH /families/{family_id}/medications/{medication_id}
```

Cho phép cập nhật:

```text
quantity
unit
expiration_date
opened_at
notes
```

Có thể cập nhật catalog metadata nhưng khuyến nghị tách logic:

```text
Family inventory fields
vs
Catalog identity fields
```

---

# 33. Không cho đổi family_id

Không được phép:

```text
PATCH family_id
```

Nếu cần chuyển thuốc giữa Family thì tạo record mới.

---

# 34. Archive Medication

Endpoint:

```http
POST /families/{family_id}/medications/{medication_id}/archive
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

# 35. Restore Medication

Endpoint:

```http
POST /families/{family_id}/medications/{medication_id}/restore
```

Quyền:

```text
OWNER
ADMIN
```

---

# 36. Quantity Rules

Không cho:

```text
quantity < 0
```

Cho phép:

```text
quantity = 0
```

Nếu quantity = 0:

```text
status = DEPLETED
```

service có thể cập nhật tự động.

---

# 37. Expiration Rule

Nếu:

```text
expiration_date < today
```

Response hoặc service có thể đánh dấu:

```text
EXPIRED
```

Task 06 chưa cần background scheduler.

---

# 38. Không tự xóa thuốc hết hạn

Thuốc hết hạn vẫn phải giữ record.

Không tự động:

```text
DELETE
```

---

# 39. Expiration Response

Có thể trả thêm computed field:

```json
{
  "is_expired": false,
  "days_until_expiry": 180
}
```

Không cần lưu trực tiếp.

---

# 40. Low Stock Foundation

Task 06 chưa xây notification.

Nhưng có thể thêm:

```text
low_stock_threshold
```

vào FamilyMedication.

Ví dụ:

```python
low_stock_threshold: Mapped[float | None]
```

Nếu:

```text
quantity <= low_stock_threshold
```

API có thể trả:

```text
is_low_stock = true
```

Notification sẽ làm task sau.

---

# 41. Low Stock Field đề xuất

Bổ sung:

```python
low_stock_threshold: Mapped[float | None] = mapped_column(
    Float,
    nullable=True,
)
```

Ví dụ:

```text
quantity = 5
threshold = 5
→ low stock
```

---

# 42. Link Medication với Member

Endpoint:

```http
POST /families/{family_id}/medications/{medication_id}/members
```

Request:

```json
{
  "member_id": 3
}
```

Flow:

```text
Check Family Authorization
      ↓
Get Medication by family_id + medication_id
      ↓
Get Member by family_id + member_id
      ↓
Check Existing Link
      ↓
Create MemberMedication
```

---

# 43. Duplicate Member Link

Nếu đã link:

```text
409 Conflict
```

---

# 44. Unlink Member

Endpoint:

```http
DELETE /families/{family_id}/medications/{medication_id}/members/{member_id}
```

Task 06 cho phép unlink.

Sau Task 07–08 nếu đã có active Prescription/Schedule, rule sẽ phức tạp hơn.

---

# 45. List Medication Members

Có thể hỗ trợ:

```http
GET /families/{family_id}/medications/{medication_id}/members
```

Response:

```json
{
  "items": [
    {
      "id": 3,
      "full_name": "Nguyen Thi Lan",
      "relationship_label": "Bà"
    }
  ]
}
```

---

# 46. List Member Medications

Endpoint:

```http
GET /families/{family_id}/members/{member_id}/medications
```

Trả tất cả thuốc đã liên kết với Member.

---

# 47. Authorization Matrix

| Action | OWNER | ADMIN | CAREGIVER | VIEWER |
|---|---:|---:|---:|---:|
| View medications | ✓ | ✓ | ✓ | ✓ |
| Create medication | ✓ | ✓ | ✓ | ✗ |
| Update medication | ✓ | ✓ | ✓ | ✗ |
| Update quantity | ✓ | ✓ | ✓ | ✗ |
| Link member | ✓ | ✓ | ✓ | ✗ |
| Unlink member | ✓ | ✓ | ✓ | ✗ |
| Archive medication | ✓ | ✓ | ✗ | ✗ |
| Restore medication | ✓ | ✓ | ✗ | ✗ |

---

# 48. Archived Family Rule

Nếu Family:

```text
ARCHIVED
```

không cho:

```text
Create Medication
Update Medication
Link Member
```

Chỉ cho view theo rule Task 04.

---

# 49. Archived Member Rule

Không cho link thuốc mới vào:

```text
ARCHIVED Member
```

---

# 50. Archived Medication Rule

Không cho:

```text
Update quantity
Link member
```

khi Medication:

```text
ARCHIVED
```

Chỉ cho:

```text
View
Restore
```

---

# 51. Family Scope Rule

Mọi query phải scope theo:

```text
family_id
```

Đúng:

```python
get_family_medication(
    family_id=family_id,
    medication_id=medication_id,
)
```

Không dùng:

```python
get_family_medication(medication_id)
```

rồi mới kiểm tra.

---

# 52. Cross-Family Attack Protection

Ví dụ:

```text
Family A
medication_id = 10
```

User thuộc Family B gọi:

```http
GET /families/B/medications/10
```

Phải trả:

```text
404
```

---

# 53. Member-Medication Cross-Family Test

Nếu:

```text
Medication → Family A
Member → Family B
```

link phải fail.

---

# 54. Repository Layer

Tạo:

```text
backend/app/modules/medications/repository.py
```

Nhiệm vụ:

```text
find_catalog()
create_catalog()

create_family_medication()
get_family_medication()
list_family_medications()
update_family_medication()

archive_medication()
restore_medication()

create_member_link()
delete_member_link()
list_medication_members()
list_member_medications()
```

---

# 55. Service Layer

Tạo:

```text
backend/app/modules/medications/service.py
```

Chịu trách nhiệm:

```text
authorization
family scope
catalog matching
inventory validation
status calculation
expiration logic
member linking
business rules
transaction
```

---

# 56. Schema Layer

Tạo:

```text
backend/app/modules/medications/schema.py
```

Schema đề xuất:

```text
MedicationCreateRequest
MedicationUpdateRequest
MedicationResponse
MedicationListResponse

MedicationCatalogResponse

MedicationMemberLinkRequest
MedicationMemberResponse

InventoryUpdateRequest
```

---

# 57. Enums

Tạo:

```text
backend/app/modules/medications/enums.py
```

Bao gồm:

```text
MedicationStatus
MedicationUnit
DosageForm
MedicationSource
```

---

# 58. Inventory Update API

Có thể hỗ trợ endpoint rõ ràng:

```http
PATCH /families/{family_id}/medications/{medication_id}/inventory
```

Request:

```json
{
  "quantity": 25
}
```

Hoặc:

```json
{
  "quantity": 25,
  "low_stock_threshold": 5
}
```

---

# 59. Không trừ tồn kho tự động ở Task 06

Task 06 chưa có:

```text
Medication Event
```

Do đó chưa tự:

```text
quantity = quantity - dosage
```

Việc trừ tự động sẽ làm ở task Schedule/Event sau.

---

# 60. Medication Detail không phải Prescription

Không hiển thị:

```text
uống 1 viên/ngày
```

trong dữ liệu Medication nếu chưa có Prescription.

Medication chỉ lưu:

```text
thuốc là gì
còn bao nhiêu
hạn dùng
ai đang được liên kết
```

---

# 61. Allergy Safety ở Task 06

Task 06 chưa kết luận tương tác.

Nhưng có thể chuẩn bị endpoint:

```text
Member Medication Link
      ↓
Member Allergy Profile
```

Chưa tự động block.

Chưa tự động kết luận:

```text
Thuốc này gây dị ứng
```

Safety logic chi tiết sẽ làm sau.

---

# 62. Migration

Cập nhật model registry:

```text
backend/app/models/__init__.py
```

Import:

```python
from backend.app.models.medication_catalog import MedicationCatalog
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.member_medication import MemberMedication
```

Tạo migration:

```bash
alembic revision --autogenerate -m "create medication tables"
```

Review.

Sau đó:

```bash
alembic upgrade head
```

---

# 63. Migration phải tạo

```text
medication_catalogs
family_medications
member_medications
```

với:

```text
Foreign Keys
Indexes
Unique Constraints
Not Null Constraints
```

---

# 64. Test — Create Medication

OWNER tạo:

```text
Amlodipine 5 mg
30 TABLET
```

Expected:

```text
201
```

Database:

```text
1 MedicationCatalog
1 FamilyMedication
```

---

# 65. Test — Catalog Reuse

Tạo cùng medication identity trong cùng/khác Family.

Expected:

```text
reuse catalog nếu match chính xác
```

nhưng tạo:

```text
FamilyMedication riêng
```

---

# 66. Test — Quantity Validation

Request:

```json
{
  "quantity": -5
}
```

Expected:

```text
422
```

---

# 67. Test — Zero Quantity

Set:

```text
quantity = 0
```

Expected:

```text
status = DEPLETED
```

hoặc response computed tương đương.

---

# 68. Test — Expired Medication

Expiration:

```text
2020-01-01
```

Expected:

```text
is_expired = true
```

và status có thể:

```text
EXPIRED
```

theo service rule.

---

# 69. Test — Link Medication to Member

Medication và Member cùng Family.

Expected:

```text
201
```

---

# 70. Test — Duplicate Link

Link lần 2.

Expected:

```text
409
```

---

# 71. Test — Cross-Family Link

Member Family B với Medication Family A.

Expected:

```text
404 hoặc 409 theo convention
```

Không leak dữ liệu.

---

# 72. Test — Viewer Cannot Update

VIEWER:

```text
PATCH inventory
```

Expected:

```text
reject
```

---

# 73. Test — Caregiver Can Update Quantity

CAREGIVER:

```text
PATCH inventory
```

Expected:

```text
success
```

---

# 74. Test — Archive Medication

OWNER:

```text
archive
→ success
```

CAREGIVER:

```text
archive
→ reject
```

---

# 75. Test — Archived Medication Cannot Link

Archived Medication:

```text
POST /members
```

Expected:

```text
reject
```

---

# 76. Test — Search

Query:

```http
?search=amlodipine
```

Expected:

```text
matching medication only
```

---

# 77. API Summary sau Task 06

Bổ sung:

```http
POST  /families/{family_id}/medications
GET   /families/{family_id}/medications

GET   /families/{family_id}/medications/{medication_id}
PATCH /families/{family_id}/medications/{medication_id}

POST  /families/{family_id}/medications/{medication_id}/archive
POST  /families/{family_id}/medications/{medication_id}/restore

PATCH /families/{family_id}/medications/{medication_id}/inventory

GET    /families/{family_id}/medications/{medication_id}/members
POST   /families/{family_id}/medications/{medication_id}/members
DELETE /families/{family_id}/medications/{medication_id}/members/{member_id}

GET /families/{family_id}/members/{member_id}/medications
```

---

# 78. Example Full Flow

```text
Login
 ↓
Select Family
 ↓
Create Medication
 ↓
Amlodipine 5 mg
 ↓
Quantity = 30
 ↓
Expiration = 05/2027
 ↓
Link Member
 ↓
Bà Lan
 ↓
Medication Detail
 ↓
Family-scoped Storage
```

---

# 79. Dữ liệu cần chuẩn bị cho Task 07

Task 06 phải tạo được dữ liệu để Task 07 dùng:

```text
FamilyMember
      +
FamilyMedication
```

Task 07 sẽ thêm:

```text
Prescription
PrescriptionItem
```

và liên kết:

```text
PrescriptionItem
   ↓
FamilyMedication / MedicationCatalog
```

---

# 80. Dữ liệu cần chuẩn bị cho Task 09–10

Task 06 phải chuẩn bị:

```text
dosage_form
quantity
unit
expiration_date
```

để sau này Digital Twin hiển thị:

```text
Medication 3D
Quantity
Expiration
Status
```

---

# 81. Acceptance Criteria

Task 06 chỉ hoàn thành khi:

- [ ] `medication_catalogs` table tồn tại.
- [ ] `family_medications` table tồn tại.
- [ ] `member_medications` table tồn tại.
- [ ] Medication Catalog tách khỏi Family inventory.
- [ ] Family Medication có family scope.
- [ ] Quantity không âm.
- [ ] Unit được validate.
- [ ] Dosage Form được validate.
- [ ] Expiration Date lưu được.
- [ ] Low-stock threshold lưu được.
- [ ] Create Medication hoạt động.
- [ ] List Medication hoạt động.
- [ ] Search Medication hoạt động.
- [ ] Get Medication Detail hoạt động.
- [ ] Update Medication hoạt động.
- [ ] Update Inventory hoạt động.
- [ ] Archive/Restore hoạt động.
- [ ] Link Medication với Member hoạt động.
- [ ] Duplicate Member Link bị chặn.
- [ ] Cross-Family Link bị chặn.
- [ ] Archived Member không được link.
- [ ] Archived Medication không được link.
- [ ] Viewer không được chỉnh sửa.
- [ ] Caregiver được update theo role matrix.
- [ ] Expired medication được nhận diện.
- [ ] Zero quantity được nhận diện DEPLETED.
- [ ] Alembic migration pass.
- [ ] Tests pass.

---

# 82. Definition of Done

Task 06 được đánh dấu:

```text
DONE
```

khi demo được chuỗi:

```text
Login
 ↓
Select Family
 ↓
Create Medication
 ↓
Medication Catalog
 ↓
Family Medication
 ↓
Set Quantity
 ↓
Set Expiration
 ↓
Link Family Member
 ↓
List Member Medications
 ↓
Update Inventory
 ↓
Archive / Restore
```

và User từ Family khác không truy cập được medication.

---

# 83. Deliverables

Sau Task 06 cần có:

```text
backend/app/models/
├── medication_catalog.py
├── family_medication.py
├── member_medication.py
└── __init__.py

backend/app/modules/medications/
├── router.py
├── service.py
├── repository.py
├── schema.py
├── dependencies.py
├── enums.py
└── exceptions.py

backend/alembic/versions/
└── xxxx_create_medication_tables.py

backend/tests/
├── test_medication_create.py
├── test_medication_list.py
├── test_medication_update.py
├── test_medication_inventory.py
├── test_medication_member_link.py
└── test_medication_authorization.py

docs/tasks/
└── TASK_06_MEDICATION_MANAGEMENT.md
```

---

# 84. Không thực hiện trong Task 06

Không làm:

```text
Prescription
Doctor
Hospital
Dosage instruction
Frequency
Schedule
Reminder
Medication event
Adherence

Cabinet
Compartment
MQTT
Digital Twin

OCR
Barcode lookup
Drug interaction
AI Pharmacist
RAG
```

---

# 85. Task tiếp theo

Sau Task 06:

```text
TASK 07 — Prescription Management
```

Task 07 dự kiến xây:

```text
Prescription
PrescriptionItem
Member ↔ Prescription
Medication ↔ Prescription Item

Doctor / Facility text fields
Issued Date
Start Date
End Date

Dosage
Frequency
Route
Instructions

Prescription CRUD
Prescription History
Family-scoped Authorization
Migration
Tests
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
Smart Cabinet Mock
        ↓
TASK 10
Digital Twin 3D
```

---

# 87. Nguyên tắc chuyển Task

Không chuyển sang Task 07 nếu chưa chứng minh được:

```text
FAMILY
  ↓
MEDICATION
  ↓
INVENTORY
  ↓
MEMBER LINK
  ↓
FAMILY AUTHORIZATION
```

và chưa test đầy đủ isolation giữa các Family.

> **Task 06 là nền tảng dữ liệu thuốc của PharmaMind AI. Từ Task 07 trở đi, Prescription và Schedule phải tham chiếu thuốc đã được quản lý đúng Family scope, thay vì tạo dữ liệu thuốc tự do không kiểm soát.**
