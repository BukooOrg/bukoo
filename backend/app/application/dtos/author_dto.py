from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.query_params import QueryParams


# commands
@dataclass(frozen=True)
class FindAuthorsCommand:
    query: QueryParams


@dataclass(frozen=True)
class ViewAuthorDetailCommand:
    author_id: str


@dataclass(frozen=True)
class CreateAuthorCommand:
    name: str


@dataclass(frozen=True)
class UpdateAuthorCommand:
    author_id: str
    name: str


@dataclass(frozen=True)
class SoftDeleteAuthorCommand:
    author_id: str


# results
@dataclass(frozen=True)
class BaseAuthorResult:
    id: str
    name: str
    created_at: datetime


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


@dataclass(frozen=True)
class UpdateAuthorResult:
    id: str
    name: str
    created_at: datetime


@dataclass(frozen=True)
class SoftDeleteAuthorResult:
    message: str
