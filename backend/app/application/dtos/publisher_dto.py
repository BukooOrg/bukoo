from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# commands
@dataclass(frozen=True)
class ViewPublisherDetailCommand:
    publisher_id: str


@dataclass(frozen=True)
class CreatePublisherCommand:
    name: str
    website: str | None


@dataclass(frozen=True)
class UpdatePublisherCommand:
    publisher_id: str
    name: str
    website: str | None


@dataclass(frozen=True)
class SoftDeletePublisherCommand:
    publisher_id: str


# results
@dataclass(frozen=True)
class BasePublisherDetailResult:
    id: str
    name: str
    website: str | None
    created_at: datetime


@dataclass(frozen=True)
class ViewPublisherDetailResult(BasePublisherDetailResult):
    pass


@dataclass(frozen=True)
class CreatePublisherResult(BasePublisherDetailResult):
    pass


@dataclass(frozen=True)
class UpdatePublisherResult(BasePublisherDetailResult):
    pass


@dataclass(frozen=True)
class SoftDeletePublisherResult:
    message: str
