from backend.app.core.exceptions import AppException, PermissionDeniedError


class ImportSessionNotFoundError(AppException):
    """Raised when an import session does not exist or belongs to another family/member."""

    status_code = 404
    default_detail = "Import session not found"


class ImportUnsupportedFileError(AppException):
    """Raised when the uploaded file format, extension, or size is invalid."""

    status_code = 422
    default_detail = "Unsupported import file"


class ImportTemplateColumnError(AppException):
    """Raised when an Excel/CSV upload is missing required columns."""

    status_code = 422
    default_detail = "Missing required columns"


class ImportValidationBlockedError(AppException):
    """Raised when attempting to commit an import session that still has blocking/error validation issues."""

    status_code = 409
    default_detail = "Import has unresolved validation issues"


class ImportAlreadyCommittedError(AppException):
    """Raised when attempting to edit or commit an already committed or rejected import session."""

    status_code = 409
    default_detail = "Import session is already finalized"


class ImportTransactionRollbackError(AppException):
    """Raised when a commit fails midway and rolls back all changes."""

    status_code = 409
    default_detail = "Import commit failed and was rolled back"


class ImportPermissionDeniedError(PermissionDeniedError):
    """Raised when user lacks write permissions for prescription import."""

    status_code = 403
    default_detail = "Insufficient permission for prescription import"
