# PharmaMind AI — TASK 08 SPECIFICATION

# TASK 08 — Medication Schedule Management

## 1. Mục tiêu

Task 08 xây dựng nền tảng **Medication Schedule Management** cho PharmaMind AI.

Sau Task 07, hệ thống đã có:

```text
User
Authentication
Family
Family Member
Health Profile
Medication
Prescription
Prescription Item
Dose
Frequency
Route
Instructions
```

Task 08 sẽ chuyển chỉ định trong `PrescriptionItem` thành lịch sử dụng thuốc cụ thể theo thời gian.

Ví dụ:

```text
Prescription Item:
Amlodipine 5 mg
1 viên
1 lần/ngày
```

được người dùng cấu hình thành:

```text
08:00
Mỗi ngày
Từ 01/11/2026
Đến 30/11/2026
```

Mục tiêu cuối cùng:

> **Mỗi thuốc trong đơn có thể được gắn với một hoặc nhiều thời điểm sử dụng cụ thể, từ đó hệ thống xác định được lịch hôm nay, liều tiếp theo và nền tảng cho reminder, medication event và smart cabinet ở các task sau.**

---

# 2. Điều kiện tiên quyết

Chỉ bắt đầu Task 08 khi Task 07 đã hoàn thành.

Phải test được:

```text
Family
  ↓
FamilyMember
  ↓
Prescription
  ↓
PrescriptionItem
  ↓
Medication
  ↓
Dose / Frequency
```

và Family scope hoạt động đúng.

---

# 3. Phạm vi Task 08

Task 08 bao gồm:

```text
1. MedicationSchedule Model
2. ScheduleTime Model
3. Schedule Status
4. Recurrence Type
5. Create Schedule
6. Update Schedule
7. Pause / Resume Schedule
8. Archive Schedule
9. Schedule Times
10. Daily Schedule Query
11. Next Dose Calculation
12. Schedule Validation
13. PrescriptionItem ↔ Schedule
14. Member ↔ Schedule
15. Medication ↔ Schedule
16. Family-scoped Authorization
17. Missed-dose foundation
18. Reminder preparation
19. Alembic Migration
20. Tests
```

Task 08 không bao gồm:

```text
Push Notification
Medication Event
Cabinet Open Event
Inventory Deduction
Adherence Calculation
MQTT
Digital Twin
AI Pharmacist
Background Worker Production
```

---

# 4. Kiến trúc tổng quát

```text
Prescription
   ↓
PrescriptionItem
   ↓
MedicationSchedule
   ↓
ScheduleTime
   ↓
Daily Timeline
   ↓
Next Dose
```

---

# 5. Phân biệt PrescriptionItem và MedicationSchedule

## PrescriptionItem

Lưu chỉ định:

```text
1 viên
2 lần/ngày
uống
sau ăn
```

## MedicationSchedule

Lưu lịch cụ thể:

```text
08:00
20:00
mỗi ngày
từ 01/11 đến 30/11
```

---

# 6. Tại sao phải tách ScheduleTime?

Nếu chỉ lưu:

```text
frequency_per_day = 2
```

hệ thống không biết chính xác uống lúc nào.

Do đó Task 08 tách:

```text
MedicationSchedule
       │
       ├── 08:00
       └── 20:00
```

---

# 7. MedicationSchedule Model

Tạo:

```text
backend/app/models/medication_schedule.py
```

Đề xuất:

```python
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    member_id: Mapped[int] = mapped_column(
        ForeignKey("family_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prescription_item_id: Mapped[int] = mapped_column(
        ForeignKey("prescription_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    family_medication_id: Mapped[int] = mapped_column(
        ForeignKey("family_medications.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    recurrence_type: Mapped[str] = mapped_column(
        String(30),
        default="DAILY",
        nullable=False,
    )

    recurrence_config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reminder_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    reminder_before_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    grace_period_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
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

# 8. ScheduleTime Model

Tạo:

```text
backend/app/models/schedule_time.py
```

```python
from datetime import datetime, time

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ScheduleTime(Base):
    __tablename__ = "schedule_times"

    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "time_of_day",
            name="uq_schedule_time",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("medication_schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    time_of_day: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

---

# 9. Schedule Status

```text
ACTIVE
PAUSED
COMPLETED
ARCHIVED
```

Ý nghĩa:

```text
ACTIVE     → lịch đang có hiệu lực
PAUSED     → tạm dừng
COMPLETED  → đã hết liệu trình
ARCHIVED   → chỉ lưu lịch sử
```

---

# 10. Recurrence Type

MVP đề xuất:

```text
DAILY
WEEKLY
CUSTOM
PRN
```

Trong đó:

```text
DAILY  → mỗi ngày
WEEKLY → theo ngày trong tuần
CUSTOM → rule riêng
PRN    → khi cần
```

Task 08 nên triển khai chắc chắn `DAILY`, đồng thời chuẩn bị dữ liệu cho các kiểu còn lại.

---

# 11. recurrence_config

Dùng `JSONB` để chuẩn bị cho recurrence mở rộng.

Ví dụ WEEKLY:

```json
{
  "days_of_week": ["MONDAY", "WEDNESDAY", "FRIDAY"]
}
```

Ví dụ CUSTOM:

```json
{
  "interval_days": 2
}
```

Không đưa business logic recurrence phức tạp vào Task 08 nếu chưa cần.

---

# 12. PRN Schedule

`PRN` nghĩa là dùng khi cần.

Ví dụ:

```text
Paracetamol
1 viên
khi đau
```

Schedule PRN có thể có:

```text
times = []
recurrence_type = PRN
```

---

# 13. Create Schedule API

```http
POST /families/{family_id}/schedules
```

Quyền:

```text
OWNER
ADMIN
CAREGIVER
```

VIEWER không được tạo.

---

# 14. Create Schedule Request

```json
{
  "prescription_item_id": 11,
  "start_date": "2026-11-01",
  "end_date": "2026-11-30",
  "recurrence_type": "DAILY",
  "times": ["08:00"],
  "reminder_enabled": true,
  "reminder_before_minutes": 0,
  "grace_period_minutes": 30,
  "notes": "Uống sau ăn sáng"
}
```

---

# 15. Create Schedule Flow

```text
Authenticated User
      ↓
Family Authorization
      ↓
Get PrescriptionItem
      ↓
Validate Prescription
      ↓
Derive Member
      ↓
Derive FamilyMedication
      ↓
Validate Family Scope
      ↓
Validate Date Range
      ↓
Validate Frequency
      ↓
Validate Times
      ↓
Create MedicationSchedule
      ↓
Create ScheduleTime records
      ↓
Commit
```

---

# 16. PrescriptionItem là nguồn dữ liệu gốc

Khi tạo Schedule:

```text
member_id
family_medication_id
```

không lấy trực tiếp từ client.

Phải derive từ:

```text
PrescriptionItem
      ↓
Prescription
      ↓
Member
```

Mục tiêu là tránh client truyền sai Member hoặc Medication.

---

# 17. Prescription Status Rule

Không tạo Schedule mới nếu Prescription:

```text
ARCHIVED
COMPLETED
```

Chỉ cho phép từ Prescription còn hợp lệ theo business rule hiện tại.

---

# 18. Frequency Consistency Check

Ví dụ PrescriptionItem:

```text
frequency_per_day = 2
```

Client gửi:

```json
{
  "times": ["08:00"]
}
```

MVP đề xuất reject:

```text
Schedule time count does not match prescription frequency
```

Nếu frequency không thể biểu diễn dạng số, dùng recurrence phù hợp hoặc `PRN`.

---

# 19. Time Validation

Mỗi giờ phải hợp lệ:

```text
00:00 → 23:59
```

Không duplicate trong cùng Schedule.

Ví dụ không hợp lệ:

```text
25:00
08:00, 08:00
```

---

# 20. Date Validation

Rule:

```text
start_date <= end_date
```

Nếu `end_date = null`, schedule được hiểu là chưa xác định ngày kết thúc.

---

# 21. Prescription Date Bounds

Nếu Prescription có `start_date`:

```text
schedule.start_date >= prescription.start_date
```

Nếu Prescription có `end_date`:

```text
schedule.end_date <= prescription.end_date
```

Không tự kéo dài đơn thuốc.

---

# 22. List Schedules

```http
GET /families/{family_id}/schedules
```

Query params đề xuất:

```text
member_id
status
date
medication_id
include_archived
```

---

# 23. List Member Schedules

```http
GET /families/{family_id}/members/{member_id}/schedules
```

---

# 24. Get Schedule Detail

```http
GET /families/{family_id}/schedules/{schedule_id}
```

Response ví dụ:

```json
{
  "id": 20,
  "member": {
    "id": 3,
    "full_name": "Nguyen Thi Lan"
  },
  "medication": {
    "id": 10,
    "name": "Amlodipine",
    "strength": "5 mg"
  },
  "dose_amount": 1,
  "dose_unit": "TABLET",
  "recurrence_type": "DAILY",
  "start_date": "2026-11-01",
  "end_date": "2026-11-30",
  "times": ["08:00"],
  "status": "ACTIVE"
}
```

---

# 25. Update Schedule

```http
PATCH /families/{family_id}/schedules/{schedule_id}
```

Cho cập nhật:

```text
start_date
end_date
recurrence_type
recurrence_config
times
reminder_enabled
reminder_before_minutes
grace_period_minutes
notes
```

Không cho cập nhật trực tiếp:

```text
family_id
member_id
family_medication_id
prescription_item_id
```

---

# 26. Update Schedule Transaction

Nếu thay đổi times:

```text
Validate list mới
      ↓
Delete old ScheduleTime
      ↓
Insert new ScheduleTime
      ↓
Commit
```

Tất cả phải nằm trong cùng transaction.

---

# 27. Pause Schedule

```http
POST /families/{family_id}/schedules/{schedule_id}/pause
```

```text
ACTIVE → PAUSED
```

---

# 28. Resume Schedule

```http
POST /families/{family_id}/schedules/{schedule_id}/resume
```

```text
PAUSED → ACTIVE
```

Nếu `end_date < today`, không resume.

---

# 29. Complete Schedule

```http
POST /families/{family_id}/schedules/{schedule_id}/complete
```

```text
ACTIVE / PAUSED → COMPLETED
```

---

# 30. Archive Schedule

```http
POST /families/{family_id}/schedules/{schedule_id}/archive
```

Quyền:

```text
OWNER
ADMIN
```

---

# 31. Restore Schedule

```http
POST /families/{family_id}/schedules/{schedule_id}/restore
```

Khuyến nghị restore về:

```text
PAUSED
```

thay vì ACTIVE để người dùng kiểm tra lịch trước.

---

# 32. Daily Schedule Query

Endpoint quan trọng cho App:

```http
GET /families/{family_id}/members/{member_id}/schedule-day?date=2026-11-01
```

Response:

```json
{
  "date": "2026-11-01",
  "items": [
    {
      "schedule_id": 20,
      "time": "08:00",
      "medication": {
        "id": 10,
        "name": "Amlodipine",
        "strength": "5 mg"
      },
      "dose_amount": 1,
      "dose_unit": "TABLET",
      "status": "SCHEDULED"
    }
  ]
}
```

---

# 33. Daily Timeline

Ứng dụng có thể hiển thị:

```text
08:00
Amlodipine 5 mg
1 viên

12:00
Vitamin D
1 viên

20:00
Metformin
1 viên
```

---

# 34. Next Dose API

```http
GET /families/{family_id}/members/{member_id}/next-dose
```

Response:

```json
{
  "schedule_id": 20,
  "date": "2026-11-01",
  "time": "20:00",
  "medication": {
    "id": 10,
    "name": "Amlodipine"
  },
  "dose_amount": 1,
  "dose_unit": "TABLET"
}
```

---

# 35. Next Dose Calculation

Thuật toán cơ bản:

```text
Get ACTIVE schedules
      ↓
Filter schedule by valid date range
      ↓
Apply recurrence rule
      ↓
Generate today's scheduled times
      ↓
Ignore times before now
      ↓
Find earliest remaining
      ↓
If none today → scan next valid date
```

Không cần materialize mọi dose trong database ở Task 08.

---

# 36. Timezone

Schedule theo giờ địa phương của Family.

Khuyến nghị sau này bổ sung vào Family:

```text
timezone
```

Trong giai đoạn hiện tại có thể dùng:

```env
DEFAULT_TIMEZONE=Asia/Bangkok
```

Mọi logic `next-dose` phải sử dụng timezone-aware datetime.

---

# 37. Reminder Foundation

Task 08 chỉ lưu cấu hình:

```text
reminder_enabled
reminder_before_minutes
```

Ví dụ:

```text
08:00 dose
reminder_before_minutes = 10
```

Sau này Notification Engine có thể trigger lúc:

```text
07:50
```

---

# 38. Grace Period Foundation

Field:

```text
grace_period_minutes
```

Ví dụ:

```text
scheduled_at = 08:00
grace_period = 30 phút
```

Sau Task Medication Event, nếu tới 08:30 chưa có event phù hợp thì mới cân nhắc trạng thái `MISSED`.

Task 08 chưa tự đánh dấu missed.

---

# 39. Schedule Instance Concept

Task 08 chưa tạo bảng `schedule_instances`.

Một occurrence có thể tính động từ:

```text
MedicationSchedule
+
ScheduleTime
+
Date
```

Task sau có thể dùng occurrence này để tạo `MedicationEvent`.

---

# 40. Không trừ tồn kho trong Task 08

Schedule chỉ là kế hoạch.

Không được:

```text
quantity = quantity - dose
```

khi đến giờ.

Chỉ Medication Event đã xác nhận mới được phép ảnh hưởng tồn kho ở task sau.

---

# 41. Family Scope Rule

Mọi query bắt buộc scope theo `family_id`.

Đúng:

```python
get_schedule(
    family_id=family_id,
    schedule_id=schedule_id,
)
```

Không dùng:

```python
get_schedule(schedule_id)
```

rồi mới kiểm tra sau.

---

# 42. Cross-Family Attack Protection

Schedule thuộc Family A.

User Family B gọi:

```http
GET /families/B/schedules/20
```

Expected:

```text
404
```

Không leak schedule tồn tại ở Family khác.

---

# 43. Prescription Scope Rule

Schedule phải tham chiếu `PrescriptionItem` thuộc cùng Family.

Không được tạo Schedule từ item ở Family khác.

---

# 44. Member Scope Rule

Member phải derive từ Prescription.

Client không được chọn tùy ý Member khác.

---

# 45. Medication Scope Rule

Medication phải derive từ PrescriptionItem.

Client không được tự đổi thuốc trong Schedule.

---

# 46. Archived Family Rule

Nếu Family `ARCHIVED`:

Không cho:

```text
Create Schedule
Update Schedule
Pause / Resume
Complete
```

Chỉ cho view theo quyền.

---

# 47. Archived Member Rule

Không tạo Schedule mới cho Member `ARCHIVED`.

---

# 48. Archived Medication Rule

Không tạo Schedule mới nếu FamilyMedication `ARCHIVED`.

---

# 49. Expired Medication Rule

Nếu Medication đã hết hạn:

```text
không cho tạo schedule mới
```

Existing schedule không tự xóa; response có thể trả warning.

Hệ thống không tự đưa ra quyết định điều trị.

---

# 50. Depleted Medication Rule

Medication `DEPLETED` vẫn có thể còn Schedule để giữ lịch sử.

Không tự xóa Schedule.

Task notification sau có thể cảnh báo tồn kho bằng 0.

---

# 51. Authorization Matrix

| Action | OWNER | ADMIN | CAREGIVER | VIEWER |
|---|---:|---:|---:|---:|
| View schedules | ✓ | ✓ | ✓ | ✓ |
| Create schedule | ✓ | ✓ | ✓ | ✗ |
| Update schedule | ✓ | ✓ | ✓ | ✗ |
| Pause | ✓ | ✓ | ✓ | ✗ |
| Resume | ✓ | ✓ | ✓ | ✗ |
| Complete | ✓ | ✓ | ✓ | ✗ |
| Archive | ✓ | ✓ | ✗ | ✗ |
| Restore | ✓ | ✓ | ✗ | ✗ |

---

# 52. Repository Layer

Tạo:

```text
backend/app/modules/schedules/repository.py
```

Nhiệm vụ:

```text
create_schedule()
get_schedule()
list_schedules()
update_schedule()

create_schedule_times()
replace_schedule_times()

pause_schedule()
resume_schedule()
complete_schedule()
archive_schedule()
restore_schedule()

get_daily_schedule()
get_next_dose()
```

---

# 53. Service Layer

Tạo:

```text
backend/app/modules/schedules/service.py
```

Service chịu trách nhiệm:

```text
authorization
prescription validation
member validation
medication validation
date validation
frequency consistency
recurrence logic
next-dose calculation
status transition
transaction
```

---

# 54. Schema Layer

Tạo:

```text
backend/app/modules/schedules/schema.py
```

Schema đề xuất:

```text
MedicationScheduleCreateRequest
MedicationScheduleUpdateRequest
MedicationScheduleResponse
MedicationScheduleListResponse
ScheduleTimeResponse
DailyScheduleResponse
DailyScheduleItem
NextDoseResponse
```

---

# 55. Enums

Tạo:

```text
backend/app/modules/schedules/enums.py
```

Bao gồm:

```text
ScheduleStatus
RecurrenceType
DayOfWeek
```

---

# 56. Cấu trúc thư mục sau Task 08

```text
backend/
│
├── app/
│   ├── models/
│   │   ├── medication_schedule.py
│   │   ├── schedule_time.py
│   │   └── __init__.py
│   │
│   └── modules/
│       └── schedules/
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
│       └── xxxx_create_medication_schedule_tables.py
│
└── tests/
    ├── test_schedule_create.py
    ├── test_schedule_update.py
    ├── test_schedule_daily.py
    ├── test_schedule_next_dose.py
    ├── test_schedule_authorization.py
    └── test_schedule_validation.py
```

---

# 57. Model Registry

Cập nhật:

```text
backend/app/models/__init__.py
```

Import:

```python
from backend.app.models.medication_schedule import MedicationSchedule
from backend.app.models.schedule_time import ScheduleTime
```

---

# 58. Alembic Migration

Tạo:

```bash
alembic revision --autogenerate -m "create medication schedule tables"
```

Review migration.

Sau đó:

```bash
alembic upgrade head
```

Migration phải tạo:

```text
medication_schedules
schedule_times
```

với:

```text
Foreign Keys
Indexes
Unique Constraint
Not Null Constraints
```

---

# 59. Test — Create Daily Schedule

PrescriptionItem:

```text
1 lần/ngày
```

Request:

```text
08:00
```

Expected:

```text
201
```

---

# 60. Test — Frequency Mismatch

Prescription:

```text
2 lần/ngày
```

Request:

```text
["08:00"]
```

Expected:

```text
reject
```

---

# 61. Test — Duplicate Time

Request:

```json
{
  "times": ["08:00", "08:00"]
}
```

Expected:

```text
422 hoặc 409
```

---

# 62. Test — Invalid Time

```text
25:00
```

Expected:

```text
422
```

---

# 63. Test — Invalid Date Range

```text
start_date > end_date
```

Expected:

```text
422
```

---

# 64. Test — Schedule Before Prescription

Prescription starts:

```text
10/11
```

Schedule starts:

```text
01/11
```

Expected:

```text
reject
```

---

# 65. Test — Schedule After Prescription End

Prescription ends:

```text
30/11
```

Schedule ends:

```text
10/12
```

Expected:

```text
reject
```

---

# 66. Test — PRN

Prescription:

```text
Khi cần
```

Schedule:

```text
recurrence_type = PRN
times = []
```

Expected:

```text
success
```

---

# 67. Test — Daily Timeline

Có schedules:

```text
08:00
12:00
20:00
```

Query date hiện tại.

Expected:

```text
items sorted ascending
```

---

# 68. Test — Next Dose

Current time:

```text
10:00
```

Schedules:

```text
08:00
12:00
20:00
```

Expected:

```text
12:00
```

---

# 69. Test — Next Day Dose

Current time:

```text
22:00
```

Không còn dose hôm nay.

Expected:

```text
dose đầu tiên của ngày hợp lệ tiếp theo
```

---

# 70. Test — Paused Schedule

Schedule `PAUSED` không xuất hiện trong:

```text
next-dose
active daily schedule
```

---

# 71. Test — Archived Schedule

Không xuất hiện mặc định.

Chỉ xuất hiện khi request phù hợp như:

```text
include_archived=true
```

---

# 72. Test — Cross-Family Read

Schedule Family A.

User Family B.

Expected:

```text
404
```

---

# 73. Test — Viewer Cannot Create

VIEWER gọi create.

Expected:

```text
reject
```

---

# 74. Test — Caregiver Can Update

CAREGIVER chỉnh:

```text
08:00 → 08:30
```

Expected:

```text
success
```

---

# 75. API Summary sau Task 08

```http
POST /families/{family_id}/schedules
GET  /families/{family_id}/schedules

GET /families/{family_id}/members/{member_id}/schedules

GET   /families/{family_id}/schedules/{schedule_id}
PATCH /families/{family_id}/schedules/{schedule_id}

POST /families/{family_id}/schedules/{schedule_id}/pause
POST /families/{family_id}/schedules/{schedule_id}/resume
POST /families/{family_id}/schedules/{schedule_id}/complete
POST /families/{family_id}/schedules/{schedule_id}/archive
POST /families/{family_id}/schedules/{schedule_id}/restore

GET /families/{family_id}/members/{member_id}/schedule-day
GET /families/{family_id}/members/{member_id}/next-dose
```

---

# 76. Example Full Flow

```text
Login
 ↓
Select Family
 ↓
Select Member
 ↓
Open Prescription
 ↓
Select PrescriptionItem
 ↓
Create Schedule
 ↓
Set 08:00 / 20:00
 ↓
ACTIVE
 ↓
Daily Timeline
 ↓
Next Dose
 ↓
Pause / Resume
```

---

# 77. Dữ liệu chuẩn bị cho Task 09

Task 08 phải cung cấp được:

```text
member
medication
dose
schedule date
schedule time
next dose
```

Task 09 sẽ dùng dữ liệu này cho:

```text
Smart Cabinet Mock / Hardware Simulator
```

Ví dụ:

```text
08:00
Amlodipine
Member: Bà Lan
```

sẽ có thể được mapping tới ngăn tủ ở Task 09.

---

# 78. Dữ liệu chuẩn bị cho Medication Event

Task 08 chưa tạo Event nhưng phải đủ dữ liệu cho task sau tạo:

```text
scheduled_at
member_id
family_medication_id
schedule_id
```

---

# 79. Acceptance Criteria

Task 08 chỉ hoàn thành khi:

- [ ] `medication_schedules` table tồn tại.
- [ ] `schedule_times` table tồn tại.
- [ ] Schedule tham chiếu đúng `PrescriptionItem`.
- [ ] Member và Medication được derive đúng nguồn.
- [ ] Family scope hoạt động.
- [ ] Schedule time không duplicate.
- [ ] Date validation hoạt động.
- [ ] Frequency consistency hoạt động.
- [ ] PRN hoạt động.
- [ ] Create Schedule hoạt động.
- [ ] List Schedule hoạt động.
- [ ] Get Detail hoạt động.
- [ ] Update Schedule hoạt động.
- [ ] Pause/Resume hoạt động.
- [ ] Complete hoạt động.
- [ ] Archive/Restore hoạt động.
- [ ] Daily Schedule hoạt động.
- [ ] Next Dose hoạt động.
- [ ] Paused Schedule không xuất hiện trong next dose.
- [ ] Archived Schedule không xuất hiện mặc định.
- [ ] Expired medication không được dùng để tạo Schedule mới.
- [ ] Cross-Family access bị chặn.
- [ ] Viewer không chỉnh sửa được.
- [ ] Caregiver chỉnh sửa được theo role matrix.
- [ ] Alembic migration pass.
- [ ] Tests pass.

---

# 80. Definition of Done

Task 08 được đánh dấu:

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
Prescription
 ↓
Prescription Item
 ↓
Create Schedule
 ↓
Set Times
 ↓
Daily Timeline
 ↓
Next Dose
 ↓
Pause / Resume
```

và toàn bộ Family authorization + schedule validation pass.

---

# 81. Deliverables

Sau Task 08 cần có:

```text
backend/app/models/
├── medication_schedule.py
├── schedule_time.py
└── __init__.py

backend/app/modules/schedules/
├── router.py
├── service.py
├── repository.py
├── schema.py
├── dependencies.py
├── enums.py
└── exceptions.py

backend/alembic/versions/
└── xxxx_create_medication_schedule_tables.py

backend/tests/
├── test_schedule_create.py
├── test_schedule_update.py
├── test_schedule_daily.py
├── test_schedule_next_dose.py
├── test_schedule_authorization.py
└── test_schedule_validation.py

docs/tasks/
└── TASK_08_MEDICATION_SCHEDULE.md
```

---

# 82. Không thực hiện trong Task 08

Không làm:

```text
Push Notification
Local Notification
Email / SMS

Medication Event
Taken / Missed / Skipped
Adherence

Inventory deduction
Cabinet event
MQTT
Digital Twin

AI
OCR
RAG
```

---

# 83. Task tiếp theo

Sau Task 08:

```text
TASK 09 — Smart Cabinet Mock / Hardware Simulator
```

Task 09 dự kiến xây:

```text
Cabinet
Compartment
Medication ↔ Compartment
Hardware Simulator
Cabinet State
Open / Close Event
Online / Offline
Mock Command
Mock Sensor Event
WebSocket update
Family-scoped Authorization
Tests
```

---

# 84. Roadmap hiện tại

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

# 85. Nguyên tắc chuyển Task

Không chuyển sang Task 09 nếu chưa chứng minh được:

```text
PRESCRIPTION ITEM
      ↓
MEDICATION SCHEDULE
      ↓
SCHEDULE TIME
      ↓
DAILY TIMELINE
      ↓
NEXT DOSE
```

và chưa test đầy đủ Family scope, status transition và date/time validation.

> **Task 08 là lớp thời gian của PharmaMind AI. Task 09 và Task 10 sẽ dùng trực tiếp dữ liệu Schedule để mô phỏng tủ thuốc, highlight đúng ngăn và đồng bộ Digital Twin.**
