from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class InventoryMetricsResponse(BaseModel):
    total_sku_count: int
    out_of_stock_count: int
    low_stock_count: int
    total_inventory_value: Decimal
