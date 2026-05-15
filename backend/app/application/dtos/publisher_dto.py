from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.query_params import QueryParams

# commands


@dataclass(frozen=True)
class FindPublishersCommand:
    query_params: QueryParams


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
class BasePublisherResult:
    id: str
    name: str
    website: str | None
    created_at: datetime


@dataclass(frozen=True)
class ViewPublisherDetailResult(BasePublisherResult):
    pass


@dataclass(frozen=True)
class CreatePublisherResult(BasePublisherResult):
    pass


@dataclass(frozen=True)
class UpdatePublisherResult(BasePublisherResult):
    pass


@dataclass(frozen=True)
class SoftDeletePublisherResult:
    message: str
