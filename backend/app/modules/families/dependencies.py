from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.models.family_membership import FamilyMembership
from backend.app.models.user import User
from backend.app.modules.auth.dependencies import get_current_user
from backend.app.modules.families.repository import FamilyRepository
from backend.app.shared.enums import FamilyRole, FamilyStatus


def get_family_membership(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FamilyMembership:
    membership = FamilyRepository().get_membership(
        db,
        family_id=family_id,
        user_id=current_user.id,
    )
    if membership is None or membership.family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found",
        )

    if (
        membership.family.status == FamilyStatus.ARCHIVED.value
        and membership.role != FamilyRole.OWNER.value
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found",
        )

    return membership


def require_family_roles(
    *allowed_roles: FamilyRole,
) -> Callable[[FamilyMembership], FamilyMembership]:
    allowed_values = {role.value for role in allowed_roles}

    def _dependency(
        membership: FamilyMembership = Depends(get_family_membership),
    ) -> FamilyMembership:
        if membership.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient family permission",
            )
        return membership

    return _dependency
