from .base import DomainException


class InvalidReportDateRangeError(DomainException):
    def __init__(self) -> None:
        super().__init__("date_from must be strictly before date_to.")


class ReportJobNotFoundError(DomainException):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Report job '{job_id}' not found.")


class ReportNotReadyError(DomainException):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Report job '{job_id}' is not yet complete.")
