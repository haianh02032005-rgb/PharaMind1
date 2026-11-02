# PharmaMind AI — TASK 04 SPECIFICATION

# TASK 04 — Family Management

## 1. Mục tiêu

Task 04 xây dựng lớp **Family Management** cho PharmaMind AI.

Sau Task 03, hệ thống đã có:

```text
User
Register
Login
JWT Access Token
Refresh Token
GET /auth/me
Protected API
```

Task 04 sẽ tạo khái niệm:

```text
Family
```

để một người dùng có thể:

- tạo gia đình;
- xem danh sách các gia đình mà mình có quyền truy cập;
- xem chi tiết gia đình;
- cập nhật thông tin gia đình;
- quản lý người dùng có quyền truy cập Family Workspace;
- phân quyền cơ bản trong gia đình;
- bảo vệ dữ liệu giữa các gia đình.

Mục tiêu cuối cùng:

> **Mọi dữ liệu sức khỏe, thuốc, tủ thuốc và Digital Twin ở các task sau đều phải thuộc về một Family Workspace cụ thể và chỉ người có quyền mới được truy cập.**

---

# 2. Phân biệt hai khái niệm quan trọng

Trong PharmaMind AI cần phân biệt rõ:

## 2.1 User

```text
User
```

là **tài khoản đăng nhập hệ thống**.

Ví dụ:

```text
Nguyễn Văn A
email: a@example.com
```

User có thể:

- đăng nhập;
- sở hữu một gia đình;
- được cấp quyền chăm sóc gia đình khác;
- quản lý dữ liệu trên app.

---

## 2.2 Family Member / Health Profile

```text
FamilyMember
```

là **người được quản lý sức khỏe trong gia đình**.

Ví dụ:

```text
Bà Lan
72 tuổi
```

Bà Lan có thể:

- có tài khoản User;
- hoặc không có tài khoản User.

`FamilyMember / HealthProfile` sẽ được xây dựng ở:

```text
TASK 05
```

Task 04 **chưa tạo hồ sơ sức khỏe thành viên**.

---

# 3. Điều kiện tiên quyết

Chỉ bắt đầu Task 04 khi Task 03 đã hoàn thành.

Phải test được:

```text
POST /auth/register
POST /auth/login
POST /auth/refresh
GET  /auth/me
```

và Authentication Test phải pass.

---

# 4. Phạm vi Task 04

Task 04 bao gồm:

```text
1. Family model
2. Family Membership model
3. Family Role
4. Family Status
5. Create Family
6. List My Families
7. Get Family Detail
8. Update Family
9. Archive Family
10. Restore Family
11. Add existing User vào Family
12. List Family Memberships
13. Update Family Role
14. Remove User khỏi Family
15. Authorization theo Family
16. Owner protection
17. Repository Layer
18. Service Layer
19. Alembic Migration
20. Unit / Integration Tests
```

Task 04 không bao gồm:

```text
Health Profile
Patient Profile
Disease
Allergy
Medication
Prescription
Cabinet
Digital Twin
Email Invitation
Invitation Token
QR Invite
Caregiver Alert
```

---

# 5. Kiến trúc tổng quát

```text
Authenticated User
        ↓
Family API
        ↓
Family Authorization
        ↓
Family Service
        ↓
Family Repository
        ↓
PostgreSQL
```

Quan hệ:

```text
User
  │
  │ many-to-many
  ▼
FamilyMembership
  │
  ▼
Family
```

---

# 6. Mô hình dữ liệu

```text
users
  │
  │ 1
  │
  └──────────< family_memberships >──────────1 families
```

Một User có thể thuộc nhiều Family.

Một Family có thể có nhiều User có quyền truy cập.

---

# 7. Family Role

Định nghĩa role:

```text
OWNER
ADMIN
CAREGIVER
VIEWER
```

## OWNER

Có toàn quyền:

```text
Update Family
Archive Family
Restore Family
Add User
Remove User
Change Role
```

## ADMIN

Có thể:

```text
View Family
Update Family
Add User
Manage common family data
```

Không được:

```text
Remove OWNER
Change OWNER
Archive Family
```

## CAREGIVER

Dùng cho người chăm sóc.

Có thể:

```text
View Family
View health-related data
Interact with medication/care features
```

Quyền chi tiết sẽ được mở rộng ở các task sau.

## VIEWER

Chỉ đọc.

---

# 8. Không sử dụng Family Role để thay thế Health Profile

Role:

```text
OWNER
ADMIN
CAREGIVER
VIEWER
```

là quyền của **User account**.

Không dùng role để biểu diễn:

```text
Bố
Mẹ
Con
Ông
Bà
```

Quan hệ gia đình của Health Profile sẽ được xử lý ở Task 05.

---

# 9. Family Status

Các trạng thái:

```text
ACTIVE
ARCHIVED
```

Không hard-delete Family trong MVP.

Khi người dùng xóa gia đình:

```text
ACTIVE
  ↓
ARCHIVED
```

Lý do:

- tránh mất dữ liệu sức khỏe;
- dễ phục hồi;
- phù hợp audit;
- chuẩn bị cho dữ liệu y tế nhạy cảm.

---

# 10. Cấu trúc thư mục sau Task 04

```text
backend/
│
├── app/
│   ├── models/
│   │   ├── user.py
│   │   ├── family.py
│   │   ├── family_membership.py
│   │   └── __init__.py
│   │
│   ├── modules/
│   │   ├── families/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schema.py
│   │   │   ├── dependencies.py
│   │   │   └── exceptions.py
│   │   │
│   │   └── users/
│   │       └── ...
│   │
│   └── shared/
│       └── enums.py
│
├── alembic/
│   └── versions/
│       └── xxxx_create_family_tables.py
│
└── tests/
    ├── test_family_create.py
    ├── test_family_list.py
    ├── test_family_authorization.py
    └── test_family_membership.py
```

---

# 11. Family Model

Tạo:

```text
backend/app/models/family.py
```

Đề xuất:

```python
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Family(Base):
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
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

# 12. Family Membership Model

Tạo:

```text
backend/app/models/family_membership.py
```

Đề xuất:

```python
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class FamilyMembership(Base):
    __tablename__ = "family_memberships"

    __table_args__ = (
        UniqueConstraint(
            "family_id",
            "user_id",
            name="uq_family_membership_family_user",
        ),
    )

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

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

---

# 13. Unique Constraint

Một User chỉ được có một membership trong cùng một Family.

Không được tồn tại:

```text
family_id = 1
user_id = 5
```

hai lần.

Database phải enforce:

```text
UNIQUE(family_id, user_id)
```

---

# 14. Family Role Enum

Có thể đặt tại:

```text
backend/app/shared/enums.py
```

hoặc:

```text
backend/app/modules/families/enums.py
```

Ví dụ:

```python
from enum import StrEnum


class FamilyRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    CAREGIVER = "CAREGIVER"
    VIEWER = "VIEWER"


class FamilyStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
```

---

# 15. Create Family API

Endpoint:

```http
POST /families
```

Authentication:

```text
Required
```

Request:

```json
{
  "name": "Gia đình Nguyễn Văn A",
  "description": "Gia đình chính"
}
```

Response:

```json
{
  "id": 1,
  "name": "Gia đình Nguyễn Văn A",
  "description": "Gia đình chính",
  "status": "ACTIVE",
  "my_role": "OWNER"
}
```

HTTP:

```text
201 Created
```

---

# 16. Create Family Transaction

Khi tạo Family phải thực hiện trong **một transaction**:

```text
Create Family
     ↓
Create Membership
role = OWNER
     ↓
Commit
```

Nếu bước tạo membership fail:

```text
Rollback Family
```

Không được để Family tồn tại mà không có OWNER.

---

# 17. Create Family Flow

```text
Authenticated User
      ↓
POST /families
      ↓
Validate Request
      ↓
Create Family
      ↓
Create OWNER Membership
      ↓
Commit
      ↓
Return Family
```

---

# 18. Family Name Validation

Đề xuất:

```text
min length = 1
max length = 150
```

Trim khoảng trắng.

Không cho:

```text
""
"     "
```

---

# 19. List My Families

Endpoint:

```http
GET /families
```

Chỉ trả các Family mà current user có membership.

Ví dụ:

```json
{
  "items": [
    {
      "id": 1,
      "name": "Gia đình A",
      "status": "ACTIVE",
      "my_role": "OWNER"
    },
    {
      "id": 2,
      "name": "Gia đình B",
      "status": "ACTIVE",
      "my_role": "CAREGIVER"
    }
  ]
}
```

---

# 20. Archived Family

Mặc định:

```http
GET /families
```

chỉ trả:

```text
ACTIVE
```

Có thể hỗ trợ:

```http
GET /families?include_archived=true
```

cho OWNER/authorized user.

---

# 21. Get Family Detail

Endpoint:

```http
GET /families/{family_id}
```

Yêu cầu:

```text
current user phải có membership trong Family
```

Response:

```json
{
  "id": 1,
  "name": "Gia đình Nguyễn Văn A",
  "description": "Gia đình chính",
  "status": "ACTIVE",
  "my_role": "OWNER",
  "created_at": "2026-11-01T10:00:00Z"
}
```

---

# 22. Unauthorized Family Access

Ví dụ:

```text
User A
```

không thuộc:

```text
Family 10
```

gọi:

```http
GET /families/10
```

Không được trả dữ liệu.

Khuyến nghị:

```text
404 Not Found
```

thay vì:

```text
403
```

để hạn chế tiết lộ Family ID tồn tại.

Quy tắc này phải nhất quán toàn project.

---

# 23. Update Family

Endpoint:

```http
PATCH /families/{family_id}
```

Cho phép:

```text
OWNER
ADMIN
```

Request:

```json
{
  "name": "Gia đình Nguyễn Văn A",
  "description": "Gia đình tại Hà Nội"
}
```

Không cho cập nhật:

```text
status
```

qua endpoint này.

Status phải có endpoint riêng.

---

# 24. Archive Family

Endpoint:

```http
POST /families/{family_id}/archive
```

Chỉ:

```text
OWNER
```

được thực hiện.

Flow:

```text
ACTIVE
  ↓
ARCHIVED
```

Không xóa:

```text
Membership
Health data
Medication
Cabinet
```

---

# 25. Restore Family

Endpoint:

```http
POST /families/{family_id}/restore
```

Chỉ:

```text
OWNER
```

Flow:

```text
ARCHIVED
   ↓
ACTIVE
```

---

# 26. Family Membership API

Các API:

```http
GET    /families/{family_id}/memberships
POST   /families/{family_id}/memberships
PATCH  /families/{family_id}/memberships/{membership_id}
DELETE /families/{family_id}/memberships/{membership_id}
```

---

# 27. List Memberships

Endpoint:

```http
GET /families/{family_id}/memberships
```

Cho phép:

```text
OWNER
ADMIN
CAREGIVER
VIEWER
```

Response:

```json
{
  "items": [
    {
      "id": 1,
      "user": {
        "id": 10,
        "email": "owner@example.com",
        "full_name": "Nguyen Van A"
      },
      "role": "OWNER"
    },
    {
      "id": 2,
      "user": {
        "id": 20,
        "email": "caregiver@example.com",
        "full_name": "Tran Thi B"
      },
      "role": "CAREGIVER"
    }
  ]
}
```

Không trả:

```text
password_hash
token
```

---

# 28. Add Existing User to Family

Trong Task 04 chưa xây invitation system.

Chỉ hỗ trợ thêm **User đã có tài khoản**.

Endpoint:

```http
POST /families/{family_id}/memberships
```

Cho phép:

```text
OWNER
ADMIN
```

Request đề xuất:

```json
{
  "email": "caregiver@example.com",
  "role": "CAREGIVER"
}
```

Flow:

```text
Normalize Email
      ↓
Find Existing User
      ↓
Check Existing Membership
      ↓
Validate Role
      ↓
Create Membership
```

---

# 29. Không cho tạo OWNER bằng Add Membership

Endpoint add membership không được nhận:

```text
OWNER
```

Role cho phép:

```text
ADMIN
CAREGIVER
VIEWER
```

Ownership transfer sẽ là task riêng sau nếu cần.

---

# 30. User chưa tồn tại

Nếu email chưa có tài khoản:

Task 04 không gửi invitation.

Có thể trả:

```text
404 User not found
```

hoặc business error:

```json
{
  "detail": "User account not found"
}
```

Email invitation sẽ được làm sau.

---

# 31. Duplicate Membership

Nếu user đã thuộc Family:

```text
409 Conflict
```

Response:

```json
{
  "detail": "User already belongs to this family"
}
```

---

# 32. Update Family Role

Endpoint:

```http
PATCH /families/{family_id}/memberships/{membership_id}
```

Chỉ:

```text
OWNER
```

được đổi role.

Request:

```json
{
  "role": "CAREGIVER"
}
```

Role cho phép:

```text
ADMIN
CAREGIVER
VIEWER
```

Không được:

```text
OWNER
```

---

# 33. Owner Protection

Không được:

```text
Remove OWNER
Downgrade OWNER
Archive bằng ADMIN
```

Nếu target membership:

```text
role = OWNER
```

thì API update/delete phải reject.

---

# 34. Remove Membership

Endpoint:

```http
DELETE /families/{family_id}/memberships/{membership_id}
```

Cho phép:

```text
OWNER
ADMIN
```

Nhưng:

- ADMIN không được remove OWNER;
- ADMIN không nên remove ADMIN khác trong MVP;
- OWNER được remove ADMIN/CAREGIVER/VIEWER;
- OWNER không được remove chính OWNER membership.

Khuyến nghị đơn giản cho MVP:

```text
OWNER → remove ADMIN/CAREGIVER/VIEWER
ADMIN → remove CAREGIVER/VIEWER
```

---

# 35. Self Leave Family

Task 04 có thể hỗ trợ:

```http
DELETE /families/{family_id}/memberships/me
```

Cho phép:

```text
ADMIN
CAREGIVER
VIEWER
```

Không cho:

```text
OWNER
```

rời Family nếu chưa chuyển ownership.

Nếu muốn giữ scope tối giản, endpoint này có thể để ngoài Task 04.

---

# 36. Family Authorization Dependency

Tạo:

```text
backend/app/modules/families/dependencies.py
```

Cần có dependency kiểu:

```python
get_family_membership(...)
```

Flow:

```text
current_user
     ↓
family_id
     ↓
Find membership
     ↓
Membership exists?
     ↓
Return membership
```

---

# 37. Require Family Roles

Có thể tạo helper:

```python
require_family_roles(
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
)
```

Dùng cho:

```text
Update Family
Add Membership
...
```

---

# 38. Authorization Matrix

| Action | OWNER | ADMIN | CAREGIVER | VIEWER |
|---|---:|---:|---:|---:|
| View Family | ✓ | ✓ | ✓ | ✓ |
| Update Family | ✓ | ✓ | ✗ | ✗ |
| Archive Family | ✓ | ✗ | ✗ | ✗ |
| Restore Family | ✓ | ✗ | ✗ | ✗ |
| List Memberships | ✓ | ✓ | ✓ | ✓ |
| Add User | ✓ | ✓ | ✗ | ✗ |
| Change Role | ✓ | ✗ | ✗ | ✗ |
| Remove Admin | ✓ | ✗ | ✗ | ✗ |
| Remove Caregiver | ✓ | ✓ | ✗ | ✗ |
| Remove Viewer | ✓ | ✓ | ✗ | ✗ |

---

# 39. Family Repository

Tạo:

```text
backend/app/modules/families/repository.py
```

Nhiệm vụ:

```text
create_family()
get_family_by_id()
list_families_for_user()
update_family()
get_membership()
list_memberships()
create_membership()
update_membership_role()
delete_membership()
```

Repository không quyết định permission.

---

# 40. Family Service

Tạo:

```text
backend/app/modules/families/service.py
```

Service xử lý:

```text
Business Rules
Authorization Rules
Owner Protection
Transaction
Conflict Check
Archive Logic
```

---

# 41. Family Schema

Tạo:

```text
backend/app/modules/families/schema.py
```

Các schema đề xuất:

```text
FamilyCreateRequest
FamilyUpdateRequest
FamilyResponse
FamilyListItem
FamilyListResponse

FamilyMembershipCreateRequest
FamilyMembershipUpdateRequest
FamilyMembershipResponse
FamilyMembershipListResponse
```

---

# 42. FamilyCreateRequest

```python
from pydantic import BaseModel, Field


class FamilyCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )
```

Service phải:

```text
strip name
```

sau validation.

---

# 43. Family Membership Schema

Ví dụ:

```python
class FamilyMembershipCreateRequest(BaseModel):
    email: str
    role: FamilyRole
```

Service phải reject:

```text
OWNER
```

---

# 44. Migration

Sau khi tạo models:

```bash
alembic revision --autogenerate -m "create family tables"
```

Review migration.

Phải tạo:

```text
families
family_memberships
```

và:

```text
Foreign Keys
Unique Constraint
Indexes
```

Sau đó:

```bash
alembic upgrade head
```

---

# 45. Model Registry

Cập nhật:

```text
backend/app/models/__init__.py
```

Import:

```python
from backend.app.models.family import Family
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.user import User
```

Để Alembic nhận metadata.

---

# 46. Router

Tạo:

```text
backend/app/modules/families/router.py
```

Endpoints:

```http
POST   /families
GET    /families

GET    /families/{family_id}
PATCH  /families/{family_id}

POST   /families/{family_id}/archive
POST   /families/{family_id}/restore

GET    /families/{family_id}/memberships
POST   /families/{family_id}/memberships

PATCH  /families/{family_id}/memberships/{membership_id}
DELETE /families/{family_id}/memberships/{membership_id}
```

---

# 47. API Router Registration

Trong:

```text
backend/app/api/router.py
```

bổ sung:

```python
from backend.app.modules.families.router import router as families_router


api_router.include_router(
    families_router,
    prefix="/families",
    tags=["Families"],
)
```

---

# 48. Create Family Test

Test:

```text
Authenticated User
        ↓
POST /families
```

Expected:

```text
201
```

Database phải có:

```text
1 Family
1 Membership
role = OWNER
```

---

# 49. Transaction Test

Giả lập lỗi khi tạo OWNER membership.

Expected:

```text
Family không được commit
```

Đây là test rất quan trọng.

---

# 50. List Families Test

Tạo:

```text
User A → Family 1 OWNER
User A → Family 2 CAREGIVER
User B → Family 3 OWNER
```

`GET /families` của User A chỉ trả:

```text
Family 1
Family 2
```

Không trả:

```text
Family 3
```

---

# 51. Family Isolation Test

User B không thuộc Family 1.

Gọi:

```http
GET /families/1
```

Expected:

```text
404
```

Không được leak dữ liệu.

---

# 52. Update Permission Test

OWNER:

```text
PATCH family
→ 200
```

ADMIN:

```text
PATCH family
→ 200
```

CAREGIVER:

```text
PATCH family
→ 403 hoặc 404 theo convention
```

VIEWER:

```text
PATCH family
→ reject
```

---

# 53. Archive Test

OWNER:

```text
archive
→ success
```

ADMIN:

```text
archive
→ reject
```

---

# 54. Add Membership Test

OWNER thêm existing User:

```text
role = CAREGIVER
```

Expected:

```text
201
```

---

# 55. Add Unknown User Test

Email chưa đăng ký.

Expected:

```text
404
```

---

# 56. Duplicate Membership Test

Thêm user đã tồn tại trong Family.

Expected:

```text
409
```

---

# 57. Owner Role Protection Test

Attempt:

```text
OWNER → VIEWER
```

Expected:

```text
reject
```

Attempt:

```text
DELETE OWNER membership
```

Expected:

```text
reject
```

---

# 58. Cross-Family Membership Attack Test

Ví dụ:

```text
Family A
membership_id = 5
```

User gửi:

```http
DELETE /families/B/memberships/5
```

Backend phải kiểm tra:

```text
membership.family_id == URL family_id
```

Nếu không:

```text
404
```

Đây là rule bắt buộc để tránh IDOR.

---

# 59. IDOR Protection

Mọi resource family-scoped phải kiểm tra:

```text
resource.family_id
```

khớp:

```text
authorized family_id
```

Không bao giờ chỉ dựa vào:

```text
resource_id
```

---

# 60. Query Scope Rule

Repository/service sau này không nên dùng:

```python
get_medication(medication_id)
```

rồi tin rằng user được quyền.

Phải ưu tiên pattern:

```python
get_medication(
    family_id=family_id,
    medication_id=medication_id,
)
```

Nguyên tắc này được đặt từ Task 04 để bảo vệ dữ liệu sức khỏe về sau.

---

# 61. Archived Family Rules

Khi Family:

```text
ARCHIVED
```

MVP đề xuất:

Cho phép:

```text
OWNER xem
OWNER restore
```

Không cho:

```text
thêm membership mới
update family data
tạo dữ liệu nghiệp vụ mới
```

Task sau sẽ áp dụng rule này cho Health/Medication.

---

# 62. Error Response

MVP tiếp tục sử dụng:

```json
{
  "detail": "..."
}
```

Các lỗi:

```text
Family not found
Membership not found
Insufficient family permission
User already belongs to family
Cannot modify owner membership
Family archived
```

---

# 63. Logging

Có thể log:

```text
FAMILY_CREATED
FAMILY_UPDATED
FAMILY_ARCHIVED
FAMILY_RESTORED
FAMILY_USER_ADDED
FAMILY_ROLE_CHANGED
FAMILY_USER_REMOVED
```

Không log dữ liệu nhạy cảm không cần thiết.

---

# 64. API Summary sau Task 04

```http
GET    /
GET    /health
GET    /health/db

POST   /auth/register
POST   /auth/login
POST   /auth/refresh
GET    /auth/me

POST   /families
GET    /families

GET    /families/{family_id}
PATCH  /families/{family_id}

POST   /families/{family_id}/archive
POST   /families/{family_id}/restore

GET    /families/{family_id}/memberships
POST   /families/{family_id}/memberships

PATCH  /families/{family_id}/memberships/{membership_id}
DELETE /families/{family_id}/memberships/{membership_id}
```

---

# 65. Example Full Flow

## User A Login

```text
User A
  ↓
JWT
```

## Create Family

```http
POST /families
```

```json
{
  "name": "Gia đình A"
}
```

Backend:

```text
Create Family #1
       ↓
Create Membership
user_id = A
role = OWNER
```

---

## Add Caregiver

User B đã có tài khoản.

```http
POST /families/1/memberships
```

```json
{
  "email": "userb@example.com",
  "role": "CAREGIVER"
}
```

Backend:

```text
Find User B
     ↓
Create Membership
     ↓
Family 1
User B
CAREGIVER
```

---

## User B Login

```text
User B
  ↓
GET /families
```

Response chứa:

```text
Family 1
my_role = CAREGIVER
```

---

# 66. Acceptance Criteria

Task 04 chỉ hoàn thành khi:

- [ ] `families` table tồn tại.
- [ ] `family_memberships` table tồn tại.
- [ ] Unique `(family_id, user_id)` hoạt động.
- [ ] Foreign keys hoạt động.
- [ ] Family Role được định nghĩa.
- [ ] Family Status được định nghĩa.
- [ ] Authenticated User tạo Family được.
- [ ] Người tạo tự động trở thành OWNER.
- [ ] Family + OWNER membership được tạo trong cùng transaction.
- [ ] List Families chỉ trả Family user có membership.
- [ ] Get Family có authorization.
- [ ] Cross-family access bị chặn.
- [ ] OWNER update Family được.
- [ ] ADMIN update Family được.
- [ ] CAREGIVER/VIEWER không update Family.
- [ ] OWNER archive Family được.
- [ ] OWNER restore Family được.
- [ ] ADMIN không archive Family.
- [ ] List Memberships hoạt động.
- [ ] OWNER/ADMIN thêm existing User được theo quyền.
- [ ] Không thêm OWNER qua endpoint membership.
- [ ] Duplicate membership trả conflict.
- [ ] OWNER role không thể downgrade.
- [ ] OWNER membership không thể xóa.
- [ ] Cross-family membership attack bị chặn.
- [ ] API không leak dữ liệu Family khác.
- [ ] Alembic migration pass.
- [ ] Family tests pass.

---

# 67. Definition of Done

Task 04 được đánh dấu:

```text
DONE
```

khi demo được đầy đủ chuỗi:

```text
User A Register/Login
        ↓
Create Family
        ↓
User A = OWNER
        ↓
User B Register
        ↓
OWNER add User B as CAREGIVER
        ↓
User B Login
        ↓
User B thấy Family
        ↓
User B xem Family
        ↓
User B không được sửa Family
        ↓
User C không thuộc Family
        ↓
User C không đọc được Family
```

và toàn bộ test authorization pass.

---

# 68. Deliverables

Sau Task 04 cần có:

```text
backend/app/models/
├── family.py
├── family_membership.py
└── __init__.py

backend/app/modules/families/
├── router.py
├── service.py
├── repository.py
├── schema.py
├── dependencies.py
└── exceptions.py

backend/app/shared/
└── enums.py

backend/alembic/versions/
└── xxxx_create_family_tables.py

backend/tests/
├── test_family_create.py
├── test_family_list.py
├── test_family_authorization.py
└── test_family_membership.py

docs/tasks/
└── TASK_04_FAMILY_MANAGEMENT.md
```

---

# 69. Không thực hiện trong Task 04

Không xây:

```text
Health Profile
Bố/Mẹ/Con relationship

Disease
Allergy
Medical History

Medication
Prescription

Cabinet
Compartment

AI
Digital Twin

Invite by email
Invite token
OTP
```

---

# 70. Task tiếp theo

Sau Task 04:

```text
TASK 05 — Family Member & Health Profile Foundation
```

Task 05 dự kiến xây:

```text
FamilyMember
Member Profile
Date of Birth
Gender
Height
Weight
Blood Type
Relationship Label
Emergency Contact

Health Profile
Medical Conditions
Allergy Profile
Drug Reaction History

Member CRUD
Family-scoped Authorization
Member Tests
```

---

# 71. Roadmap hiện tại

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

# 72. Nguyên tắc chuyển Task

Không chuyển sang Task 05 nếu chưa chứng minh được:

```text
USER
  ↓
FAMILY MEMBERSHIP
  ↓
FAMILY ROLE
  ↓
FAMILY AUTHORIZATION
```

và chưa test được dữ liệu Family bị cô lập giữa các tài khoản.

> **Task 04 là ranh giới bảo mật dữ liệu quan trọng đầu tiên của PharmaMind AI. Tất cả Health Profile, Medication, Prescription và Cabinet ở các task sau đều phải được scope theo Family ngay từ tầng database/repository/service.**
