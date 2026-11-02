# PharmaMind AI — TASK 09 SPECIFICATION

# TASK 09 — Smart Cabinet Mock / Hardware Simulator

## 1. Mục tiêu

Task 09 xây dựng lớp **Smart Cabinet Mock / Hardware Simulator** cho PharmaMind AI.

Sau Task 08, hệ thống đã có:

```text
User
Authentication
Family
Family Member
Health Profile
Medication
Prescription
Medication Schedule
Daily Timeline
Next Dose
```

Task 09 sẽ bổ sung lớp thiết bị tủ thuốc thông minh, nhưng **chưa cần phần cứng ESP32 thật**.

Hệ thống sẽ có thể:

```text
Tạo Smart Cabinet
Tạo 9 ngăn thuốc
Gán thuốc vào ngăn
Mô phỏng Cabinet Online / Offline
Mô phỏng mở ngăn
Mô phỏng đóng ngăn
Mô phỏng state của từng ngăn
Gửi command từ Backend đến Simulator
Nhận event từ Simulator
Lưu Cabinet Event
Đồng bộ realtime qua WebSocket
Chuẩn bị API cho Digital Twin 3D
```

Mục tiêu cuối cùng:

> **Backend và App có thể hoạt động như đang kết nối với tủ thuốc thật, trong khi phần cứng chưa hoàn thiện. Sau này Hardware Simulator được thay bằng ESP32 + MQTT mà không phải thay đổi business logic cốt lõi.**

---

# 2. Điều kiện tiên quyết

Chỉ bắt đầu Task 09 khi Task 08 đã hoàn thành.

Phải test được chuỗi:

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

và Family authorization hoạt động đúng.

---

# 3. Phạm vi Task 09

Task 09 bao gồm:

```text
1. Cabinet Model
2. Compartment Model
3. Cabinet Event Model
4. Cabinet Status
5. Compartment Status
6. Cabinet Command
7. Hardware Simulator Service
8. Tạo cabinet
9. Tạo tự động 9 compartments
10. Gán Medication vào Compartment
11. Bỏ Medication khỏi Compartment
12. Cabinet Online / Offline
13. Compartment Open / Close
14. Mock Sensor Event
15. Command → Simulator
16. Event → Backend
17. WebSocket realtime
18. Cabinet State API
19. Compartment Detail API
20. Family-scoped Authorization
21. Event Logging
22. Alembic Migration
23. Tests
```

Task 09 không bao gồm:

```text
ESP32 firmware thật
MQTT production
Physical sensor
Motor / lock thật
Digital Twin 3D UI
Push Notification
Automatic inventory deduction
Medication taken confirmation
AI Pharmacist
```

---

# 4. Kiến trúc tổng quát

```text
Mobile App
    ↓
FastAPI Backend
    ↓
Cabinet Service
    ↓
Hardware Interface
    ↓
Hardware Simulator
    ↓
Mock Event
    ↓
Backend Event Handler
    ↓
Database
    ↓
WebSocket
    ↓
Mobile App
```

---

# 5. Nguyên tắc quan trọng

Business logic không được phụ thuộc trực tiếp vào:

```text
ESP32
```

Backend phải giao tiếp thông qua abstraction:

```text
Hardware Interface
```

Implementation hiện tại:

```text
Hardware Simulator
```

Implementation sau này:

```text
MQTT Hardware Adapter
```

---

# 6. Kiến trúc thay thế phần cứng

Hiện tại:

```text
Backend
  ↓
HardwareSimulator
```

Sau này:

```text
Backend
  ↓
MQTTHardwareAdapter
  ↓
MQTT Broker
  ↓
ESP32
```

Các module:

```text
Medication
Schedule
Cabinet
Digital Twin
```

không phải viết lại.

---

# 7. Cabinet Model

Tạo:

```text
backend/app/models/cabinet.py
```

Đề xuất:

```python
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Cabinet(Base):
    __tablename__ = "cabinets"

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

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    device_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="OFFLINE",
        nullable=False,
        index=True,
    )

    hardware_mode: Mapped[str] = mapped_column(
        String(30),
        default="SIMULATOR",
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

# 8. Cabinet Status

Đề xuất:

```text
ONLINE
OFFLINE
ERROR
MAINTENANCE
ARCHIVED
```

Trong Task 09 dùng chính:

```text
ONLINE
OFFLINE
ERROR
ARCHIVED
```

---

# 9. Hardware Mode

Đề xuất:

```text
SIMULATOR
MQTT
```

Task 09 mặc định:

```text
SIMULATOR
```

Sau này khi có ESP32:

```text
MQTT
```

---

# 10. Device Code

Mỗi cabinet cần mã duy nhất.

Ví dụ:

```text
CAB-000001
```

hoặc:

```text
PM-CAB-A1B2C3
```

Không dùng:

```text
family_id
```

làm device code trực tiếp.

---

# 11. Compartment Model

Tạo:

```text
backend/app/models/compartment.py
```

Đề xuất:

```python
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Compartment(Base):
    __tablename__ = "compartments"

    __table_args__ = (
        UniqueConstraint(
            "cabinet_id",
            "position",
            name="uq_cabinet_compartment_position",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    cabinet_id: Mapped[int] = mapped_column(
        ForeignKey(
            "cabinets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    family_medication_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "family_medications.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="EMPTY",
        nullable=False,
        index=True,
    )

    is_open: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
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

# 12. 9 Compartments

Cabinet MVP có:

```text
9 compartments
```

Mapping:

```text
1 2 3
4 5 6
7 8 9
```

Khi tạo Cabinet:

```text
Compartment 1 → 9
```

phải được tạo tự động trong cùng transaction.

---

# 13. Compartment Status

Đề xuất:

```text
EMPTY
AVAILABLE
DOSE_DUE
LOW_STOCK
EXPIRING
WARNING
OPEN
OFFLINE
```

Ở Task 09 cần tối thiểu:

```text
EMPTY
AVAILABLE
OPEN
OFFLINE
WARNING
```

Các trạng thái:

```text
DOSE_DUE
LOW_STOCK
EXPIRING
```

sẽ được dùng mạnh hơn ở task sau.

---

# 14. Compartment và Medication

MVP:

```text
1 compartment
→ tối đa 1 FamilyMedication
```

Một Medication có thể nằm ở:

```text
1 compartment
```

trong Task 09.

Nếu sau này cần nhiều lô / nhiều ngăn:

```text
data model sẽ được mở rộng
```

---

# 15. Không duplicate Medication trong nhiều Compartment

Task 09 đề xuất:

```text
1 FamilyMedication
→ 1 Compartment
```

Service phải reject nếu Medication đã được gán ngăn khác.

---

# 16. Cabinet Event Model

Tạo:

```text
backend/app/models/cabinet_event.py
```

Đề xuất:

```python
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class CabinetEvent(Base):
    __tablename__ = "cabinet_events"

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

    cabinet_id: Mapped[int] = mapped_column(
        ForeignKey(
            "cabinets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    compartment_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "compartments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        default="SIMULATOR",
        nullable=False,
    )

    payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
```

---

# 17. Event Type

Đề xuất:

```text
CABINET_ONLINE
CABINET_OFFLINE

COMPARTMENT_OPEN
COMPARTMENT_CLOSE

COMPARTMENT_ASSIGN_MEDICATION
COMPARTMENT_UNASSIGN_MEDICATION

DEVICE_ERROR
DEVICE_RECOVERED

STATE_SYNC
```

---

# 18. Command Type

Đề xuất:

```text
SET_ONLINE
SET_OFFLINE

OPEN_COMPARTMENT
CLOSE_COMPARTMENT

SYNC_STATE
RESET_SIMULATOR
```

Task 09 chưa cần:

```text
DISPENSE
LOCK
UNLOCK
```

nếu chưa có cơ khí thật.

---

# 19. Hardware Interface

Tạo interface:

```text
backend/app/integrations/hardware/base.py
```

Ví dụ:

```python
from abc import ABC, abstractmethod


class HardwareAdapter(ABC):

    @abstractmethod
    async def open_compartment(
        self,
        cabinet_id: int,
        position: int,
    ) -> None:
        ...

    @abstractmethod
    async def close_compartment(
        self,
        cabinet_id: int,
        position: int,
    ) -> None:
        ...

    @abstractmethod
    async def get_state(
        self,
        cabinet_id: int,
    ) -> dict:
        ...
```

---

# 20. Hardware Simulator Implementation

Tạo:

```text
backend/app/integrations/hardware/simulator.py
```

Simulator implement:

```text
HardwareAdapter
```

và quản lý state:

```text
cabinet online/offline
compartment open/close
```

---

# 21. Hardware Simulator State

Ví dụ:

```json
{
  "cabinet_id": 1,
  "status": "ONLINE",
  "compartments": [
    {
      "position": 1,
      "is_open": false
    },
    {
      "position": 2,
      "is_open": true
    }
  ]
}
```

---

# 22. Simulator không phải Source of Truth duy nhất

Source of truth business:

```text
PostgreSQL
```

Simulator chỉ mô phỏng:

```text
hardware state
```

Backend phải reconcile state khi nhận event.

---

# 23. Tạo Cabinet API

Endpoint:

```http
POST /families/{family_id}/cabinets
```

Quyền:

```text
OWNER
ADMIN
```

Request:

```json
{
  "name": "Tủ thuốc gia đình",
  "device_code": "PM-CAB-001"
}
```

---

# 24. Create Cabinet Flow

```text
Authenticated User
      ↓
Family Authorization
      ↓
Create Cabinet
      ↓
Create Compartments 1..9
      ↓
Commit
      ↓
Initialize Simulator State
```

Nếu tạo Compartment lỗi:

```text
Rollback Cabinet
```

---

# 25. Một Family có bao nhiêu Cabinet?

MVP đề xuất:

```text
1 Family
→ 1 Cabinet
```

Service có thể enforce:

```text
max 1 active cabinet / family
```

Sau này có thể mở rộng nhiều tủ.

---

# 26. List Cabinet

Endpoint:

```http
GET /families/{family_id}/cabinets
```

Response:

```json
{
  "items": [
    {
      "id": 1,
      "name": "Tủ thuốc gia đình",
      "device_code": "PM-CAB-001",
      "status": "ONLINE",
      "hardware_mode": "SIMULATOR"
    }
  ]
}
```

---

# 27. Get Cabinet Detail

Endpoint:

```http
GET /families/{family_id}/cabinets/{cabinet_id}
```

Response:

```json
{
  "id": 1,
  "name": "Tủ thuốc gia đình",
  "status": "ONLINE",
  "last_seen_at": "2026-11-01T10:30:00Z",
  "compartments": [
    {
      "id": 1,
      "position": 1,
      "status": "AVAILABLE",
      "is_open": false,
      "medication": {
        "id": 10,
        "name": "Amlodipine"
      }
    }
  ]
}
```

---

# 28. Compartment List API

Endpoint:

```http
GET /families/{family_id}/cabinets/{cabinet_id}/compartments
```

Response phải luôn sort:

```text
position ASC
```

---

# 29. Assign Medication to Compartment

Endpoint:

```http
PUT /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/medication
```

Request:

```json
{
  "family_medication_id": 10
}
```

---

# 30. Assign Medication Flow

```text
Family Authorization
      ↓
Get Cabinet
      ↓
Get Compartment
      ↓
Get FamilyMedication
      ↓
Validate same Family
      ↓
Check Medication not assigned elsewhere
      ↓
Assign
      ↓
status = AVAILABLE
      ↓
Save Event
```

---

# 31. Unassign Medication

Endpoint:

```http
DELETE /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/medication
```

Kết quả:

```text
family_medication_id = null
status = EMPTY
```

---

# 32. Không assign Archived Medication

Nếu Medication:

```text
ARCHIVED
```

phải reject.

---

# 33. Expired Medication

Task 09 có thể cho phép hiển thị expired medication đang ở ngăn cũ, nhưng không nên assign mới.

Rule:

```text
new assignment of EXPIRED medication
→ reject
```

---

# 34. Cabinet Online API

Endpoint mô phỏng:

```http
POST /families/{family_id}/cabinets/{cabinet_id}/simulator/online
```

Kết quả:

```text
Cabinet.status = ONLINE
last_seen_at = now
```

Save event:

```text
CABINET_ONLINE
```

---

# 35. Cabinet Offline API

Endpoint:

```http
POST /families/{family_id}/cabinets/{cabinet_id}/simulator/offline
```

Kết quả:

```text
Cabinet.status = OFFLINE
```

Save:

```text
CABINET_OFFLINE
```

---

# 36. Open Compartment API

Endpoint:

```http
POST /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/open
```

Flow:

```text
Validate Cabinet ONLINE
      ↓
Send command to HardwareAdapter
      ↓
Simulator changes state
      ↓
Emit COMPARTMENT_OPEN
      ↓
Backend handles event
      ↓
Compartment.is_open = true
      ↓
status = OPEN
      ↓
Save CabinetEvent
      ↓
Publish WebSocket
```

---

# 37. Close Compartment API

Endpoint:

```http
POST /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/close
```

Flow tương tự.

Sau close:

```text
is_open = false
```

Status trở về:

```text
EMPTY
```

nếu không có medication,

hoặc:

```text
AVAILABLE
```

nếu có medication.

---

# 38. Offline Cabinet Rule

Nếu Cabinet:

```text
OFFLINE
```

thì:

```text
OPEN_COMPARTMENT
CLOSE_COMPARTMENT
```

phải reject.

HTTP có thể:

```text
409 Conflict
```

---

# 39. Archived Cabinet Rule

Không cho:

```text
online
offline
open
close
assign medication
```

với Cabinet:

```text
ARCHIVED
```

---

# 40. Cabinet State API

Endpoint:

```http
GET /families/{family_id}/cabinets/{cabinet_id}/state
```

Response:

```json
{
  "cabinet_id": 1,
  "status": "ONLINE",
  "hardware_mode": "SIMULATOR",
  "last_seen_at": "2026-11-01T10:30:00Z",
  "compartments": [
    {
      "position": 1,
      "is_open": false,
      "status": "AVAILABLE",
      "family_medication_id": 10
    }
  ]
}
```

---

# 41. Compartment Detail API

Endpoint:

```http
GET /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}
```

Response chuẩn bị cho Digital Twin:

```json
{
  "id": 8,
  "position": 8,
  "label": "Ngăn 08",
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
  }
}
```

---

# 42. Schedule-aware Compartment Detail

Nếu medication có schedule gần nhất:

Response có thể thêm:

```json
{
  "next_dose": {
    "date": "2026-11-01",
    "time": "20:00",
    "member": {
      "id": 3,
      "full_name": "Nguyen Thi Lan"
    },
    "dose_amount": 1,
    "dose_unit": "TABLET"
  }
}
```

Task 09 có thể reuse service của Task 08.

---

# 43. WebSocket

Task 09 bắt đầu sử dụng realtime.

Tạo:

```text
backend/app/realtime/websocket_manager.py
```

---

# 44. WebSocket Endpoint

Ví dụ:

```text
/ws/families/{family_id}/cabinets/{cabinet_id}
```

Client sau khi authenticated có thể subscribe.

---

# 45. WebSocket Authentication

Không cho anonymous subscribe vào Cabinet state.

Phải xác minh:

```text
User
  ↓
Family Membership
  ↓
Cabinet Family
```

---

# 46. WebSocket Event Format

Đề xuất:

```json
{
  "type": "COMPARTMENT_OPEN",
  "cabinet_id": 1,
  "compartment": {
    "id": 8,
    "position": 8
  },
  "timestamp": "2026-11-01T10:30:00Z"
}
```

---

# 47. Cabinet Online Event

```json
{
  "type": "CABINET_ONLINE",
  "cabinet_id": 1,
  "timestamp": "2026-11-01T10:30:00Z"
}
```

---

# 48. Compartment Close Event

```json
{
  "type": "COMPARTMENT_CLOSE",
  "cabinet_id": 1,
  "compartment": {
    "id": 8,
    "position": 8
  },
  "timestamp": "2026-11-01T10:31:00Z"
}
```

---

# 49. Realtime Flow

```text
Simulator
  ↓
Event
  ↓
Backend Event Handler
  ↓
Database Update
  ↓
CabinetEvent
  ↓
WebSocket Manager
  ↓
Connected Clients
```

---

# 50. Event Handler

Tạo:

```text
backend/app/modules/cabinets/event_handler.py
```

Nhiệm vụ:

```text
handle CABINET_ONLINE
handle CABINET_OFFLINE
handle COMPARTMENT_OPEN
handle COMPARTMENT_CLOSE
handle DEVICE_ERROR
```

---

# 51. Simulator API Service

Ngoài backend adapter, có thể tách service riêng:

```text
hardware-simulator/
```

như kiến trúc đã thống nhất.

MVP có hai phương án:

```text
A. Simulator chạy trong Backend process
B. Simulator chạy service riêng
```

Khuyến nghị Task 09:

> **Bắt đầu với A để đơn giản, nhưng code theo interface để dễ tách thành B.**

---

# 52. Hardware Simulator Directory

```text
hardware-simulator/
│
├── app/
│   ├── main.py
│   ├── simulator.py
│   ├── cabinet_state.py
│   ├── events.py
│   └── config.py
│
├── scenarios/
│   ├── cabinet_online.json
│   ├── cabinet_offline.json
│   ├── open_compartment.json
│   └── close_compartment.json
│
├── tests/
└── README.md
```

Nếu chưa tách service:

```text
backend/app/integrations/hardware/simulator.py
```

là implementation chính.

---

# 53. Simulator Scenario

Ví dụ:

```json
{
  "event": "COMPARTMENT_OPEN",
  "cabinet_id": 1,
  "position": 8
}
```

---

# 54. State Sync

Khi App reconnect hoặc Simulator restart:

```text
Backend
  ↓
get_state()
  ↓
Simulator
  ↓
full cabinet state
  ↓
Backend reconcile
```

Event:

```text
STATE_SYNC
```

---

# 55. Source of Truth Rule

Business data:

```text
Medication assignment
Family relation
Schedule
Inventory
```

Source:

```text
PostgreSQL
```

Hardware state:

```text
online
open/close
```

Source:

```text
device/simulator event
```

Không đảo ngược hai khái niệm.

---

# 56. Cabinet Event History API

Endpoint:

```http
GET /families/{family_id}/cabinets/{cabinet_id}/events
```

Query:

```text
event_type
from
to
limit
```

---

# 57. Event History Response

```json
{
  "items": [
    {
      "id": 100,
      "event_type": "COMPARTMENT_OPEN",
      "compartment_position": 8,
      "source": "SIMULATOR",
      "occurred_at": "2026-11-01T10:30:00Z"
    }
  ]
}
```

---

# 58. Không coi Open = Taken

Đây là rule bắt buộc.

Không được:

```text
COMPARTMENT_OPEN
→ MEDICATION_TAKEN
```

Open chỉ có nghĩa:

```text
ngăn đã được mở
```

Việc xác nhận đã uống sẽ được xử lý trong Task Medication Event sau.

---

# 59. Medication Event State

Task 09 chỉ chuẩn bị cho future flow:

```text
SCHEDULED
→ REMINDER_SENT
→ CABINET_OPENED
→ MEDICATION_RETRIEVED
→ USER_CONFIRMED
```

Task 09 hiện tại mới tạo được:

```text
CABINET_OPENED
```

ở mức device event.

---

# 60. Inventory Rule

Task 09 không tự trừ quantity khi mở ngăn.

Sai:

```text
OPEN
→ quantity - 1
```

Đúng:

```text
OPEN
→ CabinetEvent only
```

Inventory deduction sẽ chỉ xảy ra khi có medication confirmation/event ở task sau.

---

# 61. Authorization Matrix

| Action | OWNER | ADMIN | CAREGIVER | VIEWER |
|---|---:|---:|---:|---:|
| View cabinet | ✓ | ✓ | ✓ | ✓ |
| View compartments | ✓ | ✓ | ✓ | ✓ |
| View events | ✓ | ✓ | ✓ | ✓ |
| Create cabinet | ✓ | ✓ | ✗ | ✗ |
| Assign medication | ✓ | ✓ | ✓ | ✗ |
| Unassign medication | ✓ | ✓ | ✓ | ✗ |
| Simulator online/offline | ✓ | ✓ | ✓ | ✗ |
| Open/close compartment | ✓ | ✓ | ✓ | ✗ |
| Archive cabinet | ✓ | ✓ | ✗ | ✗ |

---

# 62. Family Scope Rule

Cabinet luôn phải được query bằng:

```text
family_id + cabinet_id
```

Không dùng:

```text
cabinet_id
```

đơn lẻ trong user-facing API.

---

# 63. Compartment Scope Rule

Compartment phải được xác định bởi:

```text
family_id
cabinet_id
position
```

hoặc:

```text
family_id
cabinet_id
compartment_id
```

---

# 64. Cross-Family Attack Protection

Cabinet Family A.

User Family B gọi:

```http
GET /families/B/cabinets/1
```

Expected:

```text
404
```

---

# 65. Cross-Family Medication Assignment

Medication Family B không thể gán vào Cabinet Family A.

Expected:

```text
reject
```

---

# 66. Archived Family Rule

Nếu Family:

```text
ARCHIVED
```

không cho:

```text
create cabinet
assign medication
open compartment
close compartment
```

---

# 67. Archived Medication Rule

Không assign medication mới nếu:

```text
ARCHIVED
```

---

# 68. Cabinet Archive

Endpoint:

```http
POST /families/{family_id}/cabinets/{cabinet_id}/archive
```

Chỉ:

```text
OWNER
ADMIN
```

Cabinet archived:

```text
status = ARCHIVED
```

Không hard delete.

---

# 69. Repository Layer

Tạo:

```text
backend/app/modules/cabinets/repository.py
```

Nhiệm vụ:

```text
create_cabinet()
get_cabinet()
list_cabinets()

create_compartments()
get_compartment()
list_compartments()

assign_medication()
unassign_medication()

update_cabinet_status()
update_compartment_state()

create_event()
list_events()
```

---

# 70. Service Layer

Tạo:

```text
backend/app/modules/cabinets/service.py
```

Chịu trách nhiệm:

```text
family authorization
cabinet creation transaction
compartment initialization
medication assignment
device command
event handling
state reconciliation
business rules
```

---

# 71. Schema Layer

Tạo:

```text
backend/app/modules/cabinets/schema.py
```

Schema đề xuất:

```text
CabinetCreateRequest
CabinetResponse
CabinetListResponse

CompartmentResponse
CompartmentDetailResponse

MedicationAssignmentRequest

CabinetStateResponse
CabinetEventResponse
CabinetEventListResponse
```

---

# 72. Enums

Tạo:

```text
backend/app/modules/cabinets/enums.py
```

Bao gồm:

```text
CabinetStatus
HardwareMode
CompartmentStatus
CabinetEventType
CabinetCommandType
```

---

# 73. Cấu trúc thư mục sau Task 09

```text
backend/
│
├── app/
│   ├── models/
│   │   ├── cabinet.py
│   │   ├── compartment.py
│   │   ├── cabinet_event.py
│   │   └── __init__.py
│   │
│   ├── modules/
│   │   └── cabinets/
│   │       ├── router.py
│   │       ├── service.py
│   │       ├── repository.py
│   │       ├── schema.py
│   │       ├── dependencies.py
│   │       ├── event_handler.py
│   │       ├── enums.py
│   │       └── exceptions.py
│   │
│   ├── integrations/
│   │   └── hardware/
│   │       ├── base.py
│   │       ├── simulator.py
│   │       └── __init__.py
│   │
│   └── realtime/
│       ├── websocket_manager.py
│       └── events.py
│
├── alembic/
│   └── versions/
│       └── xxxx_create_cabinet_tables.py
│
└── tests/
    ├── test_cabinet_create.py
    ├── test_compartment_assignment.py
    ├── test_cabinet_simulator.py
    ├── test_cabinet_events.py
    ├── test_cabinet_websocket.py
    └── test_cabinet_authorization.py
```

---

# 74. Model Registry

Cập nhật:

```text
backend/app/models/__init__.py
```

Import:

```python
from backend.app.models.cabinet import Cabinet
from backend.app.models.compartment import Compartment
from backend.app.models.cabinet_event import CabinetEvent
```

---

# 75. Alembic Migration

Tạo:

```bash
alembic revision --autogenerate -m "create smart cabinet tables"
```

Review.

Sau đó:

```bash
alembic upgrade head
```

---

# 76. Migration phải tạo

```text
cabinets
compartments
cabinet_events
```

với:

```text
Foreign Keys
Indexes
Unique device_code
Unique cabinet_id + position
```

---

# 77. Test — Create Cabinet

OWNER tạo Cabinet.

Expected:

```text
201
```

Database:

```text
1 Cabinet
9 Compartments
```

---

# 78. Test — Duplicate Device Code

Tạo cùng:

```text
device_code
```

Expected:

```text
409
```

---

# 79. Test — Second Active Cabinet

Nếu MVP chỉ cho 1 cabinet/family:

Tạo cabinet thứ 2.

Expected:

```text
409
```

---

# 80. Test — Compartment Count

Sau create:

```text
positions = 1..9
```

Không thiếu.

Không duplicate.

---

# 81. Test — Assign Medication

Medication cùng Family.

Expected:

```text
success
status = AVAILABLE
```

---

# 82. Test — Duplicate Assignment

Medication đã ở ngăn 1.

Assign sang ngăn 2.

Expected:

```text
reject
```

---

# 83. Test — Cross-Family Medication

Medication Family B.

Cabinet Family A.

Expected:

```text
404 / reject
```

---

# 84. Test — Online

Call:

```text
simulator/online
```

Expected:

```text
Cabinet ONLINE
CABINET_ONLINE event
WebSocket event
```

---

# 85. Test — Offline Open

Cabinet OFFLINE.

Call:

```text
open compartment
```

Expected:

```text
409
```

---

# 86. Test — Open Compartment

Cabinet ONLINE.

Open position 8.

Expected:

```text
is_open = true
status = OPEN
CabinetEvent created
WebSocket event sent
```

---

# 87. Test — Close Compartment

Expected:

```text
is_open = false
status restored
CabinetEvent created
```

---

# 88. Test — Open Does Not Reduce Inventory

Quantity before:

```text
20
```

Open/close.

Quantity after:

```text
20
```

---

# 89. Test — Open Does Not Mean Taken

Không tạo:

```text
USER_CONFIRMED
```

hoặc:

```text
MEDICATION_TAKEN
```

chỉ vì ngăn mở.

---

# 90. Test — WebSocket Authorization

User ngoài Family cố connect.

Expected:

```text
reject
```

---

# 91. Test — Realtime Event

Connected client.

Open ngăn.

Expected nhận:

```json
{
  "type": "COMPARTMENT_OPEN"
}
```

---

# 92. Test — State Sync

Simulator state:

```text
position 8 open
```

Backend gọi sync.

Expected DB state tương ứng.

---

# 93. API Summary sau Task 09

Bổ sung:

```http
POST /families/{family_id}/cabinets
GET  /families/{family_id}/cabinets

GET /families/{family_id}/cabinets/{cabinet_id}
GET /families/{family_id}/cabinets/{cabinet_id}/state

GET /families/{family_id}/cabinets/{cabinet_id}/compartments
GET /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}

PUT    /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/medication
DELETE /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/medication

POST /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/open
POST /families/{family_id}/cabinets/{cabinet_id}/compartments/{position}/close

POST /families/{family_id}/cabinets/{cabinet_id}/simulator/online
POST /families/{family_id}/cabinets/{cabinet_id}/simulator/offline

GET  /families/{family_id}/cabinets/{cabinet_id}/events

POST /families/{family_id}/cabinets/{cabinet_id}/archive
```

WebSocket:

```text
/ws/families/{family_id}/cabinets/{cabinet_id}
```

---

# 94. Example Full Flow

```text
Login
 ↓
Select Family
 ↓
Create Cabinet
 ↓
Auto-create 9 Compartments
 ↓
Assign Amlodipine → Compartment 08
 ↓
Simulator ONLINE
 ↓
Open Compartment 08
 ↓
Cabinet Event
 ↓
Database Update
 ↓
WebSocket
 ↓
App receives realtime event
 ↓
Close Compartment 08
```

---

# 95. Chuẩn bị cho Task 10

Task 09 phải cung cấp API đủ để Digital Twin 3D dùng:

```text
Cabinet state
9 compartments
Medication assignment
Compartment status
Open / close state
Next dose
Realtime WebSocket
```

Task 10 chỉ cần render dữ liệu này.

---

# 96. Digital Twin Mapping Contract

Mỗi compartment phải map ổn định:

```text
position = 1
→ drawer_01

position = 2
→ drawer_02

...

position = 9
→ drawer_09
```

Không thay đổi mapping tùy ý.

---

# 97. Compartment Object ID

Task 10 sẽ dùng:

```text
drawer_01
drawer_02
...
drawer_09
```

Backend dùng:

```text
position
```

Mapping:

```text
drawer_{position:02d}
```

---

# 98. Không thực hiện trong Task 09

Không làm:

```text
3D rendering
Blender
GLB viewer

ESP32
MQTT broker production
physical sensor
physical LED
physical lock

Medication confirmation
inventory deduction
adherence

AI
OCR
RAG
```

---

# 99. Acceptance Criteria

Task 09 chỉ hoàn thành khi:

- [ ] `cabinets` table tồn tại.
- [ ] `compartments` table tồn tại.
- [ ] `cabinet_events` table tồn tại.
- [ ] Create Cabinet hoạt động.
- [ ] Tự tạo đúng 9 compartments.
- [ ] Device code unique.
- [ ] Family scope hoạt động.
- [ ] Medication assignment hoạt động.
- [ ] Cross-family medication bị chặn.
- [ ] Duplicate medication assignment bị chặn.
- [ ] Simulator Online hoạt động.
- [ ] Simulator Offline hoạt động.
- [ ] Open Compartment hoạt động.
- [ ] Close Compartment hoạt động.
- [ ] Offline cabinet không nhận open/close.
- [ ] CabinetEvent được lưu.
- [ ] WebSocket publish event.
- [ ] WebSocket authorization hoạt động.
- [ ] Cabinet State API hoạt động.
- [ ] Compartment Detail API hoạt động.
- [ ] State sync hoạt động.
- [ ] Open ngăn không tự trừ inventory.
- [ ] Open ngăn không tự xác nhận đã uống.
- [ ] Archived Cabinet không nhận command.
- [ ] Alembic migration pass.
- [ ] Tests pass.

---

# 100. Definition of Done

Task 09 được đánh dấu:

```text
DONE
```

khi demo được chuỗi:

```text
Login
 ↓
Select Family
 ↓
Create Cabinet
 ↓
9 Compartments
 ↓
Assign Medication
 ↓
Simulator Online
 ↓
Open Drawer 08
 ↓
Cabinet Event
 ↓
WebSocket Event
 ↓
Close Drawer 08
 ↓
State Updated Realtime
```

mà không cần ESP32 thật.

---

# 101. Deliverables

Sau Task 09 cần có:

```text
backend/app/models/
├── cabinet.py
├── compartment.py
├── cabinet_event.py
└── __init__.py

backend/app/modules/cabinets/
├── router.py
├── service.py
├── repository.py
├── schema.py
├── dependencies.py
├── event_handler.py
├── enums.py
└── exceptions.py

backend/app/integrations/hardware/
├── base.py
├── simulator.py
└── __init__.py

backend/app/realtime/
├── websocket_manager.py
└── events.py

backend/alembic/versions/
└── xxxx_create_cabinet_tables.py

backend/tests/
├── test_cabinet_create.py
├── test_compartment_assignment.py
├── test_cabinet_simulator.py
├── test_cabinet_events.py
├── test_cabinet_websocket.py
└── test_cabinet_authorization.py

docs/tasks/
└── TASK_09_SMART_CABINET_MOCK.md
```

---

# 102. Task tiếp theo

Sau Task 09:

```text
TASK 10 — Digital Twin 3D
```

Task 10 dự kiến xây:

```text
Cabinet 3D Model
9 Drawer Objects
GLB / glTF
3D Viewer
Rotate / Zoom
Select Compartment
Drawer Open Animation
Medication 3D Templates
Compartment Detail Panel
Realtime WebSocket Sync
Highlight Next Dose
Simple Mode
Tests
```

---

# 103. Roadmap hiện tại

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

# 104. Nguyên tắc chuyển Task

Không chuyển sang Task 10 nếu chưa chứng minh được:

```text
CABINET
  ↓
9 COMPARTMENTS
  ↓
MEDICATION ASSIGNMENT
  ↓
SIMULATOR STATE
  ↓
OPEN / CLOSE EVENT
  ↓
DATABASE EVENT
  ↓
WEBSOCKET REALTIME
```

và chưa test đầy đủ Family scope + hardware abstraction.

> **Task 09 là cầu nối giữa phần mềm và phần cứng của PharmaMind AI. Digital Twin ở Task 10 phải chỉ tiêu thụ state/event từ Cabinet API và WebSocket, không tự tạo business state riêng.**
