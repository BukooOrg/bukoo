from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# commands
@dataclass(frozen=True)
class ViewAuthorDetailCommand:
    author_id: str


@dataclass(frozen=True)
class CreateAuthorCommand:
    name: str


# results
@dataclass(frozen=True)
class ViewAuthorDetailResult:
    id: str
    name: str
    created_at: datetime


@dataclass(frozen=True)
class CreateAuthorResult:
    id: str
    name: str
    created_at: datetime
