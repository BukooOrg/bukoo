from __future__ import annotations

from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, UploadFile

from app.application.dtos.book_dto import (
    ActivateBookCommand,
    BaseBookResult,
    BookAuthorItem,
    CreateBookCommand,
    DeactivateBookCommand,
    SoftDeleteBookCommand,
    UpdateBookCommand,
    UpdateBookStockQuantityCommand,
    UploadBookCoverCommand,
    ViewBookDetailCommand,
)
from app.application.dtos.review_dto import CreateReviewCommand
from app.application.use_cases.book import (
    ActivateBookUseCase,
    CreateBookUseCase,
    DeactivateBookUseCase,
    FindBooksUseCase,
    SoftDeleteBookUseCase,
    UpdateBookStockQuantityUseCase,
    UpdateBookUseCase,
    UploadBookCoverUseCase,
    ViewBookDetailUseCase,
)
from app.application.use_cases.review.create_review import CreateReviewUseCase
from app.core.constants import ALLOWED_COVER_TYPES, MAX_COVER_BYTES
from app.core.util import build_public_url
from app.domain.exceptions import FileSizeExceededError, InvalidFileTypeError
from app.domain.repositories.book_repository import BookStatusFilter
from app.presentation.dependencies.deps import (
    AdminUser,
    AuthorRepo,
    BookRepo,
    CategoryRepo,
    CustomerUser,
    DbSession,
    OrderRepo,
    PublisherRepo,
    ReviewRepo,
    StorageService,
)
from app.presentation.schemas.book_schema import (
    ActivateBookResponse,
    BaseBookResponse,
    BookAuthorItemResponse,
    BookCategoryResponse,
    BookListQueryRequest,
    BookPublisherResponse,
    CreateBookRequest,
    CreateBookResponse,
    DeactivateBookResponse,
    SoftDeleteBookResponse,
    UpdateBookRequest,
    UpdateBookResponse,
    UpdateBookStockQuantityRequest,
    UpdateBookStockQuantityResponse,
    UploadBookCoverResponse,
    ViewBookDetailQueryRequest,
    ViewBookDetailResponse,
)
from app.presentation.schemas.list_schema import PaginatedResponse, PaginationMeta
from app.presentation.schemas.review_schema import (
    CreateReviewRequest,
    CreateReviewResponse,
)

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
            cover_url=body.cover_url,
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


@router.delete(
    "/{book_id}",
    response_model=SoftDeleteBookResponse,
    operation_id="softDeleteBook",
)
async def soft_delete_book(
    book_id: str,
    _admin_user: AdminUser,
    book_repo: BookRepo,
    db_session: DbSession,
) -> SoftDeleteBookResponse:
    use_case = SoftDeleteBookUseCase(db_session=db_session, book_repo=book_repo)
    result = await use_case.execute(SoftDeleteBookCommand(book_id=book_id))
    return build_base_book_response(result, SoftDeleteBookResponse)


@router.patch(
    "/{book_id}/deactivate",
    response_model=DeactivateBookResponse,
    operation_id="deactivateBook",
)
async def deactivate_book(
    book_id: str,
    _admin_user: AdminUser,
    book_repo: BookRepo,
    db_session: DbSession,
) -> DeactivateBookResponse:
    use_case = DeactivateBookUseCase(db_session=db_session, book_repo=book_repo)
    result = await use_case.execute(DeactivateBookCommand(book_id=book_id))
    return build_base_book_response(result, DeactivateBookResponse)


@router.patch(
    "/{book_id}/activate",
    response_model=ActivateBookResponse,
    operation_id="activateBook",
)
async def activate_book(
    book_id: str,
    _admin_user: AdminUser,
    book_repo: BookRepo,
    db_session: DbSession,
) -> ActivateBookResponse:
    use_case = ActivateBookUseCase(db_session=db_session, book_repo=book_repo)
    result = await use_case.execute(ActivateBookCommand(book_id=book_id))
    return build_base_book_response(result, ActivateBookResponse)


@router.patch(
    "/{book_id}/stock",
    response_model=UpdateBookStockQuantityResponse,
    operation_id="updateBookStockQuantity",
)
async def update_book_stock_quantity(
    book_id: str,
    body: UpdateBookStockQuantityRequest,
    _admin_user: AdminUser,
    book_repo: BookRepo,
    db_session: DbSession,
) -> UpdateBookStockQuantityResponse:
    use_case = UpdateBookStockQuantityUseCase(
        db_session=db_session, book_repo=book_repo
    )
    result = await use_case.execute(
        UpdateBookStockQuantityCommand(
            book_id=book_id, stock_quantity=body.stock_quantity
        )
    )
    return build_base_book_response(result, UpdateBookStockQuantityResponse)


@router.post(
    "/{book_id}/cover",
    response_model=UploadBookCoverResponse,
    operation_id="uploadBookCover",
)
async def upload_book_cover(
    book_id: str,
    file: UploadFile,
    _admin_user: AdminUser,
    book_repo: BookRepo,
    storage_svc: StorageService,
    db_session: DbSession,
) -> UploadBookCoverResponse:
    if file.content_type not in ALLOWED_COVER_TYPES:
        raise InvalidFileTypeError(ALLOWED_COVER_TYPES)

    file_data = await file.read()
    if len(file_data) > MAX_COVER_BYTES:
        raise FileSizeExceededError(MAX_COVER_BYTES // 1024**2, "MB")

    content_type = file.content_type or "application/octet-stream"
    use_case = UploadBookCoverUseCase(
        db_session=db_session,
        book_repo=book_repo,
        storage_svc=storage_svc,
    )
    result = await use_case.execute(
        UploadBookCoverCommand(
            book_id=book_id,
            file_data=file_data,
            content_type=content_type,
        )
    )
    return build_base_book_response(result, UploadBookCoverResponse)


@router.post(
    "/{book_id}/reviews",
    response_model=CreateReviewResponse,
    status_code=201,
    operation_id="createReview",
)
async def create_review(
    book_id: str,
    body: CreateReviewRequest,
    current_user: CustomerUser,
    book_repo: BookRepo,
    order_repo: OrderRepo,
    review_repo: ReviewRepo,
    db_session: DbSession,
) -> CreateReviewResponse:
    use_case = CreateReviewUseCase(
        db_session=db_session,
        book_repo=book_repo,
        order_repo=order_repo,
        review_repo=review_repo,
    )
    result = await use_case.execute(
        CreateReviewCommand(
            user_id=current_user.id,
            book_id=book_id,
            order_item_id=body.order_item_id,
            rating=body.rating,
            comment=body.comment,
        )
    )
    return CreateReviewResponse(
        id=result.id,
        book_id=result.book_id,
        user_id=result.user_id,
        order_item_id=result.order_item_id,
        rating=result.rating,
        comment=result.comment,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
