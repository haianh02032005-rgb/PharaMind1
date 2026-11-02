# PharmaMind AI — PRODUCTION SERVER DEPLOYMENT PLAN

## 1. Mục tiêu

Triển khai toàn bộ **PharmaMind AI** lên server để nhiều người có thể sử dụng đồng thời mà không làm suy giảm đáng kể chất lượng hệ thống.

Hệ thống production cần phục vụ ổn định các nhóm chức năng:

```text
Mobile App
FastAPI Backend
PostgreSQL
Redis
OCR / Excel Import
Medication / Prescription / Schedule
Smart Cabinet
WebSocket Realtime
Digital Twin 3D
Notification
AI Pharmacist
Hardware Simulator / ESP32
```

Mục tiêu cốt lõi:

```text
Ổn định
Bảo mật
Dễ backup
Dễ monitor
Không block API khi OCR / AI chạy
Realtime ổn định
Có thể scale mà không viết lại hệ thống
```

---

## 2. Giải pháp kiến trúc

Không triển khai tất cả vào một process duy nhất.

Sai:

```text
1 process
├── API
├── OCR
├── AI
├── Database
├── WebSocket
└── Background Jobs
```

Đúng:

```text
Internet
   ↓
HTTPS / Reverse Proxy
   ↓
FastAPI API replicas
   ↓
Redis + PostgreSQL
   ↓
Background Workers
   ├── OCR / Excel
   ├── Notification
   └── AI
```

Nguyên tắc:

> **Tách workload theo chức năng, dù giai đoạn đầu các container vẫn chạy trên cùng một VPS.**

---

## 3. Kiến trúc production đề xuất

```text
                    INTERNET
                       │
                       ▼
                 DNS / HTTPS
                       │
                       ▼
                 NGINX / Caddy
                 Reverse Proxy
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
   FastAPI #1      FastAPI #2       WebSocket
       │               │                │
       └───────┬───────┴────────────────┘
               │
               ▼
             Redis
       Cache / Queue / PubSub
               │
      ┌────────┼───────────────┐
      │        │               │
      ▼        ▼               ▼
 PostgreSQL  OCR Worker     AI Worker
      │        │               │
      │        ▼               ▼
      │    OCR / Excel      LLM / RAG
      │
      ▼
Object Storage
Prescription / Image / PDF / GLB / Backup
```

---

## 4. Giai đoạn đầu — Một VPS

Có thể triển khai toàn bộ trên **một VPS**, nhưng vẫn tách container:

```text
Production VPS
├── nginx
├── api-1
├── api-2
├── worker-import
├── worker-notification
├── redis
├── postgres
├── monitoring
└── backup-agent
```

File upload lớn và backup nên được lưu ra object storage ngoài VPS nếu có thể.

---

## 5. Cấu hình server đề xuất

### Pilot nhỏ

```text
20–100 user
< 20 concurrent users
```

Khuyến nghị:

```text
4 vCPU
8 GB RAM
100 GB NVMe SSD
```

### Small Production

```text
100–500 user
20–100 concurrent users
OCR thường xuyên
WebSocket realtime
```

Khuyến nghị:

```text
8 vCPU
16 GB RAM
200 GB NVMe SSD
```

### Growth

Nếu vượt khoảng:

```text
100+ concurrent users
OCR / AI tải cao
```

nên dùng:

```text
16 vCPU
32 GB RAM
```

hoặc bắt đầu tách database / worker sang server riêng.

Các con số chỉ là điểm khởi đầu; quyết định scale phải dựa vào load test và monitoring thực tế.

---

## 6. Hệ điều hành

Khuyến nghị:

```text
Ubuntu Server LTS
```

Chỉ cài:

```text
Docker Engine
Docker Compose
Firewall
SSH
Monitoring agent
Backup tools
```

Không cần GUI.

---

## 7. Container hóa

Mỗi workload một container/service riêng:

```text
nginx
backend-api
worker-import
worker-notification
redis
postgres
monitoring
```

Không gộp PostgreSQL, Redis và FastAPI vào cùng container.

---

## 8. Cấu trúc deployment

```text
deploy/
├── compose.yaml
├── compose.production.yaml
├── nginx/
│   └── nginx.conf
├── scripts/
│   ├── deploy.sh
│   ├── backup.sh
│   ├── restore.sh
│   └── healthcheck.sh
└── env/
    └── .env.production.example
```

---

## 9. Reverse Proxy

Nginx hoặc Caddy chịu trách nhiệm:

```text
HTTPS termination
HTTP → HTTPS
Reverse proxy
WebSocket upgrade
Rate limiting
Security headers
Access logs
Upload size limit
```

Luồng:

```text
https://api.pharmamind.vn
          ↓
        Nginx
          ↓
       FastAPI
```

Mobile WebSocket:

```text
wss://api.pharmamind.vn/ws/...
```

---

## 10. HTTPS bắt buộc

Production không dùng:

```text
http://server-ip:8000
```

App phải dùng:

```text
HTTPS
WSS
```

FastAPI không expose port trực tiếp ra Internet.

---

## 11. Firewall

Chỉ public:

```text
80
443
SSH
```

Không public:

```text
5432 PostgreSQL
6379 Redis
8000 FastAPI
```

---

## 12. SSH hardening

Khuyến nghị:

```text
SSH key only
Disable password login
Disable root login
```

---

## 13. FastAPI production

Không dùng:

```bash
uvicorn ... --reload
```

Production chạy nhiều API instance/worker thích hợp.

Ban đầu:

```text
api-1
api-2
```

để tránh một workload bận làm toàn hệ thống đứng.

---

## 14. Heavy workload phải chạy bất đồng bộ

Đây là nguyên tắc quan trọng nhất.

Không chạy OCR trực tiếp trong request:

```text
POST /import
   ↓
OCR 30 giây
   ↓
Response
```

Phải dùng:

```text
POST /import
   ↓
Create ImportSession
   ↓
Queue Job
   ↓
Return 202 Accepted
```

Worker xử lý phía sau:

```text
Redis Queue
   ↓
OCR Worker
   ↓
ImportSession update
```

---

## 15. Background Job Queue

Redis dùng làm:

```text
Queue Broker
Cache
Pub/Sub
```

Worker framework có thể chọn một trong:

```text
Celery
RQ
Dramatiq
```

Chỉ chọn **một** framework cho project.

---

## 16. Queue phân loại

```text
queue: import
queue: notification
queue: ai
queue: maintenance
```

Không để OCR chiếm hết worker notification.

---

## 17. OCR / Excel Worker

Worker riêng xử lý:

```text
Image preprocessing
OCR
Excel parsing
Normalization
Validation
Import Draft
```

API chính không thực hiện OCR nặng.

---

## 18. AI Worker

Nếu dùng cloud LLM:

```text
AI Worker
   ↓
External LLM API
```

Nếu sau này chạy local model:

```text
Dedicated GPU Server
```

Không nên chạy local LLM nặng trên cùng VPS với API + PostgreSQL.

---

## 19. PostgreSQL

PostgreSQL lưu:

```text
User
Family
Member
Health
Medication
Prescription
Schedule
Cabinet
ImportSession
Audit
```

Không lưu ảnh/PDF/GLB lớn trực tiếp trong database.

---

## 20. Connection Pool

Phải cấu hình connection pool có giới hạn:

```text
pool_size
max_overflow
pool_timeout
pool_recycle
pool_pre_ping
```

Không để request mở connection vô hạn.

---

## 21. Database Index

Index các trường query nhiều:

```text
family_id
member_id
status
created_at
schedule_id
cabinet_id
```

Composite index khi cần:

```text
family_id + member_id
family_id + status
member_id + start_date
```

---

## 22. Database Migration

Production dùng Alembic:

```bash
alembic upgrade head
```

Không sửa schema production bằng tay.

---

## 23. Backup PostgreSQL

Tối thiểu:

```text
Daily logical backup
Off-site copy
Retention
Restore test
```

Khuyến nghị tốt hơn:

```text
Base Backup
+
WAL Archiving
+
Point-in-Time Recovery
```

---

## 24. Backup 3-2-1

```text
3 copies
2 storage types
1 off-site
```

Ví dụ:

```text
Primary Database
Daily Backup
Off-site Object Storage Backup
```

Backup không được nằm duy nhất trên cùng VPS.

---

## 25. Backup schedule

```text
Daily logical/full backup
Continuous WAL archive nếu có
Weekly restore verification
Monthly long-retention backup
```

---

## 26. Object Storage

Dùng cho:

```text
Prescription images
PDF
Excel
Avatar
Medication images
Digital Twin GLB
Export reports
Backups
```

Dùng S3-compatible object storage là phù hợp.

---

## 27. File Security

Không tạo public URL cố định cho đơn thuốc.

Dùng:

```text
Authenticated access
Signed URL
Short expiry
```

---

## 28. Digital Twin Assets

GLB / texture nên serve qua:

```text
Object Storage
CDN nếu cần
```

Không bắt FastAPI stream lại file 3D ở mọi request.

---

## 29. Redis

Redis dùng cho:

```text
cache
queue
rate limit
WebSocket Pub/Sub
short-lived state
```

Redis không phải database chính.

---

## 30. Cache Strategy

Có thể cache ngắn hạn:

```text
Home summary
Family summary
Medication summary
Cabinet state
Next dose
```

Khi Medication / Prescription / Schedule / Cabinet thay đổi phải invalidate cache tương ứng.

---

## 31. WebSocket scaling

Khi có nhiều API replica:

```text
Cabinet Event
   ↓
API / Worker
   ↓
Redis Pub/Sub
   ↓
All WebSocket Nodes
   ↓
Connected Mobile Clients
```

Nhờ đó user kết nối vào API node khác nhau vẫn nhận cùng event.

---

## 32. Notification Architecture

```text
Schedule Engine
    ↓
Notification Queue
    ↓
Notification Worker
    ↓
FCM / APNs
```

Không gửi push trực tiếp trong request API.

---

## 33. MQTT khi tích hợp ESP32

```text
ESP32
 ↓
MQTT Broker
 ↓
Hardware Service
 ↓
Backend
```

MQTT production phải có:

```text
TLS
Device authentication
Topic authorization
No anonymous access
```

---

## 34. Logging

Tách log:

```text
Access Log
Application Log
Worker Log
Security Log
```

Không log:

```text
password
JWT
full prescription content
full health payload
allergy details
```

Dùng structured log khi có thể.

---

## 35. Monitoring

Theo dõi:

```text
CPU
RAM
Disk
Disk IO
Network
API latency
HTTP error rate
DB connections
DB latency
Redis memory
Queue length
Worker processing time
WebSocket connections
OCR processing time
```

---

## 36. Monitoring Stack

Có thể dùng:

```text
Prometheus
Grafana
Node Exporter
cAdvisor
```

Optional:

```text
Loki
Sentry
Uptime Kuma
```

---

## 37. Health Checks

```text
GET /health
GET /health/db
GET /health/redis
GET /health/live
GET /health/ready
```

Liveness:

```text
Process còn sống?
```

Readiness:

```text
Có đủ điều kiện nhận traffic?
```

---

## 38. Alerting

Cảnh báo khi:

```text
CPU > 85%
RAM > 85%
Disk > 80%
API 5xx tăng
DB connection cao
Queue backlog cao
Backup fail
Certificate gần hết hạn
Server unreachable
```

---

## 39. SLO pilot đề xuất

```text
Availability >= 99.5%
```

Normal REST API:

```text
p95 < 400 ms
```

Read API nhẹ:

```text
p95 < 300 ms
```

WebSocket update:

```text
< 2 giây end-to-end
```

OCR là async job nên không tính vào latency API chính.

---

## 40. Load Testing

Trước production phải test:

```text
Login
Home
Family List
Member Detail
Schedule Today
Cabinet State
WebSocket
OCR Upload Queue
```

Dùng:

```text
k6
Locust
```

Test levels:

```text
10 concurrent users
25
50
100
```

Đo:

```text
p50
p95
p99
error rate
CPU
RAM
DB load
queue backlog
```

---

## 41. Trigger scale

Scale khi có số liệu như:

```text
CPU > 75% lâu dài
p95 API > 500 ms
DB resource > 70%
queue backlog tăng liên tục
WebSocket clients vượt target
```

---

## 42. Scale API

```text
api-1
api-2
api-3
api-4
```

Nginx/load balancer phân phối traffic.

---

## 43. Scale OCR Worker

Nếu queue import tăng:

```text
worker-import-1
worker-import-2
worker-import-3
```

Không cần scale toàn bộ backend API.

---

## 44. Scale Database

Khi PostgreSQL trở thành bottleneck:

```text
Move PostgreSQL to dedicated server / managed DB
```

Sau đó có thể thêm read replica khi thật sự cần.

---

## 45. CI/CD

```text
Git Push
  ↓
Automated Tests
  ↓
Build Docker Image
  ↓
Lint / Security Checks
  ↓
Push Image
  ↓
Deploy Staging
  ↓
Smoke Test
  ↓
Approval
  ↓
Deploy Production
```

---

## 46. Environment separation

Bắt buộc:

```text
DEV
STAGING
PRODUCTION
```

Không test feature mới trực tiếp production.

---

## 47. Secrets

Secrets:

```text
DATABASE_URL
JWT_SECRET
REDIS_URL
OBJECT_STORAGE_KEY
OBJECT_STORAGE_SECRET
AI_API_KEY
FCM_CREDENTIALS
```

Không commit lên Git.

---

## 48. Deployment Strategy

Không dùng:

```text
docker compose down
```

cho toàn bộ stack mỗi lần release.

Nên:

```text
Build new image
Start/recreate changed service
Health check
Switch traffic
Keep DB/Redis/Nginx alive when possible
```

---

## 49. Versioning

Docker images:

```text
pharmamind-api:1.4.0
pharmamind-api:1.4.1
```

Không chỉ dùng:

```text
latest
```

để rollback dễ dàng.

---

## 50. API versioning

Dùng:

```text
/v1/...
```

Mobile app cũ có thể tồn tại trên thiết bị nhiều ngày, nên backend cần backward compatibility.

Breaking change lớn:

```text
/v2
```

---

## 51. Rate Limiting

Áp dụng cho:

```text
/login
/register
OCR upload
AI chat
password-related endpoints
```

---

## 52. Upload Limits

Ví dụ MVP:

```text
Image <= 10 MB
PDF <= 20 MB
Excel <= 10 MB
```

Có thể điều chỉnh sau dựa trên dữ liệu thật.

---

## 53. Malware Scanning

Nếu nhận file upload từ người dùng, có thể tích hợp:

```text
ClamAV
```

Excel import chỉ đọc data, không chạy macro.

---

## 54. Dữ liệu sức khỏe

Dữ liệu:

```text
Health Profile
Allergy
Drug Reaction
Prescription
Schedule
```

phải:

```text
encrypt in transit
restrict access
minimize logs
audit important operations
backup securely
```

---

## 55. Audit

Audit các hành động quan trọng:

```text
Login
Prescription Import
Prescription Update
Health Update
Role Change
Cabinet Assignment
Critical Safety Update
```

---

## 56. Disaster Recovery

Phải có runbook cho:

```text
Server lost
Database corrupted
Object storage unavailable
Bad deployment
Expired certificate
```

Recovery priority:

```text
1. Database
2. Authentication
3. Core API
4. Medication Schedule
5. Notification
6. Cabinet realtime
7. OCR / AI
```

---

## 57. RTO / RPO đề xuất

Pilot:

```text
RTO <= 4 giờ
RPO <= 24 giờ
```

Khi có WAL/PITR:

```text
RPO có thể giảm xuống vài phút
```

Mục tiêu production trưởng thành:

```text
RTO <= 1 giờ
```

---

## 58. Restore Test

Backup phải được test restore định kỳ.

Mỗi tháng:

```text
Restore backup
Verify database
Run migrations/check
Start test API
Verify sample records
```

---

## 59. Production Directory

```text
/opt/pharmamind/
├── compose.yaml
├── compose.production.yaml
├── nginx/
├── scripts/
├── logs/
└── backups/
```

Secrets:

```text
/etc/pharmamind/production.env
```

---

## 60. Docker Network

Ví dụ:

```text
public-network
backend-network
data-network
```

PostgreSQL chỉ ở private network.

---

## 61. Persistent Volumes

```text
postgres-data
redis-data (nếu cần persistence)
monitoring-data
```

Không lưu file upload production trong container filesystem tạm thời.

---

## 62. Production Compose skeleton

```yaml
services:

  nginx:
    image: nginx
    restart: unless-stopped

  api:
    image: pharmamind-api:${APP_VERSION}
    restart: unless-stopped
    env_file:
      - /etc/pharmamind/production.env

  worker-import:
    image: pharmamind-api:${APP_VERSION}
    command: run-import-worker
    restart: unless-stopped

  worker-notification:
    image: pharmamind-api:${APP_VERSION}
    command: run-notification-worker
    restart: unless-stopped

  redis:
    image: redis
    restart: unless-stopped

  postgres:
    image: postgres
    restart: unless-stopped
```

Production thật cần thêm:

```text
healthcheck
private networks
volumes
resource limits
logging
secrets
```

---

## 63. Mobile Production Config

```text
API_BASE_URL=https://api.pharmamind.vn
WS_BASE_URL=wss://api.pharmamind.vn
```

Không hardcode IP dev vào app production.

---

## 64. Graceful Degradation

Nếu AI lỗi:

```text
Medication / Schedule / Cabinet vẫn hoạt động
```

Nếu OCR lỗi:

```text
Manual Prescription Entry vẫn hoạt động
```

Nếu Digital Twin lỗi:

```text
Simple Cabinet Mode vẫn hoạt động
```

Nếu WebSocket lỗi:

```text
REST polling fallback
```

---

## 65. Failure Isolation

Các fallback chính:

```text
AI → core system vẫn chạy
3D → simple grid
OCR → manual entry
WebSocket → polling
Push → in-app schedule
```

Đây là yếu tố quan trọng để “không suy giảm chất lượng toàn hệ thống” khi một module phụ bị lỗi.

---

## 66. Go-live checklist

```text
Migration pass
Backup pass
Restore test pass
HTTPS pass
Firewall pass
Rate limit pass
Load test pass
Mobile staging test pass
WebSocket pass
OCR queue pass
Notification pass
Audit pass
Monitoring pass
Alerting pass
```

---

## 67. Go-live plan

```text
1. Provision server
2. Harden OS
3. Install Docker
4. Create private networks
5. Deploy PostgreSQL / Redis
6. Deploy Backend
7. Deploy Workers
8. Deploy Reverse Proxy + HTTPS
9. Deploy Monitoring
10. Configure Backup
11. Run Migration
12. Smoke Test
13. Load Test
14. Connect Mobile Production Build
15. Pilot with small user group
```

---

## 68. Pilot Strategy

Không mở ngay hàng nghìn user.

Bắt đầu:

```text
10–20 families
```

Theo dõi:

```text
latency
errors
OCR performance
notification reliability
cabinet realtime
DB growth
```

Sau đó tăng dần:

```text
50 families
100 families
500 families
```

---

## 69. Capacity Dashboard

Theo dõi:

```text
Total users
Daily active users
Concurrent API requests
WebSocket clients
OCR jobs/day
AI requests/day
DB size
Object storage size
Queue length
```

---

## 70. Khi nào cần tách khỏi một server?

Nếu xuất hiện:

```text
RAM thường xuyên > 80%
CPU thường xuyên > 75%
DB IO cao
OCR queue backlog
p95 latency tăng
AI làm API chậm
backup ảnh hưởng DB
```

thì bắt đầu tách service.

---

## 71. Scale Path

### Stage 1

```text
1 VPS
Docker Compose
```

### Stage 2

```text
1 App Server
Managed PostgreSQL
Object Storage
```

### Stage 3

```text
Load Balancer
2+ App Servers
Dedicated Workers
Managed Redis
Managed DB
```

### Stage 4

```text
Container Orchestrator / Kubernetes nếu thật sự cần
```

Không nên dùng Kubernetes ngay từ MVP nếu chưa có nhu cầu vận hành tương ứng.

---

## 72. Production kiến trúc khi scale

```text
                  Load Balancer
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
         App Node 1          App Node 2
             │                   │
             └─────────┬─────────┘
                       │
                 Managed Redis
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
 Managed PostgreSQL              Worker Cluster
       │                               │
       ▼                               ▼
 Object Storage                   OCR / AI / Notify
```

---

## 73. Khuyến nghị thực tế cho PharmaMind AI

Nếu hiện tại đang ở MVP:

> **Bắt đầu với VPS 8 vCPU / 16 GB RAM / NVMe, chạy Docker Compose production, nhưng tách API / PostgreSQL / Redis / OCR worker / notification worker thành container riêng.**

File đơn thuốc, ảnh, Excel, Digital Twin asset và backup nên lưu ở object storage ngoài VPS.

Khi bắt đầu có nhiều user thật:

> **Tách PostgreSQL ra managed database trước.**

Nếu OCR tăng tải:

> **Tách OCR worker sang server riêng.**

Nếu chạy AI local cần GPU:

> **Tách AI sang GPU server riêng.**

---

## 74. Roadmap deployment

```text
LOCAL DEVELOPMENT
      ↓
STAGING SERVER
      ↓
SINGLE VPS PRODUCTION
      ↓
MONITORING + BACKUP
      ↓
PILOT USERS
      ↓
LOAD TEST
      ↓
MANAGED DATABASE
      ↓
MULTI-NODE API
      ↓
DEDICATED WORKERS
      ↓
HIGH AVAILABILITY
```

---

## 75. Acceptance Criteria

Production deployment chỉ đạt khi:

- [ ] HTTPS hoạt động.
- [ ] FastAPI không public trực tiếp.
- [ ] PostgreSQL không public.
- [ ] Redis không public.
- [ ] OCR chạy background worker.
- [ ] Notification chạy background worker.
- [ ] AI không block core API.
- [ ] File upload nằm ngoài ephemeral container storage.
- [ ] Object storage được bảo vệ.
- [ ] Daily backup hoạt động.
- [ ] Có off-site backup.
- [ ] Restore test thành công.
- [ ] Monitoring hoạt động.
- [ ] Alerting hoạt động.
- [ ] Health checks hoạt động.
- [ ] WebSocket hoạt động qua WSS.
- [ ] Redis Pub/Sub hỗ trợ realtime khi scale.
- [ ] Migration pipeline hoạt động.
- [ ] CI/CD có staging.
- [ ] Application rollback hoạt động.
- [ ] Load test đạt target.
- [ ] Mobile production build kết nối production API.
- [ ] Cross-family authorization pass.
- [ ] Sensitive logs đã được loại bỏ.
- [ ] Pilot test thành công.

---

## 76. Definition of Done

Deployment production hoàn thành khi demo được:

```text
Mobile App
   ↓
HTTPS API
   ↓
Login
   ↓
Family / Member
   ↓
Medication / Prescription
   ↓
OCR Import queued
   ↓
App vẫn phản hồi bình thường
   ↓
Worker xử lý OCR
   ↓
Schedule updated
   ↓
Notification sent
   ↓
Cabinet realtime WebSocket
   ↓
Digital Twin updated
   ↓
AI query
```

và monitoring cho thấy:

```text
API latency ổn định
DB ổn định
Queue không backlog bất thường
Backup hoạt động
Không có lỗi bảo mật cơ bản
```

---

## 77. Deliverables

```text
docs/deployment/
├── PRODUCTION_SERVER_DEPLOYMENT_PLAN.md
├── SERVER_HARDENING.md
├── BACKUP_RESTORE.md
├── MONITORING_ALERTING.md
├── CI_CD.md
└── DISASTER_RECOVERY.md

deploy/
├── compose.yaml
├── compose.production.yaml
├── nginx/
│   └── nginx.conf
├── scripts/
│   ├── deploy.sh
│   ├── backup.sh
│   ├── restore.sh
│   └── healthcheck.sh
└── env/
    └── .env.production.example
```

---

## 78. Kết luận

> **Giải pháp phù hợp nhất với PharmaMind AI hiện tại là mô hình “single-server, multi-container, scale-ready”. Ban đầu tất cả service có thể chạy trên một VPS để tiết kiệm chi phí, nhưng API, PostgreSQL, Redis, OCR, notification và AI phải được tách workload ngay từ kiến trúc. Khi tải tăng, chỉ cần chuyển từng service sang server/managed service riêng mà không phải viết lại hệ thống.**

Nguyên tắc cốt lõi:

```text
Separate workloads
Async heavy jobs
One source of truth
Secure by default
Backup off-site
Monitor everything
Test restore
Scale by metrics
Graceful degradation
No rewrite when scaling
```
