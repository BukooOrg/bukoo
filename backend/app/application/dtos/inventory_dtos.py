from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

# commands


# results
@dataclass(frozen=True)
class GetInventoryMetricsResult:
    total_sku_count: int
    out_of_stock_count: int
    low_stock_count: int
    total_inventory_value: Decimal
