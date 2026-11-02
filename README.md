# PharmaMind AI

Hệ thống quản lý thuốc gia đình với **Digital Twin 3D** tủ thuốc thông minh,
**Hardware Simulator** (thay thế tạm thời cho ESP32) và **AI Pharmacist**.

> Tài liệu chi tiết: [README_PharmaMind_AI.md](README_PharmaMind_AI.md),
> [docs/architecture/](docs/architecture/), [docs/tasks/](docs/tasks/).
> Trạng thái trước phát hành app: [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md).
> Hướng dẫn preview trên tên miền miễn phí: [docs/deployment/FREE_HOSTING_PREVIEW.md](docs/deployment/FREE_HOSTING_PREVIEW.md).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/haianh02032005-rgb/PharaMind1)

Blueprint tự tạo PostgreSQL Free và nối `DATABASE_URL` cho backend; không cần nhập database secret trong bước deploy.

## Yêu cầu

- Python **3.12.x** (xem `.python-version`)

## Cài đặt

```bash
py -3.12 -m venv .venv            # Linux/macOS: python3.12 -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env            # Linux/macOS: cp .env.example .env
```

## Database (PostgreSQL 17)

Dùng Docker:

```bash
docker compose up -d postgres
```

Hoặc PostgreSQL cài trực tiếp: tạo user `pharmamind` / password `pharmamind_dev`
và database `pharmamind` (khớp `DATABASE_URL` trong `.env.example`).

Chạy migration:

```bash
cd backend
alembic upgrade head              # hoặc từ root: alembic -c backend/alembic.ini upgrade head
```

Quy trình thay đổi schema: sửa model → `alembic revision --autogenerate -m "..."`
→ review migration → `alembic upgrade head` → `pytest` → commit model + migration.

## Chạy backend

```bash
uvicorn backend.app.main:app --reload
```

| URL | Mô tả |
|---|---|
| http://127.0.0.1:8000/ | Thông tin hệ thống |
| http://127.0.0.1:8000/health | Health check |
| http://127.0.0.1:8000/health/db | Database health check |
| `POST /auth/register` | Đăng ký người dùng |
| `POST /auth/login` | Đăng nhập (trả về access & refresh token) |
| `POST /auth/refresh` | Đổi refresh token lấy access token mới |
| `GET /auth/me` | Thông tin người dùng hiện tại (JWT Bearer) |
| `POST /families`, `GET /families` | Tạo và liệt kê Family Workspace |
| `GET /families/{id}`, `PATCH /families/{id}` | Chi tiết và cập nhật Family |
| `POST /families/{id}/archive`, `POST /families/{id}/restore` | Lưu trữ và khôi phục Family |
| `GET/POST/PATCH/DELETE /families/{id}/memberships` | Quản lý thành viên & phân quyền Family |
| `GET/POST /families/{family_id}/members` | Tạo và liệt kê Family Member |
| `GET/PATCH /families/{family_id}/members/{member_id}` | Chi tiết và cập nhật Family Member |
| `POST /families/{family_id}/members/{member_id}/archive` & `/restore` | Lưu trữ và khôi phục Family Member |
| `GET/PATCH /families/{family_id}/members/{member_id}/health-profile` | Hồ sơ sức khỏe của Member |
| `GET/POST/PATCH/DELETE .../members/{member_id}/conditions` | Bệnh lý nền (`MedicalCondition`) |
| `GET/POST/PATCH/DELETE .../members/{member_id}/allergies` | Dị ứng (`AllergyProfile`) |
| `GET/POST/PATCH/DELETE .../members/{member_id}/drug-reactions` | Phản ứng thuốc (`DrugReactionHistory`) |
| `GET/POST/PATCH/DELETE .../members/{member_id}/emergency-contacts` | Liên hệ khẩn cấp (`EmergencyContact`) |
| `GET/POST /families/{family_id}/medications` | Tạo và liệt kê thuốc trong Family (`FamilyMedication`) |
| `GET/PATCH /families/{family_id}/medications/{medication_id}` | Chi tiết và cập nhật thuốc |
| `PATCH /families/{family_id}/medications/{medication_id}/inventory` | Cập nhật tồn kho thuốc |
| `POST /families/{family_id}/medications/{medication_id}/archive` & `/restore` | Lưu trữ và khôi phục thuốc |
| `GET/POST/DELETE .../medications/{medication_id}/members[/{member_id}]` | Liên kết thuốc với Family Member |
| `GET /families/{family_id}/members/{member_id}/medications` | Danh sách thuốc của một Family Member |
| `GET/POST /families/{family_id}/prescriptions` | Tạo và liệt kê đơn thuốc (`Prescription`) |
| `GET /families/{family_id}/members/{member_id}/prescriptions` | Danh sách đơn thuốc của một Family Member |
| `GET/PATCH /families/{family_id}/prescriptions/{prescription_id}` | Chi tiết và cập nhật đơn thuốc |
| `POST /families/{family_id}/prescriptions/{prescription_id}/complete`, `/archive`, `/restore` | Hoàn thành, lưu trữ, khôi phục đơn thuốc |
| `POST/PATCH/DELETE .../prescriptions/{prescription_id}/items[/{item_id}]` | Quản lý thuốc trong đơn (`PrescriptionItem`) |
| `GET/POST /families/{family_id}/schedules` | Tạo và liệt kê lịch uống thuốc (`MedicationSchedule`) |
| `GET/PATCH /families/{family_id}/schedules/{schedule_id}` | Chi tiết và cập nhật lịch uống thuốc |
| `POST .../schedules/{schedule_id}/pause`, `/resume`, `/complete`, `/archive`, `/restore` | Tạm dừng, tiếp tục, hoàn thành, lưu trữ, khôi phục lịch |
| `GET /families/{family_id}/members/{member_id}/schedules` | Danh sách lịch uống thuốc của một Family Member |
| `GET /families/{family_id}/members/{member_id}/schedule-day` | Timeline lịch uống thuốc trong ngày |
| `GET /families/{family_id}/members/{member_id}/next-dose` | Liều uống tiếp theo của Family Member |
| `GET/POST /families/{family_id}/cabinets` | Tạo (tự tạo 9 ngăn) và liệt kê tủ thuốc (`Cabinet`) |
| `GET /families/{family_id}/cabinets/{cabinet_id}` & `/state` | Chi tiết tủ thuốc và trạng thái phần cứng |
| `GET .../cabinets/{cabinet_id}/compartments[/{position}]` | Danh sách 9 ngăn và chi tiết từng ngăn (`drawer_01`..`drawer_09`) |
| `PUT/DELETE .../compartments/{position}/medication` | Gán / gỡ thuốc trong ngăn |
| `POST .../compartments/{position}/open` & `/close` | Mô phỏng mở / đóng ngăn thuốc |
| `POST .../cabinets/{cabinet_id}/simulator/online`, `/offline`, `/sync` | Điều khiển & đồng bộ Hardware Simulator |
| `GET /families/{family_id}/cabinets/{cabinet_id}/events` | Lịch sử sự kiện tủ thuốc (`CabinetEvent`) |
| `WS /ws/families/{family_id}/cabinets/{cabinet_id}` | Kênh WebSocket realtime đồng bộ trạng thái tủ |
| http://127.0.0.1:8000/docs | Swagger UI |

## Chạy test

```bash
pytest
```

## Ứng dụng Flutter

Mã nguồn mobile MVP nằm trong [`mobile/`](mobile/README.md). App hiện kết nối trực tiếp FastAPI cho đăng nhập/đăng ký, Family, thành viên, lịch uống, thuốc và trạng thái tủ. Cần cài Flutter SDK để sinh Android/iOS project và chạy app; hướng dẫn địa chỉ API cho emulator và thiết bị thật nằm trong README của mobile.

## Cấu trúc thư mục

```text
backend/             FastAPI backend (Router → Service → Repository → Database)
mobile/              Flutter app
ai/                  AI Pharmacist (RAG, agents, tools, safety)
hardware-simulator/  Mock cabinet thay thế ESP32
firmware/            ESP32 firmware (tương lai)
3d-assets/           Mô hình 3D tủ thuốc và viên thuốc
docs/                Kiến trúc, API, database, task specs
scripts/             Script hỗ trợ phát triển
tests/               Integration / E2E tests
```

## Tiến độ

| Task | Nội dung | Trạng thái |
|---|---|---|
| 01 | Project Initialization | ✅ DONE |
| 02 | Database Foundation | ✅ DONE |
| 03 | Authentication & User | ✅ DONE |
| 04 | Family Management | ✅ DONE |
| 05 | Family Member & Health Profile | ✅ DONE |
| 06 | Medication Management | ✅ DONE |
| 07 | Prescription Management | ✅ DONE |
| 08 | Medication Schedule | ✅ DONE |
| 09 | Smart Cabinet Mock | ✅ DONE |
| 10 | Digital Twin 3D | ⏳ |
| Mobile | Flutter foundation, auth, family, dashboard, schedule, cabinet summary | 🟡 MVP foundation |
#   P h a r a M i n d 1  
 #   P h a r a M i n d 1  
 
