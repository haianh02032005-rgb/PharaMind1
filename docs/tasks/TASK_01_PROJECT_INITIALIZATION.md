# PharmaMind AI — TASK 01 SPECIFICATION

# TASK 01 — Khởi tạo nền tảng dự án

## 1. Mục tiêu

Task đầu tiên nhằm tạo một nền tảng dự án sạch, thống nhất và có thể chạy được để toàn bộ các task tiếp theo của **PharmaMind AI** được xây dựng tuần tự trên cùng một cấu trúc.

Task này **chưa xây dựng nghiệp vụ sức khỏe, thuốc, AI hay Digital Twin**.

Mục tiêu duy nhất là:

> **Khởi tạo repository, môi trường Python, FastAPI backend và cấu trúc thư mục nền tảng để hệ thống có thể chạy được thành công.**

---

# 2. Phạm vi Task 01

Task 01 bao gồm:

```text
1. Tạo repository PharmaMind AI
2. Tạo cấu trúc thư mục ban đầu
3. Thiết lập Python 3.12
4. Tạo virtual environment
5. Cài dependencies backend
6. Khởi tạo FastAPI
7. Tạo endpoint kiểm tra hệ thống
8. Chuẩn hóa biến môi trường
9. Tạo .gitignore
10. Kiểm tra backend chạy thành công
```

Task này chưa bao gồm:

```text
Database schema
PostgreSQL integration
Authentication
Family Management
Medication Management
Digital Twin
Hardware Simulator
AI
Flutter App
```

Những phần trên sẽ được thực hiện ở các task tiếp theo.

---

# 3. Kết quả mong muốn

Sau khi hoàn thành Task 01, project phải có thể chạy lệnh:

```bash
uvicorn backend.app.main:app --reload
```

và truy cập:

```text
http://127.0.0.1:8000
```

Backend phải trả về:

```json
{
  "name": "PharmaMind AI",
  "status": "running",
  "version": "0.1.0"
}
```

Đồng thời endpoint:

```text
GET /health
```

phải trả về:

```json
{
  "status": "ok"
}
```

---

# 4. Công nghệ sử dụng

## Python

```text
Python 3.12.x
```

Khuyến nghị:

```text
Python 3.12
```

---

## Backend Framework

```text
FastAPI
```

---

## ASGI Server

```text
Uvicorn
```

---

## Data Validation

```text
Pydantic
```

---

## Environment Configuration

```text
pydantic-settings
```

---

# 5. Cấu trúc thư mục sau Task 01

Sau Task 01 repository tối thiểu phải có cấu trúc:

```text
pharmamind-ai/
│
├── README.md
├── requirements.txt
├── .python-version
├── .gitignore
├── .env.example
│
├── backend/
│   ├── __init__.py
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       │
│       └── core/
│           ├── __init__.py
│           └── config.py
│
├── mobile/
│
├── hardware-simulator/
│
├── 3d-assets/
│
├── ai/
│
├── docs/
│   ├── architecture/
│   └── tasks/
│       └── TASK_01_PROJECT_INITIALIZATION.md
│
└── tests/
```

Các thư mục chưa dùng ngay vẫn được tạo trước để thống nhất kiến trúc.

---

# 6. Bước 1 — Tạo repository

Tên repository đề xuất:

```text
pharmamind-ai
```

Khởi tạo:

```bash
mkdir pharmamind-ai
cd pharmamind-ai
git init
```

---

# 7. Bước 2 — Tạo virtual environment

Windows:

```bash
py -3.12 -m venv .venv
```

hoặc:

```bash
python -m venv .venv
```

Kích hoạt:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

---

# 8. Bước 3 — Kiểm tra phiên bản Python

Chạy:

```bash
python --version
```

Kết quả mong muốn:

```text
Python 3.12.x
```

Nếu không đúng phiên bản thì chưa tiếp tục task.

---

# 9. Bước 4 — Cài dependencies

File:

```text
requirements.txt
```

sử dụng file requirements đã thống nhất của dự án.

Cài đặt:

```bash
python -m pip install --upgrade pip
```

sau đó:

```bash
pip install -r requirements.txt
```

Kiểm tra FastAPI:

```bash
python -c "import fastapi; print(fastapi.__version__)"
```

---

# 10. Bước 5 — Tạo FastAPI Application

Tạo file:

```text
backend/app/main.py
```

Nội dung ban đầu:

```python
from fastapi import FastAPI

app = FastAPI(
    title="PharmaMind AI API",
    description="Backend API for PharmaMind AI",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "PharmaMind AI",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }
```

---

# 11. Bước 6 — Tạo Config

Tạo:

```text
backend/app/core/config.py
```

Nội dung:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PharmaMind AI"
    app_version: str = "0.1.0"
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
```

---

# 12. Bước 7 — Sử dụng Config trong main.py

Sau đó có thể sửa:

```text
backend/app/main.py
```

thành:

```python
from fastapi import FastAPI

from backend.app.core.config import settings


app = FastAPI(
    title=f"{settings.app_name} API",
    version=settings.app_version,
)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "running",
        "version": settings.app_version,
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }
```

---

# 13. Bước 8 — Environment file

Không commit trực tiếp file:

```text
.env
```

Tạo file mẫu:

```text
.env.example
```

Nội dung:

```env
APP_NAME=PharmaMind AI
APP_VERSION=0.1.0
DEBUG=true

DATABASE_URL=
JWT_SECRET=
REDIS_URL=
MQTT_URL=
OPENAI_API_KEY=
```

Ở Task 01 chỉ sử dụng:

```env
APP_NAME
APP_VERSION
DEBUG
```

Các biến khác để chuẩn bị cho task sau.

---

# 14. Bước 9 — .gitignore

Tạo:

```text
.gitignore
```

Nội dung tối thiểu:

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd

# Virtual Environment
.venv/
venv/

# Environment
.env

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Pytest
.pytest_cache/

# Coverage
.coverage
htmlcov/

# Logs
*.log

# Build
dist/
build/

# Python packaging
*.egg-info/
```

---

# 15. Bước 10 — Tạo __init__.py

Phải có:

```text
backend/__init__.py
backend/app/__init__.py
backend/app/core/__init__.py
```

Các file này có thể để trống.

Mục đích:

```text
đảm bảo Python nhận diện package
```

---

# 16. Bước 11 — Khởi động Backend

Từ thư mục root:

```bash
uvicorn backend.app.main:app --reload
```

Kết quả mong muốn:

```text
Uvicorn running on http://127.0.0.1:8000
```

---

# 17. Bước 12 — Kiểm tra Endpoint Root

Mở:

```text
http://127.0.0.1:8000/
```

Response:

```json
{
  "name": "PharmaMind AI",
  "status": "running",
  "version": "0.1.0"
}
```

---

# 18. Bước 13 — Kiểm tra Health Endpoint

Mở:

```text
http://127.0.0.1:8000/health
```

Response:

```json
{
  "status": "ok"
}
```

---

# 19. Bước 14 — Kiểm tra Swagger

FastAPI tự sinh tài liệu API.

Mở:

```text
http://127.0.0.1:8000/docs
```

Phải xuất hiện:

```text
PharmaMind AI API
```

và có hai endpoint:

```text
GET /
GET /health
```

---

# 20. Bước 15 — Tạo Test đầu tiên

Tạo:

```text
backend/tests/test_health.py
```

Nội dung:

```python
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
```

---

# 21. Chạy Test

Chạy:

```bash
pytest
```

Kết quả mong muốn:

```text
1 passed
```

---

# 22. API của Task 01

Task này chỉ có hai endpoint.

## Root

```http
GET /
```

Response:

```json
{
  "name": "PharmaMind AI",
  "status": "running",
  "version": "0.1.0"
}
```

---

## Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

---

# 23. Quy tắc code từ Task 01

Từ task đầu tiên cần thống nhất một số nguyên tắc.

## Rule 01

Không đặt toàn bộ code vào:

```text
main.py
```

`main.py` chỉ dùng để:

```text
khởi tạo app
đăng ký router
middleware
startup / shutdown
```

---

## Rule 02

Business logic phải được tách theo module ở các task sau.

Luồng chuẩn:

```text
Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

---

## Rule 03

Không hard-code:

```text
secret key
database password
API key
```

Các giá trị này phải nằm trong:

```text
.env
```

---

## Rule 04

Không commit:

```text
.env
.venv/
API key
password
secret
```

---

## Rule 05

Mỗi task phải có tài liệu riêng trong:

```text
docs/tasks/
```

Ví dụ:

```text
TASK_01_PROJECT_INITIALIZATION.md
TASK_02_DATABASE_SETUP.md
TASK_03_AUTHENTICATION.md
...
```

---

# 24. Acceptance Criteria

Task 01 chỉ được coi là hoàn thành khi đáp ứng toàn bộ các điều kiện sau.

- [ ] Repository PharmaMind AI đã được tạo.
- [ ] Python 3.12 được sử dụng.
- [ ] `.venv` hoạt động.
- [ ] `requirements.txt` được cài thành công.
- [ ] Cấu trúc thư mục cơ bản đã được tạo.
- [ ] FastAPI khởi động không lỗi.
- [ ] `GET /` trả về HTTP 200.
- [ ] `GET /health` trả về HTTP 200.
- [ ] Swagger chạy tại `/docs`.
- [ ] `pytest` chạy thành công.
- [ ] Có `.env.example`.
- [ ] `.env` được ignore.
- [ ] `.venv` được ignore.
- [ ] Không có secret trong source code.

---

# 25. Definition of Done

Task được đánh dấu:

```text
DONE
```

khi có thể chạy:

```bash
git clone <repository>
cd pharmamind-ai

python -m venv .venv
```

sau đó:

```bash
pip install -r requirements.txt
```

và:

```bash
uvicorn backend.app.main:app --reload
```

mà không cần sửa source code thủ công.

---

# 26. Deliverables

Sau Task 01 cần có:

```text
README.md

requirements.txt

.python-version

.env.example

.gitignore

backend/
└── app/
    ├── main.py
    └── core/
        └── config.py

backend/tests/
└── test_health.py

docs/tasks/
└── TASK_01_PROJECT_INITIALIZATION.md
```

---

# 27. Không thực hiện trong Task 01

Để tránh scope creep, không làm:

```text
PostgreSQL
SQLAlchemy models
Alembic migrations

JWT Auth
User model

Family
Member

Medication
Prescription
Schedule

Flutter UI

Digital Twin

Hardware Simulator

AI Pharmacist
```

Các nội dung này được triển khai tuần tự ở task sau.

---

# 28. Task tiếp theo

Sau khi Task 01 hoàn thành, task tiếp theo đề xuất là:

```text
TASK 02 — PostgreSQL Database Foundation
```

Task 02 sẽ gồm:

```text
PostgreSQL
SQLAlchemy
Database connection
Base Model
Alembic
Migration đầu tiên
Database health check
```

---

# 29. Luồng phát triển

```text
TASK 01
Project Initialization
        ↓
TASK 02
Database Foundation
        ↓
TASK 03
Authentication
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
        ↓
...
```

Nguyên tắc của dự án:

> **Chỉ chuyển sang task tiếp theo khi Acceptance Criteria của task hiện tại đã đạt đầy đủ.**
