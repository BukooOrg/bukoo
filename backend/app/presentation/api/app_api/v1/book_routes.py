from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.use_cases.book import FindBooksUseCase
from app.core.util import build_public_url
from app.presentation.dependencies.deps import BookRepo, DbSession
from app.presentation.schemas.book_schema import (
    BaseBookResponse,
    BookAuthorItemResponse,
    BookCategoryResponse,
    BookListQueryRequest,
    BookPublisherResponse,
)
from app.presentation.schemas.list_schema import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/books", tags=["book"])


@router.get(
    "",
    response_model=PaginatedResponse[BaseBookResponse],
    operation_id="findBooks",
)
async def find_books(
    book_repo: BookRepo,
    db_session: DbSession,
    list_params: Annotated[BookListQueryRequest, Depends(BookListQueryRequest)],
) -> PaginatedResponse[BaseBookResponse]:
    use_case = FindBooksUseCase(db_session=db_session, book_repo=book_repo)
    result = await use_case.execute(list_params.to_command())
    return PaginatedResponse(
        items=[
            BaseBookResponse(
                id=b.id,
                title=b.title,
                price=b.price,
                language=b.language,
                stock_quantity=b.stock_quantity,
                cover_url=build_public_url(b.cover_url),
                isbn=b.isbn,
                description=b.description,
                page_count=b.page_count,
                published_date=b.published_date,
                is_active=b.is_active,
                publisher=(
                    BookPublisherResponse(id=b.publisher.id, name=b.publisher.name)
                    if b.publisher
                    else None
                ),
                category=(
                    BookCategoryResponse(id=b.category.id, name=b.category.name)
                    if b.category
                    else None
                ),
                authors=[
                    BookAuthorItemResponse(
                        id=a.id, name=a.name, display_order=a.display_order
                    )
                    for a in b.authors
                ],
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
            for b in result.items
        ],
        pagination=PaginationMeta.from_result(result),
    )
