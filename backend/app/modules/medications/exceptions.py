from backend.app.core.exceptions import AppException


class MedicationNotFoundError(AppException):
    def __init__(self, detail: str = "Medication not found") -> None:
        super().__init__(status_code=404, detail=detail)


class MedicationArchivedError(AppException):
    def __init__(self, detail: str = "Medication archived") -> None:
        super().__init__(status_code=409, detail=detail)


class DuplicateMemberMedicationLinkError(AppException):
    def __init__(
        self,
        detail: str = "Medication is already linked to this member",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class MemberMedicationLinkNotFoundError(AppException):
    def __init__(
        self,
        detail: str = "Member medication link not found",
    ) -> None:
        super().__init__(status_code=404, detail=detail)
