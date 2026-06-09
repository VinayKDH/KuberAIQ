"""Quotation use-case orchestration."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.application.ports.pdf import PdfGeneratorPort
from app.application.ports.storage import StoragePort
from app.application.services.invoice_service import CreateInvoiceInput, InvoiceItemInput, InvoiceService
from app.core.constants import (
    BLOB_QUOTATION_PREFIX,
    DEFAULT_QUOTATION_PREFIX,
    DEFAULT_UNIT,
    PDF_SIGNED_URL_TTL_SECONDS,
    AuditAction,
    EntityType,
    ErrorCode,
)
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.domain.entities.quotation import Quotation, QuotationItem
from app.domain.enums import InvoiceStatus, QuotationStatus
from app.domain.exceptions import DomainError, InvalidStateTransition
from app.domain.services.invoice_numbering import financial_year
from app.domain.value_objects.money import Money


@dataclass
class QuotationItemInput:
    description: str
    quantity: Decimal
    unit_price: Decimal
    gst_rate: Decimal
    hsn_sac: str | None = None
    unit: str = DEFAULT_UNIT
    product_id: uuid.UUID | None = None


@dataclass
class CreateQuotationInput:
    customer_id: uuid.UUID
    issue_date: date
    valid_until: date
    items: list[QuotationItemInput]


@dataclass
class UpdateQuotationInput:
    customer_id: uuid.UUID | None = None
    issue_date: date | None = None
    valid_until: date | None = None
    items: list[QuotationItemInput] | None = None


class QuotationService:
    def __init__(
        self,
        uow_factory,
        storage: StoragePort,
        pdf: PdfGeneratorPort,
        invoice_service: InvoiceService,
    ) -> None:
        self._uow_factory = uow_factory
        self._storage = storage
        self._pdf = pdf
        self._invoice_service = invoice_service

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: CreateQuotationInput,
        ip: str | None = None,
    ) -> Quotation:
        async with self._uow_factory() as uow:
            customer = await uow.customers.get_by_id(company_id, data.customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            company = await uow.companies.get_by_id(company_id)
            if not company:
                raise NotFoundError("Company not found")
            if data.valid_until < data.issue_date:
                raise ValidationAppError("Valid until must be on or after issue date")
            items = await self._enrich_items_from_catalog(uow, company_id, data.items)
            quotation = Quotation(
                company_id=company_id,
                customer_id=data.customer_id,
                issue_date=data.issue_date,
                valid_until=data.valid_until,
                items=self._build_items(items),
                created_by=actor_id,
            )
            try:
                quotation.recalculate(
                    supplier_state=company.state_code,
                    customer_state=customer.state_code,
                )
            except DomainError as exc:
                raise ValidationAppError(str(exc)) from exc
            fy = financial_year(data.issue_date)
            number = await uow.quotations.allocate_number(
                company_id, fy, DEFAULT_QUOTATION_PREFIX
            )
            quotation.assign_number(number=number, fy=fy)
            saved = await uow.quotations.create(quotation)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.QUOTATION,
                entity_id=saved.id,
                action=AuditAction.CREATE,
                before=None,
                after={"quotation_number": saved.quotation_number},
                ip_address=ip,
            )
            return saved

    async def get(self, company_id: uuid.UUID, quotation_id: uuid.UUID) -> Quotation:
        async with self._uow_factory() as uow:
            quotation = await uow.quotations.get_by_id(company_id, quotation_id)
            if not quotation:
                raise NotFoundError("Quotation not found")
            return quotation

    async def search(
        self,
        company_id: uuid.UUID,
        *,
        q: str | None = None,
        status: QuotationStatus | None = None,
        customer_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Quotation], int]:
        async with self._uow_factory() as uow:
            return await uow.quotations.search(
                company_id,
                q=q,
                status=status,
                customer_id=customer_id,
                page=page,
                page_size=page_size,
            )

    async def update(
        self,
        *,
        company_id: uuid.UUID,
        quotation_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: UpdateQuotationInput,
        ip: str | None = None,
    ) -> Quotation:
        async with self._uow_factory() as uow:
            quotation = await uow.quotations.get_by_id(company_id, quotation_id)
            if not quotation:
                raise NotFoundError("Quotation not found")
            try:
                quotation.ensure_editable()
            except InvalidStateTransition as exc:
                raise ConflictError(str(exc), code=ErrorCode.INVALID_STATE_TRANSITION) from exc

            customer_id = data.customer_id or quotation.customer_id
            customer = await uow.customers.get_by_id(company_id, customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            company = await uow.companies.get_by_id(company_id)
            if not company:
                raise NotFoundError("Company not found")

            if data.customer_id:
                quotation.customer_id = data.customer_id
            if data.issue_date:
                quotation.issue_date = data.issue_date
            if data.valid_until:
                quotation.valid_until = data.valid_until
            if data.items is not None:
                enriched = await self._enrich_items_from_catalog(uow, company_id, data.items)
                quotation.items = self._build_items(enriched)
            try:
                quotation.recalculate(
                    supplier_state=company.state_code,
                    customer_state=customer.state_code,
                )
            except DomainError as exc:
                raise ValidationAppError(str(exc)) from exc

            saved = await uow.quotations.update(quotation)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.QUOTATION,
                entity_id=saved.id,
                action=AuditAction.UPDATE,
                before=None,
                after={"status": saved.status.value},
                ip_address=ip,
            )
            return saved

    async def send(
        self,
        *,
        company_id: uuid.UUID,
        quotation_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> Quotation:
        async with self._uow_factory() as uow:
            quotation = await uow.quotations.get_by_id(company_id, quotation_id)
            if not quotation:
                raise NotFoundError("Quotation not found")
            try:
                quotation.send()
            except InvalidStateTransition as exc:
                raise ConflictError(str(exc), code=ErrorCode.INVALID_STATE_TRANSITION) from exc
            saved = await uow.quotations.update(quotation)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.QUOTATION,
                entity_id=saved.id,
                action=AuditAction.UPDATE,
                before=None,
                after={"status": saved.status.value},
                ip_address=ip,
            )
            return saved

    async def convert_to_invoice(
        self,
        *,
        company_id: uuid.UUID,
        quotation_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> tuple[Quotation, object]:
        quotation = await self.get(company_id, quotation_id)
        if not quotation.can_convert():
            raise ConflictError(
                f"Quotation in status {quotation.status} cannot be converted",
                code=ErrorCode.INVALID_STATE_TRANSITION,
            )
        due_date = quotation.valid_until
        invoice = await self._invoice_service.create(
            company_id=company_id,
            actor_id=actor_id,
            data=CreateInvoiceInput(
                customer_id=quotation.customer_id,
                issue_date=date.today(),
                due_date=due_date,
                status=InvoiceStatus.DRAFT,
                items=[
                    InvoiceItemInput(
                        description=item.description,
                        quantity=item.quantity,
                        unit_price=item.unit_price.amount,
                        gst_rate=item.gst_rate,
                        hsn_sac=item.hsn_sac,
                        unit=item.unit,
                        product_id=item.product_id,
                    )
                    for item in quotation.items
                ],
            ),
            ip=ip,
        )
        issued = await self._invoice_service.issue(
            company_id=company_id,
            invoice_id=invoice.id,
            actor_id=actor_id,
            ip=ip,
        )
        async with self._uow_factory() as uow:
            quotation = await uow.quotations.get_by_id(company_id, quotation_id)
            if not quotation:
                raise NotFoundError("Quotation not found")
            quotation.mark_converted(issued.id)
            saved = await uow.quotations.update(quotation)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.QUOTATION,
                entity_id=saved.id,
                action=AuditAction.CONVERT,
                before=None,
                after={"invoice_id": str(issued.id)},
                ip_address=ip,
            )
        return saved, issued

    async def generate_pdf(
        self, company_id: uuid.UUID, quotation_id: uuid.UUID
    ) -> tuple[str, str]:
        async with self._uow_factory() as uow:
            quotation = await uow.quotations.get_by_id(company_id, quotation_id)
            if not quotation:
                raise NotFoundError("Quotation not found")
            company = await uow.companies.get_by_id(company_id)
            customer = await uow.customers.get_by_id(company_id, quotation.customer_id)
            if not company or not customer:
                raise NotFoundError("Company or customer not found")

        pdf_bytes = await self._pdf.generate_quotation_pdf(
            company={
                "legal_name": company.legal_name,
                "address": company.address,
                "gstin": company.gstin,
                "state_code": company.state_code,
            },
            customer={
                "name": customer.name,
                "billing_address": customer.billing_address,
                "gstin": customer.gstin.value if customer.gstin else None,
                "phone": customer.phone.value,
                "email": customer.email,
                "state_code": customer.state_code,
            },
            quotation=self._quotation_to_dict(quotation),
        )
        path = f"{BLOB_QUOTATION_PREFIX}/{company_id}/{quotation.id}.pdf"
        await self._storage.upload(path, pdf_bytes, content_type="application/pdf")
        async with self._uow_factory() as uow:
            quotation = await uow.quotations.get_by_id(company_id, quotation_id)
            if quotation:
                quotation.pdf_blob_path = path
                await uow.quotations.update(quotation)
        url = await self._storage.get_signed_url(path, PDF_SIGNED_URL_TTL_SECONDS)
        return path, url

    async def expire_overdue(self, company_id: uuid.UUID) -> int:
        today = date.today()
        async with self._uow_factory() as uow:
            candidates = await uow.quotations.list_expired_candidates(company_id, today)
            count = 0
            for quotation in candidates:
                try:
                    quotation.mark_expired()
                    await uow.quotations.update(quotation)
                    count += 1
                except InvalidStateTransition:
                    continue
            return count

    async def _enrich_items_from_catalog(
        self,
        uow,
        company_id: uuid.UUID,
        items: list[QuotationItemInput],
    ) -> list[QuotationItemInput]:
        invoice_items = [
            InvoiceItemInput(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                gst_rate=item.gst_rate,
                hsn_sac=item.hsn_sac,
                unit=item.unit,
                product_id=item.product_id,
            )
            for item in items
        ]
        enriched = await self._invoice_service._enrich_items_from_catalog(
            uow, company_id, invoice_items
        )
        return [
            QuotationItemInput(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                gst_rate=item.gst_rate,
                hsn_sac=item.hsn_sac,
                unit=item.unit,
                product_id=item.product_id,
            )
            for item in enriched
        ]

    @staticmethod
    def _build_items(items: list[QuotationItemInput]) -> list[QuotationItem]:
        if not items:
            raise ValidationAppError("At least one line item is required")
        return [
            QuotationItem(
                line_no=idx + 1,
                description=item.description,
                hsn_sac=item.hsn_sac,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=Money.of(item.unit_price),
                gst_rate=item.gst_rate,
                product_id=item.product_id,
            )
            for idx, item in enumerate(items)
        ]

    @staticmethod
    def _quotation_to_dict(quotation: Quotation) -> dict:
        return {
            "quotation_number": quotation.quotation_number,
            "issue_date": str(quotation.issue_date),
            "valid_until": str(quotation.valid_until),
            "status": quotation.status.value,
            "items": [
                {
                    "line_no": i.line_no,
                    "description": i.description,
                    "hsn_sac": i.hsn_sac,
                    "quantity": float(i.quantity),
                    "unit": i.unit,
                    "unit_price": float(i.unit_price.amount),
                    "gst_rate": float(i.gst_rate),
                    "taxable_amount": float(i.taxable_amount.amount),
                    "cgst_amount": float(i.cgst_amount.amount),
                    "sgst_amount": float(i.sgst_amount.amount),
                    "igst_amount": float(i.igst_amount.amount),
                    "line_total": float(i.line_total.amount),
                }
                for i in quotation.items
            ],
            "taxable_amount": float(quotation.taxable_amount.amount),
            "cgst_amount": float(quotation.cgst_amount.amount),
            "sgst_amount": float(quotation.sgst_amount.amount),
            "igst_amount": float(quotation.igst_amount.amount),
            "total_tax": float(quotation.total_tax.amount),
            "round_off": float(quotation.round_off.amount),
            "grand_total": float(quotation.grand_total.amount),
            "place_of_supply": quotation.place_of_supply,
        }
