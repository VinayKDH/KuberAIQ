"""Product API schemas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.core.constants import STOCK_ADJUSTMENT_REASONS


class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    hsn_sac: str | None = Field(default=None, max_length=10)
    unit: str = Field(default="NOS", max_length=20)
    default_price: Decimal = Field(ge=0)
    gst_rate: Decimal | None = Field(default=None, ge=0, le=28)
    stock_qty: Decimal = Field(default=0, ge=0)


class UpdateProductRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    hsn_sac: str | None = Field(default=None, max_length=10)
    unit: str | None = Field(default=None, max_length=20)
    default_price: Decimal | None = Field(default=None, ge=0)
    gst_rate: Decimal | None = Field(default=None, ge=0, le=28)
    stock_qty: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class HsnLookupResponse(BaseModel):
    hsn_sac: str | None = None
    gst_rate: Decimal | None = None
    source: str | None = None
    matched_label: str | None = None


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    hsn_sac: str | None = None
    unit: str
    default_price: Decimal
    gst_rate: Decimal
    stock_qty: Decimal = Decimal("0")
    is_active: bool


class AdjustStockRequest(BaseModel):
    delta: Decimal | None = None
    qty: Decimal | None = Field(default=None, ge=0)
    reason: str = Field(default="Other", max_length=100)

    @model_validator(mode="after")
    def validate_adjustment(self) -> "AdjustStockRequest":
        if self.delta is None and self.qty is None:
            raise ValueError("Provide delta or qty")
        if self.delta is not None and self.qty is not None:
            raise ValueError("Provide either delta or qty, not both")
        reason = self.reason.strip()
        if not reason:
            raise ValueError("Reason is required")
        if reason not in STOCK_ADJUSTMENT_REASONS:
            raise ValueError(f"Reason must be one of: {', '.join(STOCK_ADJUSTMENT_REASONS)}")
        self.reason = reason
        return self
