# PharmaMind AI — FEATURE SPECIFICATION

# FEATURE — Personalized Prescription Import via OCR & Excel

## 1. Mục tiêu

Xây dựng tính năng cho phép **cập nhật đơn thuốc điện tử của từng thành viên gia đình bằng OCR hoặc Excel**, sau đó đồng bộ có kiểm soát vào:

- `FamilyMember`
- `HealthProfile`
- `MedicalCondition`
- `AllergyProfile`
- `DrugReactionHistory`
- `MedicationCatalog`
- `FamilyMedication`
- `Prescription`
- `PrescriptionItem`
- `MedicationSchedule`

Luồng tổng quát:

```text
Ảnh / PDF / Excel
        ↓
Import Session
        ↓
OCR / Excel Parser
        ↓
Normalize
        ↓
Validate
        ↓
Resolve Member + Medication
        ↓
Draft
        ↓
Review / Confirm
        ↓
Transaction Commit
        ↓
Database cá nhân hóa theo Member
```

Nguyên tắc quan trọng:

> **Không ghi trực tiếp dữ liệu OCR/Excel vào hồ sơ sức khỏe. Mọi dữ liệu phải đi qua staging, kiểm tra, preview và xác nhận trước khi commit.**

---

## 2. “Database riêng” cho từng thành viên

Không nên tạo một PostgreSQL database vật lý riêng cho từng người.

PharmaMind AI nên dùng:

```text
Một database hệ thống
+
Family scope
+
Member scope
+
Strict authorization
```

Mọi record cá nhân hóa phải có liên kết rõ:

```text
family_id
member_id
source_import_session_id
```

Ví dụ:

```text
FamilyMember #15
├── HealthProfile
├── MedicalConditions
├── Allergies
├── DrugReactions
├── Prescriptions
├── PrescriptionItems
├── MedicationSchedules
└── ImportHistory
```

Như vậy dữ liệu của mỗi thành viên vẫn độc lập và cá nhân hóa, nhưng dễ backup, migrate, audit và bảo trì.

---

## 3. Nguồn dữ liệu hỗ trợ

### OCR

```text
JPG
JPEG
PNG
PDF
```

Nguồn có thể là:

- ảnh chụp đơn thuốc;
- ảnh scan;
- PDF đơn thuốc;
- ảnh đơn thuốc điện tử.

### Excel

MVP ưu tiên:

```text
.xlsx
```

Có thể mở rộng sau:

```text
.xls
.csv
```

---

## 4. Import Session

Mỗi lần import phải tạo một `ImportSession`.

Model đề xuất:

```text
backend/app/models/import_session.py
```

Fields:

```text
id
family_id
member_id
created_by_user_id

source_type
source_filename
source_hash
source_storage_key

status

raw_payload
normalized_payload
validation_result

created_at
reviewed_at
committed_at
```

Status:

```text
UPLOADED
PROCESSING
REVIEW_REQUIRED
READY_TO_COMMIT
COMMITTED
FAILED
REJECTED
ROLLED_BACK
```

Flow:

```text
UPLOADED
   ↓
PROCESSING
   ↓
REVIEW_REQUIRED
   ↓
READY_TO_COMMIT
   ↓
COMMITTED
```

---

## 5. OCR Pipeline

```text
Upload Image / PDF
      ↓
Image Preprocessing
      ↓
OCR Text Extraction
      ↓
Layout / Field Parsing
      ↓
Medication Entity Extraction
      ↓
Prescription Structuring
      ↓
Normalization
      ↓
Validation
      ↓
Review
```

OCR cần cố gắng trích:

```text
Patient / Member Name
Prescription Date
Doctor Name
Facility Name

Medication Name
Active Ingredient
Strength
Dosage Form

Dose Amount
Dose Unit
Frequency
Route
Instructions

Start Date
End Date
Duration

Diagnosis / Condition
Allergy Note
Drug Reaction Note
Other Clinical Notes
```

---

## 6. OCR Confidence

Mỗi field nên có:

```text
value
confidence
source_position
```

Ví dụ:

```json
{
  "field": "medication_name",
  "value": "Amlodipine",
  "confidence": 0.94
}
```

Gợi ý mức hiển thị:

```text
>= 0.90      → High confidence
0.70–0.89    → Review recommended
< 0.70       → Review required
```

Confidence không phải căn cứ để tự commit.

---

## 7. Excel Template chuẩn

Tên đề xuất:

```text
PHARMAMIND_PRESCRIPTION_IMPORT_TEMPLATE.xlsx
```

Các cột:

```text
member_identifier
member_name

prescription_title
doctor_name
facility_name
issued_at
start_date
end_date

medication_name
active_ingredient
strength
dosage_form
manufacturer

dose_amount
dose_unit
frequency_per_day
frequency_text
route
instructions

schedule_times

quantity
inventory_unit
expiration_date

condition_name
allergy_note
drug_reaction_note

notes
```

`schedule_times` có thể dùng:

```text
08:00;20:00
```

---

## 8. Member Resolution

Ưu tiên xác định thành viên theo:

```text
1. Member đã được user chọn trước upload
2. member_identifier
3. Exact normalized member name
4. Manual confirmation
```

Nếu có ambiguity:

```text
Không tự chọn
```

Nếu tên trong đơn không khớp thành viên đang chọn:

```text
Blocking warning
```

Ví dụ UI:

> Tên người bệnh trong tài liệu không khớp với thành viên đang chọn. Vui lòng kiểm tra trước khi tiếp tục.

---

## 9. Medication Resolution

Sau parsing:

```text
Parsed Medication
      ↓
MedicationCatalog Match
      ↓
FamilyMedication Match
```

Matching dựa trên:

```text
name
active ingredient
strength
dosage form
manufacturer
```

Kết quả:

```text
MATCHED
NEW_MEDICATION
AMBIGUOUS
```

Nếu `AMBIGUOUS`:

```text
Bắt buộc user chọn
```

Nếu `NEW_MEDICATION`:

```text
Tạo MedicationCatalog draft
Tạo FamilyMedication draft
```

chỉ commit sau khi xác nhận.

---

## 10. Prescription Draft

Import tạo `Prescription Draft` gồm:

```text
Member
Doctor
Facility
Issued date
Start / End date
Medication items
Dose
Frequency
Route
Instructions
Health update candidates
```

Hỗ trợ 2 mode:

```text
CREATE_NEW
UPDATE_EXISTING
```

---

## 11. Cập nhật đơn hiện có

Nếu import dùng để cập nhật đơn hiện tại:

```text
Existing Prescription
      ↓
Compare Draft
      ↓
Show Diff
      ↓
User Confirm
      ↓
Apply Changes
```

Diff categories:

```text
ADDED
REMOVED
CHANGED
UNCHANGED
```

Ví dụ:

```text
Amlodipine
Dose:
OLD: 1 tablet/day
NEW: 2 tablets/day
```

Không được overwrite âm thầm.

---

## 12. Medication bị loại khỏi đơn mới

Nếu đơn mới không còn một thuốc cũ:

Không tự:

```text
DELETE Medication
```

Nên đề xuất:

```text
Complete / end old PrescriptionItem
Pause / complete related Schedule
```

và yêu cầu xác nhận.

---

## 13. Schedule Draft

Từ PrescriptionItem:

```text
dose
frequency
start_date
end_date
```

system tạo:

```text
MedicationSchedule Draft
```

Rule bắt buộc:

> Nếu đơn chỉ ghi “2 lần/ngày” nhưng không có giờ cụ thể thì **không tự suy đoán 08:00 và 20:00**.

UI phải yêu cầu:

```text
Vui lòng chọn giờ uống.
```

Nếu source có giờ cụ thể thì có thể tạo draft giờ đó để user review.

---

## 14. Cập nhật Health Profile

OCR / Excel có thể chứa:

```text
Diagnosis
Condition
Allergy
Drug reaction
Clinical note
```

Các dữ liệu này chỉ tạo candidate:

```text
NEW_CONDITION
UPDATE_CONDITION
NEW_ALLERGY
NEW_DRUG_REACTION
GENERAL_NOTE
```

Không commit nếu chưa review.

Đặc biệt:

```text
Drug reaction != confirmed allergy
```

Không tự chuyển phản ứng thuốc thành dị ứng xác nhận.

---

## 15. Provenance

Mọi dữ liệu được tạo/cập nhật từ import phải có khả năng truy vết:

```text
source_type
source_import_session_id
source_filename
source_record_index
source_confidence
verified_by_user_id
verified_at
```

Hệ thống phải trả lời được:

```text
Dữ liệu này đến từ file nào?
Ai import?
Ai xác nhận?
Khi nào?
OCR confidence bao nhiêu?
```

---

## 16. Raw Data + Normalized Data

Nên lưu cả:

```text
raw OCR text
raw Excel row
normalized data
validation issues
```

để audit/debug.

---

## 17. Duplicate Detection

Tạo:

```text
source_hash = SHA-256(file)
```

Nếu:

```text
same family
same member
same source_hash
```

thì cảnh báo:

> Tài liệu này đã được nhập trước đó.

Không tự tạo duplicate prescription.

---

## 18. Conflict Detection

Phải phát hiện ít nhất:

```text
Dose changed
Frequency changed
Medication added
Medication removed
Schedule changed
Existing active prescription conflict
Allergy / drug reaction warning
Expired medication
Member mismatch
```

Không tự merge nếu conflict quan trọng.

---

## 19. Health Conflict

Ví dụ database có:

```text
Penicillin allergy — SEVERE
```

file mới ghi:

```text
No known allergy
```

Không được xóa allergy cũ.

Phải đưa vào review.

---

## 20. Review Wizard

Khuyến nghị 5 bước:

```text
Step 1 — Chọn thành viên
Step 2 — Upload OCR / Excel
Step 3 — Kiểm tra dữ liệu đơn thuốc
Step 4 — Kiểm tra lịch uống & sức khỏe
Step 5 — Xác nhận cập nhật
```

---

## 21. Review UI

Mỗi field có thể hiển thị:

```text
Original
Parsed
Confidence
Validation status
Edit
```

Status:

```text
✓ Valid
⚠ Needs review
✕ Conflict / blocking
```

Không dựa vào màu duy nhất.

---

## 22. Preview trước commit

Ví dụ:

```text
Thành viên:
Bà Lan

Đơn thuốc:
Bệnh viện A — 02/11/2026

Thuốc:
1. Amlodipine 5 mg
   1 viên — 1 lần/ngày

2. Metformin 500 mg
   1 viên — 2 lần/ngày

Lịch cần xác nhận:
Amlodipine → chưa có giờ
Metformin → chưa có giờ

Thông tin sức khỏe:
+ Tăng huyết áp

Cảnh báo:
1 trường OCR confidence thấp
```

---

## 23. Commit Transaction

Commit phải chạy trong một transaction:

```text
Create / Update Prescription
        ↓
Create / Update PrescriptionItems
        ↓
Create / Link FamilyMedication
        ↓
Create / Update MedicationSchedule
        ↓
Apply confirmed Health Updates
        ↓
Create Audit records
        ↓
Commit
```

Nếu có lỗi:

```text
ROLLBACK toàn bộ
```

MVP không partial commit.

---

## 24. Import Entity Links

Nên tạo:

```text
import_entity_links
```

Fields:

```text
import_session_id
entity_type
entity_id
action
previous_snapshot
new_snapshot
```

Entity type:

```text
PRESCRIPTION
PRESCRIPTION_ITEM
FAMILY_MEDICATION
MEDICATION_SCHEDULE
MEDICAL_CONDITION
ALLERGY_PROFILE
DRUG_REACTION
```

Action:

```text
CREATE
UPDATE
ARCHIVE
COMPLETE
```

---

## 25. File Storage

Không nên lưu toàn bộ file nhị phân trực tiếp trong PostgreSQL ở MVP.

Nên lưu file trong:

```text
Private object/file storage
```

DB chỉ lưu metadata:

```text
storage_key
filename
mime_type
size
hash
```

Không dùng public URL.

---

## 26. Security

File đơn thuốc là dữ liệu sức khỏe nhạy cảm.

Cần:

```text
Authentication
Family authorization
Member scope
Protected file access
Audit
Retention policy
No sensitive logging
```

Role được import:

```text
OWNER
ADMIN
CAREGIVER
```

VIEWER:

```text
read only
```

---

## 27. Backend structure

```text
backend/app/modules/imports/
├── router.py
├── service.py
├── repository.py
├── schema.py
├── enums.py
├── exceptions.py
│
├── adapters/
│   ├── base.py
│   ├── ocr_adapter.py
│   └── excel_adapter.py
│
├── parsers/
│   ├── prescription_parser.py
│   ├── medication_parser.py
│   ├── schedule_parser.py
│   └── health_parser.py
│
├── normalizers/
│   ├── medication_normalizer.py
│   ├── date_normalizer.py
│   ├── dosage_normalizer.py
│   └── member_normalizer.py
│
├── validators/
│   ├── prescription_validator.py
│   ├── medication_validator.py
│   ├── schedule_validator.py
│   └── health_validator.py
│
├── resolvers/
│   ├── member_resolver.py
│   ├── medication_resolver.py
│   └── prescription_resolver.py
│
└── commit/
    └── import_commit_service.py
```

Models:

```text
backend/app/models/
├── import_session.py
├── import_item.py
├── import_validation_issue.py
└── import_entity_link.py
```

---

## 28. API đề xuất

### Upload

```http
POST /families/{family_id}/members/{member_id}/imports
```

Multipart:

```text
file
source_type
```

### Get review

```http
GET /families/{family_id}/members/{member_id}/imports/{import_id}
```

### Edit draft

```http
PATCH /families/{family_id}/members/{member_id}/imports/{import_id}/draft
```

### Validate lại

```http
POST /families/{family_id}/members/{member_id}/imports/{import_id}/validate
```

### Commit

```http
POST /families/{family_id}/members/{member_id}/imports/{import_id}/commit
```

### Reject

```http
POST /families/{family_id}/members/{member_id}/imports/{import_id}/reject
```

### Import history

```http
GET /families/{family_id}/members/{member_id}/imports
```

### Download Excel template

```http
GET /imports/templates/prescription.xlsx
```

---

## 29. Frontend structure

```text
frontend/src/features/importPrescription/
├── api.ts
├── types.ts
├── hooks.ts
├── validation.ts
├── mapping.ts
└── store.ts

frontend/src/pages/import-prescription/
├── ImportPrescriptionPage.tsx
├── MemberStep.tsx
├── UploadStep.tsx
├── ReviewStep.tsx
├── ScheduleStep.tsx
├── HealthUpdateStep.tsx
└── ConfirmStep.tsx
```

Components:

```text
ImportSummaryCard
OCRConfidenceBadge
FieldReviewRow
MedicationMatchCard
PrescriptionDiffCard
SchedulePreview
HealthUpdatePreview
ConflictAlert
CommitSummary
```

---

## 30. Đồng bộ với hệ thống sau commit

Sau commit frontend phải refresh/invalidate:

```text
Member Detail
Health Profile
Medications
Prescriptions
Schedules
Dashboard
Next Dose
Cabinet
Digital Twin
```

Nếu imported medication chưa có ngăn:

```text
Thuốc này chưa được gán vào tủ.
[ Gán ngăn ]
```

Nếu medication đã ở cabinet và schedule đổi:

```text
Next Dose
Digital Twin Highlight
Drawer Reveal Info
```

phải cập nhật theo.

---

## 31. Safety Rules

OCR/AI chỉ được:

```text
extract
normalize
suggest mapping
detect conflict
```

Không được:

```text
chẩn đoán
kê đơn
đổi liều
ngừng thuốc
thêm thuốc không có nguồn
xóa medication dựa trên suy luận
```

---

## 32. Test scenarios

### OCR Happy Path

```text
Upload image
Parse
Review
Confirm
Commit
Prescription + Schedule updated
```

### Low Confidence

```text
confidence thấp
→ review required
```

### Wrong Member

```text
member mismatch
→ blocking warning
```

### Excel Valid

```text
Upload template
Parse rows
Preview
Commit
```

### Missing Required Column

```text
validation error
```

### Duplicate File

```text
same source_hash
→ duplicate warning
```

### Existing Prescription Update

```text
dose changed
→ diff shown
→ user confirms
→ update
```

### Health Update

```text
condition extracted
→ candidate
→ confirm
→ HealthProfile updated
```

### Transaction Failure

```text
schedule creation fails
→ rollback prescription
→ rollback medication changes
→ rollback health updates
```

---

## 33. Acceptance Criteria

- [ ] OCR image import hoạt động.
- [ ] OCR/PDF pipeline được chuẩn bị rõ ràng.
- [ ] Excel `.xlsx` template import hoạt động.
- [ ] Import gắn đúng `family_id` và `member_id`.
- [ ] Có `ImportSession`.
- [ ] Có raw + normalized payload.
- [ ] Có SHA-256 source hash.
- [ ] Duplicate import được cảnh báo.
- [ ] OCR confidence được lưu.
- [ ] Low-confidence field được highlight.
- [ ] Medication matching hoạt động.
- [ ] Ambiguous match bắt buộc review.
- [ ] Có Prescription Draft.
- [ ] Có diff khi update existing prescription.
- [ ] Có Schedule Draft.
- [ ] Không tự suy đoán giờ uống nếu source không có.
- [ ] Health information chỉ là candidate trước review.
- [ ] Có conflict detection.
- [ ] Có preview trước commit.
- [ ] User phải xác nhận trước commit.
- [ ] Commit chạy transaction.
- [ ] Không partial commit trong MVP.
- [ ] Có provenance.
- [ ] Có audit trail.
- [ ] Có import history.
- [ ] Cross-family access bị chặn.
- [ ] VIEWER không được import.
- [ ] Commit cập nhật đúng Prescription.
- [ ] Commit cập nhật đúng MedicationSchedule.
- [ ] Commit cập nhật đúng HealthProfile.
- [ ] Frontend refresh đúng dữ liệu sau commit.
- [ ] Tests pass.

---

## 34. Definition of Done

Feature hoàn thành khi demo được:

```text
Login
 ↓
Select Family
 ↓
Select Member
 ↓
Upload Prescription Image / Excel
 ↓
Parse
 ↓
Review
 ↓
Resolve Medication
 ↓
Preview Prescription Changes
 ↓
Confirm Schedule
 ↓
Confirm Health Updates
 ↓
Commit
 ↓
Member Data Updated
 ↓
Prescription Updated
 ↓
Schedule Updated
 ↓
Health Profile Updated
 ↓
Dashboard / Next Dose / Cabinet / Digital Twin Updated
```

---

## 35. Deliverables

```text
docs/features/
└── FEATURE_PERSONALIZED_PRESCRIPTION_IMPORT_OCR_EXCEL.md

backend/app/models/
├── import_session.py
├── import_item.py
├── import_validation_issue.py
└── import_entity_link.py

backend/app/modules/imports/
├── router.py
├── service.py
├── repository.py
├── schema.py
├── enums.py
├── exceptions.py
├── adapters/
├── parsers/
├── normalizers/
├── validators/
├── resolvers/
└── commit/

frontend/src/features/importPrescription/
├── api.ts
├── types.ts
├── hooks.ts
├── validation.ts
├── mapping.ts
└── store.ts

frontend/src/pages/import-prescription/
├── ImportPrescriptionPage.tsx
├── MemberStep.tsx
├── UploadStep.tsx
├── ReviewStep.tsx
├── ScheduleStep.tsx
├── HealthUpdateStep.tsx
└── ConfirmStep.tsx
```

---

## 36. Kết luận

> **OCR + Excel trong PharmaMind AI phải là một pipeline nhập dữ liệu có kiểm soát, không phải “đọc file rồi ghi thẳng database”. Quy trình chuẩn là: parse → normalize → validate → review → confirm → commit.**

Nguyên tắc cốt lõi:

```text
Import to staging first
Human confirmation before commit
Member-specific data isolation
No silent overwrite
Full provenance
Safety before automation
```
