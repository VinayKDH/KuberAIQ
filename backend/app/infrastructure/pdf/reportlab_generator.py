"""ReportLab PDF generator for GST invoices."""
from __future__ import annotations

import io
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.core.constants import CURRENCY_SYMBOL


class ReportLabPdfGenerator:
    async def generate_invoice_pdf(
        self,
        *,
        company: dict[str, Any],
        customer: dict[str, Any],
        invoice: dict[str, Any],
    ) -> bytes:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 20 * mm

        c.setFont("Helvetica-Bold", 16)
        c.drawString(20 * mm, y, company.get("legal_name", "Company"))
        y -= 8 * mm
        c.setFont("Helvetica", 10)
        if company.get("gstin"):
            c.drawString(20 * mm, y, f"GSTIN: {company['gstin']}")
            y -= 6 * mm

        c.setFont("Helvetica-Bold", 14)
        c.drawString(20 * mm, y, f"TAX INVOICE — {invoice.get('invoice_number', 'DRAFT')}")
        y -= 10 * mm

        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"Bill To: {customer.get('name', '')}")
        y -= 6 * mm
        if customer.get("gstin"):
            c.drawString(20 * mm, y, f"GSTIN: {customer['gstin']}")
            y -= 6 * mm
        c.drawString(20 * mm, y, f"Date: {invoice.get('issue_date')}  Due: {invoice.get('due_date')}")
        y -= 10 * mm

        c.setFont("Helvetica-Bold", 9)
        c.drawString(20 * mm, y, "Description")
        c.drawString(100 * mm, y, "Qty")
        c.drawString(120 * mm, y, "Rate")
        c.drawString(140 * mm, y, "GST%")
        c.drawString(160 * mm, y, "Total")
        y -= 6 * mm
        c.setFont("Helvetica", 9)

        for item in invoice.get("items", []):
            c.drawString(20 * mm, y, str(item.get("description", ""))[:40])
            c.drawString(100 * mm, y, str(item.get("quantity", "")))
            c.drawString(120 * mm, y, str(item.get("unit_price", "")))
            c.drawString(140 * mm, y, str(item.get("gst_rate", "")))
            c.drawString(160 * mm, y, str(item.get("line_total", "")))
            y -= 6 * mm

        y -= 6 * mm
        c.drawString(120 * mm, y, f"Taxable: {CURRENCY_SYMBOL}{invoice.get('taxable_amount', 0)}")
        y -= 6 * mm
        c.drawString(120 * mm, y, f"CGST: {CURRENCY_SYMBOL}{invoice.get('cgst_amount', 0)}")
        y -= 6 * mm
        c.drawString(120 * mm, y, f"SGST: {CURRENCY_SYMBOL}{invoice.get('sgst_amount', 0)}")
        y -= 6 * mm
        c.drawString(120 * mm, y, f"IGST: {CURRENCY_SYMBOL}{invoice.get('igst_amount', 0)}")
        y -= 8 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(120 * mm, y, f"Grand Total: {CURRENCY_SYMBOL}{invoice.get('grand_total', 0)}")

        c.showPage()
        c.save()
        return buffer.getvalue()
