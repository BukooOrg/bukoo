from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BaseCategoryResult:
    id: str
    collection_id: str
    name: str
    url_slug: str
    created_at: datetime
