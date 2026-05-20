from __future__ import annotations

from fastapi import APIRouter

from app.application.use_cases.inventory import GetInventoryMetricsUseCase
from app.presentation.dependencies.deps import AdminUser, BookRepo, DbSession
from app.presentation.schemas.inventory_schema import InventoryMetricsResponse

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
