"""Stock movement audit entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class StockMovement:
    company_id: uuid.UUID
    product_id: uuid.UUID
    delta: Decimal
    qty_after: Decimal
    reason: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime | None = None
