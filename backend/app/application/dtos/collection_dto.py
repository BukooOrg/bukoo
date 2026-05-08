from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CreateCollectionCommand:
    name: str
    url_slug: str


@dataclass(frozen=True)
class CreateCollectionResult:
    id: str
    name: str
    url_slug: str
    created_at: datetime
    categories: list[object] = field(default_factory=list)
