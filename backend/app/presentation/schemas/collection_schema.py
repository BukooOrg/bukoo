from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateCollectionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url_slug: str = Field(min_length=1, max_length=100)


class CollectionResponse(BaseModel):
    id: str
    name: str
    url_slug: str
    categories: list[object]
    created_at: datetime
