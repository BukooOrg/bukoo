from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.query_params import QueryParams


# commands
@dataclass(frozen=True)
class FindLowStockItemsCommand:
    query_params: QueryParams
    threshold: int


@dataclass(frozen=True)
class FindOutOfStockItemsCommand:
    query_params: QueryParams


# results
@dataclass(frozen=True)
class GetInventoryMetricsResult:
    total_sku_count: int
    out_of_stock_count: int
    low_stock_count: int
    total_inventory_value: Decimal
