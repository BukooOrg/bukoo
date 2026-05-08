from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.presentation.schemas.category_schema import CategoryResponse


# requests
class BaseCollectionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url_slug: str = Field(min_length=1, max_length=100)


class CreateCollectionRequest(BaseCollectionRequest):
    pass


class UpdateCollectionRequest(BaseCollectionRequest):
    pass


# responses
class BaseCollectionResponse(BaseModel):
    id: str
    name: str
    url_slug: str
    categories: list[CategoryResponse]
    created_at: datetime


class ViewCollectionDetailResponse(BaseCollectionResponse):
    pass


class CreateCollectionResponse(BaseCollectionResponse):
    pass


class CollectionListItemResponse(BaseModel):
    id: str
    name: str
    url_slug: str
    categories: list[CategoryResponse]
    created_at: datetime


class UpdateCollectionResponse(BaseCollectionResponse):
    pass
