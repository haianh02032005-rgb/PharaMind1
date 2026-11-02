from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.allergy_profile import AllergyProfile
from backend.app.models.drug_reaction_history import DrugReactionHistory
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.medication_catalog import MedicationCatalog
from backend.app.models.member_medication import MemberMedication
from backend.app.modules.imports.enums import ImportResolutionStatus
from backend.app.modules.imports.normalizers.medication_normalizer import (
    normalize_medication_key,
)
from backend.app.modules.medications.enums import MedicationStatus


def resolve_medication_item(
    db: Session,
    *,
    family_id: int,
    member_id: int,
    med_item: dict[str, Any],
) -> dict[str, Any]:
    """Run the 4-step Medication Resolution Pipeline (§11) plus allergy/reaction safety checks."""
    med_name = med_item.get("medication_name") or ""
    norm_name = normalize_medication_key(med_name)
    norm_strength = (med_item.get("strength") or "").strip().lower().replace(" ", "")
    norm_form = (med_item.get("dosage_form") or "").strip().upper()
    norm_ingredient = normalize_medication_key(med_item.get("active_ingredient"))

    family_meds = list(
        db.scalars(
            select(FamilyMedication).where(
                FamilyMedication.family_id == family_id,
                FamilyMedication.status != MedicationStatus.ARCHIVED.value,
            )
        ).all()
    )
    catalogs = list(db.scalars(select(MedicationCatalog)).all())

    member_links = {
        row.family_medication_id
        for row in db.scalars(
            select(MemberMedication).where(MemberMedication.member_id == member_id)
        ).all()
    }

    matched_family_med: FamilyMedication | None = None
    matched_catalog: MedicationCatalog | None = None
    candidates: list[dict[str, Any]] = []

    # Step 1: Exact match in FamilyMedication
    for fm in family_meds:
        cat = fm.catalog
        if not cat:
            continue
        cat_name = normalize_medication_key(cat.name)
        cat_strength = (cat.strength or "").strip().lower().replace(" ", "")
        cat_form = (cat.dosage_form or "").strip().upper()

        exact_name = bool(norm_name and (cat_name == norm_name or norm_name in cat_name or cat_name in norm_name))
        strength_ok = (not norm_strength or not cat_strength or norm_strength == cat_strength)
        form_ok = (not norm_form or not cat_form or norm_form == cat_form)

        if exact_name and strength_ok and form_ok:
            if matched_family_med is None:
                matched_family_med = fm
                matched_catalog = cat
            candidates.append(
                {
                    "type": "FAMILY_MEDICATION",
                    "family_medication_id": fm.id,
                    "catalog_id": cat.id,
                    "name": cat.name,
                    "active_ingredient": cat.active_ingredient,
                    "strength": cat.strength,
                    "dosage_form": cat.dosage_form,
                    "quantity": fm.quantity,
                    "unit": fm.unit,
                    "status": fm.status,
                    "linked_to_member": fm.id in member_links,
                    "match_type": "EXACT_FAMILY_MEDICATION",
                }
            )
        elif exact_name or (norm_ingredient and normalize_medication_key(cat.active_ingredient) == norm_ingredient):
            candidates.append(
                {
                    "type": "FAMILY_MEDICATION",
                    "family_medication_id": fm.id,
                    "catalog_id": cat.id,
                    "name": cat.name,
                    "active_ingredient": cat.active_ingredient,
                    "strength": cat.strength,
                    "dosage_form": cat.dosage_form,
                    "quantity": fm.quantity,
                    "unit": fm.unit,
                    "status": fm.status,
                    "linked_to_member": fm.id in member_links,
                    "match_type": "FUZZY_FAMILY_MEDICATION",
                }
            )

    # Step 2: Exact/Fuzzy match in MedicationCatalog if not already matched to FamilyMedication
    if matched_family_med is None:
        for cat in catalogs:
            cat_name = normalize_medication_key(cat.name)
            cat_strength = (cat.strength or "").strip().lower().replace(" ", "")
            cat_form = (cat.dosage_form or "").strip().upper()

            exact_name = bool(norm_name and (cat_name == norm_name or norm_name in cat_name or cat_name in norm_name))
            strength_ok = (not norm_strength or not cat_strength or norm_strength == cat_strength)
            form_ok = (not norm_form or not cat_form or norm_form == cat_form)

            if exact_name and strength_ok and form_ok:
                if matched_catalog is None:
                    matched_catalog = cat
                candidates.append(
                    {
                        "type": "MEDICATION_CATALOG",
                        "family_medication_id": None,
                        "catalog_id": cat.id,
                        "name": cat.name,
                        "active_ingredient": cat.active_ingredient,
                        "strength": cat.strength,
                        "dosage_form": cat.dosage_form,
                        "match_type": "EXACT_CATALOG",
                    }
                )

    # Determine initial resolution status and action
    if matched_family_med is not None:
        resolution_status = ImportResolutionStatus.AUTO_MATCHED.value
        action = "LINK_EXISTING"
        matched_entity_type = "FamilyMedication"
        matched_entity_id = matched_family_med.id
    elif matched_catalog is not None:
        resolution_status = ImportResolutionStatus.AUTO_MATCHED.value
        action = "CREATE_NEW"
        matched_entity_type = "MedicationCatalog"
        matched_entity_id = matched_catalog.id
    else:
        resolution_status = ImportResolutionStatus.CREATE_NEW.value
        action = "CREATE_NEW"
        matched_entity_type = None
        matched_entity_id = None

    # Check member's existing AllergyProfile & DrugReactionHistory for warnings
    allergies = list(
        db.scalars(select(AllergyProfile).where(AllergyProfile.member_id == member_id)).all()
    )
    reactions = list(
        db.scalars(
            select(DrugReactionHistory).where(DrugReactionHistory.member_id == member_id)
        ).all()
    )

    allergy_warnings: list[str] = []
    for al in allergies:
        al_key = normalize_medication_key(al.allergen)
        if al_key and (
            (norm_name and (al_key in norm_name or norm_name in al_key))
            or (norm_ingredient and (al_key in norm_ingredient or norm_ingredient in al_key))
        ):
            allergy_warnings.append(
                f"Thành viên có tiền sử dị ứng với '{al.allergen}' (Mức độ: {al.severity})."
            )

    reaction_warnings: list[str] = []
    for rx in reactions:
        rx_drug = normalize_medication_key(rx.drug_name)
        rx_ing = normalize_medication_key(rx.active_ingredient)
        if (rx_drug and norm_name and (rx_drug in norm_name or norm_name in rx_drug)) or (
            rx_ing and norm_ingredient and (rx_ing in norm_ingredient or norm_ingredient in rx_ing)
        ):
            reaction_warnings.append(
                f"Thành viên từng gặp phản ứng thuốc với '{rx.drug_name}': {rx.reaction}."
            )

    return {
        "resolution_status": resolution_status,
        "action": action,
        "matched_entity_type": matched_entity_type,
        "matched_entity_id": matched_entity_id,
        "family_medication_id": matched_family_med.id if matched_family_med else None,
        "catalog_id": matched_catalog.id if matched_catalog else None,
        "linked_to_member": (
            matched_family_med.id in member_links if matched_family_med else False
        ),
        "candidates": candidates,
        "allergy_warnings": allergy_warnings,
        "reaction_warnings": reaction_warnings,
    }

