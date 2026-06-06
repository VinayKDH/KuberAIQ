"""PDF generation port."""
from __future__ import annotations

from typing import Any, Protocol


class PdfGeneratorPort(Protocol):
    async def generate_invoice_pdf(
        self,
        *,
        company: dict[str, Any],
        customer: dict[str, Any],
        invoice: dict[str, Any],
    ) -> bytes: ...
