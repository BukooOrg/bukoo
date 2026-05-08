from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# requests
class BaseCategoryRequest(BaseModel):
    collection_id: str
    name: str = Field(min_length=1, max_length=100)
    url_slug: str = Field(min_length=1, max_length=100)


class CreateCategoryRequest(BaseCategoryRequest):
    pass


# responses
class BaseCategoryResponse(BaseModel):
    id: str
    collection_id: str
    name: str
    url_slug: str
    created_at: datetime


class ViewCategoryDetailResponse(BaseCategoryResponse):
    pass


class CreateCategoryResponse(BaseCategoryResponse):
    pass
