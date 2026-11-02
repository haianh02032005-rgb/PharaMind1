from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.models.family_member import FamilyMember
from backend.app.models.family_membership import FamilyMembership
from backend.app.modules.families.dependencies import get_family_membership
from backend.app.modules.members.repository import MemberRepository


def get_family_member(
    family_id: int,
    member_id: int,
    membership: FamilyMembership = Depends(get_family_membership),
    db: Session = Depends(get_db),
) -> FamilyMember:
    member = MemberRepository().get_member(
        db,
        family_id=membership.family_id,
        member_id=member_id,
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    return member
