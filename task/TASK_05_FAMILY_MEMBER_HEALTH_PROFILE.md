# PharmaMind AI — TASK 05 SPECIFICATION

# TASK 05 — Family Member & Health Profile Foundation

## 1. Mục tiêu

Task 05 xây dựng nền tảng **Family Member & Health Profile** cho PharmaMind AI.

Sau Task 04, hệ thống đã có:

```text
User
Authentication
Family
Family Membership
Family Role
Family Authorization
```

Task 05 sẽ tạo đối tượng:

```text
FamilyMember
```

đại diện cho **mỗi người được quản lý sức khỏe trong gia đình**.

Ví dụ:

```text
Gia đình Nguyễn Văn A
│
├── Bà Lan
├── Ông Minh
├── Nguyễn Văn A
└── Nguyễn Minh C
```

Mỗi `FamilyMember` sẽ có:

```text
Thông tin cá nhân
Thông tin sức khỏe cơ bản
Bệnh nền
Dị ứng
Dị ứng thuốc
Tiền sử phản ứng thuốc
Liên hệ khẩn cấp
Ghi chú chăm sóc
```

Mục tiêu cuối cùng:

> **Mỗi thành viên trong một Family có một hồ sơ sức khỏe độc lập, được bảo vệ theo Family authorization và sẵn sàng liên kết với Medication, Prescription, Schedule và Smart Cabinet ở các task tiếp theo.**

---

# 2. Phân biệt User và FamilyMember

Đây là nguyên tắc kiến trúc bắt buộc.

## User

`User` là tài khoản đăng nhập.

Ví dụ:

```text
Nguyễn Văn A
email: nguyenvana@example.com
```

User có thể:

- đăng nhập;
- quản lý gia đình;
- chăm sóc nhiều người;
- xem dữ liệu được cấp quyền.

---

## FamilyMember

`FamilyMember` là người có hồ sơ sức khỏe.

Ví dụ:

```text
Bà Lan
72 tuổi
```

Bà Lan có thể:

```text
có tài khoản User
```

hoặc:

```text
không có tài khoản User
```

Ví dụ người cao tuổi không sử dụng smartphone vẫn có thể có `FamilyMember`.

---

# 3. Điều kiện tiên quyết

Chỉ bắt đầu Task 05 khi Task 04 đã hoàn thành.

Phải test được:

```text
User Login
    ↓
Family Membership
    ↓
Family Role
    ↓
Family Authorization
```

và dữ liệu giữa các Family đã được cô lập.

---

# 4. Phạm vi Task 05

Task 05 bao gồm:

```text
1. FamilyMember Model
2. HealthProfile Model
3. MedicalCondition Model
4. AllergyProfile Model
5. DrugReactionHistory Model
6. EmergencyContact Model
7. Create Member
8. List Members
9. Get Member Detail
10. Update Member
11. Archive Member
12. Restore Member
13. Update Health Profile
14. CRUD Medical Conditions
15. CRUD Allergy Profile
16. CRUD Drug Reaction History
17. CRUD Emergency Contacts
18. Family-scoped Authorization
19. Data Validation
20. Alembic Migration
21. Tests
```

Task 05 không bao gồm:

```text
Medication
Prescription
Medication Schedule
Health Metrics time-series
Cabinet
Digital Twin
AI Pharmacist
OCR
Wearables
Medical document upload
```

---

# 5. Kiến trúc tổng quát

```text
Authenticated User
        ↓
Family Authorization
        ↓
FamilyMember API
        ↓
Health Profile Service
        ↓
Repository
        ↓
PostgreSQL
```

Quan hệ chính:

```text
Family
  │
  └── FamilyMember
        │
        ├── HealthProfile
        ├── MedicalCondition
        ├── AllergyProfile
        ├── DrugReactionHistory
        └── EmergencyContact
```

---

# 6. Cấu trúc dữ liệu

```text
families
   │
   └── family_members
          │
          ├── health_profiles
          ├── medical_conditions
          ├── allergy_profiles
          ├── drug_reaction_histories
          └── emergency_contacts
```

---

# 7. FamilyMember Status

Các trạng thái:

```text
ACTIVE
ARCHIVED
```

Không hard-delete Member trong MVP.

Khi xóa:

```text
ACTIVE
  ↓
ARCHIVED
```

Lý do:

- tránh mất lịch sử sức khỏe;
- chuẩn bị liên kết thuốc;
- dễ audit;
- có thể restore.

---

# 8. FamilyMember Model

Tạo:

```text
backend/app/models/family_member.py
```

Đề xuất:

```python
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class FamilyMember(Base):
    __tablename__ = "family_members"

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

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    gender: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    relationship_label: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="ACTIVE",
        nullable=False,
        index=True,
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

# 9. relationship_label

Ví dụ:

```text
Bố
Mẹ
Con
Ông
Bà
Vợ
Chồng
Anh
Chị
Em
Khác
```

Không nên hard-code toàn bộ logic dựa vào trường này.

Đây chỉ là:

```text
display label
```

không phải authorization role.

---

# 10. Gender

MVP có thể dùng:

```text
MALE
FEMALE
OTHER
UNSPECIFIED
```

Không bắt buộc người dùng nhập.

---

# 11. HealthProfile Model

Tạo:

```text
backend/app/models/health_profile.py
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


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    member_id: Mapped[int] = mapped_column(
        ForeignKey(
            "family_members.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    blood_type: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    height_cm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    weight_kg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    general_notes: Mapped[str | None] = mapped_column(
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

Quan hệ:

```text
FamilyMember 1 — 1 HealthProfile
```

---

# 12. Blood Type

Các giá trị:

```text
A+
A-
B+
B-
AB+
AB-
O+
O-
UNKNOWN
```

Có thể nullable.

---

# 13. Height Validation

Đề xuất:

```text
height_cm > 0
height_cm <= 300
```

Không cho:

```text
-170
0
500
```

---

# 14. Weight Validation

Đề xuất:

```text
weight_kg > 0
weight_kg <= 500
```

---

# 15. Không lưu BMI trực tiếp ở Task 05

BMI có thể tính:

```text
BMI = weight_kg / (height_m²)
```

Không cần lưu trong database để tránh dữ liệu không đồng bộ.

Có thể trả dưới dạng computed field trong API sau.

---

# 16. MedicalCondition Model

Tạo:

```text
backend/app/models/medical_condition.py
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


class MedicalCondition(Base):
    __tablename__ = "medical_conditions"

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

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    diagnosed_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE",
        nullable=False,
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
```

---

# 17. MedicalCondition Status

Có thể dùng:

```text
ACTIVE
RESOLVED
UNKNOWN
```

Ví dụ:

```text
Tăng huyết áp → ACTIVE
Viêm họng → RESOLVED
```

---

# 18. AllergyProfile Model

Đây là entity quan trọng để hỗ trợ Medication Safety ở các task sau.

Tạo:

```text
backend/app/models/allergy_profile.py
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


class AllergyProfile(Base):
    __tablename__ = "allergy_profiles"

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

    allergen: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    allergy_type: Mapped[str] = mapped_column(
        String(30),
        default="OTHER",
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        default="UNKNOWN",
        nullable=False,
    )

    reaction_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recorded_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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
```

---

# 19. Allergy Type

Các loại:

```text
DRUG
FOOD
ENVIRONMENT
OTHER
```

Ví dụ:

```text
Penicillin → DRUG
Tôm → FOOD
Phấn hoa → ENVIRONMENT
```

---

# 20. Allergy Severity

MVP:

```text
MILD
MODERATE
SEVERE
UNKNOWN
```

Lưu ý:

> Severity trong hồ sơ là dữ liệu được khai báo/ghi nhận, không phải kết luận tự động của AI.

---

# 21. DrugReactionHistory Model

Tách riêng khỏi AllergyProfile.

Lý do:

```text
Drug reaction != confirmed allergy
```

Một người có thể từng có phản ứng với thuốc nhưng chưa được xác nhận là dị ứng.

Tạo:

```text
backend/app/models/drug_reaction_history.py
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


class DrugReactionHistory(Base):
    __tablename__ = "drug_reaction_histories"

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

    drug_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    active_ingredient: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    reaction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        default="UNKNOWN",
        nullable=False,
    )

    occurred_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    confirmed_by_professional: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
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
```

---

# 22. Không tự động chuyển DrugReaction thành Allergy

Không được tự động:

```text
DrugReactionHistory
      ↓
AllergyProfile
```

Hai entity phải độc lập.

Việc xác nhận dị ứng có thể do:

```text
User nhập
Medical record
Doctor/Pharmacist xác nhận
```

ở các task sau.

---

# 23. EmergencyContact Model

Tạo:

```text
backend/app/models/emergency_contact.py
```

Đề xuất:

```python
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

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

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    relationship: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

---

# 24. Cấu trúc thư mục sau Task 05

```text
backend/
│
├── app/
│   ├── models/
│   │   ├── family_member.py
│   │   ├── health_profile.py
│   │   ├── medical_condition.py
│   │   ├── allergy_profile.py
│   │   ├── drug_reaction_history.py
│   │   ├── emergency_contact.py
│   │   └── __init__.py
│   │
│   └── modules/
│       └── members/
│           ├── router.py
│           ├── service.py
│           ├── repository.py
│           ├── schema.py
│           ├── dependencies.py
│           └── exceptions.py
│
├── alembic/
│   └── versions/
│       └── xxxx_create_member_health_tables.py
│
└── tests/
    ├── test_member_create.py
    ├── test_member_list.py
    ├── test_member_authorization.py
    ├── test_health_profile.py
    ├── test_medical_condition.py
    ├── test_allergy_profile.py
    └── test_drug_reaction.py
```

---

# 25. Create Member API

Endpoint:

```http
POST /families/{family_id}/members
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

Request:

```json
{
  "full_name": "Nguyen Thi Lan",
  "date_of_birth": "1954-05-20",
  "gender": "FEMALE",
  "relationship_label": "Bà"
}
```

Response:

```json
{
  "id": 1,
  "family_id": 1,
  "full_name": "Nguyen Thi Lan",
  "date_of_birth": "1954-05-20",
  "gender": "FEMALE",
  "relationship_label": "Bà",
  "status": "ACTIVE"
}
```

HTTP:

```text
201 Created
```

---

# 26. Create Member Flow

```text
Authenticated User
      ↓
Family Authorization
      ↓
Validate Request
      ↓
Create FamilyMember
      ↓
Create Empty HealthProfile
      ↓
Commit Transaction
      ↓
Return Member
```

Khuyến nghị:

> Tạo `HealthProfile` rỗng ngay cùng transaction với Member.

Như vậy mọi Member luôn có HealthProfile.

---

# 27. Transaction Rule

Create Member:

```text
Create FamilyMember
      ↓
Create HealthProfile
      ↓
Commit
```

Nếu HealthProfile fail:

```text
Rollback Member
```

---

# 28. List Members

Endpoint:

```http
GET /families/{family_id}/members
```

Mặc định chỉ trả:

```text
ACTIVE
```

Response:

```json
{
  "items": [
    {
      "id": 1,
      "full_name": "Nguyen Thi Lan",
      "relationship_label": "Bà",
      "status": "ACTIVE"
    }
  ]
}
```

---

# 29. Include Archived

Có thể hỗ trợ:

```http
GET /families/{family_id}/members?include_archived=true
```

---

# 30. Get Member Detail

Endpoint:

```http
GET /families/{family_id}/members/{member_id}
```

Response tổng hợp:

```json
{
  "id": 1,
  "full_name": "Nguyen Thi Lan",
  "date_of_birth": "1954-05-20",
  "gender": "FEMALE",
  "relationship_label": "Bà",
  "status": "ACTIVE",
  "health_profile": {
    "blood_type": "O+",
    "height_cm": 155,
    "weight_kg": 54
  }
}
```

Không cần trả toàn bộ Allergy/Condition trong endpoint này nếu response quá lớn.

Có thể dùng endpoint riêng.

---

# 31. Update Member

Endpoint:

```http
PATCH /families/{family_id}/members/{member_id}
```

Quyền:

```text
OWNER
ADMIN
CAREGIVER
```

Cho cập nhật:

```text
full_name
date_of_birth
gender
relationship_label
avatar_url
```

Không cập nhật:

```text
family_id
status
```

qua endpoint này.

---

# 32. Archive Member

Endpoint:

```http
POST /families/{family_id}/members/{member_id}/archive
```

Quyền đề xuất:

```text
OWNER
ADMIN
```

CAREGIVER không archive Member ở MVP.

---

# 33. Restore Member

Endpoint:

```http
POST /families/{family_id}/members/{member_id}/restore
```

Quyền:

```text
OWNER
ADMIN
```

---

# 34. Health Profile API

Endpoint:

```http
GET /families/{family_id}/members/{member_id}/health-profile
```

và:

```http
PATCH /families/{family_id}/members/{member_id}/health-profile
```

---

# 35. Health Profile Update Request

Ví dụ:

```json
{
  "blood_type": "O+",
  "height_cm": 155,
  "weight_kg": 54,
  "general_notes": "Theo dõi huyết áp thường xuyên"
}
```

---

# 36. BMI Computation

Response có thể trả:

```json
{
  "height_cm": 155,
  "weight_kg": 54,
  "bmi": 22.48
}
```

Nhưng:

```text
bmi
```

không lưu trực tiếp.

---

# 37. Medical Conditions API

Endpoints:

```http
GET    /families/{family_id}/members/{member_id}/conditions
POST   /families/{family_id}/members/{member_id}/conditions
PATCH  /families/{family_id}/members/{member_id}/conditions/{condition_id}
DELETE /families/{family_id}/members/{member_id}/conditions/{condition_id}
```

DELETE có thể là hard delete ở MVP nếu chỉ là record user-entered chưa liên kết.

Tuy nhiên khuyến nghị dùng:

```text
status = RESOLVED
```

thay vì delete cho bệnh nền.

---

# 38. Create Medical Condition

Request:

```json
{
  "name": "Tăng huyết áp",
  "diagnosed_at": "2023-01-15",
  "status": "ACTIVE",
  "notes": "Đang theo dõi"
}
```

---

# 39. Allergy API

Endpoints:

```http
GET    /families/{family_id}/members/{member_id}/allergies
POST   /families/{family_id}/members/{member_id}/allergies
PATCH  /families/{family_id}/members/{member_id}/allergies/{allergy_id}
DELETE /families/{family_id}/members/{member_id}/allergies/{allergy_id}
```

---

# 40. Create Allergy

Ví dụ:

```json
{
  "allergen": "Penicillin",
  "allergy_type": "DRUG",
  "severity": "SEVERE",
  "reaction_description": "Phát ban và khó thở",
  "recorded_at": "2020-03-10",
  "source": "Người dùng khai báo"
}
```

---

# 41. Allergy Data Safety

API phải hiển thị rõ:

```text
source
```

nếu có.

Ví dụ:

```text
User reported
Medical record
Doctor confirmed
Unknown
```

Không được biến dữ liệu user-entered thành:

```text
medically confirmed
```

---

# 42. Drug Reaction History API

Endpoints:

```http
GET    /families/{family_id}/members/{member_id}/drug-reactions
POST   /families/{family_id}/members/{member_id}/drug-reactions
PATCH  /families/{family_id}/members/{member_id}/drug-reactions/{reaction_id}
DELETE /families/{family_id}/members/{member_id}/drug-reactions/{reaction_id}
```

---

# 43. Create Drug Reaction

Request:

```json
{
  "drug_name": "Amoxicillin",
  "active_ingredient": "Amoxicillin",
  "reaction": "Phát ban",
  "severity": "MODERATE",
  "occurred_at": "2021-05-01",
  "confirmed_by_professional": false
}
```

---

# 44. Emergency Contact API

Endpoints:

```http
GET    /families/{family_id}/members/{member_id}/emergency-contacts
POST   /families/{family_id}/members/{member_id}/emergency-contacts
PATCH  /families/{family_id}/members/{member_id}/emergency-contacts/{contact_id}
DELETE /families/{family_id}/members/{member_id}/emergency-contacts/{contact_id}
```

---

# 45. Primary Emergency Contact

Một Member nên có tối đa:

```text
1 primary contact
```

Khi set contact mới:

```text
is_primary = true
```

Service phải:

```text
set các contact khác = false
```

trong cùng transaction.

---

# 46. Family Authorization

Mọi endpoint Member phải kiểm tra:

```text
current_user
      ↓
family_id
      ↓
FamilyMembership
      ↓
role
```

Không được truy cập Member chỉ bằng:

```text
member_id
```

---

# 47. Member Scope Rule

Mọi query phải đảm bảo:

```text
member.family_id == family_id
```

Ví dụ đúng:

```python
get_member(
    family_id=family_id,
    member_id=member_id,
)
```

Không dùng:

```python
get_member(member_id)
```

rồi mới kiểm tra sau.

---

# 48. Cross-Family Attack Protection

Ví dụ:

```text
Family A
member_id = 5
```

User có quyền Family B gửi:

```http
GET /families/B/members/5
```

Backend phải trả:

```text
404
```

Không leak:

```text
Member 5 thuộc Family A
```

---

# 49. Role Matrix

| Action | OWNER | ADMIN | CAREGIVER | VIEWER |
|---|---:|---:|---:|---:|
| View Members | ✓ | ✓ | ✓ | ✓ |
| Create Member | ✓ | ✓ | ✓ | ✗ |
| Update Member | ✓ | ✓ | ✓ | ✗ |
| Archive Member | ✓ | ✓ | ✗ | ✗ |
| View Health Profile | ✓ | ✓ | ✓ | ✓ |
| Update Health Profile | ✓ | ✓ | ✓ | ✗ |
| Manage Conditions | ✓ | ✓ | ✓ | ✗ |
| Manage Allergies | ✓ | ✓ | ✓ | ✗ |
| Manage Drug Reactions | ✓ | ✓ | ✓ | ✗ |
| Manage Emergency Contacts | ✓ | ✓ | ✓ | ✗ |

---

# 50. Archived Family Rule

Nếu Family:

```text
ARCHIVED
```

không cho:

```text
Create Member
Update Member
Add Health Data
```

Cho phép:

```text
View
Restore Family
```

theo Task 04.

---

# 51. Archived Member Rule

Nếu Member:

```text
ARCHIVED
```

không cho:

```text
Update Health Profile
Add Condition
Add Allergy
Add Drug Reaction
```

Cho phép:

```text
View
Restore Member
```

---

# 52. Repository Layer

Tạo:

```text
backend/app/modules/members/repository.py
```

Nhiệm vụ:

```text
create_member()
get_member()
list_members()
update_member()
archive_member()
restore_member()

get_health_profile()
update_health_profile()

list_conditions()
create_condition()
update_condition()

list_allergies()
create_allergy()
update_allergy()

list_drug_reactions()
create_drug_reaction()
update_drug_reaction()

list_emergency_contacts()
create_emergency_contact()
update_emergency_contact()
```

---

# 53. Service Layer

Tạo:

```text
backend/app/modules/members/service.py
```

Service chịu trách nhiệm:

```text
authorization
validation
transaction
family scope
archived checks
primary emergency contact logic
business rules
```

---

# 54. Schema Layer

Tạo:

```text
backend/app/modules/members/schema.py
```

Các schema:

```text
MemberCreateRequest
MemberUpdateRequest
MemberResponse
MemberListResponse

HealthProfileUpdateRequest
HealthProfileResponse

MedicalConditionCreateRequest
MedicalConditionUpdateRequest
MedicalConditionResponse

AllergyCreateRequest
AllergyUpdateRequest
AllergyResponse

DrugReactionCreateRequest
DrugReactionUpdateRequest
DrugReactionResponse

EmergencyContactCreateRequest
EmergencyContactUpdateRequest
EmergencyContactResponse
```

---

# 55. Age không nên lưu trực tiếp

Không lưu:

```text
age = 72
```

Vì age thay đổi theo thời gian.

Chỉ lưu:

```text
date_of_birth
```

Age được tính khi response nếu cần.

---

# 56. Validation Date of Birth

Không cho:

```text
date_of_birth > today
```

Ví dụ:

```text
2030-01-01
```

phải reject nếu hiện tại chưa đến ngày đó.

---

# 57. Validation Name

```text
full_name
```

đề xuất:

```text
1–150 ký tự
strip whitespace
```

---

# 58. Phone Validation

MVP không cần validate theo quốc gia quá phức tạp.

Tối thiểu:

```text
strip spaces
max length
allow + and digits
```

Sau này có thể dùng:

```text
E.164
```

---

# 59. Model Registry

Cập nhật:

```text
backend/app/models/__init__.py
```

Import:

```python
from backend.app.models.family_member import FamilyMember
from backend.app.models.health_profile import HealthProfile
from backend.app.models.medical_condition import MedicalCondition
from backend.app.models.allergy_profile import AllergyProfile
from backend.app.models.drug_reaction_history import DrugReactionHistory
from backend.app.models.emergency_contact import EmergencyContact
```

---

# 60. Alembic Migration

Tạo migration:

```bash
alembic revision --autogenerate -m "create member health profile tables"
```

Review.

Phải tạo:

```text
family_members
health_profiles
medical_conditions
allergy_profiles
drug_reaction_histories
emergency_contacts
```

Sau đó:

```bash
alembic upgrade head
```

---

# 61. Migration Constraints

Phải kiểm tra:

```text
Foreign Keys
Unique member_id on health_profiles
Indexes on family_id/member_id
Not Null constraints
```

---

# 62. Member Router

Tạo:

```text
backend/app/modules/members/router.py
```

Endpoints chính:

```http
POST  /families/{family_id}/members
GET   /families/{family_id}/members

GET   /families/{family_id}/members/{member_id}
PATCH /families/{family_id}/members/{member_id}

POST  /families/{family_id}/members/{member_id}/archive
POST  /families/{family_id}/members/{member_id}/restore
```

---

# 63. Health Profile Endpoints

```http
GET   /families/{family_id}/members/{member_id}/health-profile
PATCH /families/{family_id}/members/{member_id}/health-profile
```

---

# 64. Condition Endpoints

```http
GET    /families/{family_id}/members/{member_id}/conditions
POST   /families/{family_id}/members/{member_id}/conditions
PATCH  /families/{family_id}/members/{member_id}/conditions/{condition_id}
DELETE /families/{family_id}/members/{member_id}/conditions/{condition_id}
```

---

# 65. Allergy Endpoints

```http
GET    /families/{family_id}/members/{member_id}/allergies
POST   /families/{family_id}/members/{member_id}/allergies
PATCH  /families/{family_id}/members/{member_id}/allergies/{allergy_id}
DELETE /families/{family_id}/members/{member_id}/allergies/{allergy_id}
```

---

# 66. Drug Reaction Endpoints

```http
GET    /families/{family_id}/members/{member_id}/drug-reactions
POST   /families/{family_id}/members/{member_id}/drug-reactions
PATCH  /families/{family_id}/members/{member_id}/drug-reactions/{reaction_id}
DELETE /families/{family_id}/members/{member_id}/drug-reactions/{reaction_id}
```

---

# 67. Emergency Contact Endpoints

```http
GET    /families/{family_id}/members/{member_id}/emergency-contacts
POST   /families/{family_id}/members/{member_id}/emergency-contacts
PATCH  /families/{family_id}/members/{member_id}/emergency-contacts/{contact_id}
DELETE /families/{family_id}/members/{member_id}/emergency-contacts/{contact_id}
```

---

# 68. Test — Create Member

OWNER tạo Member:

```text
201
```

Database phải có:

```text
1 FamilyMember
1 HealthProfile
```

---

# 69. Test — Viewer Cannot Create

VIEWER gọi:

```http
POST /families/{id}/members
```

Expected:

```text
403/404 theo convention
```

---

# 70. Test — List Members

Chỉ trả Member thuộc Family hiện tại.

Không trả Member Family khác.

---

# 71. Test — Cross-Family Access

User thuộc Family B cố truy cập:

```text
Family A / Member 10
```

Expected:

```text
404
```

---

# 72. Test — Update Health Profile

CAREGIVER:

```text
PATCH health-profile
→ success
```

VIEWER:

```text
PATCH health-profile
→ reject
```

---

# 73. Test — Invalid Height

```json
{
  "height_cm": -20
}
```

Expected:

```text
422
```

---

# 74. Test — Future Date of Birth

```text
date_of_birth = future
```

Expected:

```text
422
```

---

# 75. Test — Allergy

Tạo Allergy:

```text
Penicillin
DRUG
SEVERE
```

List lại phải đúng.

---

# 76. Test — Drug Reaction not Allergy

Tạo DrugReactionHistory.

Kiểm tra:

```text
không tự tạo AllergyProfile
```

---

# 77. Test — Primary Emergency Contact

Tạo:

```text
Contact A = primary
```

sau đó:

```text
Contact B = primary
```

Expected:

```text
Contact A → false
Contact B → true
```

---

# 78. Test — Archived Member

Sau archive:

```text
PATCH health profile
```

phải reject.

GET vẫn có thể trả nếu include archived/authorized.

---

# 79. API Summary sau Task 05

Ngoài API Task 01–04, bổ sung:

```http
POST  /families/{family_id}/members
GET   /families/{family_id}/members

GET   /families/{family_id}/members/{member_id}
PATCH /families/{family_id}/members/{member_id}

POST  /families/{family_id}/members/{member_id}/archive
POST  /families/{family_id}/members/{member_id}/restore

GET   /families/{family_id}/members/{member_id}/health-profile
PATCH /families/{family_id}/members/{member_id}/health-profile

GET/POST/PATCH/DELETE
/families/{family_id}/members/{member_id}/conditions

GET/POST/PATCH/DELETE
/families/{family_id}/members/{member_id}/allergies

GET/POST/PATCH/DELETE
/families/{family_id}/members/{member_id}/drug-reactions

GET/POST/PATCH/DELETE
/families/{family_id}/members/{member_id}/emergency-contacts
```

---

# 80. Example Full Flow

```text
User Login
   ↓
Select Family
   ↓
Create Member
   ↓
Bà Lan
   ↓
Create Health Profile
   ↓
Blood Type
Height
Weight
   ↓
Add Medical Condition
Tăng huyết áp
   ↓
Add Allergy
Penicillin
   ↓
Add Drug Reaction
Amoxicillin → phát ban
   ↓
Add Emergency Contact
Nguyễn Văn A
```

---

# 81. Dữ liệu nhạy cảm

Task 05 bắt đầu xử lý dữ liệu sức khỏe.

Do đó phải tuân thủ:

```text
Authentication
Authorization
Family Scope
Least Privilege
No Cross-Family Access
No Sensitive Logging
```

Không log:

```text
full health profile
allergy details
medical condition details
emergency contact phone
```

nếu không cần.

---

# 82. Không dùng AI ở Task 05

Task 05 không đưa AI vào xử lý:

```text
diagnosis
risk classification
allergy inference
drug advice
```

Task này chỉ:

```text
store
retrieve
update
protect
```

dữ liệu người dùng nhập.

---

# 83. Acceptance Criteria

Task 05 chỉ hoàn thành khi:

- [ ] `family_members` table tồn tại.
- [ ] `health_profiles` table tồn tại.
- [ ] `medical_conditions` table tồn tại.
- [ ] `allergy_profiles` table tồn tại.
- [ ] `drug_reaction_histories` table tồn tại.
- [ ] `emergency_contacts` table tồn tại.
- [ ] Mỗi Member thuộc đúng một Family.
- [ ] Mỗi Member có một HealthProfile.
- [ ] Create Member tạo HealthProfile cùng transaction.
- [ ] List Members có family scope.
- [ ] Get Member có family scope.
- [ ] Update Member có authorization.
- [ ] Archive/Restore Member hoạt động.
- [ ] Health Profile CRUD hoạt động.
- [ ] Medical Condition CRUD hoạt động.
- [ ] Allergy CRUD hoạt động.
- [ ] Drug Reaction CRUD hoạt động.
- [ ] Emergency Contact CRUD hoạt động.
- [ ] Chỉ có tối đa một primary emergency contact.
- [ ] Viewer không sửa dữ liệu.
- [ ] Caregiver được phép cập nhật theo role matrix.
- [ ] Archived Member không nhận dữ liệu mới.
- [ ] Future DOB bị reject.
- [ ] Height/Weight invalid bị reject.
- [ ] Drug Reaction không tự biến thành Allergy.
- [ ] Cross-family access bị chặn.
- [ ] Alembic migration pass.
- [ ] Tests pass.

---

# 84. Definition of Done

Task 05 được đánh dấu:

```text
DONE
```

khi demo được chuỗi:

```text
Login
 ↓
Select Family
 ↓
Create Member
 ↓
Member Profile
 ↓
Health Profile
 ↓
Medical Condition
 ↓
Allergy
 ↓
Drug Reaction
 ↓
Emergency Contact
 ↓
Read / Update
 ↓
Family Authorization
```

và User của Family khác không truy cập được.

---

# 85. Deliverables

Sau Task 05 cần có:

```text
backend/app/models/
├── family_member.py
├── health_profile.py
├── medical_condition.py
├── allergy_profile.py
├── drug_reaction_history.py
├── emergency_contact.py
└── __init__.py

backend/app/modules/members/
├── router.py
├── service.py
├── repository.py
├── schema.py
├── dependencies.py
└── exceptions.py

backend/alembic/versions/
└── xxxx_create_member_health_tables.py

backend/tests/
├── test_member_create.py
├── test_member_list.py
├── test_member_authorization.py
├── test_health_profile.py
├── test_medical_condition.py
├── test_allergy_profile.py
├── test_drug_reaction.py
└── test_emergency_contact.py

docs/tasks/
└── TASK_05_FAMILY_MEMBER_HEALTH_PROFILE.md
```

---

# 86. Không thực hiện trong Task 05

Không làm:

```text
Medication
Drug database
Prescription
Dosage
Medication schedule
Reminder
Inventory

Health Metrics history
Blood pressure timeline
Glucose timeline

Cabinet
Compartment
Digital Twin

AI Pharmacist
RAG
OCR
```

---

# 87. Task tiếp theo

Sau Task 05:

```text
TASK 06 — Medication Management Foundation
```

Task 06 dự kiến xây:

```text
Medication Catalog
Family Medication
Medication Name
Active Ingredient
Strength
Dosage Form
Manufacturer
Expiration Date
Quantity
Unit

Medication CRUD
Medication ↔ Family
Medication ↔ Compartment preparation
Medication Safety lookup preparation

Family-scoped Authorization
Migration
Tests
```

---

# 88. Roadmap hiện tại

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
Prescription
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

# 89. Nguyên tắc chuyển Task

Không chuyển sang Task 06 nếu chưa chứng minh được:

```text
FAMILY
  ↓
FAMILY MEMBER
  ↓
HEALTH PROFILE
  ↓
ALLERGY / DRUG REACTION
  ↓
FAMILY AUTHORIZATION
```

và chưa test được isolation giữa các Family.

> **Task 05 là nền tảng dữ liệu sức khỏe cá nhân của PharmaMind AI. Từ Task 06 trở đi, Medication, Prescription và Smart Cabinet phải luôn liên kết với Member/Family theo đúng phạm vi quyền truy cập đã xây dựng ở Task 04–05.**
