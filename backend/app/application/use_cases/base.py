from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class BaseUseCase(ABC):
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any | None:
        raise NotImplementedError
