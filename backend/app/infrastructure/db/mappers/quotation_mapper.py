"""ORM ↔ domain mapping for Quotation aggregate."""
from __future__ import annotations

from decimal import Decimal

from app.domain.entities.quotation import Quotation, QuotationItem
from app.domain.value_objects.money import Money
from app.infrastructure.db.models.quotation import QuotationItemModel, QuotationModel


class QuotationMapper:
    @staticmethod
    def to_domain(model: QuotationModel) -> Quotation:
        items = [
            QuotationItem(
                line_no=item.line_no,
                description=item.description,
                hsn_sac=item.hsn_sac,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=Money.of(item.unit_price),
                gst_rate=item.gst_rate,
                product_id=item.product_id,
                taxable_amount=Money.of(item.taxable_amount),
                cgst_amount=Money.of(item.cgst_amount),
                sgst_amount=Money.of(item.sgst_amount),
                igst_amount=Money.of(item.igst_amount),
            )
            for item in sorted(model.items, key=lambda i: i.line_no)
        ]
        return Quotation(
            id=model.id,
            company_id=model.company_id,
            customer_id=model.customer_id,
            quotation_number=model.quotation_number,
            financial_year=model.financial_year,
            status=model.status,
            issue_date=model.issue_date,
            valid_until=model.valid_until,
            items=items,
            place_of_supply=model.place_of_supply,
            pdf_blob_path=model.pdf_blob_path,
            converted_invoice_id=model.converted_invoice_id,
            created_by=model.created_by,
            taxable_amount=Money.of(model.taxable_amount),
            cgst_amount=Money.of(model.cgst_amount),
            sgst_amount=Money.of(model.sgst_amount),
            igst_amount=Money.of(model.igst_amount),
            total_tax=Money.of(model.total_tax),
            round_off=Money.of(model.round_off),
            grand_total=Money.of(model.grand_total),
        )

    @staticmethod
    def to_model(entity: Quotation) -> QuotationModel:
        model = QuotationModel(
            id=entity.id,
            company_id=entity.company_id,
            customer_id=entity.customer_id,
            quotation_number=entity.quotation_number,
            financial_year=entity.financial_year,
            status=entity.status,
            issue_date=entity.issue_date,
            valid_until=entity.valid_until,
            taxable_amount=entity.taxable_amount.amount,
            cgst_amount=entity.cgst_amount.amount,
            sgst_amount=entity.sgst_amount.amount,
            igst_amount=entity.igst_amount.amount,
            total_tax=entity.total_tax.amount,
            round_off=entity.round_off.amount,
            grand_total=entity.grand_total.amount,
            place_of_supply=entity.place_of_supply,
            pdf_blob_path=entity.pdf_blob_path,
            converted_invoice_id=entity.converted_invoice_id,
            created_by=entity.created_by,
        )
        model.items = [
            QuotationMapper._item_to_model(entity.id, item) for item in entity.items
        ]
        return model

    @staticmethod
    def update_model(model: QuotationModel, entity: Quotation) -> None:
        model.customer_id = entity.customer_id
        model.quotation_number = entity.quotation_number
        model.financial_year = entity.financial_year
        model.status = entity.status
        model.issue_date = entity.issue_date
        model.valid_until = entity.valid_until
        model.taxable_amount = entity.taxable_amount.amount
        model.cgst_amount = entity.cgst_amount.amount
        model.sgst_amount = entity.sgst_amount.amount
        model.igst_amount = entity.igst_amount.amount
        model.total_tax = entity.total_tax.amount
        model.round_off = entity.round_off.amount
        model.grand_total = entity.grand_total.amount
        model.place_of_supply = entity.place_of_supply
        model.pdf_blob_path = entity.pdf_blob_path
        model.converted_invoice_id = entity.converted_invoice_id

        existing_by_line = {item.line_no: item for item in model.items}
        entity_line_nos = {item.line_no for item in entity.items}

        for line_no in list(existing_by_line):
            if line_no not in entity_line_nos:
                model.items.remove(existing_by_line[line_no])

        for item in entity.items:
            existing = existing_by_line.get(item.line_no)
            if existing is not None:
                existing.description = item.description
                existing.hsn_sac = item.hsn_sac
                existing.quantity = item.quantity
                existing.unit = item.unit
                existing.unit_price = item.unit_price.amount
                existing.gst_rate = Decimal(str(item.gst_rate))
                existing.product_id = item.product_id
                existing.taxable_amount = item.taxable_amount.amount
                existing.cgst_amount = item.cgst_amount.amount
                existing.sgst_amount = item.sgst_amount.amount
                existing.igst_amount = item.igst_amount.amount
                existing.line_total = item.line_total.amount
            else:
                model.items.append(QuotationMapper._item_to_model(entity.id, item))

    @staticmethod
    def _item_to_model(quotation_id, item: QuotationItem) -> QuotationItemModel:
        return QuotationItemModel(
            quotation_id=quotation_id,
            line_no=item.line_no,
            description=item.description,
            hsn_sac=item.hsn_sac,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price.amount,
            gst_rate=Decimal(str(item.gst_rate)),
            product_id=item.product_id,
            taxable_amount=item.taxable_amount.amount,
            cgst_amount=item.cgst_amount.amount,
            sgst_amount=item.sgst_amount.amount,
            igst_amount=item.igst_amount.amount,
            line_total=item.line_total.amount,
        )
