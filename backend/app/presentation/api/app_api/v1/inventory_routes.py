from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.dtos.inventory_dtos import FindLowStockItemsCommand
from app.application.use_cases.inventory import (
    FindLowStockItemsUseCase,
    GetInventoryMetricsUseCase,
)
from app.core.query_params import PageParams, QueryParams, parse_sort
from app.presentation.dependencies.deps import AdminUser, BookRepo, DbSession
from app.presentation.schemas.book_schema import (
    BaseBookResponse,
    build_base_book_response,
)
from app.presentation.schemas.inventory_schema import (
    InventoryMetricsResponse,
    LowStockQueryRequest,
)
from app.presentation.schemas.list_schema import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get(
    "/metrics",
    response_model=InventoryMetricsResponse,
    operation_id="getInventoryMetrics",
)
async def get_inventory_metrics(
    _admin_user: AdminUser,
    book_repo: BookRepo,
    db_session: DbSession,
) -> InventoryMetricsResponse:
    use_case = GetInventoryMetricsUseCase(db_session=db_session, book_repo=book_repo)
    result = await use_case.execute()
    return InventoryMetricsResponse(
        total_sku_count=result.total_sku_count,
        out_of_stock_count=result.out_of_stock_count,
        low_stock_count=result.low_stock_count,
        total_inventory_value=result.total_inventory_value,
    )


@router.get(
    "/low-stock",
    response_model=PaginatedResponse[BaseBookResponse],
    operation_id="findLowStockItems",
)
async def find_low_stock_items(
    _admin_user: AdminUser,
    book_repo: BookRepo,
    db_session: DbSession,
    query: Annotated[LowStockQueryRequest, Depends()],
) -> PaginatedResponse[BaseBookResponse]:
    cmd = FindLowStockItemsCommand(
        query_params=QueryParams(
            page=PageParams(page=query.page, page_size=query.page_size),
            sorts=parse_sort(query.sort),
        ),
        threshold=query.threshold,
    )
    use_case = FindLowStockItemsUseCase(db_session=db_session, book_repo=book_repo)
    result = await use_case.execute(cmd)
    return PaginatedResponse(
        items=[build_base_book_response(b, BaseBookResponse) for b in result.items],
        pagination=PaginationMeta.from_result(result),
    )
