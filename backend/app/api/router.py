from fastapi import APIRouter

from backend.app.modules.auth.router import router as auth_router
from backend.app.modules.users.router import router as users_router
from backend.app.modules.cabinets.router import (
    router as cabinets_router,
    ws_router as cabinets_ws_router,
)
from backend.app.modules.families.router import router as families_router
from backend.app.modules.imports.router import (
    router as imports_router,
    template_router as imports_template_router,
)
from backend.app.modules.medications.router import router as medications_router
from backend.app.modules.members.router import router as members_router
from backend.app.modules.prescriptions.router import router as prescriptions_router
from backend.app.modules.schedules.router import router as schedules_router


api_router = APIRouter()

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    families_router,
    prefix="/families",
    tags=["Families"],
)

api_router.include_router(
    members_router,
    prefix="/families/{family_id}/members",
    tags=["Family Members & Health Profiles"],
)

api_router.include_router(
    medications_router,
    prefix="/families/{family_id}/medications",
    tags=["Family Medications"],
)

api_router.include_router(
    prescriptions_router,
    prefix="/families/{family_id}/prescriptions",
    tags=["Prescriptions"],
)

api_router.include_router(
    schedules_router,
    prefix="/families/{family_id}/schedules",
    tags=["Medication Schedules"],
)

api_router.include_router(
    cabinets_router,
    prefix="/families/{family_id}/cabinets",
    tags=["Smart Cabinets"],
)

api_router.include_router(
    cabinets_ws_router,
    tags=["Smart Cabinets Realtime"],
)

api_router.include_router(
    imports_router,
    prefix="/families/{family_id}/members/{member_id}/imports",
    tags=["Prescription Imports (OCR & Excel)"],
)

api_router.include_router(
    imports_template_router,
    prefix="/imports",
    tags=["Prescription Imports (OCR & Excel)"],
)
