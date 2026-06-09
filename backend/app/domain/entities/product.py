"""Product catalog entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from app.core.constants import DEFAULT_UNIT


@dataclass
class Product:
    company_id: uuid.UUID
    name: str
    default_price: Decimal
    gst_rate: Decimal
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    description: str | None = None
    hsn_sac: str | None = None
    unit: str = DEFAULT_UNIT
    is_active: bool = True

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def rename(self, name: str) -> None:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Product name is required")
        self.name = cleaned
