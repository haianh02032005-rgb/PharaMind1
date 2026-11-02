from backend.app.core.exceptions import AppException


class MemberNotFoundError(AppException):
    """Raised when a family member does not exist within the scoped family."""

    status_code = 404
    default_detail = "Member not found"


class MemberArchivedError(AppException):
    """Raised when attempting write operations on an archived member."""

    status_code = 409
    default_detail = "Member archived"


class HealthProfileNotFoundError(AppException):
    """Raised when a member's health profile cannot be found."""

    status_code = 404
    default_detail = "Health profile not found"


class MedicalConditionNotFoundError(AppException):
    """Raised when a medical condition does not exist for the scoped member."""

    status_code = 404
    default_detail = "Medical condition not found"


class AllergyNotFoundError(AppException):
    """Raised when an allergy profile does not exist for the scoped member."""

    status_code = 404
    default_detail = "Allergy not found"


class DrugReactionNotFoundError(AppException):
    """Raised when a drug reaction history does not exist for the scoped member."""

    status_code = 404
    default_detail = "Drug reaction not found"


class EmergencyContactNotFoundError(AppException):
    """Raised when an emergency contact does not exist for the scoped member."""

    status_code = 404
    default_detail = "Emergency contact not found"
