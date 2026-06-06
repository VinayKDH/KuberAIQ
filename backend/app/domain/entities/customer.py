"""Customer entity (pure domain)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.domain.value_objects.gstin import Gstin
from app.domain.value_objects.phone import Phone


@dataclass
class Customer:
    company_id: uuid.UUID
    name: str
    phone: Phone
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    email: str | None = None
    gstin: Gstin | None = None
    billing_address: str | None = None
    notes: str | None = None

    @property
    def state_code(self) -> str | None:
        return self.gstin.state_code if self.gstin else None

    def rename(self, name: str) -> None:
        if not name.strip():
            raise ValueError("Customer name cannot be empty")
        self.name = name.strip()
