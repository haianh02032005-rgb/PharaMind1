from backend.app.core.exceptions import AppException


class PrescriptionNotFoundError(AppException):
    def __init__(self, detail: str = "Prescription not found") -> None:
        super().__init__(status_code=404, detail=detail)


class PrescriptionItemNotFoundError(AppException):
    def __init__(self, detail: str = "Prescription item not found") -> None:
        super().__init__(status_code=404, detail=detail)


class PrescriptionArchivedError(AppException):
    def __init__(self, detail: str = "Prescription is archived") -> None:
        super().__init__(status_code=409, detail=detail)


class PrescriptionCompletedError(AppException):
    def __init__(
        self,
        detail: str = "Completed prescription cannot be modified",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class DuplicatePrescriptionItemError(AppException):
    def __init__(
        self,
        detail: str = "Medication is already added to this prescription",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class MedicationNotLinkedToMemberError(AppException):
    def __init__(
        self,
        detail: str = "Medication must be linked to the member before adding to prescription",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class InvalidPrescriptionDateRangeError(AppException):
    def __init__(
        self,
        detail: str = "start_date cannot be after end_date",
    ) -> None:
        super().__init__(status_code=422, detail=detail)
