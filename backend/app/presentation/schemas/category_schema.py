from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: str
    collection_id: str
    name: str
    url_slug: str
    created_at: datetime
