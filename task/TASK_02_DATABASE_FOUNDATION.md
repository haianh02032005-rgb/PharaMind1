# PharmaMind AI — TASK 02 SPECIFICATION

# TASK 02 — PostgreSQL Database Foundation

## 1. Mục tiêu

Task 02 nhằm xây dựng nền tảng cơ sở dữ liệu cho PharmaMind AI sau khi Task 01 đã hoàn thành.

Task này tập trung vào:

- PostgreSQL;
- SQLAlchemy;
- Database session;
- cấu hình kết nối bằng biến môi trường;
- Alembic migration;
- database health check;
- migration đầu tiên để xác minh toàn bộ pipeline database hoạt động.

Task này **chưa xây dựng User/Auth, Family, Medication hay các entity nghiệp vụ thực tế**.

Mục tiêu cuối cùng:

> **Backend có thể kết nối PostgreSQL ổn định, chạy migration bằng Alembic, kiểm tra health database và sẵn sàng cho các model nghiệp vụ ở Task 03 trở đi.**

---

# 2. Điều kiện tiên quyết

Task 02 chỉ bắt đầu khi Task 01 đã đạt:

```text
FastAPI chạy được
GET /health hoạt động
pytest chạy được
Python 3.12
requirements.txt đã cài
.env.example đã tồn tại
```

---

# 3. Phạm vi Task 02

Bao gồm:

```text
1. Khởi tạo PostgreSQL
2. Bổ sung DATABASE_URL
3. Tạo SQLAlchemy engine
4. Tạo SessionLocal
5. Tạo Declarative Base
6. Tạo database dependency
7. Khởi tạo Alembic
8. Cấu hình Alembic dùng metadata của project
9. Tạo model kỹ thuật đầu tiên
10. Tạo migration đầu tiên
11. Upgrade database
12. Tạo GET /health/db
13. Viết test kết nối database
14. Chuẩn hóa workflow migration
```

Không bao gồm:

```text
User table
JWT
Family
Member
Medication
Prescription
Schedule
Cabinet
AI
Flutter
```

---

# 4. Tech Stack

```text
PostgreSQL
SQLAlchemy 2.x
psycopg 3
Alembic
FastAPI
Pydantic Settings
pytest
```

Python:

```text
Python 3.12.x
```

---

# 5. Cấu trúc thư mục sau Task 02

```text
pharmamind-ai/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── __init__.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   ├── system_info.py
│   │   │   └── __init__.py
│   │   └── api/
│   │       ├── dependencies.py
│   │       └── __init__.py
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   └── tests/
│       ├── test_health.py
│       └── test_database.py
│
├── .env.example
├── docker-compose.yml
└── docs/
    └── tasks/
        └── TASK_02_DATABASE_FOUNDATION.md
```

---

# 6. PostgreSQL Setup

Khuyến nghị dùng PostgreSQL qua Docker để môi trường giữa các máy đồng nhất.

Ví dụ `docker-compose.yml` tối thiểu:

```yaml
services:
  postgres:
    image: postgres:17
    container_name: pharmamind-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: pharmamind
      POSTGRES_USER: pharmamind
      POSTGRES_PASSWORD: pharmamind_dev
    ports:
      - "5432:5432"
    volumes:
      - pharmamind_postgres_data:/var/lib/postgresql/data

volumes:
  pharmamind_postgres_data:
```

Khởi động:

```bash
docker compose up -d postgres
```

Kiểm tra:

```bash
docker compose ps
```

---

# 7. Database URL

Bổ sung vào `.env.example`:

```env
DATABASE_URL=postgresql+psycopg://pharmamind:pharmamind_dev@localhost:5432/pharmamind
```

File `.env` local:

```env
APP_NAME=PharmaMind AI
APP_VERSION=0.1.0
DEBUG=true
DATABASE_URL=postgresql+psycopg://pharmamind:pharmamind_dev@localhost:5432/pharmamind
```

Không commit `.env`.

---

# 8. Update Config

File:

```text
backend/app/core/config.py
```

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PharmaMind AI"
    app_version: str = "0.1.0"
    debug: bool = True
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
```

---

# 9. SQLAlchemy Declarative Base

Tạo:

```text
backend/app/db/base.py
```

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Mọi model SQLAlchemy về sau đều kế thừa `Base`.

---

# 10. Database Engine và Session

Tạo:

```text
backend/app/db/session.py
```

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
```

---

# 11. Database Dependency

Tạo:

```text
backend/app/api/dependencies.py
```

```python
from collections.abc import Generator
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
```

---

# 12. Model kỹ thuật đầu tiên

Task 02 chưa tạo model nghiệp vụ thực tế.

Tạo:

```text
backend/app/models/system_info.py
```

```python
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class SystemInfo(Base):
    __tablename__ = "system_info"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

Mục đích:

```text
Model
→ Alembic
→ Migration
→ PostgreSQL
```

---

# 13. Model Registry

Tạo:

```text
backend/app/models/__init__.py
```

```python
from backend.app.models.system_info import SystemInfo

__all__ = [
    "SystemInfo",
]
```

---

# 14. Khởi tạo Alembic

Từ thư mục `backend/`:

```bash
alembic init alembic
```

---

# 15. Cấu hình Alembic

Trong:

```text
backend/alembic/env.py
```

Import:

```python
from backend.app.core.config import settings
from backend.app.db.base import Base
import backend.app.models
```

Thiết lập:

```python
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)

target_metadata = Base.metadata
```

Mục tiêu:

> Alembic phải autogenerate được migration từ model SQLAlchemy.

---

# 16. Migration đầu tiên

Chạy:

```bash
alembic revision --autogenerate -m "create system_info table"
```

Kết quả mong muốn:

```text
backend/alembic/versions/
xxxx_create_system_info_table.py
```

Sau đó:

```bash
alembic upgrade head
```

PostgreSQL phải có:

```text
alembic_version
system_info
```

---

# 17. Database Health Check

Tạo endpoint:

```http
GET /health/db
```

Ví dụ:

```python
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db


@app.get("/health/db")
def database_health(
    db: Session = Depends(get_db),
):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }
```

Response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

---

# 18. Test Database

Tạo:

```text
backend/tests/test_database.py
```

```python
from sqlalchemy import text

from backend.app.db.session import SessionLocal


def test_database_connection():
    with SessionLocal() as session:
        result = session.execute(
            text("SELECT 1")
        ).scalar_one()

    assert result == 1
```

Test API:

```python
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_database_health_endpoint():
    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "connected",
    }
```

---

# 19. Quy tắc Session

Không tạo Session global kiểu:

```python
db = SessionLocal()
```

Phải dùng:

```text
Request
  ↓
get_db()
  ↓
Session
  ↓
Close
```

---

# 20. Quy tắc Transaction

Ở các task sau:

```text
Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

Việc `commit` và `rollback` không được thực hiện tùy tiện trong router.

---

# 21. Quy tắc Migration

Mọi thay đổi schema phải đi qua Alembic.

Workflow:

```text
Update Model
   ↓
alembic revision --autogenerate
   ↓
Review migration
   ↓
alembic upgrade head
   ↓
Run tests
   ↓
Commit model + migration
```

Không dùng `Base.metadata.create_all()` làm cơ chế quản lý schema chính.

---

# 22. Docker Compose hoàn chỉnh cho Task 02

```yaml
services:
  postgres:
    image: postgres:17
    container_name: pharmamind-postgres
    restart: unless-stopped

    environment:
      POSTGRES_DB: pharmamind
      POSTGRES_USER: pharmamind
      POSTGRES_PASSWORD: pharmamind_dev

    ports:
      - "5432:5432"

    volumes:
      - pharmamind_postgres_data:/var/lib/postgresql/data

    healthcheck:
      test:
        [
          "CMD-SHELL",
          "pg_isready -U pharmamind -d pharmamind"
        ]
      interval: 5s
      timeout: 5s
      retries: 5


volumes:
  pharmamind_postgres_data:
```

---

# 23. API sau Task 02

```http
GET /
GET /health
GET /health/db
```

---

# 24. Luồng Database

```text
FastAPI Request
      ↓
get_db()
      ↓
SessionLocal
      ↓
SQLAlchemy Engine
      ↓
psycopg
      ↓
PostgreSQL
```

---

# 25. Luồng Migration

```text
SQLAlchemy Model
      ↓
Base.metadata
      ↓
Alembic
      ↓
Autogenerate
      ↓
Review
      ↓
Upgrade
      ↓
PostgreSQL
```

---

# 26. Acceptance Criteria

Task 02 chỉ hoàn thành khi:

- [ ] PostgreSQL chạy thành công.
- [ ] `DATABASE_URL` lấy từ environment.
- [ ] SQLAlchemy engine được tạo.
- [ ] `SessionLocal` hoạt động.
- [ ] `Base` được tạo.
- [ ] `get_db()` hoạt động.
- [ ] Alembic được khởi tạo.
- [ ] `target_metadata = Base.metadata`.
- [ ] Alembic đọc đúng `DATABASE_URL`.
- [ ] `SystemInfo` model tồn tại.
- [ ] Migration đầu tiên được tạo.
- [ ] `alembic upgrade head` chạy thành công.
- [ ] PostgreSQL có bảng `alembic_version`.
- [ ] PostgreSQL có bảng `system_info`.
- [ ] `GET /health/db` trả HTTP 200.
- [ ] `SELECT 1` thành công.
- [ ] Database tests pass.
- [ ] Không hard-code DB password trong Python source.
- [ ] `.env` không được commit.

---

# 27. Definition of Done

Task 02 được đánh dấu `DONE` khi developer mới có thể:

```bash
git clone <repo>
cd pharmamind-ai
docker compose up -d postgres
```

sau đó tạo `.env`, rồi chạy:

```bash
alembic upgrade head
uvicorn backend.app.main:app --reload
```

và truy cập:

```text
GET /health/db
```

nhận:

```json
{
  "status": "ok",
  "database": "connected"
}
```

mà không cần chỉnh sửa source code.

---

# 28. Deliverables

```text
backend/app/core/config.py

backend/app/db/
├── base.py
├── session.py
└── __init__.py

backend/app/api/
├── dependencies.py
└── __init__.py

backend/app/models/
├── system_info.py
└── __init__.py

backend/alembic/
├── env.py
├── versions/
└── script.py.mako

backend/alembic.ini

backend/tests/
└── test_database.py

docker-compose.yml

.env.example

docs/tasks/
└── TASK_02_DATABASE_FOUNDATION.md
```

---

# 29. Không thực hiện trong Task 02

Không làm:

```text
users table
password
JWT
roles
Family
FamilyMember
HealthProfile
Medication
Prescription
MedicationSchedule
Cabinet
Digital Twin
AI
```

Task 02 chỉ xây nền database.

---

# 30. Task tiếp theo

Sau Task 02:

```text
TASK 03 — Authentication & User Foundation
```

Task 03 dự kiến gồm:

```text
User model
Email
Password hash
User status
Register
Login
JWT Access Token
Refresh Token
GET /auth/me
Authentication dependency
Protected endpoint
Auth tests
```

---

# 31. Roadmap hiện tại

```text
TASK 01
Project Initialization
        ↓
TASK 02
PostgreSQL Database Foundation
        ↓
TASK 03
Authentication & User
        ↓
TASK 04
Family Management
        ↓
TASK 05
Member / Health Profile
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

# 32. Nguyên tắc chuyển task

Không chuyển sang Task 03 nếu:

```text
Alembic chưa hoạt động
```

hoặc:

```text
GET /health/db
```

chưa pass.

> **Mỗi task phải tạo ra một nền tảng ổn định cho task tiếp theo.**
