import json
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models.allergy_profile import AllergyProfile
from backend.app.models.drug_reaction_history import DrugReactionHistory
from backend.app.models.family import Family
from backend.app.models.import_entity_link import ImportEntityLink
from backend.app.models.import_session import ImportSession
from backend.app.models.medical_condition import MedicalCondition
from backend.app.models.medication_catalog import MedicationCatalog
from backend.app.models.medication_schedule import MedicationSchedule
from backend.app.models.prescription import Prescription
from backend.app.models.user import User
from backend.app.modules.imports.adapters.excel_adapter import (
    TEMPLATE_COLUMNS,
    build_xlsx_bytes,
)

client = TestClient(app)


def _create_user_and_token(label: str) -> tuple[int, str, str]:
    email = f"{label}_{uuid4().hex[:10]}@example.com"
    password = "StrongPass123"
    reg = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"User {label}",
        },
    )
    assert reg.status_code == 201
    login = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return reg.json()["id"], email, login.json()["access_token"]


def _cleanup(user_ids: list[int], family_ids: list[int]) -> None:
    with SessionLocal() as session:
        if family_ids:
            session.execute(
                delete(ImportSession).where(ImportSession.family_id.in_(family_ids))
            )
            session.execute(
                delete(MedicationSchedule).where(
                    MedicationSchedule.family_id.in_(family_ids)
                )
            )
            session.execute(
                delete(Prescription).where(Prescription.family_id.in_(family_ids))
            )
            session.execute(delete(Family).where(Family.id.in_(family_ids)))
        session.execute(
            delete(MedicationCatalog).where(
                MedicationCatalog.source.in_(["OCR_IMPORT", "EXCEL_IMPORT"])
            )
        )
        if user_ids:
            session.execute(delete(User).where(User.id.in_(user_ids)))
        session.commit()


def test_prescription_import_ocr_excel_scenarios():
    """Verify all 9 scenarios in FEATURE_PERSONALIZED_PRESCRIPTION_IMPORT_OCR_EXCEL.md §32-33."""
    owner_id, _, owner_token = _create_user_and_token("imp_owner")
    viewer_id, viewer_email, viewer_token = _create_user_and_token("imp_viewer")
    other_id, _, other_token = _create_user_and_token("imp_other")
    family_ids: list[int] = []

    try:
        fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"name": "Gia đình Nhập Đơn Thuốc"},
        ).json()["id"]
        family_ids.append(fam_id)

        other_fam_id = client.post(
            "/families",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"name": "Gia đình Khác"},
        ).json()["id"]
        family_ids.append(other_fam_id)

        # Add VIEWER user to fam_id
        client.post(
            f"/families/{fam_id}/memberships",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"email": viewer_email, "role": "VIEWER"},
        )

        # Create Member A: Nguyễn Minh An
        member_an = client.post(
            f"/families/{fam_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"full_name": "Nguyễn Minh An", "relationship_label": "Con trai"},
        ).json()["id"]

        # ------------------------------------------------------------------
        # Scenario 4a: Download standard Excel template
        # ------------------------------------------------------------------
        tpl_res = client.get(
            "/imports/templates/prescription.xlsx",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert tpl_res.status_code == 200
        assert (
            "PHARMAMIND_PRESCRIPTION_IMPORT_TEMPLATE.xlsx"
            in tpl_res.headers.get("content-disposition", "")
        )
        assert len(tpl_res.content) > 500

        # ------------------------------------------------------------------
        # Scenario 1 & 2: OCR Upload with Low Confidence + Missing Schedule Time (Non-Guessing §13)
        # ------------------------------------------------------------------
        ocr_payload = {
            "overall_confidence": 0.65,
            "prescription_meta": {
                "member_name": "Nguyễn Minh An",
                "prescription_title": "Đơn thuốc viêm phế quản",
                "doctor_name": "BS. Lê Hoàng Nam",
                "facility_name": "Bệnh viện Nhi Đồng",
                "issued_at": "2026-11-01",
                "start_date": "2026-11-01",
                "end_date": "2026-11-05",
            },
            "medications": [
                {
                    "medication_name": f"Cefuroxim_{uuid4().hex[:4]} 250mg",
                    "active_ingredient": "Cefuroxime",
                    "strength": "250mg",
                    "dosage_form": "TABLET",
                    "dose_amount": 1.0,
                    "dose_unit": "tablet",
                    "frequency_per_day": 2.0,
                    "frequency_text": "Ngày uống 2 lần sáng, tối",
                    # Note: No explicit schedule_times -> must emit MISSING_SCHEDULE_TIMES and NOT guess 08:00/20:00!
                    "route": "ORAL",
                    "instructions": "Uống sau ăn sáng và tối",
                    "quantity": 10.0,
                    "unit": "tablet",
                    "confidence": 0.64,
                }
            ],
        }
        ocr_res = client.post(
            f"/families/{fam_id}/members/{member_an}/imports",
            headers={"Authorization": f"Bearer {owner_token}"},
            files={
                "file": (
                    "don_thuoc_blur.png",
                    json.dumps(ocr_payload).encode("utf-8"),
                    "image/png",
                )
            },
            data={"source_type": "OCR_IMAGE"},
        )
        assert ocr_res.status_code == 201
        ocr_session = ocr_res.json()
        ocr_import_id = ocr_session["id"]
        assert ocr_session["status"] == "REVIEW_REQUIRED"

        issue_codes = {iss["code"] for iss in ocr_session["validation_issues"]}
        assert "MISSING_SCHEDULE_TIMES" in issue_codes
        assert "LOW_OCR_CONFIDENCE_MEDICATION" in issue_codes

        # Attempting to commit before selecting schedule_times must fail (409)
        blocked_commit = client.post(
            f"/families/{fam_id}/members/{member_an}/imports/{ocr_import_id}/commit",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "confirm_member_id": member_an,
                "confirm_import_mode": "CREATE_NEW_PRESCRIPTION",
                "confirm_schedule_creation": True,
                "confirm_health_updates": False,
            },
        )
        assert blocked_commit.status_code == 409

        # Patch draft to provide explicit schedule_times ["07:30", "19:30"]
        patch_res = client.patch(
            f"/families/{fam_id}/members/{member_an}/imports/{ocr_import_id}/draft",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "items": [
                    {
                        "row_index": 0,
                        "schedule_times": ["07:30", "19:30"],
                        "create_schedule": True,
                    }
                ]
            },
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "READY_TO_COMMIT"

        # Commit OCR session
        commit_ocr = client.post(
            f"/families/{fam_id}/members/{member_an}/imports/{ocr_import_id}/commit",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "confirm_member_id": member_an,
                "confirm_import_mode": "CREATE_NEW_PRESCRIPTION",
                "confirm_schedule_creation": True,
                "confirm_health_updates": False,
            },
        )
        assert commit_ocr.status_code == 200
        committed_data = commit_ocr.json()
        assert committed_data["status"] == "COMMITTED"
        assert committed_data["commit_summary"]["prescriptions_created"] == 1
        assert committed_data["commit_summary"]["prescription_items_created"] == 1
        assert committed_data["commit_summary"]["schedules_created"] == 1
        assert len(committed_data["entity_links"]) >= 5
        first_prescription_id = committed_data["commit_summary"]["prescription_id"]

        # ------------------------------------------------------------------
        # Scenario 3: Wrong Member in Document (Blocking Warning)
        # ------------------------------------------------------------------
        wrong_member_ocr = {
            "overall_confidence": 0.95,
            "prescription_meta": {
                "member_name": "Trần Thị Bích Ngọc",
                "prescription_title": "Đơn thuốc của người khác",
                "issued_at": "2026-11-01",
            },
            "medications": [
                {
                    "medication_name": "Ibuprofen 400mg",
                    "dose_amount": 1.0,
                    "dose_unit": "tablet",
                    "frequency_per_day": 2.0,
                    "schedule_times": ["08:00", "20:00"],
                }
            ],
        }
        wrong_res = client.post(
            f"/families/{fam_id}/members/{member_an}/imports",
            headers={"Authorization": f"Bearer {owner_token}"},
            files={
                "file": (
                    "wrong_member.jpg",
                    json.dumps(wrong_member_ocr).encode("utf-8"),
                    "image/jpeg",
                )
            },
        )
        assert wrong_res.status_code == 201
        wrong_data = wrong_res.json()
        assert wrong_data["status"] == "REVIEW_REQUIRED"
        assert any(
            iss["code"] == "MEMBER_MISMATCH" and iss["severity"] == "BLOCKING"
            for iss in wrong_data["validation_issues"]
        )
        # Commit must be blocked
        assert (
            client.post(
                f"/families/{fam_id}/members/{member_an}/imports/{wrong_data['id']}/commit",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={"confirm_member_id": member_an},
            ).status_code
            == 409
        )

        # Reject this wrong-member session
        rej_res = client.post(
            f"/families/{fam_id}/members/{member_an}/imports/{wrong_data['id']}/reject",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"reason": "Nhầm đơn thuốc của thành viên khác"},
        )
        assert rej_res.status_code == 200
        assert rej_res.json()["status"] == "REJECTED"

        # ------------------------------------------------------------------
        # Scenario 4b & 6: Valid Excel Upload + Duplicate File SHA-256 Detection
        # ------------------------------------------------------------------
        xlsx_bytes = tpl_res.content
        excel_up_1 = client.post(
            f"/families/{fam_id}/members/{member_an}/imports",
            headers={"Authorization": f"Bearer {owner_token}"},
            files={
                "file": (
                    "valid_prescription.xlsx",
                    xlsx_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"source_type": "EXCEL_XLSX"},
        )
        assert excel_up_1.status_code == 201
        ex_data_1 = excel_up_1.json()
        assert ex_data_1["is_duplicate"] is False
        assert ex_data_1["status"] == "READY_TO_COMMIT"
        assert len(ex_data_1["items"]) == 2

        # Upload exact same file again -> Duplicate detection (§17, §32.6)
        excel_up_2 = client.post(
            f"/families/{fam_id}/members/{member_an}/imports",
            headers={"Authorization": f"Bearer {owner_token}"},
            files={
                "file": (
                    "valid_prescription_copy.xlsx",
                    xlsx_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"source_type": "EXCEL_XLSX"},
        )
        assert excel_up_2.status_code == 201
        ex_data_2 = excel_up_2.json()
        assert ex_data_2["is_duplicate"] is True
        assert ex_data_2["duplicate_of_import_id"] == ex_data_1["id"]
        assert any(
            iss["code"] == "DUPLICATE_FILE" for iss in ex_data_2["validation_issues"]
        )

        # ------------------------------------------------------------------
        # Scenario 5: Excel Missing Required Column (`dose_amount` missing)
        # ------------------------------------------------------------------
        bad_xlsx = build_xlsx_bytes(
            ["medication_name", "dose_unit", "frequency_per_day"],
            [["Paracetamol 500mg", "tablet", "2"]],
        )
        bad_res = client.post(
            f"/families/{fam_id}/members/{member_an}/imports",
            headers={"Authorization": f"Bearer {owner_token}"},
            files={
                "file": (
                    "missing_col.xlsx",
                    bad_xlsx,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert bad_res.status_code == 422

        # ------------------------------------------------------------------
        # Scenario 7: Update Existing Prescription & Diff (No Auto-Delete!)
        # ------------------------------------------------------------------
        update_ocr = {
            "overall_confidence": 0.96,
            "prescription_meta": {
                "member_name": "Nguyễn Minh An",
                "prescription_title": "Đơn thuốc viêm phế quản (Tái khám)",
                "issued_at": "2026-11-02",
                "start_date": "2026-11-02",
                "end_date": "2026-11-08",
            },
            "medications": [
                {
                    "medication_name": f"Loratadin_{uuid4().hex[:4]} 10mg",
                    "strength": "10mg",
                    "dose_amount": 1.0,
                    "dose_unit": "tablet",
                    "frequency_per_day": 1.0,
                    "schedule_times": ["08:00"],
                }
            ],
        }
        upd_session_res = client.post(
            f"/families/{fam_id}/members/{member_an}/imports",
            headers={"Authorization": f"Bearer {owner_token}"},
            files={
                "file": (
                    "tai_kham.png",
                    json.dumps(update_ocr).encode("utf-8"),
                    "image/png",
                )
            },
            data={
                "source_type": "OCR_IMAGE",
                "import_mode": "UPDATE_EXISTING_PRESCRIPTION",
                "target_prescription_id": str(first_prescription_id),
            },
        )
        assert upd_session_res.status_code == 201
        upd_session = upd_session_res.json()
        diff = upd_session["review_payload"]["prescription_diff"]
        assert diff is not None
        assert diff["target_prescription_id"] == first_prescription_id
        assert len(diff["added_items"]) == 1
        # Existing Cefuroxim item must be retained, NOT removed (§12.2)
        assert len(diff["retained_existing_items"]) == 1

        upd_commit = client.post(
            f"/families/{fam_id}/members/{member_an}/imports/{upd_session['id']}/commit",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "confirm_member_id": member_an,
                "confirm_import_mode": "UPDATE_EXISTING_PRESCRIPTION",
                "confirm_schedule_creation": True,
                "confirm_health_updates": False,
            },
        )
        assert upd_commit.status_code == 200
        # Verify the prescription now has BOTH items (existing + newly added)
        rx_detail = client.get(
            f"/families/{fam_id}/prescriptions/{first_prescription_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        ).json()
        assert len(rx_detail["items"]) == 2

        # ------------------------------------------------------------------
        # Scenario 8: Health Update Candidates & Allergy Conflict Safety (§14, §19)
        # ------------------------------------------------------------------
        # First add an existing allergy "Penicillin" to member_an
        client.post(
            f"/families/{fam_id}/members/{member_an}/allergies",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "allergen": "Penicillin",
                "allergy_type": "DRUG",
                "severity": "SEVERE",
                "reaction_description": "Sốc phản vệ",
            },
        )

        health_ocr = {
            "overall_confidence": 0.94,
            "prescription_meta": {
                "member_name": "Nguyễn Minh An",
                "prescription_title": "Đơn thuốc kèm chẩn đoán & phản ứng",
                "issued_at": "2026-11-02",
                "diagnosis_notes": "Viêm xoang cấp",
                "allergy_notes": "No known allergy",
                "adverse_reaction_notes": "Ibuprofen: Đau thượng vị nhẹ",
            },
            "medications": [
                {
                    "medication_name": f"Desloratadin_{uuid4().hex[:4]} 5mg",
                    "dose_amount": 1.0,
                    "dose_unit": "tablet",
                    "frequency_per_day": 1.0,
                    "schedule_times": ["20:00"],
                }
            ],
        }
        h_res = client.post(
            f"/families/{fam_id}/members/{member_an}/imports",
            headers={"Authorization": f"Bearer {owner_token}"},
            files={
                "file": (
                    "health_rx.png",
                    json.dumps(health_ocr).encode("utf-8"),
                    "image/png",
                )
            },
        )
        assert h_res.status_code == 201
        h_session = h_res.json()
        # Must emit HEALTH_CONFLICT warning because document says "No known allergy" while Penicillin exists
        assert any(
            iss["code"] == "HEALTH_CONFLICT" for iss in h_session["validation_issues"]
        )

        # Confirm condition & drug reaction in draft
        client.patch(
            f"/families/{fam_id}/members/{member_an}/imports/{h_session['id']}/draft",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "health_updates": {
                    "confirm_conditions": True,
                    "conditions": [
                        {
                            "name": "Viêm xoang cấp",
                            "status": "ACTIVE",
                            "confirmed": True,
                        }
                    ],
                    "confirm_drug_reactions": True,
                    "drug_reactions": [
                        {
                            "drug_name": "Ibuprofen",
                            "reaction": "Đau thượng vị nhẹ",
                            "severity": "MILD",
                            "confirmed": True,
                        }
                    ],
                }
            },
        )
        h_commit = client.post(
            f"/families/{fam_id}/members/{member_an}/imports/{h_session['id']}/commit",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "confirm_member_id": member_an,
                "confirm_import_mode": "CREATE_NEW_PRESCRIPTION",
                "confirm_schedule_creation": True,
                "confirm_health_updates": True,
            },
        )
        assert h_commit.status_code == 200
        assert h_commit.json()["commit_summary"]["conditions_created"] == 1
        assert h_commit.json()["commit_summary"]["drug_reactions_created"] == 1

        # Verify Penicillin allergy still exists and Ibuprofen reaction was NOT turned into AllergyProfile
        with SessionLocal() as db_check:
            allergies = list(
                db_check.scalars(
                    select(AllergyProfile).where(AllergyProfile.member_id == member_an)
                ).all()
            )
            assert len(allergies) == 1
            assert allergies[0].allergen == "Penicillin"

            conditions = list(
                db_check.scalars(
                    select(MedicalCondition).where(
                        MedicalCondition.member_id == member_an
                    )
                ).all()
            )
            assert any(c.name == "Viêm xoang cấp" for c in conditions)

            reactions = list(
                db_check.scalars(
                    select(DrugReactionHistory).where(
                        DrugReactionHistory.member_id == member_an
                    )
                ).all()
            )
            assert any(r.drug_name == "Ibuprofen" for r in reactions)

        # ------------------------------------------------------------------
        # Scenario 9: Transaction Failure Rollback & Role/Cross-Family Security
        # ------------------------------------------------------------------
        rb_commit = client.post(
            f"/families/{fam_id}/members/{member_an}/imports/{ex_data_1['id']}/commit",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "confirm_member_id": member_an,
                "confirm_import_mode": "CREATE_NEW_PRESCRIPTION",
                "confirm_schedule_creation": True,
                "confirm_health_updates": False,
                "simulate_failure": True,
            },
        )
        assert rb_commit.status_code == 409

        # Verify ex_data_1 is still READY_TO_COMMIT and has 0 entity_links after rollback
        after_rb = client.get(
            f"/families/{fam_id}/members/{member_an}/imports/{ex_data_1['id']}",
            headers={"Authorization": f"Bearer {owner_token}"},
        ).json()
        assert after_rb["status"] == "READY_TO_COMMIT"
        assert after_rb["entity_links"] == []

        # VIEWER role cannot upload or commit (403)
        viewer_up = client.post(
            f"/families/{fam_id}/members/{member_an}/imports",
            headers={"Authorization": f"Bearer {viewer_token}"},
            files={
                "file": (
                    "viewer.xlsx",
                    xlsx_bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert viewer_up.status_code == 403

        # Cross-family access denied (403/404)
        cross_res = client.get(
            f"/families/{other_fam_id}/members/{member_an}/imports",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert cross_res.status_code == 404
    finally:
        _cleanup([owner_id, viewer_id, other_id], family_ids)

