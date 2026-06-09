"""GSTR-1 and GSTR-3B export reports derived from issued invoices."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.core.constants import (
    GSTR1_DISCLAIMER,
    GSTR3B_DISCLAIMER,
    GSTR_B2C_LARGE_THRESHOLD,
)
from app.domain.entities.invoice import Invoice
from app.domain.enums import DocumentType


class GstrReportService:
    def __init__(self, uow_factory) -> None:
        self._uow_factory = uow_factory

    async def gstr1_report(
        self, company_id: uuid.UUID, from_date: date, to_date: date
    ) -> dict:
        async with self._uow_factory() as uow:
            invoices = await uow.invoices.list_issued_in_period(company_id, from_date, to_date)
            customers = {}
            for inv in invoices:
                if inv.customer_id not in customers:
                    customer = await uow.customers.get_by_id(company_id, inv.customer_id)
                    customers[inv.customer_id] = customer

        b2b: list[dict] = []
        b2c_large: list[dict] = []
        b2c_small_by_rate: dict[str, dict] = {}
        hsn_summary: dict[str, dict] = {}

        for inv in invoices:
            customer = customers.get(inv.customer_id)
            signed = self._signed_amounts(inv)
            row = self._invoice_row(inv, customer, signed)

            if inv.document_type == DocumentType.CREDIT_NOTE:
                self._apply_credit_to_summaries(row, b2c_small_by_rate, hsn_summary, inv)
                continue

            gstin = customer.gstin.value if customer and customer.gstin else None
            if gstin:
                b2b.append(row)
            elif abs(signed["taxable"]) >= GSTR_B2C_LARGE_THRESHOLD:
                b2c_large.append(row)
            else:
                rate_key = self._dominant_rate(inv)
                bucket = b2c_small_by_rate.setdefault(
                    rate_key,
                    {
                        "place_of_supply": inv.place_of_supply or "",
                        "rate": rate_key,
                        "taxable_value": Decimal("0"),
                        "cgst": Decimal("0"),
                        "sgst": Decimal("0"),
                        "igst": Decimal("0"),
                        "invoice_count": 0,
                    },
                )
                bucket["taxable_value"] += signed["taxable"]
                bucket["cgst"] += signed["cgst"]
                bucket["sgst"] += signed["sgst"]
                bucket["igst"] += signed["igst"]
                bucket["invoice_count"] += 1

            for item in inv.items:
                hsn = item.hsn_sac or "NA"
                entry = hsn_summary.setdefault(
                    hsn,
                    {
                        "hsn_sac": hsn,
                        "description": item.description[:50],
                        "uqc": item.unit,
                        "total_quantity": Decimal("0"),
                        "taxable_value": Decimal("0"),
                        "cgst": Decimal("0"),
                        "sgst": Decimal("0"),
                        "igst": Decimal("0"),
                    },
                )
                qty_sign = Decimal("-1") if inv.document_type is DocumentType.CREDIT_NOTE else Decimal("1")
                entry["total_quantity"] += item.quantity * qty_sign
                entry["taxable_value"] += item.taxable_amount.amount * qty_sign
                entry["cgst"] += item.cgst_amount.amount * qty_sign
                entry["sgst"] += item.sgst_amount.amount * qty_sign
                entry["igst"] += item.igst_amount.amount * qty_sign

        return {
            "from_date": str(from_date),
            "to_date": str(to_date),
            "metadata": {
                "disclaimer": GSTR1_DISCLAIMER,
                "invoice_count": len(invoices),
            },
            "b2b": b2b,
            "b2c_large": b2c_large,
            "b2c_small": list(b2c_small_by_rate.values()),
            "hsn_summary": list(hsn_summary.values()),
        }

    async def gstr3b_report(
        self, company_id: uuid.UUID, from_date: date, to_date: date
    ) -> dict:
        async with self._uow_factory() as uow:
            invoices = await uow.invoices.list_issued_in_period(company_id, from_date, to_date)

        outward_taxable = Decimal("0")
        cgst = Decimal("0")
        sgst = Decimal("0")
        igst = Decimal("0")
        credit_note_count = 0
        invoice_count = 0

        for inv in invoices:
            signed = self._signed_amounts(inv)
            outward_taxable += signed["taxable"]
            cgst += signed["cgst"]
            sgst += signed["sgst"]
            igst += signed["igst"]
            if inv.document_type == DocumentType.CREDIT_NOTE:
                credit_note_count += 1
            else:
                invoice_count += 1

        total_tax = cgst + sgst + igst
        return {
            "from_date": str(from_date),
            "to_date": str(to_date),
            "metadata": {
                "disclaimer": GSTR3B_DISCLAIMER,
                "invoice_count": invoice_count,
                "credit_note_count": credit_note_count,
                "includes_itc": False,
            },
            "outward_taxable": outward_taxable,
            "outward_cgst": cgst,
            "outward_sgst": sgst,
            "outward_igst": igst,
            "total_outward_tax": total_tax,
        }

    @staticmethod
    def _signed_amounts(inv: Invoice) -> dict[str, Decimal]:
        sign = Decimal("-1") if inv.document_type == DocumentType.CREDIT_NOTE else Decimal("1")
        return {
            "taxable": inv.taxable_amount.amount * sign,
            "cgst": inv.cgst_amount.amount * sign,
            "sgst": inv.sgst_amount.amount * sign,
            "igst": inv.igst_amount.amount * sign,
            "total": inv.grand_total.amount * sign,
        }

    @staticmethod
    def _invoice_row(inv: Invoice, customer, signed: dict[str, Decimal]) -> dict:
        return {
            "invoice_number": inv.invoice_number,
            "invoice_date": str(inv.issue_date),
            "document_type": str(inv.document_type),
            "customer_name": customer.name if customer else "",
            "customer_gstin": customer.gstin.value if customer and customer.gstin else "",
            "place_of_supply": inv.place_of_supply or "",
            "taxable_value": float(signed["taxable"]),
            "cgst": float(signed["cgst"]),
            "sgst": float(signed["sgst"]),
            "igst": float(signed["igst"]),
            "invoice_value": float(signed["total"]),
        }

    @staticmethod
    def _dominant_rate(inv: Invoice) -> str:
        if not inv.items:
            return "0"
        top = max(inv.items, key=lambda i: i.taxable_amount.amount)
        return str(top.gst_rate)

    @staticmethod
    def _apply_credit_to_summaries(
        row: dict,
        b2c_small_by_rate: dict,
        hsn_summary: dict,
        inv: Invoice,
    ) -> None:
        rate_key = GstrReportService._dominant_rate(inv)
        bucket = b2c_small_by_rate.setdefault(
            rate_key,
            {
                "place_of_supply": inv.place_of_supply or "",
                "rate": rate_key,
                "taxable_value": Decimal("0"),
                "cgst": Decimal("0"),
                "sgst": Decimal("0"),
                "igst": Decimal("0"),
                "invoice_count": 0,
            },
        )
        bucket["taxable_value"] += Decimal(str(row["taxable_value"]))
        bucket["cgst"] += Decimal(str(row["cgst"]))
        bucket["sgst"] += Decimal(str(row["sgst"]))
        bucket["igst"] += Decimal(str(row["igst"]))
