from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.presentation.schemas.category_schema import CategoryResponse


class CreateCollectionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url_slug: str = Field(min_length=1, max_length=100)


class CollectionResponse(BaseModel):
    id: str
    name: str
    url_slug: str
    categories: list[CategoryResponse]
    created_at: datetime


class ViewCollectionDetailResponse(CollectionResponse):
    pass


class CollectionListItemResponse(BaseModel):
    id: str
    name: str
    url_slug: str
    categories: list[CategoryResponse]
    created_at: datetime
