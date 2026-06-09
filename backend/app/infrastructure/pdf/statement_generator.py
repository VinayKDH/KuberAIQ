"""ReportLab PDF generator for customer account statements."""
from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.constants import (
    PDF_ACCENT_COLOR,
    PDF_BORDER_COLOR,
    PDF_BRAND_COLOR,
    PDF_MUTED_COLOR,
    PDF_STATEMENT_TITLE,
    PDF_TABLE_HEADER_BG,
)
from app.infrastructure.pdf.formatting import format_inr_pdf
from app.infrastructure.pdf.pdf_common import escape_xml, html_para, para, state_label


class StatementPdfGenerator:
    async def generate_statement_pdf(
        self,
        *,
        company: dict[str, Any],
        customer: dict[str, Any],
        summary: dict[str, Any],
        invoices: list[dict[str, Any]],
        payments: list[dict[str, Any]],
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title=PDF_STATEMENT_TITLE,
        )

        styles = getSampleStyleSheet()
        subtitle = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor(PDF_MUTED_COLOR),
            leading=12,
        )
        section_title = ParagraphStyle(
            "SectionTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=colors.HexColor(PDF_BRAND_COLOR),
            spaceAfter=4,
        )
        body = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
        )
        title = ParagraphStyle(
            "StatementTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=colors.HexColor(PDF_ACCENT_COLOR),
            alignment=TA_RIGHT,
        )

        company_name = escape_xml(company.get("legal_name", "Company"))
        company_details: list[str] = []
        if company.get("address"):
            company_details.append(escape_xml(str(company["address"])))
        if company.get("gstin"):
            company_details.append(f"GSTIN: {escape_xml(str(company['gstin']))}")
        company_details.append(f"State: {escape_xml(state_label(company.get('state_code')))}")

        header_data = [
            [
                html_para(
                    f"<b><font size='14'>{company_name}</font></b><br/>"
                    f"{'<br/>'.join(company_details)}",
                    subtitle,
                ),
                para(PDF_STATEMENT_TITLE, title),
            ]
        ]
        header_table = Table(header_data, colWidths=[110 * mm, 68 * mm])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor(PDF_ACCENT_COLOR)),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        customer_lines = [
            f"<b>{escape_xml(customer.get('name', ''))}</b>",
        ]
        if customer.get("billing_address"):
            customer_lines.append(escape_xml(str(customer["billing_address"])))
        if customer.get("gstin"):
            customer_lines.append(f"GSTIN: {escape_xml(str(customer['gstin']))}")
        if customer.get("phone"):
            customer_lines.append(f"Phone: {escape_xml(str(customer['phone']))}")
        if customer.get("email"):
            customer_lines.append(f"Email: {escape_xml(str(customer['email']))}")

        party_table = Table(
            [
                [para("Customer", section_title)],
                [html_para("<br/>".join(customer_lines), body)],
            ],
            colWidths=[178 * mm],
        )
        party_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_TABLE_HEADER_BG)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        summary_rows = [
            ["Total billed", format_inr_pdf(summary.get("total_billed", 0))],
            ["Total paid", format_inr_pdf(summary.get("total_paid", 0))],
            ["Outstanding", format_inr_pdf(summary.get("outstanding", 0))],
        ]
        summary_table = Table(summary_rows, colWidths=[42 * mm, 32 * mm])
        summary_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor(PDF_MUTED_COLOR)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(PDF_TABLE_HEADER_BG)),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        aging = summary.get("aging", {})
        if aging:
            aging_rows = [["Aging bucket", "Amount"]]
            for bucket, amount in aging.items():
                aging_rows.append([bucket, format_inr_pdf(amount)])
            aging_table = Table(aging_rows, colWidths=[42 * mm, 32 * mm])
            aging_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_TABLE_HEADER_BG)),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor(PDF_BORDER_COLOR)),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
        else:
            aging_table = Spacer(1, 1)

        invoice_header = ["Date", "Invoice #", "Due", "Status", "Billed", "Due Amt"]
        invoice_rows: list[list[str]] = [invoice_header]
        for inv in invoices:
            if inv.get("status") == "CANCELLED":
                continue
            invoice_rows.append(
                [
                    str(inv.get("issue_date", "—")),
                    str(inv.get("invoice_number") or "—"),
                    str(inv.get("due_date", "—")),
                    str(inv.get("status", "—")).replace("_", " "),
                    format_inr_pdf(inv.get("grand_total", 0)),
                    format_inr_pdf(inv.get("amount_due", 0)),
                ]
            )

        invoices_table = Table(
            invoice_rows,
            colWidths=[24 * mm, 34 * mm, 24 * mm, 28 * mm, 32 * mm, 32 * mm],
            repeatRows=1,
        )
        invoices_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_TABLE_HEADER_BG)),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor(PDF_BORDER_COLOR)),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        payment_header = ["Date", "Invoice #", "Method", "Reference", "Amount"]
        payment_rows: list[list[str]] = [payment_header]
        for payment in payments:
            payment_rows.append(
                [
                    str(payment.get("paid_on", "—")),
                    str(payment.get("invoice_number") or "—"),
                    str(payment.get("method", "—")).replace("_", " "),
                    str(payment.get("reference") or "—"),
                    format_inr_pdf(payment.get("amount", 0)),
                ]
            )

        payments_table = Table(
            payment_rows,
            colWidths=[24 * mm, 34 * mm, 28 * mm, 50 * mm, 32 * mm],
            repeatRows=1,
        )
        payments_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_TABLE_HEADER_BG)),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor(PDF_BORDER_COLOR)),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        summary_layout = Table(
            [[summary_table, aging_table]],
            colWidths=[74 * mm, 74 * mm],
        )
        summary_layout.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))

        story = [
            header_table,
            Spacer(1, 8),
            party_table,
            Spacer(1, 10),
            summary_layout,
            Spacer(1, 10),
            para("Open invoices", section_title),
            invoices_table,
            Spacer(1, 10),
            para("Payment history", section_title),
            payments_table,
        ]

        doc.build(story)
        return buffer.getvalue()
