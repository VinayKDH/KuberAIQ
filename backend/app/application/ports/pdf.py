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

    async def generate_quotation_pdf(
        self,
        *,
        company: dict[str, Any],
        customer: dict[str, Any],
        quotation: dict[str, Any],
    ) -> bytes: ...

    async def generate_statement_pdf(
        self,
        *,
        company: dict[str, Any],
        customer: dict[str, Any],
        summary: dict[str, Any],
        invoices: list[dict[str, Any]],
        payments: list[dict[str, Any]],
    ) -> bytes: ...
