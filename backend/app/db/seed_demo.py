"""Demo data seeder for community public trial.

Provides an automated, rich initial dataset:
- Demo User: demo@pharmamind.vn / DemoPass123!
- Family: Gia đình Kiểu mẫu PharmaMind
- 3 Family Members with realistic HealthProfiles, medical conditions, and allergies
- 1 Smart Cabinet (PM-CAB-DEMO-01) with 9 compartments fully configured
- 9 Family Medications mapped to the 9 compartments
- Active Prescriptions and Medication Schedules with daily times (08:00, 20:00)
- Allergy warning trigger: Amoxicillin in compartment 4 vs Penicillin/Amoxicillin allergy of Member 1

Run standalone:
    python -m backend.app.db.seed_demo
"""

import logging
import sys
from datetime import date, datetime, time, timezone
from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password, normalize_email
from backend.app.db.session import SessionLocal
from backend.app.models.allergy_profile import AllergyProfile
from backend.app.models.cabinet import Cabinet
from backend.app.models.compartment import Compartment
from backend.app.models.family import Family
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.family_member import FamilyMember
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.health_profile import HealthProfile
from backend.app.models.import_session import ImportSession
from backend.app.models.medical_condition import MedicalCondition
from backend.app.models.medication_catalog import MedicationCatalog
from backend.app.models.medication_schedule import MedicationSchedule
from backend.app.models.member_medication import MemberMedication
from backend.app.models.prescription import Prescription
from backend.app.models.prescription_item import PrescriptionItem
from backend.app.models.schedule_time import ScheduleTime
from backend.app.models.user import User, UserStatus
from backend.app.modules.medications.enums import MedicationSource, MedicationStatus
from backend.app.modules.imports.file_storage import PrescriptionFileStorage
from backend.app.modules.prescriptions.enums import PrescriptionStatus
from backend.app.shared.enums import AllergyType, ConditionStatus, FamilyRole, FamilyStatus, MemberStatus, Severity

DEMO_EMAIL = "demo@pharmamind.vn"
DEMO_PASSWORD = "DemoPass123!"
DEMO_NAME = "Nguyễn Minh An (Demo)"
logger = logging.getLogger(__name__)


def _clear_demo_ecosystem(db: Session, user: User) -> list[str]:
    """Remove demo-owned data while preserving the login identity and other users' data."""
    owned_family_ids = list(
        db.scalars(
            select(FamilyMembership.family_id).where(
                FamilyMembership.user_id == user.id,
                FamilyMembership.role == FamilyRole.OWNER.value,
            )
        ).all()
    )

    # A family is safe to delete only while the demo account is its sole owner.
    # If ownership was shared with a registered user, only detach the demo account.
    deletable_family_ids: list[int] = []
    for family_id in owned_family_ids:
        other_owner = db.scalars(
            select(FamilyMembership.id)
            .where(
                FamilyMembership.family_id == family_id,
                FamilyMembership.user_id != user.id,
                FamilyMembership.role == FamilyRole.OWNER.value,
            )
            .limit(1)
        ).first()
        if other_owner is None:
            deletable_family_ids.append(family_id)

    storage_paths: list[str] = []
    catalog_ids: list[int] = []
    if deletable_family_ids:
        storage_paths = [
            path
            for path in db.scalars(
                select(ImportSession.storage_path).where(
                    ImportSession.family_id.in_(deletable_family_ids),
                    ImportSession.storage_path.is_not(None),
                )
            ).all()
            if path
        ]
        catalog_ids = list(
            db.scalars(
                select(FamilyMedication.catalog_id).where(
                    FamilyMedication.family_id.in_(deletable_family_ids),
                    FamilyMedication.catalog_id.is_not(None),
                )
            ).all()
        )
        # These two tables also point at family_medications with RESTRICT.
        # Delete them first so PostgreSQL does not depend on cascade order.
        db.execute(
            delete(MedicationSchedule).where(
                MedicationSchedule.family_id.in_(deletable_family_ids)
            )
        )
        db.execute(
            delete(Prescription).where(Prescription.family_id.in_(deletable_family_ids))
        )
        db.execute(delete(Family).where(Family.id.in_(deletable_family_ids)))
        if catalog_ids:
            db.execute(
                delete(MedicationCatalog).where(
                    MedicationCatalog.id.in_(catalog_ids),
                    ~exists(
                        select(FamilyMedication.id).where(
                            FamilyMedication.catalog_id == MedicationCatalog.id
                        )
                    ),
                )
            )

    # Remove memberships from families that are retained because another owner
    # exists, plus any non-owner memberships the shared demo account acquired.
    db.execute(delete(FamilyMembership).where(FamilyMembership.user_id == user.id))
    db.flush()
    return storage_paths


def _delete_demo_uploads(storage_paths: list[str]) -> None:
    storage = PrescriptionFileStorage()
    for path in storage_paths:
        try:
            storage.delete(path)
        except Exception:
            # The database reset is already committed. A missing/unavailable
            # object must not prevent visitors from using the demo account.
            logger.exception("Could not remove demo upload %s", path)


def reset_demo_account(db: Session, user: User) -> None:
    """Return the shared demo login to a brand-new, completely empty account."""
    storage_paths = _clear_demo_ecosystem(db, user)
    user.password_hash = hash_password(DEMO_PASSWORD)
    user.full_name = DEMO_NAME
    user.status = UserStatus.ACTIVE.value
    user.is_email_verified = False
    db.commit()
    _delete_demo_uploads(storage_paths)


def seed_demo_data(
    db: Session,
    force_reset: bool = False,
    *,
    quiet: bool = False,
) -> None:
    norm_email = normalize_email(DEMO_EMAIL)
    existing_user = db.scalars(select(User).where(User.email == norm_email)).first()

    if existing_user is not None and not force_reset:
        if not quiet:
            print(f"[Seed] Demo user '{norm_email}' already exists. Skipping seed.")
        return

    storage_paths: list[str] = []
    if existing_user is not None and force_reset:
        if not quiet:
            print(f"[Seed] Force reset: clearing demo data for '{norm_email}'...")
        storage_paths = _clear_demo_ecosystem(db, existing_user)
        user = existing_user
        user.password_hash = hash_password(DEMO_PASSWORD)
        user.full_name = DEMO_NAME
        user.status = UserStatus.ACTIVE.value
        user.is_email_verified = False
    else:
        # 1. User
        user = User(
            email=norm_email,
            password_hash=hash_password(DEMO_PASSWORD),
            full_name=DEMO_NAME,
            status=UserStatus.ACTIVE.value,
        )
        db.add(user)
        db.flush()

    if not quiet:
        print("[Seed] Creating demo account & sample health ecosystem...")

    # 2. Family
    family = Family(
        name="Gia đình Kiểu mẫu PharmaMind",
        description="Không gian thử nghiệm và mô phỏng hệ sinh thái PharmaMind AI cho cộng đồng",
        status=FamilyStatus.ACTIVE.value,
    )
    db.add(family)
    db.flush()

    # 3. Membership
    membership = FamilyMembership(
        family_id=family.id,
        user_id=user.id,
        role=FamilyRole.OWNER.value,
    )
    db.add(membership)
    db.flush()

    # 4. Members & Health Profiles
    # Member 1: Nguyễn Minh An (Bố)
    member_an = FamilyMember(
        family_id=family.id,
        full_name="Nguyễn Minh An",
        relationship_label="Bố / Trưởng gia đình",
        date_of_birth=date(1982, 5, 15),
        gender="MALE",
        status=MemberStatus.ACTIVE.value,
    )
    db.add(member_an)
    db.flush()

    hp_an = HealthProfile(
        member_id=member_an.id,
        blood_type="O+",
        height_cm=172.0,
        weight_kg=68.5,
        general_notes="Thể trạng tốt, tiền sử huyết áp dao động nhẹ, cần nhắc uống thuốc đúng giờ.",
    )
    db.add(hp_an)

    cond_an = MedicalCondition(
        member_id=member_an.id,
        name="Tăng huyết áp vô căn",
        diagnosed_at=date(2023, 3, 10),
        status=ConditionStatus.ACTIVE.value,
        notes="Theo dõi huyết áp định kỳ mỗi sáng",
    )
    db.add(cond_an)

    allergy_an = AllergyProfile(
        member_id=member_an.id,
        allergen="Amoxicillin",
        allergy_type=AllergyType.DRUG.value,
        severity=Severity.SEVERE.value,
        reaction_description="Phù Quincke, nổi mề đay toàn thân và khó thở cấp tính khi dùng kháng sinh nhóm Penicillin/Amoxicillin",
        recorded_at=date(2020, 1, 15),
        source="Bệnh viện Chợ Rẫy",
        notes="CHỐNG CHỈ ĐỊNH TUYỆT ĐỐI kháng sinh nhóm beta-lactam",
    )
    db.add(allergy_an)

    # Member 2: Trần Thị Lan (Mẹ)
    member_lan = FamilyMember(
        family_id=family.id,
        full_name="Trần Thị Lan",
        relationship_label="Mẹ",
        date_of_birth=date(1985, 8, 20),
        gender="FEMALE",
        status=MemberStatus.ACTIVE.value,
    )
    db.add(member_lan)
    db.flush()

    hp_lan = HealthProfile(
        member_id=member_lan.id,
        blood_type="A+",
        height_cm=160.0,
        weight_kg=52.0,
        general_notes="Sức khỏe ổn định, thường bổ sung vitamin và khoáng chất định kỳ.",
    )
    db.add(hp_lan)

    cond_lan = MedicalCondition(
        member_id=member_lan.id,
        name="Viêm mũi dị ứng theo mùa",
        diagnosed_at=date(2022, 10, 5),
        status=ConditionStatus.ACTIVE.value,
    )
    db.add(cond_lan)

    # Member 3: Nguyễn Tuấn Kiệt (Con trai)
    member_kiet = FamilyMember(
        family_id=family.id,
        full_name="Nguyễn Tuấn Kiệt",
        relationship_label="Con trai",
        date_of_birth=date(2015, 11, 2),
        gender="MALE",
        status=MemberStatus.ACTIVE.value,
    )
    db.add(member_kiet)
    db.flush()

    hp_kiet = HealthProfile(
        member_id=member_kiet.id,
        blood_type="O+",
        height_cm=140.0,
        weight_kg=35.0,
        general_notes="Trẻ phát triển bình thường, chưa ghi nhận dị ứng.",
    )
    db.add(hp_kiet)
    db.flush()

    # 5. Smart Cabinet
    cabinet = Cabinet(
        family_id=family.id,
        name="Tủ thuốc thông minh phòng khách",
        device_code="PM-CAB-DEMO-01",
        status="ONLINE",
        hardware_mode="SIMULATED",
        notes="Tủ thuốc 9 ngăn Digital Twin 3D đang kết nối bộ giả lập phần kéo mở ngăn thời gian thực.",
        last_seen_at=datetime.now(timezone.utc),
    )
    db.add(cabinet)
    db.flush()

    # 6. Catalog Medications (9 items for 9 compartments)
    med_specs = [
        # (pos, name, active_ingredient, strength, form, qty, unit, exp_date, threshold, note)
        (1, "Paracetamol 500mg", "Paracetamol", "500mg", "TABLET", 18.0, "tablet", date(2028, 12, 31), 5.0, "Hạ sốt, giảm đau nhanh sau ăn"),
        (2, "Vitamin C 500mg", "Ascorbic Acid", "500mg", "TABLET", 24.0, "tablet", date(2028, 6, 30), 6.0, "Tăng sức đề kháng, uống buổi sáng"),
        (3, "Oresol 245mg", "Glucose & Điện giải", "245mg", "POWDER", 10.0, "unit", date(2027, 9, 30), 3.0, "Bù nước và điện giải khi sốt hoặc tiêu chảy"),
        (4, "Amoxicillin 500mg", "Amoxicillin Trihydrate", "500mg", "CAPSULE", 12.0, "capsule", date(2028, 8, 31), 4.0, "Kháng sinh (Cảnh báo dị ứng với bố Nguyễn Minh An)"),
        (5, "Men vi sinh Enterogermina", "Bacillus clausii", "2 tỷ bào tử/5ml", "SYRUP", 10.0, "unit", date(2027, 11, 30), 2.0, "Hỗ trợ tiêu hóa"),
        (6, "Băng gạc y tế tiệt trùng", "Gạc Cotton", "Gói 10 miếng", "OTHER", 5.0, "unit", date(2029, 1, 1), 2.0, "Sơ cứu vết thương ngoài da"),
        (7, "Cồn sát trùng 70 độ", "Ethanol 70%", "Chai 100ml", "OTHER", 2.0, "unit", date(2028, 5, 20), 1.0, "Sát khuẩn vết thương ngoài da"),
        (8, "Nước muối sinh lý 0.9%", "Natri Clorid 0.9%", "Lọ 10ml", "DROPS", 6.0, "unit", date(2028, 3, 15), 2.0, "Nhỏ mắt, nhỏ mũi khi bụi bẩn"),
        (9, "Siro hạ sốt Hapacol 250mg", "Paracetamol", "250mg/gói", "SYRUP", 8.0, "unit", date(2028, 1, 10), 2.0, "Hạ sốt trẻ em dành cho Tuấn Kiệt"),
    ]

    fam_med_by_pos: dict[int, FamilyMedication] = {}

    for pos, name, active_ing, strength, form, qty, unit, exp_date, threshold, note in med_specs:
        cat = MedicationCatalog(
            name=name,
            active_ingredient=active_ing,
            strength=strength,
            dosage_form=form,
            source=MedicationSource.SEEDED.value,
            description=note,
        )
        db.add(cat)
        db.flush()

        fm = FamilyMedication(
            family_id=family.id,
            catalog_id=cat.id,
            quantity=qty,
            unit=unit,
            expiration_date=exp_date,
            low_stock_threshold=threshold,
            status=MedicationStatus.ACTIVE.value,
            notes=note,
        )
        db.add(fm)
        db.flush()
        fam_med_by_pos[pos] = fm

    # Link medications to members
    # An uses Paracetamol, Vitamin C
    db.add(MemberMedication(member_id=member_an.id, family_medication_id=fam_med_by_pos[1].id))
    db.add(MemberMedication(member_id=member_an.id, family_medication_id=fam_med_by_pos[2].id))
    # Lan uses Paracetamol, Vitamin C, Oresol
    db.add(MemberMedication(member_id=member_lan.id, family_medication_id=fam_med_by_pos[1].id))
    db.add(MemberMedication(member_id=member_lan.id, family_medication_id=fam_med_by_pos[2].id))
    db.add(MemberMedication(member_id=member_lan.id, family_medication_id=fam_med_by_pos[3].id))
    # Kiet uses Siro Hapacol, Men vi sinh
    db.add(MemberMedication(member_id=member_kiet.id, family_medication_id=fam_med_by_pos[9].id))
    db.add(MemberMedication(member_id=member_kiet.id, family_medication_id=fam_med_by_pos[5].id))
    db.flush()

    # 7. 9 Compartments assigned
    for pos in range(1, 10):
        fm = fam_med_by_pos.get(pos)
        comp = Compartment(
            cabinet_id=cabinet.id,
            position=pos,
            label=f"Ngăn {pos:02d}",
            family_medication_id=fm.id if fm else None,
            status="OCCUPIED" if fm else "EMPTY",
            is_open=False,
        )
        db.add(comp)
    db.flush()

    # 8. Prescription for Nguyễn Minh An
    rx_an = Prescription(
        family_id=family.id,
        member_id=member_an.id,
        title="Đơn thuốc điều trị tăng huyết áp & dự phòng cảm sốt",
        doctor_name="BS.CKII Trần Quốc Hùng",
        facility_name="Bệnh viện Đa khoa Quốc tế",
        issued_at=date(2026, 11, 1),
        start_date=date(2026, 11, 1),
        end_date=date(2027, 11, 1),
        status=PrescriptionStatus.ACTIVE.value,
        notes="Uống đều đặn đúng giờ mỗi ngày. Tái khám sau 6 tháng.",
    )
    db.add(rx_an)
    db.flush()

    # Prescription items
    rx_item_1 = PrescriptionItem(
        prescription_id=rx_an.id,
        family_medication_id=fam_med_by_pos[1].id,  # Paracetamol
        dose_amount=1.0,
        dose_unit="tablet",
        frequency_per_day=2.0,
        frequency_text="2 lần/ngày sáng và tối sau ăn",
        route="ORAL",
        instructions="Uống sau ăn sáng (08:00) và sau ăn tối (20:00)",
    )
    db.add(rx_item_1)

    rx_item_2 = PrescriptionItem(
        prescription_id=rx_an.id,
        family_medication_id=fam_med_by_pos[2].id,  # Vitamin C
        dose_amount=1.0,
        dose_unit="tablet",
        frequency_per_day=1.0,
        frequency_text="1 lần/ngày buổi sáng sau ăn",
        route="ORAL",
        instructions="Uống sau ăn sáng (08:00) để hấp thu tối ưu",
    )
    db.add(rx_item_2)
    db.flush()

    # 9. Medication Schedules
    # Schedule for Paracetamol (08:00, 20:00)
    sched_1 = MedicationSchedule(
        family_id=family.id,
        member_id=member_an.id,
        prescription_item_id=rx_item_1.id,
        family_medication_id=fam_med_by_pos[1].id,
        recurrence_type="DAILY",
        start_date=date(2026, 11, 1),
        end_date=date(2027, 11, 1),
        reminder_enabled=True,
        reminder_before_minutes=15,
        grace_period_minutes=30,
        status="ACTIVE",
        notes="Nhắc nhở qua chuông tủ thuốc và ứng dụng",
    )
    db.add(sched_1)
    db.flush()
    db.add(ScheduleTime(schedule_id=sched_1.id, time_of_day=time(8, 0)))
    db.add(ScheduleTime(schedule_id=sched_1.id, time_of_day=time(20, 0)))

    # Schedule for Vitamin C (08:00)
    sched_2 = MedicationSchedule(
        family_id=family.id,
        member_id=member_an.id,
        prescription_item_id=rx_item_2.id,
        family_medication_id=fam_med_by_pos[2].id,
        recurrence_type="DAILY",
        start_date=date(2026, 11, 1),
        end_date=date(2027, 11, 1),
        reminder_enabled=True,
        reminder_before_minutes=15,
        grace_period_minutes=30,
        status="ACTIVE",
        notes="Nhắc nhở uống buổi sáng",
    )
    db.add(sched_2)
    db.flush()
    db.add(ScheduleTime(schedule_id=sched_2.id, time_of_day=time(8, 0)))

    db.commit()
    _delete_demo_uploads(storage_paths)
    if not quiet:
        print("[Seed] Successfully seeded demo ecosystem for PharmaMind AI!")
        print(f"       Account : {DEMO_EMAIL}")
        print(f"       Password: {DEMO_PASSWORD}")
        try:
            print(f"       Family  : {family.name}")
            print(f"       Cabinet : {cabinet.name} (9/9 compartments mapped)")
        except UnicodeEncodeError:
            print(f"       Family ID : {family.id}")
            print(f"       Cabinet ID: {cabinet.id}")


if __name__ == "__main__":
    force = "--reset" in sys.argv
    with SessionLocal() as session:
        seed_demo_data(session, force_reset=force)
