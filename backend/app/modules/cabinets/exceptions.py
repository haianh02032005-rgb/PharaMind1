from backend.app.core.exceptions import AppException


class CabinetNotFoundError(AppException):
    def __init__(self, detail: str = "Cabinet not found") -> None:
        super().__init__(status_code=404, detail=detail)


class CompartmentNotFoundError(AppException):
    def __init__(self, detail: str = "Compartment not found") -> None:
        super().__init__(status_code=404, detail=detail)


class DuplicateDeviceCodeError(AppException):
    def __init__(
        self,
        detail: str = "Cabinet with this device_code already exists",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class ActiveCabinetAlreadyExistsError(AppException):
    def __init__(
        self,
        detail: str = "Family already has an active cabinet",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class CabinetArchivedError(AppException):
    def __init__(self, detail: str = "Cabinet is archived") -> None:
        super().__init__(status_code=409, detail=detail)


class CabinetOfflineError(AppException):
    def __init__(
        self,
        detail: str = "Cannot operate compartment while cabinet is offline",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class DuplicateCompartmentMedicationError(AppException):
    def __init__(
        self,
        detail: str = "Medication is already assigned to another compartment",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class MedicationExpiredAssignmentError(AppException):
    def __init__(
        self,
        detail: str = "Cannot assign expired medication to a compartment",
    ) -> None:
        super().__init__(status_code=409, detail=detail)
