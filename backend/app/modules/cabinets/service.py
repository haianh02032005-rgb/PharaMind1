from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.integrations.hardware.base import HardwareAdapter
from backend.app.integrations.hardware.simulator import hardware_simulator
from backend.app.models.cabinet import Cabinet
from backend.app.models.compartment import Compartment
from backend.app.models.family import Family
from backend.app.models.family_medication import FamilyMedication
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.medication_schedule import MedicationSchedule
from backend.app.modules.cabinets.enums import (
    CabinetEventType,
    CabinetStatus,
    HardwareMode,
)
from backend.app.modules.cabinets.event_handler import CabinetEventHandler
from backend.app.modules.cabinets.exceptions import (
    ActiveCabinetAlreadyExistsError,
    CabinetArchivedError,
    CabinetNotFoundError,
    CabinetOfflineError,
    CompartmentNotFoundError,
    DuplicateCompartmentMedicationError,
    DuplicateDeviceCodeError,
    MedicationExpiredAssignmentError,
)
from backend.app.modules.cabinets.repository import CabinetRepository
from backend.app.modules.cabinets.schema import (
    CabinetCompartmentStateItem,
    CabinetCreateRequest,
    CabinetEventListResponse,
    CabinetEventResponse,
    CabinetListResponse,
    CabinetResponse,
    CabinetStateResponse,
    CompartmentDetailResponse,
    CompartmentListResponse,
    CompartmentMedicationSummary,
    CompartmentNextDoseMemberSummary,
    CompartmentNextDoseSummary,
    CompartmentResponse,
    CompartmentRevealMemberItem,
    CompartmentRevealResponse,
    CompartmentRevealWarningItem,
    DigitalTwinAllergyAlert,
    DigitalTwinCabinetHeader,
    DigitalTwinCompartmentItem,
    DigitalTwinMemberSummary,
    DigitalTwinResponse,
    DigitalTwinScheduleBrief,
    MedicationAssignmentRequest,
)
from backend.app.modules.families.exceptions import (
    FamilyArchivedError,
    InsufficientFamilyPermissionError,
)
from backend.app.modules.medications.enums import MedicationStatus
from backend.app.modules.medications.exceptions import (
    MedicationArchivedError,
    MedicationNotFoundError,
)
from backend.app.modules.medications.repository import MedicationRepository
from backend.app.modules.members.repository import MemberRepository
from backend.app.modules.schedules.enums import ScheduleStatus
from backend.app.modules.schedules.repository import ScheduleRepository
from backend.app.modules.schedules.schema import format_time_obj
from backend.app.modules.schedules.service import ScheduleService
from backend.app.shared.enums import FamilyRole, FamilyStatus


ADMIN_CABINET_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
)

WRITE_CABINET_ROLES = (
    FamilyRole.OWNER,
    FamilyRole.ADMIN,
    FamilyRole.CAREGIVER,
)


class CabinetService:
    def __init__(
        self,
        repository: CabinetRepository | None = None,
        medication_repository: MedicationRepository | None = None,
        schedule_repository: ScheduleRepository | None = None,
        member_repository: MemberRepository | None = None,
        hardware_adapter: HardwareAdapter | None = None,
        event_handler: CabinetEventHandler | None = None,
    ) -> None:
        self.repository = repository or CabinetRepository()
        self.medication_repository = (
            medication_repository or MedicationRepository()
        )
        self.schedule_repository = schedule_repository or ScheduleRepository()
        self.member_repository = member_repository or MemberRepository()
        self.hardware_adapter = hardware_adapter or hardware_simulator
        self.event_handler = event_handler or CabinetEventHandler(
            repository=self.repository
        )

    # ------------------------------------------------------------------
    # Cabinet CRUD & Archive
    # ------------------------------------------------------------------

    async def create_cabinet(
        self,
        db: Session,
        membership: FamilyMembership,
        payload: CabinetCreateRequest,
    ) -> CabinetResponse:
        self._ensure_roles(membership, *ADMIN_CABINET_ROLES)
        self._ensure_family_active(membership.family)

        # Enforce max 1 active cabinet per family (§25, §79)
        existing_active = self.repository.get_active_cabinet_for_family(
            db,
            family_id=membership.family_id,
        )
        if existing_active is not None:
            raise ActiveCabinetAlreadyExistsError(
                "Family already has an active cabinet"
            )

        # Enforce unique device_code (§10, §78)
        existing_device = self.repository.get_cabinet_by_device_code(
            db,
            device_code=payload.device_code,
        )
        if existing_device is not None:
            raise DuplicateDeviceCodeError(
                "Cabinet with this device_code already exists"
            )

        cabinet = Cabinet(
            family_id=membership.family_id,
            name=payload.name,
            device_code=payload.device_code,
            status=CabinetStatus.OFFLINE.value,
            hardware_mode=HardwareMode.SIMULATOR.value,
            notes=payload.notes,
        )
        created = self.repository.create_cabinet(db, cabinet)
        self.repository.create_compartments(
            db,
            cabinet_id=created.id,
            count=6,
        )
        db.commit()
        db.refresh(created)

        await self.hardware_adapter.initialize_cabinet(
            created.id,
            status=created.status,
            positions=[c.position for c in created.compartments],
        )
        return CabinetResponse.from_model(created)

    def list_cabinets(
        self,
        db: Session,
        membership: FamilyMembership,
        *,
        include_archived: bool = False,
    ) -> CabinetListResponse:
        rows = self.repository.list_cabinets(
            db,
            family_id=membership.family_id,
            include_archived=include_archived,
        )
        return CabinetListResponse(
            items=[CabinetResponse.from_model(row) for row in rows]
        )

    def get_cabinet_detail(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
    ) -> CabinetResponse:
        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        return CabinetResponse.from_model(cabinet)

    def get_cabinet_state(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
    ) -> CabinetStateResponse:
        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        comps = sorted(cabinet.compartments, key=lambda c: c.position)
        return CabinetStateResponse(
            cabinet_id=cabinet.id,
            status=cabinet.status,
            hardware_mode=cabinet.hardware_mode,
            last_seen_at=cabinet.last_seen_at,
            compartments=[
                CabinetCompartmentStateItem(
                    id=c.id,
                    position=c.position,
                    object_id=f"drawer_{c.position:02d}",
                    is_open=c.is_open,
                    status=c.status,
                    family_medication_id=c.family_medication_id,
                )
                for c in comps
            ],
        )

    def get_digital_twin_summary(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
        *,
        member_id: int | None = None,
    ) -> DigitalTwinResponse:
        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        comps = sorted(cabinet.compartments, key=lambda c: c.position)
        tz = ZoneInfo(settings.default_timezone)
        today = datetime.now(tz).date()

        dt_compartments: list[DigitalTwinCompartmentItem] = []
        best_overall_next_dose: CompartmentNextDoseSummary | None = None
        best_overall_position: int | None = None

        for comp in comps:
            object_id = f"drawer_{comp.position:02d}"
            med = comp.family_medication
            if med is None:
                dt_compartments.append(
                    DigitalTwinCompartmentItem(
                        id=comp.id,
                        position=comp.position,
                        object_id=object_id,
                        label=comp.label,
                        status=comp.status,
                        is_open=comp.is_open,
                        medication=None,
                        members=[],
                        next_dose=None,
                        warnings=[],
                        allergy_alerts=[],
                    )
                )
                continue

            med_summary = CompartmentMedicationSummary.from_model(med)
            warnings = self._compute_medication_warnings(med, today=today)

            schedules = self.schedule_repository.list_schedules(
                db,
                family_id=membership.family_id,
                medication_id=med.id,
                member_id=member_id,
                status=ScheduleStatus.ACTIVE.value,
            )

            # Collect distinct members linked to this medication or scheduled on it
            member_ids_ordered: list[int] = []
            for link in getattr(med, "member_links", None) or []:
                if member_id is not None and link.member_id != member_id:
                    continue
                if link.member_id not in member_ids_ordered:
                    member_ids_ordered.append(link.member_id)
            for sched in schedules:
                if member_id is not None and sched.member_id != member_id:
                    continue
                if sched.member_id not in member_ids_ordered:
                    member_ids_ordered.append(sched.member_id)

            member_summaries: list[DigitalTwinMemberSummary] = []
            allergy_alerts: list[DigitalTwinAllergyAlert] = []

            for m_id in member_ids_ordered:
                member_obj = self.member_repository.get_member(
                    db,
                    family_id=membership.family_id,
                    member_id=m_id,
                )
                if member_obj is None:
                    continue

                member_scheds = [s for s in schedules if s.member_id == m_id]
                sched_briefs: list[DigitalTwinScheduleBrief] = []
                for s in member_scheds:
                    item = s.prescription_item
                    sched_briefs.append(
                        DigitalTwinScheduleBrief(
                            schedule_id=s.id,
                            recurrence_type=s.recurrence_type,
                            times=[
                                format_time_obj(st.time_of_day)
                                for st in s.schedule_times
                            ],
                            dose_amount=(
                                item.dose_amount if item is not None else None
                            ),
                            dose_unit=(
                                item.dose_unit if item is not None else None
                            ),
                            instructions=(
                                item.instructions if item is not None else None
                            ),
                        )
                    )

                member_next = self._compute_medication_next_dose(
                    db,
                    family_id=membership.family_id,
                    family_medication_id=med.id,
                    member_id=m_id,
                )
                member_summaries.append(
                    DigitalTwinMemberSummary(
                        id=member_obj.id,
                        full_name=member_obj.full_name,
                        relationship_label=member_obj.relationship_label,
                        schedules=sched_briefs,
                        next_schedule=(
                            member_next.time if member_next is not None else None
                        ),
                        next_dose_date=(
                            member_next.date if member_next is not None else None
                        ),
                        next_dose_time=(
                            member_next.time if member_next is not None else None
                        ),
                        next_dose_amount=(
                            member_next.dose_amount
                            if member_next is not None
                            else None
                        ),
                        next_dose_unit=(
                            member_next.dose_unit
                            if member_next is not None
                            else None
                        ),
                    )
                )

                member_alerts = self._evaluate_member_allergy_alerts(
                    db,
                    member_id=member_obj.id,
                    member_name=member_obj.full_name,
                    medication=med,
                )
                for alert in member_alerts:
                    allergy_alerts.append(alert)
                    if (
                        alert.alert_type == "ALLERGY"
                        and "ALLERGY_RISK" not in warnings
                    ):
                        warnings.append("ALLERGY_RISK")
                    elif (
                        alert.alert_type == "DRUG_REACTION"
                        and "DRUG_REACTION_RISK" not in warnings
                    ):
                        warnings.append("DRUG_REACTION_RISK")

            comp_next_dose = self._compute_medication_next_dose(
                db,
                family_id=membership.family_id,
                family_medication_id=med.id,
                member_id=member_id,
            )

            if comp_next_dose is not None:
                if best_overall_next_dose is None:
                    best_overall_next_dose = comp_next_dose
                    best_overall_position = comp.position
                else:
                    cand_key = (
                        comp_next_dose.date,
                        comp_next_dose.time,
                        comp.position,
                    )
                    best_key = (
                        best_overall_next_dose.date,
                        best_overall_next_dose.time,
                        best_overall_position or 999,
                    )
                    if cand_key < best_key:
                        best_overall_next_dose = comp_next_dose
                        best_overall_position = comp.position

            dt_compartments.append(
                DigitalTwinCompartmentItem(
                    id=comp.id,
                    position=comp.position,
                    object_id=object_id,
                    label=comp.label,
                    status=comp.status,
                    is_open=comp.is_open,
                    medication=med_summary,
                    members=member_summaries,
                    next_dose=comp_next_dose,
                    warnings=warnings,
                    allergy_alerts=allergy_alerts,
                )
            )

        return DigitalTwinResponse(
            cabinet=DigitalTwinCabinetHeader(
                id=cabinet.id,
                name=cabinet.name,
                device_code=cabinet.device_code,
                status=cabinet.status,
                hardware_mode=cabinet.hardware_mode,
                last_seen_at=cabinet.last_seen_at,
            ),
            next_dose_position=best_overall_position,
            next_dose=best_overall_next_dose,
            compartments=dt_compartments,
        )

    def archive_cabinet(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
    ) -> CabinetResponse:
        self._ensure_roles(membership, *ADMIN_CABINET_ROLES)
        self._ensure_family_active(membership.family)

        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        updated = self.repository.update_cabinet_status(
            db,
            cabinet,
            status=CabinetStatus.ARCHIVED.value,
        )
        db.commit()
        db.refresh(updated)
        return CabinetResponse.from_model(updated)

    # ------------------------------------------------------------------
    # Compartments & Medication Assignment
    # ------------------------------------------------------------------

    def list_compartments(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
    ) -> CompartmentListResponse:
        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        comps = self.repository.list_compartments(db, cabinet_id=cabinet.id)
        return CompartmentListResponse(
            items=[CompartmentResponse.from_model(c) for c in comps]
        )

    def get_compartment_detail(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
        position: int,
    ) -> CompartmentDetailResponse:
        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        comp = self._get_scoped_compartment(
            db, membership, cabinet.id, position
        )
        base_resp = CompartmentResponse.from_model(comp)
        next_dose = None
        if comp.family_medication_id is not None:
            next_dose = self._compute_medication_next_dose(
                db,
                family_id=membership.family_id,
                family_medication_id=comp.family_medication_id,
            )
        return CompartmentDetailResponse(
            **base_resp.model_dump(),
            next_dose=next_dose,
        )

    def get_compartment_reveal(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
        position: int,
    ) -> CompartmentRevealResponse:
        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        comp = self._get_scoped_compartment(
            db, membership, cabinet.id, position
        )
        object_id = f"drawer_{comp.position:02d}"
        med = comp.family_medication
        if med is None:
            return CompartmentRevealResponse(
                cabinet_id=cabinet.id,
                cabinet_status=cabinet.status,
                position=comp.position,
                object_id=object_id,
                label=comp.label,
                status=comp.status,
                is_open=comp.is_open,
                is_next_dose=False,
                medication=None,
                members=[],
                next_dose=None,
                warnings=[],
            )

        tz = ZoneInfo(settings.default_timezone)
        today = datetime.now(tz).date()
        med_summary = CompartmentMedicationSummary.from_model(med)

        # Evaluate overall next dose across cabinet to know if this compartment is_next_dose
        dt_summary = self.get_digital_twin_summary(
            db, membership, cabinet.id
        )
        is_next_dose = dt_summary.next_dose_position == comp.position

        schedules = self.schedule_repository.list_schedules(
            db,
            family_id=membership.family_id,
            medication_id=med.id,
            status=ScheduleStatus.ACTIVE.value,
        )

        member_ids_ordered: list[int] = []
        for link in getattr(med, "member_links", None) or []:
            if link.member_id not in member_ids_ordered:
                member_ids_ordered.append(link.member_id)
        for sched in schedules:
            if sched.member_id not in member_ids_ordered:
                member_ids_ordered.append(sched.member_id)

        reveal_members: list[CompartmentRevealMemberItem] = []
        warnings_list: list[CompartmentRevealWarningItem] = []

        # Stock / Expiry warnings
        raw_warnings = self._compute_medication_warnings(med, today=today)
        for w_code in raw_warnings:
            if w_code == "LOW_STOCK":
                warnings_list.append(
                    CompartmentRevealWarningItem(
                        type="LOW_STOCK_WARNING",
                        severity="MODERATE",
                        message=(
                            f"⚠ Thuốc {med_summary.name} sắp hết "
                            f"(còn {med_summary.quantity} {med_summary.unit})."
                        ),
                    )
                )
            elif w_code == "DEPLETED":
                warnings_list.append(
                    CompartmentRevealWarningItem(
                        type="DEPLETED_WARNING",
                        severity="SEVERE",
                        message=f"⚠ Thuốc {med_summary.name} trong ngăn đã hết.",
                    )
                )
            elif w_code == "EXPIRING":
                warnings_list.append(
                    CompartmentRevealWarningItem(
                        type="EXPIRING_WARNING",
                        severity="MODERATE",
                        message=(
                            f"⚠ Thuốc {med_summary.name} sắp đến hạn sử dụng "
                            f"({med_summary.expiration_date})."
                        ),
                    )
                )
            elif w_code == "EXPIRED":
                warnings_list.append(
                    CompartmentRevealWarningItem(
                        type="EXPIRED_WARNING",
                        severity="SEVERE",
                        message=(
                            f"⚠ Thuốc {med_summary.name} đã quá hạn sử dụng "
                            f"({med_summary.expiration_date}). Vui lòng kiểm tra trước khi dùng."
                        ),
                    )
                )

        for m_id in member_ids_ordered:
            member_obj = self.member_repository.get_member(
                db,
                family_id=membership.family_id,
                member_id=m_id,
            )
            if member_obj is None:
                continue

            member_scheds = [s for s in schedules if s.member_id == m_id]
            all_times: list[str] = []
            first_dose_amount: float | None = None
            first_dose_unit: str | None = None
            first_instructions: str | None = None

            for s in member_scheds:
                for st in s.schedule_times:
                    t_str = format_time_obj(st.time_of_day)
                    if t_str not in all_times:
                        all_times.append(t_str)
                item = s.prescription_item
                if item is not None:
                    if first_dose_amount is None:
                        first_dose_amount = item.dose_amount
                    if first_dose_unit is None:
                        first_dose_unit = item.dose_unit
                    if first_instructions is None and item.instructions:
                        first_instructions = item.instructions

            all_times.sort()
            member_next = self._compute_medication_next_dose(
                db,
                family_id=membership.family_id,
                family_medication_id=med.id,
                member_id=m_id,
            )

            next_iso: str | None = None
            if member_next is not None and member_next.date and member_next.time:
                h_str, m_str = member_next.time.split(":")
                dt_combined = datetime(
                    member_next.date.year,
                    member_next.date.month,
                    member_next.date.day,
                    int(h_str),
                    int(m_str),
                    tzinfo=tz,
                )
                next_iso = dt_combined.isoformat()

            reveal_members.append(
                CompartmentRevealMemberItem(
                    id=member_obj.id,
                    full_name=member_obj.full_name,
                    relationship_label=member_obj.relationship_label,
                    dose_amount=(
                        member_next.dose_amount
                        if member_next and member_next.dose_amount is not None
                        else first_dose_amount
                    ),
                    dose_unit=(
                        member_next.dose_unit
                        if member_next and member_next.dose_unit is not None
                        else (first_dose_unit or med_summary.unit)
                    ),
                    next_schedule=next_iso,
                    next_date=(
                        member_next.date if member_next is not None else None
                    ),
                    next_time=(
                        member_next.time if member_next is not None else None
                    ),
                    times=all_times,
                    instructions=first_instructions,
                )
            )

            # Evaluate soft allergy / drug reaction warnings (§15, §37, §38)
            member_alerts = self._evaluate_member_allergy_alerts(
                db,
                member_id=member_obj.id,
                member_name=member_obj.full_name,
                medication=med,
            )
            for alert in member_alerts:
                warnings_list.append(
                    CompartmentRevealWarningItem(
                        type=(
                            "ALLERGY_WARNING"
                            if alert.alert_type == "ALLERGY"
                            else "DRUG_REACTION_WARNING"
                        ),
                        severity=alert.severity,
                        member_id=alert.member_id,
                        member_name=alert.member_name,
                        substance=alert.substance,
                        message=(
                            f"⚠ Thành viên {alert.member_name} có tiền sử "
                            f"{'dị ứng' if alert.alert_type == 'ALLERGY' else 'phản ứng thuốc'} "
                            f"với {alert.substance}. Vui lòng kiểm tra trước khi dùng thuốc."
                        ),
                    )
                )

        # Sort members so the one with the earliest next_schedule comes first (§13)
        reveal_members.sort(
            key=lambda m: (
                0 if m.next_schedule is not None else 1,
                m.next_schedule or "9999-12-31",
                m.id,
            )
        )

        comp_next_dose = self._compute_medication_next_dose(
            db,
            family_id=membership.family_id,
            family_medication_id=med.id,
        )

        return CompartmentRevealResponse(
            cabinet_id=cabinet.id,
            cabinet_status=cabinet.status,
            position=comp.position,
            object_id=object_id,
            label=comp.label,
            status=comp.status,
            is_open=comp.is_open,
            is_next_dose=is_next_dose,
            medication=med_summary,
            members=reveal_members,
            next_dose=comp_next_dose,
            warnings=warnings_list,
        )

    def assign_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
        position: int,
        payload: MedicationAssignmentRequest,
    ) -> CompartmentResponse:
        self._ensure_roles(membership, *WRITE_CABINET_ROLES)
        self._ensure_family_active(membership.family)

        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        self._ensure_cabinet_not_archived(cabinet)

        comp = self._get_scoped_compartment(
            db, membership, cabinet.id, position
        )
        medication = self._get_scoped_medication(
            db, membership, payload.family_medication_id
        )
        self._ensure_medication_valid_for_assignment(medication)

        existing_comp = self.repository.get_compartment_by_medication(
            db,
            family_medication_id=medication.id,
        )
        if existing_comp is not None and existing_comp.id != comp.id:
            raise DuplicateCompartmentMedicationError(
                "Medication is already assigned to another compartment"
            )

        updated = self.repository.assign_medication(
            db,
            comp,
            family_medication_id=medication.id,
        )
        self.repository.create_event(
            db,
            family_id=membership.family_id,
            cabinet_id=cabinet.id,
            compartment_id=comp.id,
            event_type=CabinetEventType.COMPARTMENT_ASSIGN_MEDICATION.value,
            source="BACKEND",
            payload={
                "position": comp.position,
                "family_medication_id": medication.id,
            },
        )
        db.commit()
        db.refresh(updated)
        return CompartmentResponse.from_model(updated)

    def unassign_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
        position: int,
    ) -> CompartmentResponse:
        self._ensure_roles(membership, *WRITE_CABINET_ROLES)
        self._ensure_family_active(membership.family)

        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        self._ensure_cabinet_not_archived(cabinet)

        comp = self._get_scoped_compartment(
            db, membership, cabinet.id, position
        )
        prev_med_id = comp.family_medication_id
        updated = self.repository.unassign_medication(db, comp)
        self.repository.create_event(
            db,
            family_id=membership.family_id,
            cabinet_id=cabinet.id,
            compartment_id=comp.id,
            event_type=CabinetEventType.COMPARTMENT_UNASSIGN_MEDICATION.value,
            source="BACKEND",
            payload={
                "position": comp.position,
                "previous_family_medication_id": prev_med_id,
            },
        )
        db.commit()
        db.refresh(updated)
        return CompartmentResponse.from_model(updated)

    # ------------------------------------------------------------------
    # Simulator & Compartment Commands
    # ------------------------------------------------------------------

    async def set_simulator_online(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
    ) -> CabinetResponse:
        self._ensure_roles(membership, *WRITE_CABINET_ROLES)
        self._ensure_family_active(membership.family)

        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        self._ensure_cabinet_not_archived(cabinet)

        await self.hardware_adapter.set_online(cabinet.id)
        updated = await self.event_handler.handle_cabinet_online(
            db,
            cabinet,
            source="SIMULATOR",
        )
        return CabinetResponse.from_model(updated)

    async def set_simulator_offline(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
    ) -> CabinetResponse:
        self._ensure_roles(membership, *WRITE_CABINET_ROLES)
        self._ensure_family_active(membership.family)

        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        self._ensure_cabinet_not_archived(cabinet)

        await self.hardware_adapter.set_offline(cabinet.id)
        updated = await self.event_handler.handle_cabinet_offline(
            db,
            cabinet,
            source="SIMULATOR",
        )
        return CabinetResponse.from_model(updated)

    async def open_compartment(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
        position: int,
    ) -> CompartmentResponse:
        self._ensure_roles(membership, *WRITE_CABINET_ROLES)
        self._ensure_family_active(membership.family)

        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        self._ensure_cabinet_not_archived(cabinet)
        self._ensure_cabinet_online(cabinet)

        comp = self._get_scoped_compartment(
            db, membership, cabinet.id, position
        )
        await self.hardware_adapter.open_compartment(cabinet.id, comp.position)
        updated_comp = await self.event_handler.handle_compartment_open(
            db,
            cabinet,
            comp,
            source="SIMULATOR",
        )
        return CompartmentResponse.from_model(updated_comp)

    async def close_compartment(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
        position: int,
    ) -> CompartmentResponse:
        self._ensure_roles(membership, *WRITE_CABINET_ROLES)
        self._ensure_family_active(membership.family)

        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        self._ensure_cabinet_not_archived(cabinet)
        self._ensure_cabinet_online(cabinet)

        comp = self._get_scoped_compartment(
            db, membership, cabinet.id, position
        )
        await self.hardware_adapter.close_compartment(
            cabinet.id, comp.position
        )
        updated_comp = await self.event_handler.handle_compartment_close(
            db,
            cabinet,
            comp,
            source="SIMULATOR",
        )
        return CompartmentResponse.from_model(updated_comp)

    async def sync_cabinet_state(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
    ) -> CabinetStateResponse:
        self._ensure_roles(membership, *WRITE_CABINET_ROLES)
        self._ensure_family_active(membership.family)

        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        self._ensure_cabinet_not_archived(cabinet)

        sim_state = await self.hardware_adapter.get_state(cabinet.id)
        await self.event_handler.handle_state_sync(
            db,
            cabinet,
            sim_state,
            source="SIMULATOR",
        )
        return self.get_cabinet_state(db, membership, cabinet.id)

    # ------------------------------------------------------------------
    # Event History
    # ------------------------------------------------------------------

    def list_events(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
        *,
        event_type: CabinetEventType | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        limit: int = 100,
    ) -> CabinetEventListResponse:
        cabinet = self._get_scoped_cabinet(db, membership, cabinet_id)
        rows = self.repository.list_events(
            db,
            family_id=membership.family_id,
            cabinet_id=cabinet.id,
            event_type=event_type.value if event_type is not None else None,
            from_time=from_time,
            to_time=to_time,
            limit=limit,
        )
        return CabinetEventListResponse(
            items=[CabinetEventResponse.from_model(r) for r in rows]
        )

    # ------------------------------------------------------------------
    # Internal Helpers & Guards
    # ------------------------------------------------------------------

    def _compute_medication_next_dose(
        self,
        db: Session,
        *,
        family_id: int,
        family_medication_id: int,
        member_id: int | None = None,
    ) -> CompartmentNextDoseSummary | None:
        tz = ZoneInfo(settings.default_timezone)
        ref_now = datetime.now(tz)
        today = ref_now.date()
        current_time = ref_now.timetz().replace(tzinfo=None)

        schedules = self.schedule_repository.list_schedules(
            db,
            family_id=family_id,
            medication_id=family_medication_id,
            member_id=member_id,
            status=ScheduleStatus.ACTIVE.value,
        )
        if not schedules:
            return None

        min_start = min(s.start_date for s in schedules)
        scan_start = max(today, min_start)

        for offset in range(0, 367):
            candidate_date = scan_start + timedelta(days=offset)
            day_candidates: list[tuple[time, int, MedicationSchedule]] = []
            for schedule in schedules:
                if not ScheduleService._schedule_matches_date(
                    schedule, candidate_date
                ):
                    continue
                for st in schedule.schedule_times:
                    if (
                        candidate_date == today
                        and st.time_of_day <= current_time
                    ):
                        continue
                    day_candidates.append(
                        (st.time_of_day, schedule.id, schedule)
                    )
            if day_candidates:
                day_candidates.sort(key=lambda entry: (entry[0], entry[1]))
                best_time, _, best_sched = day_candidates[0]
                item = best_sched.prescription_item
                member = best_sched.member
                return CompartmentNextDoseSummary(
                    schedule_id=best_sched.id,
                    date=candidate_date,
                    time=format_time_obj(best_time),
                    member=CompartmentNextDoseMemberSummary(
                        id=member.id,
                        full_name=member.full_name,
                    ),
                    dose_amount=item.dose_amount if item is not None else None,
                    dose_unit=item.dose_unit if item is not None else None,
                )
        return None

    @staticmethod
    def _compute_medication_warnings(
        medication: FamilyMedication,
        *,
        today: date,
    ) -> list[str]:
        warnings: list[str] = []
        if (
            medication.quantity <= 0
            or medication.status == MedicationStatus.DEPLETED.value
        ):
            warnings.append("DEPLETED")
        elif (
            medication.low_stock_threshold is not None
            and medication.quantity <= medication.low_stock_threshold
        ):
            warnings.append("LOW_STOCK")

        if medication.status == MedicationStatus.EXPIRED.value or (
            medication.expiration_date is not None
            and medication.expiration_date < today
        ):
            warnings.append("EXPIRED")
        elif medication.expiration_date is not None:
            days_left = (medication.expiration_date - today).days
            if 0 <= days_left <= 30:
                warnings.append("EXPIRING")
        return warnings

    def _evaluate_member_allergy_alerts(
        self,
        db: Session,
        *,
        member_id: int,
        member_name: str,
        medication: FamilyMedication,
    ) -> list[DigitalTwinAllergyAlert]:
        alerts: list[DigitalTwinAllergyAlert] = []
        catalog = medication.catalog
        med_name_norm = (catalog.name if catalog else "").strip().lower()
        active_ing_norm = (
            (catalog.active_ingredient if catalog and catalog.active_ingredient else "")
            .strip()
            .lower()
        )

        allergies = self.member_repository.list_allergies(db, member_id)
        for allergy in allergies:
            allergen_norm = (allergy.allergen or "").strip().lower()
            if not allergen_norm:
                continue
            matched = False
            if med_name_norm and (
                allergen_norm in med_name_norm or med_name_norm in allergen_norm
            ):
                matched = True
            elif active_ing_norm and (
                allergen_norm in active_ing_norm
                or active_ing_norm in allergen_norm
            ):
                matched = True

            if matched:
                alerts.append(
                    DigitalTwinAllergyAlert(
                        member_id=member_id,
                        member_name=member_name,
                        alert_type="ALLERGY",
                        substance=allergy.allergen,
                        severity=allergy.severity,
                        reaction=allergy.reaction_description,
                        message=(
                            f"Thành viên {member_name} có tiền sử dị ứng với "
                            f"{allergy.allergen} (Mức độ: {allergy.severity}). "
                            f"Vui lòng kiểm tra kỹ trước khi dùng thuốc."
                        ),
                    )
                )

        reactions = self.member_repository.list_drug_reactions(db, member_id)
        for rx in reactions:
            rx_drug_norm = (rx.drug_name or "").strip().lower()
            rx_ing_norm = (rx.active_ingredient or "").strip().lower()
            matched = False
            if rx_drug_norm and med_name_norm and (
                rx_drug_norm in med_name_norm or med_name_norm in rx_drug_norm
            ):
                matched = True
            elif rx_drug_norm and active_ing_norm and (
                rx_drug_norm in active_ing_norm or active_ing_norm in rx_drug_norm
            ):
                matched = True
            elif rx_ing_norm and med_name_norm and (
                rx_ing_norm in med_name_norm or med_name_norm in rx_ing_norm
            ):
                matched = True
            elif rx_ing_norm and active_ing_norm and (
                rx_ing_norm in active_ing_norm or active_ing_norm in rx_ing_norm
            ):
                matched = True

            if matched:
                substance_label = rx.drug_name
                if rx.active_ingredient:
                    substance_label = f"{rx.drug_name} ({rx.active_ingredient})"
                alerts.append(
                    DigitalTwinAllergyAlert(
                        member_id=member_id,
                        member_name=member_name,
                        alert_type="DRUG_REACTION",
                        substance=substance_label,
                        severity=rx.severity,
                        reaction=rx.reaction,
                        message=(
                            f"Thành viên {member_name} có tiền sử phản ứng thuốc "
                            f"với {substance_label}: {rx.reaction}."
                        ),
                    )
                )

        return alerts

    def _get_scoped_cabinet(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
    ) -> Cabinet:
        cabinet = self.repository.get_cabinet(
            db,
            family_id=membership.family_id,
            cabinet_id=cabinet_id,
        )
        if cabinet is None:
            raise CabinetNotFoundError("Cabinet not found")
        return cabinet

    def _get_scoped_compartment(
        self,
        db: Session,
        membership: FamilyMembership,
        cabinet_id: int,
        position: int,
    ) -> Compartment:
        comp = self.repository.get_compartment(
            db,
            family_id=membership.family_id,
            cabinet_id=cabinet_id,
            position=position,
        )
        if comp is None:
            raise CompartmentNotFoundError("Compartment not found")
        return comp

    def _get_scoped_medication(
        self,
        db: Session,
        membership: FamilyMembership,
        medication_id: int,
    ) -> FamilyMedication:
        med = self.medication_repository.get_family_medication(
            db,
            family_id=membership.family_id,
            medication_id=medication_id,
        )
        if med is None:
            raise MedicationNotFoundError("Medication not found")
        return med

    @staticmethod
    def _ensure_roles(
        membership: FamilyMembership,
        *allowed_roles: FamilyRole,
    ) -> None:
        allowed_values = {r.value for r in allowed_roles}
        if membership.role not in allowed_values:
            raise InsufficientFamilyPermissionError(
                "Insufficient family permission"
            )

    @staticmethod
    def _ensure_family_active(family: Family) -> None:
        if family.status != FamilyStatus.ACTIVE.value:
            raise FamilyArchivedError("Family archived")

    @staticmethod
    def _ensure_cabinet_not_archived(cabinet: Cabinet) -> None:
        if cabinet.status == CabinetStatus.ARCHIVED.value:
            raise CabinetArchivedError("Cabinet is archived")

    @staticmethod
    def _ensure_cabinet_online(cabinet: Cabinet) -> None:
        if cabinet.status != CabinetStatus.ONLINE.value:
            raise CabinetOfflineError(
                "Cannot operate compartment while cabinet is offline"
            )

    @staticmethod
    def _ensure_medication_valid_for_assignment(
        medication: FamilyMedication,
    ) -> None:
        if medication.status == MedicationStatus.ARCHIVED.value:
            raise MedicationArchivedError("Medication archived")
        tz = ZoneInfo(settings.default_timezone)
        today = datetime.now(tz).date()
        if medication.status == MedicationStatus.EXPIRED.value or (
            medication.expiration_date is not None
            and medication.expiration_date < today
        ):
            raise MedicationExpiredAssignmentError(
                "Cannot assign expired medication to a compartment"
            )
