from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# commands
@dataclass(frozen=True)
class CreatePublisherCommand:
    name: str
    website: str | None


@dataclass(frozen=True)
class UpdatePublisherCommand:
    publisher_id: str
    name: str
    website: str | None


# results
@dataclass(frozen=True)
class CreatePublisherResult:
    id: str
    name: str
    website: str | None
    created_at: datetime


@dataclass(frozen=True)
class UpdatePublisherResult:
    id: str
    name: str
    website: str | None
    created_at: datetime
