from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.constants import LOW_STOCK_THRESHOLD
from app.presentation.schemas.list_schema import ListQueryRequest


class InventoryMetricsResponse(BaseModel):
    total_sku_count: int
    out_of_stock_count: int
    low_stock_count: int
    total_inventory_value: Decimal


class LowStockQueryRequest(ListQueryRequest):
    threshold: int = Field(default=LOW_STOCK_THRESHOLD, ge=1)
