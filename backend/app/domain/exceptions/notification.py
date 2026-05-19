from .base import DomainException


class NotificationNotFoundError(DomainException):
    def __init__(self, notification_id: str) -> None:
        self.notification_id = notification_id
        super().__init__(f"Notification '{notification_id}' not found.")
