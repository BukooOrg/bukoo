from __future__ import annotations

from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends

from app.application.dtos.book_dto import (
    BaseBookResult,
    BookAuthorItem,
    CreateBookCommand,
    UpdateBookCommand,
    ViewBookDetailCommand,
)
from app.application.use_cases.book import (
    CreateBookUseCase,
    FindBooksUseCase,
    UpdateBookUseCase,
    ViewBookDetailUseCase,
)
from app.core.util import build_public_url
from app.domain.repositories.book_repository import BookStatusFilter
from app.presentation.dependencies.deps import (
    AdminUser,
    AuthorRepo,
    BookRepo,
    CategoryRepo,
    DbSession,
    PublisherRepo,
)
from app.presentation.schemas.book_schema import (
    BaseBookResponse,
    BookAuthorItemResponse,
    BookCategoryResponse,
    BookListQueryRequest,
    BookPublisherResponse,
    CreateBookRequest,
    CreateBookResponse,
    UpdateBookRequest,
    UpdateBookResponse,
    ViewBookDetailQueryRequest,
    ViewBookDetailResponse,
)
from app.presentation.schemas.list_schema import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/books", tags=["book"])

T = TypeVar("T", bound=BaseBookResult)
P = TypeVar("P", bound=BaseBookResponse)


def build_base_book_response(book_result: T, response_cls: type[P]) -> P:  # noqa: UP047 # type: ignore
    return response_cls(
        id=book_result.id,
        title=book_result.title,
        price=book_result.price,
        language=book_result.language,
        stock_quantity=book_result.stock_quantity,
        cover_url=build_public_url(book_result.cover_url),
        isbn=book_result.isbn,
        description=book_result.description,
        page_count=book_result.page_count,
        published_date=book_result.published_date,
        is_active=book_result.is_active,
        publisher=(
            BookPublisherResponse(
                id=book_result.publisher.id, name=book_result.publisher.name
            )
            if book_result.publisher
            else None
        ),
        category=(
            BookCategoryResponse(
                id=book_result.category.id, name=book_result.category.name
            )
            if book_result.category
            else None
        ),
        authors=[
            BookAuthorItemResponse(id=a.id, name=a.name, display_order=a.display_order)
            for a in book_result.authors
        ],
        created_at=book_result.created_at,
        updated_at=book_result.updated_at,
    )


@router.get(
    "",
    response_model=PaginatedResponse[BaseBookResponse],
    operation_id="findBooks",
)
async def find_books(
    query_params: Annotated[BookListQueryRequest, Depends(BookListQueryRequest)],
    book_repo: BookRepo,
    db_session: DbSession,
) -> PaginatedResponse[BaseBookResponse]:
    use_case = FindBooksUseCase(db_session=db_session, book_repo=book_repo)
    result = await use_case.execute(query_params.to_command())
    return PaginatedResponse(
        items=[build_base_book_response(b, BaseBookResponse) for b in result.items],
        pagination=PaginationMeta.from_result(result),
    )


@router.get(
    "/{book_id}", response_model=ViewBookDetailResponse, operation_id="viewBookDetail"
)
async def view_book_detail(
    book_id: str,
    query_params: Annotated[
        ViewBookDetailQueryRequest, Depends(ViewBookDetailQueryRequest)
    ],
    book_repo: BookRepo,
    db_session: DbSession,
) -> ViewBookDetailResponse:
    use_case = ViewBookDetailUseCase(db_session=db_session, book_repo=book_repo)
    result = await use_case.execute(
        ViewBookDetailCommand(
            book_id=book_id, filters=BookStatusFilter(status=query_params.status)
        )
    )
    return build_base_book_response(result, ViewBookDetailResponse)


@router.post(
    "",
    response_model=CreateBookResponse,
    status_code=201,
    operation_id="createBook",
)
async def create_book(
    body: CreateBookRequest,
    _admin_user: AdminUser,
    book_repo: BookRepo,
    publisher_repo: PublisherRepo,
    category_repo: CategoryRepo,
    author_repo: AuthorRepo,
    db_session: DbSession,
) -> CreateBookResponse:
    use_case = CreateBookUseCase(
        db_session=db_session,
        book_repo=book_repo,
        publisher_repo=publisher_repo,
        category_repo=category_repo,
        author_repo=author_repo,
    )
    result = await use_case.execute(
        CreateBookCommand(
            title=body.title,
            price=body.price,
            stock_quantity=body.stock_quantity,
            language=body.language,
            isbn=body.isbn,
            description=body.description,
            page_count=body.page_count,
            published_date=body.published_date,
            publisher_id=body.publisher_id,
            category_id=body.category_id,
            authors=[
                BookAuthorItem(author_id=a.author_id, display_order=a.display_order)
                for a in body.authors
            ],
        )
    )
    return build_base_book_response(result, CreateBookResponse)


@router.patch(
    "/{book_id}",
    response_model=UpdateBookResponse,
    operation_id="updateBook",
)
async def update_book(
    book_id: str,
    body: UpdateBookRequest,
    _admin_user: AdminUser,
    book_repo: BookRepo,
    publisher_repo: PublisherRepo,
    category_repo: CategoryRepo,
    author_repo: AuthorRepo,
    db_session: DbSession,
) -> UpdateBookResponse:
    use_case = UpdateBookUseCase(
        db_session=db_session,
        book_repo=book_repo,
        publisher_repo=publisher_repo,
        category_repo=category_repo,
        author_repo=author_repo,
    )
    result = await use_case.execute(
        UpdateBookCommand(
            book_id=book_id,
            title=body.title,
            price=body.price,
            stock_quantity=body.stock_quantity,
            language=body.language,
            isbn=body.isbn,
            description=body.description,
            page_count=body.page_count,
            published_date=body.published_date,
            publisher_id=body.publisher_id,
            category_id=body.category_id,
            authors=[
                BookAuthorItem(author_id=a.author_id, display_order=a.display_order)
                for a in body.authors
            ]
            if isinstance(body.authors, list)
            else body.authors,
        )
    )
    return build_base_book_response(result, UpdateBookResponse)
