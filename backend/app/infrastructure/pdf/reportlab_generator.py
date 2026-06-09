"""ReportLab PDF generator for GST-compliant tax invoices."""
from __future__ import annotations

import io
from typing import Any

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.constants import (
    PDF_ACCENT_COLOR,
    PDF_BORDER_COLOR,
    PDF_BRAND_COLOR,
    PDF_CREDIT_NOTE_FOOTER,
    PDF_CREDIT_NOTE_TITLE,
    PDF_FOOTER_TEXT,
    PDF_MUTED_COLOR,
    PDF_QUOTATION_FOOTER,
    PDF_QUOTATION_TITLE,
    PDF_TABLE_HEADER_BG,
    PDF_UPI_SECTION_TITLE,
    UPI_LINK_LABEL,
)
from app.domain.services.upi import build_upi_payment_link
from app.infrastructure.pdf.formatting import amount_to_words_inr, format_inr_pdf
from app.infrastructure.pdf.pdf_common import escape_xml, html_para, para, state_label
from app.infrastructure.pdf.statement_generator import StatementPdfGenerator


def _make_qr_image(link: str, size_mm: float = 28) -> RLImage:
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    size = size_mm * mm
    return RLImage(buf, width=size, height=size)


def _build_upi_section(
    *,
    company: dict[str, Any],
    invoice: dict[str, Any],
    body: ParagraphStyle,
    section_title: ParagraphStyle,
) -> list[Any]:
    upi_id = company.get("upi_id")
    if not upi_id:
        return []

    payee_name = company.get("upi_payee_name") or company.get("legal_name", "Merchant")
    invoice_number = invoice.get("invoice_number") or "Invoice"
    amount_due = invoice.get("amount_due", 0)
    link = build_upi_payment_link(
        upi_id=upi_id,
        payee_name=payee_name,
        amount=amount_due,
        transaction_note=f"Payment for {invoice_number}",
    )
    upi_text = html_para(
        f"<b>{PDF_UPI_SECTION_TITLE}</b><br/>"
        f"{escape_xml(UPI_LINK_LABEL)}<br/>"
        f"UPI ID: {escape_xml(upi_id)}<br/>"
        f"Amount: {escape_xml(format_inr_pdf(amount_due))}<br/>"
        f"<font size='7'>{escape_xml(link)}</font>",
        body,
    )
    upi_layout = Table(
        [[_make_qr_image(link), upi_text]],
        colWidths=[34 * mm, 144 * mm],
    )
    upi_layout.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PDF_TABLE_HEADER_BG)),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [Spacer(1, 10), para(PDF_UPI_SECTION_TITLE, section_title), upi_layout]


class ReportLabPdfGenerator:
    def __init__(self) -> None:
        self._statement = StatementPdfGenerator()

    async def generate_statement_pdf(
        self,
        *,
        company: dict[str, Any],
        customer: dict[str, Any],
        summary: dict[str, Any],
        invoices: list[dict[str, Any]],
        payments: list[dict[str, Any]],
    ) -> bytes:
        return await self._statement.generate_statement_pdf(
            company=company,
            customer=customer,
            summary=summary,
            invoices=invoices,
            payments=payments,
        )

    async def generate_invoice_pdf(
        self,
        *,
        company: dict[str, Any],
        customer: dict[str, Any],
        invoice: dict[str, Any],
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title=invoice.get("invoice_number") or "Tax Invoice",
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
        body_right = ParagraphStyle(
            "BodyRight",
            parent=body,
            alignment=TA_RIGHT,
        )
        invoice_title = ParagraphStyle(
            "InvoiceTitle",
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

        left_header = html_para(
            f"<b><font size='14'>{company_name}</font></b><br/>{'<br/>'.join(company_details)}",
            subtitle,
        )
        header_data = [[left_header, para(invoice.get("document_title", "TAX INVOICE"), invoice_title)]]
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

        inv_number = invoice.get("invoice_number") or "DRAFT"
        meta_rows = [
            ["Invoice No.", inv_number],
            ["Invoice Date", str(invoice.get("issue_date", "—"))],
            ["Due Date", str(invoice.get("due_date", "—"))],
            ["Status", str(invoice.get("status", "—")).replace("_", " ")],
        ]
        if invoice.get("credit_reason"):
            meta_rows.insert(1, ["Credit Reason", str(invoice["credit_reason"])[:80]])

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
        customer_lines.append(f"State: {escape_xml(state_label(customer.get('state_code')))}")

        party_data = [
            [
                para("Bill To", section_title),
                para("Invoice Details", section_title),
            ],
            [
                html_para("<br/>".join(customer_lines), body),
                Table(
                    meta_rows,
                    colWidths=[28 * mm, 40 * mm],
                    style=TableStyle(
                        [
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor(PDF_MUTED_COLOR)),
                            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    ),
                ),
            ],
        ]
        party_table = Table(party_data, colWidths=[89 * mm, 89 * mm])
        party_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_TABLE_HEADER_BG)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor(PDF_BORDER_COLOR)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        item_header = [
            "#",
            "Description",
            "HSN/SAC",
            "Qty",
            "Unit",
            "Rate",
            "GST%",
            "Taxable",
            "Amount",
        ]
        item_rows: list[list[str]] = [item_header]
        for item in invoice.get("items", []):
            item_rows.append(
                [
                    str(item.get("line_no", "")),
                    str(item.get("description", ""))[:48],
                    str(item.get("hsn_sac") or "—"),
                    f"{item.get('quantity', 0):g}",
                    str(item.get("unit") or "NOS"),
                    format_inr_pdf(item.get("unit_price", 0)),
                    f"{item.get('gst_rate', 0):g}%",
                    format_inr_pdf(item.get("taxable_amount", 0)),
                    format_inr_pdf(item.get("line_total", 0)),
                ]
            )

        items_table = Table(
            item_rows,
            colWidths=[8 * mm, 48 * mm, 18 * mm, 12 * mm, 12 * mm, 20 * mm, 12 * mm, 22 * mm, 22 * mm],
            repeatRows=1,
        )
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_TABLE_HEADER_BG)),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (3, 0), (6, -1), "CENTER"),
                    ("ALIGN", (5, 1), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor(PDF_BORDER_COLOR)),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                ]
            )
        )

        cgst = float(invoice.get("cgst_amount", 0))
        sgst = float(invoice.get("sgst_amount", 0))
        igst = float(invoice.get("igst_amount", 0))
        tax_rows = [["Taxable Value", format_inr_pdf(invoice.get("taxable_amount", 0))]]
        if cgst > 0 or sgst > 0:
            tax_rows.append(["CGST", format_inr_pdf(cgst)])
            tax_rows.append(["SGST", format_inr_pdf(sgst)])
        if igst > 0:
            tax_rows.append(["IGST", format_inr_pdf(igst)])
        tax_rows.append(["Total Tax", format_inr_pdf(invoice.get("total_tax", 0))])
        round_off = float(invoice.get("round_off", 0))
        if round_off:
            tax_rows.append(["Round Off", format_inr_pdf(round_off)])
        tax_rows.append(["Grand Total", format_inr_pdf(invoice.get("grand_total", 0))])
        tax_rows.append(["Amount Due", format_inr_pdf(invoice.get("amount_due", 0))])

        tax_table = Table(tax_rows, colWidths=[42 * mm, 32 * mm])
        tax_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
                    ("FONTNAME", (1, 0), (1, -2), "Helvetica"),
                    ("FONTNAME", (0, -2), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor(PDF_MUTED_COLOR)),
                    ("LINEABOVE", (0, -2), (-1, -2), 0.75, colors.HexColor(PDF_BORDER_COLOR)),
                    ("BACKGROUND", (0, -2), (-1, -1), colors.HexColor(PDF_TABLE_HEADER_BG)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        summary_layout = Table(
            [[Spacer(1, 1), tax_table]],
            colWidths=[105 * mm, 74 * mm],
        )
        summary_layout.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT")]))

        words = amount_to_words_inr(invoice.get("grand_total", 0))
        amount_words = html_para(f"<b>Amount in words:</b> {escape_xml(words)}", body)

        footer_text = PDF_FOOTER_TEXT
        if invoice.get("document_title") == PDF_CREDIT_NOTE_TITLE:
            footer_text = PDF_CREDIT_NOTE_FOOTER
        footer = para(footer_text, subtitle)
        upi_section: list[Any] = []
        if invoice.get("document_type") != "CREDIT_NOTE":
            upi_section = _build_upi_section(
                company=company,
                invoice=invoice,
                body=body,
                section_title=section_title,
            )

        story = [
            header_table,
            Spacer(1, 8),
            party_table,
            Spacer(1, 10),
            items_table,
            Spacer(1, 10),
            summary_layout,
            Spacer(1, 8),
            amount_words,
            *upi_section,
            Spacer(1, 12),
            footer,
        ]

        doc.build(story)
        return buffer.getvalue()

    async def generate_quotation_pdf(
        self,
        *,
        company: dict[str, Any],
        customer: dict[str, Any],
        quotation: dict[str, Any],
    ) -> bytes:
        payload = {
            **quotation,
            "document_title": PDF_QUOTATION_TITLE,
            "document_type": "QUOTATION",
            "invoice_number": quotation.get("quotation_number"),
            "due_date": quotation.get("valid_until"),
            "amount_due": quotation.get("grand_total", 0),
        }
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title=quotation.get("quotation_number") or "Quotation",
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
        invoice_title = ParagraphStyle(
            "InvoiceTitle",
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
        left_header = html_para(
            f"<b><font size='14'>{company_name}</font></b><br/>{'<br/>'.join(company_details)}",
            subtitle,
        )
        header_data = [[left_header, para(PDF_QUOTATION_TITLE, invoice_title)]]
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
        meta_rows = [
            ["Quotation No.", payload.get("invoice_number") or "DRAFT"],
            ["Date", str(payload.get("issue_date", "—"))],
            ["Valid Until", str(payload.get("due_date", "—"))],
            ["Status", str(payload.get("status", "—")).replace("_", " ")],
        ]
        customer_lines = [f"<b>{escape_xml(customer.get('name', ''))}</b>"]
        if customer.get("billing_address"):
            customer_lines.append(escape_xml(str(customer["billing_address"])))
        if customer.get("gstin"):
            customer_lines.append(f"GSTIN: {escape_xml(str(customer['gstin']))}")
        if customer.get("phone"):
            customer_lines.append(f"Phone: {escape_xml(str(customer['phone']))}")
        customer_lines.append(f"State: {escape_xml(state_label(customer.get('state_code')))}")
        party_data = [
            [para("Quote For", section_title), para("Quotation Details", section_title)],
            [
                html_para("<br/>".join(customer_lines), body),
                Table(
                    meta_rows,
                    colWidths=[28 * mm, 40 * mm],
                    style=TableStyle(
                        [
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ]
                    ),
                ),
            ],
        ]
        party_table = Table(party_data, colWidths=[89 * mm, 89 * mm])
        party_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        item_header = ["#", "Description", "HSN/SAC", "Qty", "Unit", "Rate", "GST%", "Amount"]
        item_rows: list[list[str]] = [item_header]
        for item in payload.get("items", []):
            item_rows.append(
                [
                    str(item.get("line_no", "")),
                    str(item.get("description", ""))[:48],
                    str(item.get("hsn_sac") or "—"),
                    f"{item.get('quantity', 0):g}",
                    str(item.get("unit") or "NOS"),
                    format_inr_pdf(item.get("unit_price", 0)),
                    f"{item.get('gst_rate', 0):g}%",
                    format_inr_pdf(item.get("line_total", 0)),
                ]
            )
        items_table = Table(
            item_rows,
            colWidths=[8 * mm, 58 * mm, 18 * mm, 12 * mm, 12 * mm, 22 * mm, 12 * mm, 24 * mm],
            repeatRows=1,
        )
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_TABLE_HEADER_BG)),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(PDF_BORDER_COLOR)),
                ]
            )
        )
        tax_rows = [
            ["Taxable Value", format_inr_pdf(payload.get("taxable_amount", 0))],
            ["Total Tax", format_inr_pdf(payload.get("total_tax", 0))],
            ["Grand Total", format_inr_pdf(payload.get("grand_total", 0))],
        ]
        tax_table = Table(tax_rows, colWidths=[42 * mm, 32 * mm])
        tax_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story = [
            header_table,
            Spacer(1, 8),
            party_table,
            Spacer(1, 10),
            items_table,
            Spacer(1, 10),
            Table([[Spacer(1, 1), tax_table]], colWidths=[105 * mm, 74 * mm]),
            Spacer(1, 12),
            para(PDF_QUOTATION_FOOTER, subtitle),
        ]
        doc.build(story)
        return buffer.getvalue()
