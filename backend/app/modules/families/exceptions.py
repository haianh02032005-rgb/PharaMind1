from backend.app.core.exceptions import AppException, PermissionDeniedError


class FamilyNotFoundError(AppException):
    """Raised when a family does not exist or the user has no access to it."""

    status_code = 404
    default_detail = "Family not found"


class MembershipNotFoundError(AppException):
    """Raised when a family membership does not exist within the scoped family."""

    status_code = 404
    default_detail = "Membership not found"


class InsufficientFamilyPermissionError(PermissionDeniedError):
    """Raised when the user's family role is insufficient for the action."""

    status_code = 403
    default_detail = "Insufficient family permission"


class DuplicateFamilyMembershipError(AppException):
    """Raised when adding a user who already belongs to the family."""

    status_code = 409
    default_detail = "User already belongs to this family"


class OwnerModificationNotAllowedError(PermissionDeniedError):
    """Raised when attempting to assign, downgrade, or remove an OWNER membership."""

    status_code = 403
    default_detail = "Cannot modify owner membership"


class FamilyArchivedError(AppException):
    """Raised when attempting write operations on an archived family."""

    status_code = 409
    default_detail = "Family archived"
