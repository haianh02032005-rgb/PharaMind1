# PharmaMind AI — Project Folder Structure

## 1. Mục tiêu

Tài liệu này mô tả cấu trúc thư mục đề xuất cho dự án **PharmaMind AI**.

Kiến trúc hiện tại ưu tiên:

- phát triển phần mềm trước;
- phần cứng có thể mock;
- backend modular;
- dễ mở rộng AI sau;
- Digital Twin 3D độc lập;
- tài liệu hóa rõ ràng;
- dễ chia task cho nhiều thành viên.

---

# 2. Cấu trúc tổng thể

```text
pharmamind-ai/
│
├── README.md
├── requirements.txt
├── .python-version
├── .gitignore
├── docker-compose.yml
├── .env.example
│
├── mobile/
│
├── backend/
│
├── ai/
│
├── hardware-simulator/
│
├── firmware/
│
├── 3d-assets/
│
├── docs/
│
├── scripts/
│
└── tests/
```

---

# 3. Thư mục gốc

```text
pharmamind-ai/
```

Đây là repository chính chứa toàn bộ hệ thống.

Các file quan trọng:

```text
README.md
```

Mô tả tổng quan dự án.

```text
requirements.txt
```

Các thư viện Python cho backend.

```text
.python-version
```

Phiên bản Python đề xuất.

```text
docker-compose.yml
```

Khởi tạo nhanh:

- PostgreSQL;
- Redis;
- backend;
- các service khác trong tương lai.

```text
.env.example
```

Mẫu biến môi trường.

Ví dụ:

```env
DATABASE_URL=
JWT_SECRET=
REDIS_URL=
OPENAI_API_KEY=
MQTT_URL=
```

---

# 4. Mobile App

```text
mobile/
```

Dùng cho ứng dụng Flutter.

Cấu trúc đề xuất:

```text
mobile/
│
├── android/
├── ios/
├── web/
│
├── assets/
│   ├── images/
│   ├── icons/
│   └── models/
│
├── lib/
│   ├── main.dart
│   │
│   ├── app/
│   │   ├── app.dart
│   │   ├── routes.dart
│   │   └── theme.dart
│   │
│   ├── core/
│   │   ├── constants/
│   │   ├── network/
│   │   ├── storage/
│   │   ├── utils/
│   │   └── widgets/
│   │
│   ├── features/
│   │   ├── auth/
│   │   ├── family/
│   │   ├── member/
│   │   ├── health/
│   │   ├── medication/
│   │   ├── prescription/
│   │   ├── schedule/
│   │   ├── cabinet/
│   │   ├── digital_twin/
│   │   ├── notification/
│   │   ├── caregiver/
│   │   └── ai_chat/
│   │
│   └── services/
│       ├── api_service.dart
│       ├── websocket_service.dart
│       └── auth_service.dart
│
├── test/
│
├── pubspec.yaml
└── README.md
```

---

# 5. Mobile — Feature Structure

Mỗi feature nên có cấu trúc riêng.

Ví dụ:

```text
mobile/lib/features/medication/
│
├── data/
│   ├── models/
│   ├── datasources/
│   └── repositories/
│
├── domain/
│   ├── entities/
│   ├── repositories/
│   └── usecases/
│
└── presentation/
    ├── pages/
    ├── widgets/
    └── state/
```

Cách này giúp project không bị rối khi số màn hình tăng.

---

# 6. Backend

```text
backend/
```

Backend sử dụng FastAPI.

Cấu trúc đề xuất:

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   │
│   ├── api/
│   │   ├── dependencies.py
│   │   └── router.py
│   │
│   ├── modules/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── families/
│   │   ├── members/
│   │   ├── health/
│   │   ├── medications/
│   │   ├── prescriptions/
│   │   ├── schedules/
│   │   ├── cabinets/
│   │   ├── compartments/
│   │   ├── notifications/
│   │   ├── caregivers/
│   │   └── ai/
│   │
│   ├── realtime/
│   │   ├── websocket_manager.py
│   │   └── events.py
│   │
│   ├── integrations/
│   │   ├── hardware_simulator.py
│   │   ├── mqtt.py
│   │   └── external_api.py
│   │
│   └── shared/
│       ├── enums.py
│       ├── schemas.py
│       └── utils.py
│
├── alembic/
├── tests/
├── requirements.txt
├── alembic.ini
└── README.md
```

---

# 7. Backend Module Pattern

Mỗi module nên có cấu trúc giống nhau.

Ví dụ:

```text
backend/app/modules/medications/
│
├── router.py
├── service.py
├── repository.py
├── model.py
├── schema.py
├── dependencies.py
└── exceptions.py
```

Vai trò:

```text
router.py
```

Định nghĩa API endpoint.

```text
service.py
```

Business logic.

```text
repository.py
```

Truy cập database.

```text
model.py
```

SQLAlchemy model.

```text
schema.py
```

Pydantic schema.

```text
dependencies.py
```

Dependency injection.

```text
exceptions.py
```

Exception riêng của module.

---

# 8. Database Migration

```text
backend/alembic/
```

Cấu trúc:

```text
alembic/
│
├── versions/
├── env.py
└── script.py.mako
```

Dùng để quản lý thay đổi schema PostgreSQL.

---

# 9. AI

```text
ai/
```

Tạm thời chưa cần phát triển sâu, nhưng nên tạo cấu trúc sẵn.

```text
ai/
│
├── app/
│   ├── main.py
│   │
│   ├── rag/
│   │   ├── retriever.py
│   │   ├── embeddings.py
│   │   └── knowledge_base.py
│   │
│   ├── agents/
│   │   └── pharmacist_agent.py
│   │
│   ├── tools/
│   │   ├── family_tool.py
│   │   ├── medication_tool.py
│   │   ├── schedule_tool.py
│   │   ├── cabinet_tool.py
│   │   └── allergy_tool.py
│   │
│   ├── safety/
│   │   ├── guardrails.py
│   │   └── medical_safety.py
│   │
│   └── prompts/
│       └── pharmacist_prompt.md
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── knowledge_base/
│
├── tests/
└── requirements-ai.txt
```

---

# 10. Hardware Simulator

```text
hardware-simulator/
```

Đây là phần rất quan trọng trong giai đoạn chưa có phần cứng thật.

Cấu trúc:

```text
hardware-simulator/
│
├── app/
│   ├── main.py
│   │
│   ├── simulator.py
│   ├── cabinet_state.py
│   ├── events.py
│   └── config.py
│   │
│   └── api/
│       └── routes.py
│
├── scenarios/
│   ├── cabinet_online.json
│   ├── open_drawer.json
│   ├── close_drawer.json
│   └── cabinet_offline.json
│
├── tests/
└── README.md
```

Simulator có thể giả lập:

```text
CABINET_ONLINE
CABINET_OFFLINE
COMPARTMENT_OPEN
COMPARTMENT_CLOSE
LOW_STOCK
INVENTORY_UPDATED
```

---

# 11. Firmware

```text
firmware/
```

Chưa cần phát triển ngay nhưng nên tạo sẵn.

```text
firmware/
│
├── esp32/
│   ├── src/
│   ├── include/
│   ├── lib/
│   ├── platformio.ini
│   └── README.md
│
└── docs/
    ├── mqtt_topics.md
    ├── pin_mapping.md
    └── protocol.md
```

Sau này thư mục này sẽ chứa code cho:

- ESP32;
- cảm biến cửa;
- LED;
- motor;
- khóa;
- Wi-Fi;
- MQTT.

---

# 12. 3D Assets

```text
3d-assets/
```

Cấu trúc:

```text
3d-assets/
│
├── blender/
│   ├── pharmamind_cabinet.blend
│   └── medication_templates.blend
│
├── export/
│   ├── cabinet/
│   │   └── pharmamind_cabinet.glb
│   │
│   ├── compartments/
│   │   └── drawer.glb
│   │
│   └── medication/
│       ├── tablet_round.glb
│       ├── tablet_oval.glb
│       ├── capsule.glb
│       ├── softgel.glb
│       ├── bottle.glb
│       └── medicine_box.glb
│
├── textures/
│
└── README.md
```

---

# 13. Quy tắc đặt tên Object 3D

Mỗi ngăn phải là object riêng.

Ví dụ:

```text
cabinet_body
screen

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

Điều này giúp app nhận diện được ngăn khi người dùng click.

---

# 14. Docs

```text
docs/
```

Cấu trúc đề xuất:

```text
docs/
│
├── architecture/
│   ├── SYSTEM_FLOW.md
│   ├── FOLDER_STRUCTURE.md
│   ├── SYSTEM_ARCHITECTURE.md
│   └── DATABASE_ERD.md
│
├── api/
│   ├── AUTH_API.md
│   ├── FAMILY_API.md
│   ├── MEDICATION_API.md
│   ├── CABINET_API.md
│   └── AI_API.md
│
├── database/
│   ├── SCHEMA.md
│   └── MIGRATION_GUIDE.md
│
├── digital-twin/
│   ├── DIGITAL_TWIN.md
│   ├── MODEL_NAMING.md
│   └── INTERACTION_FLOW.md
│
├── ai/
│   ├── AI_ARCHITECTURE.md
│   ├── RAG.md
│   └── SAFETY.md
│
├── hardware/
│   ├── CABINET_PROTOCOL.md
│   ├── MQTT_TOPICS.md
│   └── HARDWARE_SIMULATOR.md
│
└── ui-ux/
    ├── SCREEN_LIST.md
    ├── USER_FLOW.md
    └── DESIGN_SYSTEM.md
```

---

# 15. Scripts

```text
scripts/
```

Dùng cho các script hỗ trợ phát triển.

Ví dụ:

```text
scripts/
│
├── init_db.py
├── seed_data.py
├── create_admin.py
├── reset_db.py
└── run_dev.sh
```

---

# 16. Tests

Có thể có test riêng trong từng module và test tích hợp toàn hệ thống.

```text
tests/
│
├── integration/
│   ├── test_auth_flow.py
│   ├── test_medication_flow.py
│   ├── test_schedule_flow.py
│   └── test_cabinet_flow.py
│
└── e2e/
    └── test_full_mvp_flow.py
```

---

# 17. Cấu trúc repository đầy đủ

```text
pharmamind-ai/
│
├── README.md
├── requirements.txt
├── .python-version
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── mobile/
│   ├── android/
│   ├── ios/
│   ├── web/
│   ├── assets/
│   │   ├── images/
│   │   ├── icons/
│   │   └── models/
│   │
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app/
│   │   ├── core/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── family/
│   │   │   ├── member/
│   │   │   ├── health/
│   │   │   ├── medication/
│   │   │   ├── prescription/
│   │   │   ├── schedule/
│   │   │   ├── cabinet/
│   │   │   ├── digital_twin/
│   │   │   ├── notification/
│   │   │   ├── caregiver/
│   │   │   └── ai_chat/
│   │   └── services/
│   │
│   ├── test/
│   └── pubspec.yaml
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── api/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   ├── users/
│   │   │   ├── families/
│   │   │   ├── members/
│   │   │   ├── health/
│   │   │   ├── medications/
│   │   │   ├── prescriptions/
│   │   │   ├── schedules/
│   │   │   ├── cabinets/
│   │   │   ├── compartments/
│   │   │   ├── notifications/
│   │   │   ├── caregivers/
│   │   │   └── ai/
│   │   ├── realtime/
│   │   ├── integrations/
│   │   └── shared/
│   │
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── alembic.ini
│
├── ai/
│   ├── app/
│   │   ├── rag/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── safety/
│   │   └── prompts/
│   ├── data/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── knowledge_base/
│   ├── tests/
│   └── requirements-ai.txt
│
├── hardware-simulator/
│   ├── app/
│   │   ├── main.py
│   │   ├── simulator.py
│   │   ├── cabinet_state.py
│   │   ├── events.py
│   │   └── api/
│   ├── scenarios/
│   ├── tests/
│   └── README.md
│
├── firmware/
│   ├── esp32/
│   │   ├── src/
│   │   ├── include/
│   │   ├── lib/
│   │   └── platformio.ini
│   └── docs/
│
├── 3d-assets/
│   ├── blender/
│   ├── export/
│   │   ├── cabinet/
│   │   ├── compartments/
│   │   └── medication/
│   ├── textures/
│   └── README.md
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   ├── digital-twin/
│   ├── ai/
│   ├── hardware/
│   └── ui-ux/
│
├── scripts/
│   ├── init_db.py
│   ├── seed_data.py
│   ├── create_admin.py
│   └── reset_db.py
│
└── tests/
    ├── integration/
    └── e2e/
```

---

# 18. Cấu trúc tối giản cho giai đoạn đầu

Không nhất thiết phải tạo toàn bộ ngay từ ngày đầu.

Có thể bắt đầu bằng:

```text
pharmamind-ai/
│
├── README.md
├── requirements.txt
├── .python-version
├── .env.example
│
├── mobile/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   └── modules/
│   │       ├── auth/
│   │       ├── families/
│   │       ├── members/
│   │       ├── medications/
│   │       ├── schedules/
│   │       └── cabinets/
│   └── tests/
│
├── hardware-simulator/
│
├── 3d-assets/
│
└── docs/
```

Đây là cấu trúc nên dùng cho MVP đầu tiên.

---

# 19. Thứ tự tạo thư mục

Đề xuất tạo theo thứ tự:

```text
1. backend/
2. mobile/
3. docs/
4. hardware-simulator/
5. 3d-assets/
6. ai/
7. firmware/
```

Lý do:

- backend và mobile là nền tảng chính;
- mock hardware giúp test trước;
- 3D làm song song;
- AI và firmware có thể bổ sung sau.

---

# 20. Nguyên tắc tổ chức code

## Modular

Mỗi nghiệp vụ nằm trong module riêng.

## Không trộn tầng

Không viết SQL trực tiếp trong router.

Luồng nên là:

```text
Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

## Tách phần cứng khỏi business logic

Backend không nên phụ thuộc trực tiếp vào ESP32.

Nên đi qua:

```text
Hardware Interface
```

để có thể dùng:

```text
Hardware Simulator
```

hoặc:

```text
ESP32 thật
```

---

# 21. Nguyên tắc với Digital Twin

Không đặt logic thuốc trực tiếp trong model 3D.

Model 3D chỉ chứa:

```text
Object
Animation
Interaction ID
```

Dữ liệu thật lấy từ backend:

```text
Medication
Quantity
Member
Schedule
Alert
```

---

# 22. Nguyên tắc với AI

AI không được truy cập database tùy ý.

Nên gọi qua các tool:

```text
get_member()
get_medication()
get_schedule()
get_compartment()
get_allergy()
```

Điều này giúp:

- dễ kiểm soát;
- dễ audit;
- an toàn hơn;
- tránh AI truy cập sai dữ liệu.

---

# 23. Kết luận

Cấu trúc thư mục đề xuất cho PharmaMind AI được thiết kế theo hướng:

```text
MODULAR
+
SCALABLE
+
HARDWARE-INDEPENDENT
+
AI-READY
+
DIGITAL-TWIN-READY
```

Ở giai đoạn hiện tại, nên tập trung trước vào:

```text
backend/
mobile/
hardware-simulator/
3d-assets/
docs/
```

Sau khi MVP ổn định mới mở rộng mạnh sang:

```text
ai/
firmware/
```
