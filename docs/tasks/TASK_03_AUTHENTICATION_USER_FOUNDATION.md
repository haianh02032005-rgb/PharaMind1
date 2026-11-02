# PharmaMind AI — TASK 03 SPECIFICATION

# TASK 03 — Authentication & User Foundation

## 1. Mục tiêu

Task 03 xây dựng nền tảng xác thực người dùng cho PharmaMind AI.

Sau Task 01 và Task 02, hệ thống đã có:

```text
FastAPI
PostgreSQL
SQLAlchemy
Alembic
Database Session
Health Check
```

Task 03 sẽ bổ sung:

```text
User Model
Password Hashing
Register
Login
JWT Access Token
Refresh Token
GET /auth/me
Authentication Dependency
Protected Route
Auth Tests
```

Mục tiêu cuối cùng:

> **Người dùng có thể đăng ký tài khoản, đăng nhập, nhận access token/refresh token và truy cập các API được bảo vệ bằng JWT.**

---

# 2. Điều kiện tiên quyết

Chỉ bắt đầu Task 03 khi Task 02 đã hoàn thành đầy đủ.

Phải kiểm tra:

```text
GET /health
GET /health/db
```

đều hoạt động.

Lệnh:

```bash
alembic current
```

phải cho thấy database đang ở migration mới nhất.

---

# 3. Phạm vi Task 03

Task 03 bao gồm:

```text
1. Thiết kế User model
2. User status
3. Email normalization
4. Password hashing
5. User Repository
6. User Service
7. Register API
8. Login API
9. JWT Access Token
10. JWT Refresh Token
11. Refresh Token API
12. Authentication Dependency
13. GET /auth/me
14. Protected endpoint
15. Logout strategy cơ bản
16. Alembic migration
17. Validation
18. Error handling
19. Authentication tests
20. Security rules cơ bản
```

Task 03 không bao gồm:

```text
Family
Family Member
Health Profile
Medication
Prescription
Role Permission nâng cao
OAuth Google
OTP
2FA
Forgot Password
Email Verification
Admin Portal
```

---

# 4. Công nghệ sử dụng

```text
FastAPI
SQLAlchemy
PostgreSQL
Alembic
Pydantic
PyJWT
argon2-cffi
pytest
httpx
```

Python:

```text
Python 3.12.x
```

---

# 5. Kiến trúc Authentication

Luồng đăng nhập:

```text
Client
  ↓
POST /auth/login
  ↓
Auth Router
  ↓
Auth Service
  ↓
User Repository
  ↓
PostgreSQL
  ↓
Verify Password
  ↓
Generate JWT
  ↓
Access Token + Refresh Token
```

Luồng API bảo vệ:

```text
Client
  ↓
Authorization: Bearer <access_token>
  ↓
Auth Dependency
  ↓
Decode JWT
  ↓
Find User
  ↓
Validate User Status
  ↓
Protected Endpoint
```

---

# 6. Cấu trúc thư mục sau Task 03

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── exceptions.py
│   │
│   ├── api/
│   │   ├── dependencies.py
│   │   └── router.py
│   │
│   ├── models/
│   │   ├── system_info.py
│   │   ├── user.py
│   │   └── __init__.py
│   │
│   └── modules/
│       ├── auth/
│       │   ├── router.py
│       │   ├── service.py
│       │   ├── schema.py
│       │   └── dependencies.py
│       │
│       └── users/
│           ├── repository.py
│           ├── service.py
│           ├── schema.py
│           └── exceptions.py
│
├── alembic/
│   └── versions/
│       └── xxxx_create_users_table.py
│
└── tests/
    ├── test_auth_register.py
    ├── test_auth_login.py
    ├── test_auth_me.py
    └── test_auth_refresh.py
```

---

# 7. User Model

Tạo:

```text
backend/app/models/user.py
```

Đề xuất:

```python
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=UserStatus.ACTIVE.value,
        nullable=False,
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
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

# 8. Quy tắc User ID

Giai đoạn MVP có thể sử dụng:

```text
BIGINT / INTEGER AUTO INCREMENT
```

Không cần chuyển sang UUID ngay nếu chưa có yêu cầu phân tán hệ thống.

Nếu sau này cần public resource ID, có thể bổ sung:

```text
public_id UUID
```

riêng.

---

# 9. Email Normalization

Trước khi lưu email:

```text
Remove leading/trailing spaces
Convert lowercase
```

Ví dụ:

```text
" User@Example.COM "
```

trở thành:

```text
"user@example.com"
```

Function đề xuất:

```python
def normalize_email(email: str) -> str:
    return email.strip().lower()
```

---

# 10. Password Policy

MVP tối thiểu:

```text
Minimum length: 8
Maximum length: 128
```

Khuyến nghị:

```text
ít nhất 1 chữ
ít nhất 1 số
```

Không bắt buộc rule quá phức tạp ở MVP.

Không lưu:

```text
plain password
```

trong database.

---

# 11. Password Hashing

Sử dụng:

```text
Argon2
```

Tạo:

```text
backend/app/core/security.py
```

Ví dụ:

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    try:
        return password_hasher.verify(
            password_hash,
            password,
        )
    except VerifyMismatchError:
        return False
```

---

# 12. Không tự hash bằng SHA256

Không sử dụng:

```python
hashlib.sha256(password.encode()).hexdigest()
```

để lưu mật khẩu.

Password hashing phải dùng thuật toán chuyên dụng như:

```text
Argon2
```

---

# 13. JWT Configuration

Bổ sung `.env.example`:

```env
JWT_SECRET=change-me
JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

Trong môi trường thật:

```text
JWT_SECRET
```

phải là chuỗi ngẫu nhiên mạnh.

Không commit secret thật.

---

# 14. Update Settings

Trong:

```text
backend/app/core/config.py
```

bổ sung:

```python
jwt_secret: str
jwt_algorithm: str = "HS256"

access_token_expire_minutes: int = 30
refresh_token_expire_days: int = 30
```

---

# 15. JWT Claims

Access token tối thiểu gồm:

```json
{
  "sub": "123",
  "type": "access",
  "iat": 1730000000,
  "exp": 1730001800
}
```

Refresh token:

```json
{
  "sub": "123",
  "type": "refresh",
  "iat": 1730000000,
  "exp": 1732592000
}
```

---

# 16. Access Token

Access token dùng để gọi API.

TTL đề xuất:

```text
30 phút
```

Không nên dùng access token kéo dài nhiều ngày.

---

# 17. Refresh Token

Refresh token dùng để lấy access token mới.

TTL đề xuất:

```text
30 ngày
```

Task 03 có thể sử dụng JWT refresh token stateless.

Ở giai đoạn sau có thể nâng cấp thành:

```text
Refresh Token Rotation
Token Revocation
Session Table
Device Management
```

---

# 18. JWT Utility

Trong:

```text
backend/app/core/security.py
```

bổ sung:

```python
from datetime import datetime, timedelta, timezone

import jwt

from backend.app.core.config import settings


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(
            days=settings.refresh_token_expire_days
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
```

---

# 19. Decode Token

Function:

```python
def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
```

Phải xử lý:

```text
ExpiredSignatureError
InvalidTokenError
```

---

# 20. User Repository

Tạo:

```text
backend/app/modules/users/repository.py
```

Nhiệm vụ:

```text
find_by_id()
find_by_email()
create()
```

Không đặt business logic trong repository.

Ví dụ interface logic:

```python
class UserRepository:

    def get_by_id(self, db, user_id):
        ...

    def get_by_email(self, db, email):
        ...

    def create(self, db, user):
        ...
```

---

# 21. User Service

Tạo:

```text
backend/app/modules/users/service.py
```

Nhiệm vụ:

```text
normalize email
kiểm tra duplicate email
hash password
create user
```

---

# 22. Auth Schema

Tạo:

```text
backend/app/modules/auth/schema.py
```

Các schema tối thiểu:

```text
RegisterRequest
LoginRequest
TokenResponse
RefreshTokenRequest
CurrentUserResponse
```

---

# 23. RegisterRequest

Ví dụ:

```python
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    full_name: str = Field(
        min_length=1,
        max_length=150,
    )
```

Nếu dùng `EmailStr`, cần đảm bảo dependency email validator có trong môi trường.

Nếu chưa muốn thêm dependency, có thể sử dụng validation email đơn giản trong Task 03 và nâng cấp sau.

---

# 24. Register API

Endpoint:

```http
POST /auth/register
```

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPass123",
  "full_name": "Nguyen Van A"
}
```

Response đề xuất:

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Nguyen Van A",
  "status": "ACTIVE"
}
```

HTTP:

```text
201 Created
```

---

# 25. Register Flow

```text
POST /auth/register
      ↓
Validate Request
      ↓
Normalize Email
      ↓
Check Existing User
      ↓
Hash Password
      ↓
Insert User
      ↓
Commit
      ↓
Return Public User
```

---

# 26. Duplicate Email

Nếu email đã tồn tại:

HTTP:

```text
409 Conflict
```

Response:

```json
{
  "detail": "Email already registered"
}
```

Không tạo user thứ hai.

---

# 27. Login API

Endpoint:

```http
POST /auth/login
```

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPass123"
}
```

Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

---

# 28. Login Flow

```text
POST /auth/login
      ↓
Normalize Email
      ↓
Find User
      ↓
Verify Password
      ↓
Check User Status
      ↓
Create Access Token
      ↓
Create Refresh Token
      ↓
Return Tokens
```

---

# 29. Login Failure

Nếu:

```text
email không tồn tại
```

hoặc:

```text
password sai
```

nên trả chung:

```text
401 Unauthorized
```

Response:

```json
{
  "detail": "Invalid email or password"
}
```

Không nên cho biết cụ thể:

```text
email tồn tại hay không
```

---

# 30. User Status

Các trạng thái:

```text
ACTIVE
INACTIVE
BLOCKED
```

Chỉ:

```text
ACTIVE
```

được login.

Nếu user bị block:

```text
403 Forbidden
```

---

# 31. Authentication Dependency

Tạo:

```text
backend/app/modules/auth/dependencies.py
```

Sử dụng:

```python
OAuth2PasswordBearer
```

hoặc Bearer header parser tương đương.

Flow:

```text
Authorization Header
      ↓
Bearer Token
      ↓
Decode JWT
      ↓
Check type == access
      ↓
Read sub
      ↓
Find User
      ↓
Check ACTIVE
      ↓
return User
```

---

# 32. Current User Dependency

Ví dụ:

```python
def get_current_user(...):
    ...
```

Task sau sẽ dùng dependency này cho:

```text
Family API
Health Profile
Medication
Cabinet
```

---

# 33. GET /auth/me

Endpoint:

```http
GET /auth/me
```

Header:

```text
Authorization: Bearer <access_token>
```

Response:

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Nguyen Van A",
  "status": "ACTIVE",
  "is_email_verified": false
}
```

---

# 34. /auth/me không có token

HTTP:

```text
401 Unauthorized
```

---

# 35. Refresh Token API

Endpoint:

```http
POST /auth/refresh
```

Request:

```json
{
  "refresh_token": "..."
}
```

Flow:

```text
Decode Token
   ↓
Check type == refresh
   ↓
Read User ID
   ↓
Find User
   ↓
Check ACTIVE
   ↓
Generate New Access Token
   ↓
Return
```

Response tối thiểu:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

---

# 36. Không dùng Access Token để Refresh

Nếu gửi:

```text
type = access
```

vào:

```text
POST /auth/refresh
```

phải reject.

HTTP:

```text
401 Unauthorized
```

---

# 37. Logout Strategy cho MVP

JWT access token là stateless.

Ở Task 03, logout phía client có thể là:

```text
Delete access token
Delete refresh token
```

Server-side token revocation chưa cần triển khai.

Sau này có thể bổ sung:

```text
Auth Session
Refresh Token Rotation
Revoked Token Table
Device Sessions
```

---

# 38. API Router

Tạo:

```text
backend/app/api/router.py
```

Ví dụ:

```python
from fastapi import APIRouter

from backend.app.modules.auth.router import router as auth_router


api_router = APIRouter()

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)
```

Trong `main.py`:

```python
app.include_router(api_router)
```

---

# 39. Auth Router

Tạo:

```text
backend/app/modules/auth/router.py
```

Các endpoint:

```text
POST /auth/register
POST /auth/login
POST /auth/refresh
GET  /auth/me
```

---

# 40. Separation of Concerns

Không viết toàn bộ logic trong router.

Sai:

```text
router
 ├─ query DB
 ├─ hash password
 ├─ create JWT
 └─ commit
```

Đúng:

```text
Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

Security utility:

```text
core/security.py
```

---

# 41. Migration users

Sau khi tạo User model:

```bash
alembic revision --autogenerate -m "create users table"
```

Review migration.

Sau đó:

```bash
alembic upgrade head
```

Database phải có:

```text
users
```

---

# 42. Kiểm tra Database

Có thể kiểm tra:

```sql
SELECT
    id,
    email,
    full_name,
    status,
    created_at
FROM users;
```

Không query/log:

```text
password_hash
```

nếu không cần thiết.

---

# 43. User Public Schema

Không bao giờ trả:

```text
password_hash
```

qua API.

Response user chỉ gồm:

```text
id
email
full_name
status
is_email_verified
created_at
```

---

# 44. Test — Register Success

Test:

```text
POST /auth/register
```

Expected:

```text
201
```

Sau đó kiểm tra user tồn tại trong DB.

---

# 45. Test — Duplicate Register

Đăng ký cùng email hai lần.

Expected lần 2:

```text
409
```

---

# 46. Test — Email Normalization

Register:

```text
TEST@EXAMPLE.COM
```

Login:

```text
test@example.com
```

phải thành công.

---

# 47. Test — Password Hashing

Sau register:

```text
stored password != input password
```

Phải xác minh:

```text
password_hash
```

không chứa plain text password.

---

# 48. Test — Login Success

Expected:

```text
200
access_token
refresh_token
token_type=bearer
```

---

# 49. Test — Wrong Password

Expected:

```text
401
```

---

# 50. Test — Unknown Email

Expected:

```text
401
```

Response không tiết lộ user tồn tại hay không.

---

# 51. Test — GET /auth/me

Với access token hợp lệ:

```text
200
```

User trả về phải đúng.

---

# 52. Test — /auth/me Without Token

Expected:

```text
401
```

---

# 53. Test — Invalid Token

Token:

```text
abc.invalid.token
```

Expected:

```text
401
```

---

# 54. Test — Expired Token

Token hết hạn:

Expected:

```text
401
```

---

# 55. Test — Refresh Success

Refresh token hợp lệ:

```text
POST /auth/refresh
```

Expected:

```text
200
new access_token
```

---

# 56. Test — Refresh bằng Access Token

Expected:

```text
401
```

---

# 57. Test — Blocked User

Nếu:

```text
status = BLOCKED
```

Login phải fail.

Protected endpoint cũng phải fail.

---

# 58. Error Response Convention

MVP có thể dùng format:

```json
{
  "detail": "Error message"
}
```

Task sau có thể chuẩn hóa thành:

```json
{
  "error": {
    "code": "...",
    "message": "...",
    "details": {}
  }
}
```

---

# 59. Security Rules

## Rule 01

Không lưu plain password.

## Rule 02

Không log password.

## Rule 03

Không log full token.

## Rule 04

Không trả password hash.

## Rule 05

JWT secret chỉ lấy từ environment.

## Rule 06

Access token phải có expiration.

## Rule 07

Refresh token phải có expiration.

## Rule 08

Kiểm tra claim `type`.

## Rule 09

User phải tồn tại khi token được sử dụng.

## Rule 10

User phải `ACTIVE`.

---

# 60. Không lưu token trong source code

Sai:

```python
JWT_SECRET = "my-secret"
```

Đúng:

```python
settings.jwt_secret
```

---

# 61. Logging

Không log:

```text
password
password_hash
JWT
refresh token
```

Có thể log:

```text
user_id
event
status
timestamp
```

Ví dụ:

```text
AUTH_LOGIN_SUCCESS user_id=12
```

---

# 62. Authentication Event — Future Ready

Task 03 chưa cần DB audit log.

Nhưng nên thiết kế để sau có:

```text
REGISTER
LOGIN_SUCCESS
LOGIN_FAILED
REFRESH
LOGOUT
PASSWORD_CHANGED
ACCOUNT_BLOCKED
```

---

# 63. API Summary

Sau Task 03:

```http
GET  /
GET  /health
GET  /health/db

POST /auth/register
POST /auth/login
POST /auth/refresh
GET  /auth/me
```

---

# 64. Example Full Flow

## Register

```http
POST /auth/register
```

```json
{
  "email": "lan@example.com",
  "password": "Password123",
  "full_name": "Nguyen Thi Lan"
}
```

↓

```json
{
  "id": 1,
  "email": "lan@example.com",
  "full_name": "Nguyen Thi Lan",
  "status": "ACTIVE"
}
```

---

## Login

```http
POST /auth/login
```

```json
{
  "email": "lan@example.com",
  "password": "Password123"
}
```

↓

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

---

## Current User

```http
GET /auth/me
Authorization: Bearer <access_token>
```

↓

```json
{
  "id": 1,
  "email": "lan@example.com",
  "full_name": "Nguyen Thi Lan",
  "status": "ACTIVE"
}
```

---

# 65. Acceptance Criteria

Task 03 chỉ được coi là hoàn thành khi:

- [ ] User model đã được tạo.
- [ ] Email unique.
- [ ] Email được normalize.
- [ ] Password được hash bằng Argon2.
- [ ] Plain password không được lưu.
- [ ] Migration users được tạo.
- [ ] `alembic upgrade head` thành công.
- [ ] Register API hoạt động.
- [ ] Duplicate email trả 409.
- [ ] Login hoạt động.
- [ ] Sai password trả 401.
- [ ] User không tồn tại trả 401.
- [ ] Access token được tạo.
- [ ] Refresh token được tạo.
- [ ] Access token có expiration.
- [ ] Refresh token có expiration.
- [ ] Token có claim `type`.
- [ ] `/auth/me` hoạt động.
- [ ] `/auth/me` được bảo vệ.
- [ ] Refresh endpoint hoạt động.
- [ ] Access token không dùng được làm refresh token.
- [ ] Blocked user không được login.
- [ ] API không bao giờ trả `password_hash`.
- [ ] Authentication tests pass.

---

# 66. Definition of Done

Task 03 được đánh dấu:

```text
DONE
```

khi có thể thực hiện toàn bộ chuỗi:

```text
Register
   ↓
Login
   ↓
Receive Access Token
   ↓
GET /auth/me
   ↓
Access Token Expires
   ↓
POST /auth/refresh
   ↓
Receive New Access Token
```

mà không cần thao tác database thủ công.

---

# 67. Deliverables

Sau Task 03 cần có:

```text
backend/app/models/
└── user.py

backend/app/core/
└── security.py

backend/app/modules/auth/
├── router.py
├── service.py
├── schema.py
└── dependencies.py

backend/app/modules/users/
├── repository.py
├── service.py
├── schema.py
└── exceptions.py

backend/alembic/versions/
└── xxxx_create_users_table.py

backend/tests/
├── test_auth_register.py
├── test_auth_login.py
├── test_auth_me.py
└── test_auth_refresh.py

docs/tasks/
└── TASK_03_AUTHENTICATION_USER_FOUNDATION.md
```

---

# 68. Không thực hiện trong Task 03

Không làm:

```text
Family
Family roles
Caregiver

Health profile
Allergy profile

Medication
Prescription
Schedule

Digital Twin

AI Pharmacist

Google Login
Apple Login
2FA
OTP
Forgot Password
Email Verification Flow
```

---

# 69. Task tiếp theo

Sau Task 03:

```text
TASK 04 — Family Management
```

Task 04 sẽ tập trung:

```text
Family model
Family membership
Family owner
Create family
List families
Get family
Update family
Add member relationship
Authorization theo family
Family tests
```

---

# 70. Roadmap

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
```

---

# 71. Nguyên tắc chuyển task

Không chuyển sang Task 04 nếu chưa test được chuỗi:

```text
REGISTER
  ↓
LOGIN
  ↓
JWT
  ↓
GET /auth/me
  ↓
REFRESH TOKEN
```

và toàn bộ Authentication Test chưa pass.

> **Task 03 là lớp danh tính của toàn bộ PharmaMind AI. Mọi dữ liệu gia đình, sức khỏe, thuốc và tủ thuốc ở các task sau đều phải gắn với người dùng đã được xác thực.**
