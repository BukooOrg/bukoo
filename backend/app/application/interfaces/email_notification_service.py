from __future__ import annotations

from abc import ABC, abstractmethod


class IEmailNotificationService(ABC):
    @abstractmethod
    def send_welcome(self, to: str, full_name: str) -> None:
        pass
