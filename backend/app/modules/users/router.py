from fastapi import APIRouter, Depends, status

from backend.app.models.user import User
from backend.app.modules.auth.dependencies import get_current_user
from backend.app.modules.auth.schema import CurrentUserResponse


router = APIRouter()


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
