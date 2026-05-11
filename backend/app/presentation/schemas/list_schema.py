from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.query_params import (
    PageParams,
    PaginatedResult,
    QueryParams,
    parse_sort,
)


class ListQueryRequest(BaseModel):
    sort: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    search: str | None = None

    def to_query_params(self) -> QueryParams:
        return QueryParams(
            page=PageParams(page=self.page, page_size=self.page_size),
            sorts=parse_sort(self.sort),
            search=self.search,
        )


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def from_result(cls, result: PaginatedResult[Any]) -> PaginationMeta:
        return cls(
            page=result.page,
            page_size=result.page_size,
            total_items=result.total_items,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )


class PaginatedResponse[DataType](BaseModel):
    items: list[DataType]
    pagination: PaginationMeta
