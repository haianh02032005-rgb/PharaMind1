from backend.app.core.exceptions import AppException


class ScheduleNotFoundError(AppException):
    def __init__(self, detail: str = "Schedule not found") -> None:
        super().__init__(status_code=404, detail=detail)


class ScheduleArchivedError(AppException):
    def __init__(self, detail: str = "Schedule is archived") -> None:
        super().__init__(status_code=409, detail=detail)


class ScheduleCompletedError(AppException):
    def __init__(
        self,
        detail: str = "Completed schedule cannot be modified",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class ScheduleInvalidStatusTransitionError(AppException):
    def __init__(
        self,
        detail: str = "Invalid schedule status transition",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class MedicationExpiredError(AppException):
    def __init__(
        self,
        detail: str = "Cannot create schedule for expired medication",
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class InvalidScheduleDateRangeError(AppException):
    def __init__(
        self,
        detail: str = "Invalid schedule date range",
    ) -> None:
        super().__init__(status_code=422, detail=detail)


class ScheduleFrequencyMismatchError(AppException):
    def __init__(
        self,
        detail: str = "Schedule time count does not match prescription frequency",
    ) -> None:
        super().__init__(status_code=422, detail=detail)


class InvalidScheduleTimesError(AppException):
    def __init__(
        self,
        detail: str = "Invalid schedule times",
    ) -> None:
        super().__init__(status_code=422, detail=detail)
