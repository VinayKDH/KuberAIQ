"""Invoice use-case orchestration."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.application.ports.notifier import NotifierPort
from app.application.ports.pdf import PdfGeneratorPort
from app.application.ports.storage import StoragePort
from app.core.constants import (
    BLOB_INVOICE_PREFIX,
    DEFAULT_CREDIT_NOTE_PREFIX,
    DEFAULT_UNIT,
    PDF_SIGNED_URL_TTL_SECONDS,
    WHATSAPP_TEMPLATE_INVOICE_SHARE,
    AuditAction,
    EntityType,
    ErrorCode,
)
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.domain.entities.invoice import Invoice, InvoiceItem
from app.domain.enums import DocumentType, InvoiceStatus, ReminderChannel
from app.domain.exceptions import (
    DomainError,
    InvalidGstRate,
    InvoiceHasPayments,
    InvoiceNotEditable,
    InvalidStateTransition,
    PaymentExceedsDue,
)
from app.domain.services.hsn_gst_lookup import suggest_hsn_from_name
from app.domain.services.invoice_numbering import financial_year
from app.domain.value_objects.money import Money
from app.infrastructure.billing.razorpay_client import RazorpayClient


@dataclass
class InvoiceItemInput:
    description: str
    quantity: Decimal
    unit_price: Decimal
    gst_rate: Decimal
    hsn_sac: str | None = None
    unit: str = DEFAULT_UNIT
    product_id: uuid.UUID | None = None


@dataclass
class CreateCreditNoteInput:
    reason: str
    items: list[InvoiceItemInput] | None = None


@dataclass
class CreateInvoiceInput:
    customer_id: uuid.UUID
    issue_date: date
    due_date: date
    items: list[InvoiceItemInput]
    status: InvoiceStatus = InvoiceStatus.DRAFT


@dataclass
class UpdateInvoiceInput:
    customer_id: uuid.UUID | None = None
    issue_date: date | None = None
    due_date: date | None = None
    items: list[InvoiceItemInput] | None = None


class InvoiceService:
    def __init__(
        self,
        uow_factory,
        storage: StoragePort,
        pdf: PdfGeneratorPort,
        notifier: NotifierPort,
    ) -> None:
        self._uow_factory = uow_factory
        self._storage = storage
        self._pdf = pdf
        self._notifier = notifier

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: CreateInvoiceInput,
        ip: str | None = None,
    ) -> Invoice:
        async with self._uow_factory() as uow:
            customer = await uow.customers.get_by_id(company_id, data.customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            company = await uow.companies.get_by_id(company_id)
            if not company:
                raise NotFoundError("Company not found")
            try:
                items = await self._enrich_items_from_catalog(uow, company_id, data.items)
                invoice = self._build_invoice(
                    company_id=company_id,
                    customer_id=data.customer_id,
                    issue_date=data.issue_date,
                    due_date=data.due_date,
                    items=items,
                    created_by=actor_id,
                )
                invoice.recalculate(
                    supplier_state=company.state_code,
                    customer_state=customer.state_code,
                )
            except DomainError as exc:
                raise ValidationAppError(str(exc)) from exc

            if data.status == InvoiceStatus.ISSUED:
                fy = financial_year(data.issue_date)
                number = await uow.invoices.allocate_number(
                    company_id, fy, company.invoice_prefix
                )
                invoice.issue(number=number, fy=fy)

            saved = await uow.invoices.create(invoice)
            if saved.status == InvoiceStatus.ISSUED:
                await self._decrement_stock_for_invoice(
                    uow,
                    company_id=company_id,
                    invoice=saved,
                    actor_id=actor_id,
                )
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.INVOICE,
                entity_id=saved.id,
                action=AuditAction.CREATE if saved.status == InvoiceStatus.DRAFT else AuditAction.ISSUE,
                before=None,
                after={"invoice_number": saved.invoice_number, "status": saved.status},
                ip_address=ip,
            )
            return saved

    async def get(self, company_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            return invoice

    async def update(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: UpdateInvoiceInput,
        ip: str | None = None,
    ) -> Invoice:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            try:
                invoice.ensure_editable()
            except InvoiceNotEditable as exc:
                raise ConflictError(str(exc), code=ErrorCode.INVOICE_NOT_EDITABLE) from exc

            customer_id = data.customer_id or invoice.customer_id
            customer = await uow.customers.get_by_id(company_id, customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            company = await uow.companies.get_by_id(company_id)
            if not company:
                raise NotFoundError("Company not found")

            if data.customer_id:
                invoice.customer_id = data.customer_id
            if data.issue_date:
                invoice.issue_date = data.issue_date
            if data.due_date:
                invoice.due_date = data.due_date
            if data.items is not None:
                enriched = await self._enrich_items_from_catalog(uow, company_id, data.items)
                invoice.items = self._build_items(enriched)
            try:
                invoice.recalculate(
                    supplier_state=company.state_code,
                    customer_state=customer.state_code,
                )
            except DomainError as exc:
                raise ValidationAppError(str(exc)) from exc

            saved = await uow.invoices.update(invoice)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.INVOICE,
                entity_id=saved.id,
                action=AuditAction.UPDATE,
                before=None,
                after={"status": saved.status},
                ip_address=ip,
            )
            return saved

    async def issue(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> Invoice:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            company = await uow.companies.get_by_id(company_id)
            if not company:
                raise NotFoundError("Company not found")
            try:
                fy = financial_year(invoice.issue_date)
                number = await uow.invoices.allocate_number(
                    company_id, fy, company.invoice_prefix
                )
                invoice.issue(number=number, fy=fy)
            except InvalidStateTransition as exc:
                raise ConflictError(str(exc), code=ErrorCode.INVALID_STATE_TRANSITION) from exc
            saved = await uow.invoices.update(invoice)
            await self._decrement_stock_for_invoice(
                uow,
                company_id=company_id,
                invoice=saved,
                actor_id=actor_id,
            )
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.INVOICE,
                entity_id=saved.id,
                action=AuditAction.ISSUE,
                before=None,
                after={"invoice_number": saved.invoice_number},
                ip_address=ip,
            )
            return saved

    async def create_credit_note(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: CreateCreditNoteInput,
        ip: str | None = None,
    ) -> Invoice:
        if not data.reason.strip():
            raise ValidationAppError("Credit note reason is required")
        async with self._uow_factory() as uow:
            original = await uow.invoices.get_by_id(company_id, invoice_id)
            if not original:
                raise NotFoundError("Invoice not found")
            if original.document_type != DocumentType.INVOICE:
                raise ValidationAppError("Credit notes can only be issued against tax invoices")
            if original.status in {InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED, InvoiceStatus.PAID}:
                raise ConflictError(
                    f"Cannot issue credit note against {original.status} invoice",
                    code=ErrorCode.INVALID_STATE_TRANSITION,
                )
            customer = await uow.customers.get_by_id(company_id, original.customer_id)
            company = await uow.companies.get_by_id(company_id)
            if not customer or not company:
                raise NotFoundError("Customer or company not found")

            if data.items:
                items_input = data.items
            else:
                items_input = [
                    InvoiceItemInput(
                        description=item.description,
                        quantity=item.quantity,
                        unit_price=item.unit_price.amount,
                        gst_rate=item.gst_rate,
                        hsn_sac=item.hsn_sac,
                        unit=item.unit,
                        product_id=item.product_id,
                    )
                    for item in original.items
                ]

            credit_note = Invoice(
                company_id=company_id,
                customer_id=original.customer_id,
                issue_date=date.today(),
                due_date=date.today(),
                items=self._build_items(items_input),
                created_by=actor_id,
                document_type=DocumentType.CREDIT_NOTE,
                original_invoice_id=original.id,
                credit_reason=data.reason.strip(),
            )
            try:
                credit_note.recalculate(
                    supplier_state=company.state_code,
                    customer_state=customer.state_code,
                )
                original.apply_credit(credit_note.grand_total)
            except DomainError as exc:
                code = ErrorCode.VALIDATION_ERROR
                if isinstance(exc, InvalidStateTransition):
                    code = ErrorCode.INVALID_STATE_TRANSITION
                elif isinstance(exc, PaymentExceedsDue):
                    code = ErrorCode.PAYMENT_EXCEEDS_DUE
                raise ValidationAppError(str(exc), code=code) from exc

            fy = financial_year(credit_note.issue_date)
            number = await uow.invoices.allocate_number(
                company_id, f"CN:{fy}", DEFAULT_CREDIT_NOTE_PREFIX
            )
            credit_note.issue(number=number, fy=fy)

            saved = await uow.invoices.create(credit_note)
            await uow.invoices.update(original)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.CREDIT_NOTE,
                entity_id=saved.id,
                action=AuditAction.ISSUE,
                before=None,
                after={
                    "credit_note_number": saved.invoice_number,
                    "original_invoice_id": str(original.id),
                    "amount": str(saved.grand_total.amount),
                },
                ip_address=ip,
            )
            return saved

    async def list_credit_notes(
        self, company_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> list[Invoice]:
        async with self._uow_factory() as uow:
            return await uow.invoices.list_credit_notes_for_invoice(company_id, invoice_id)

    async def cancel(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        reason: str,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> Invoice:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            try:
                invoice.cancel(reason)
            except (InvoiceHasPayments, InvalidStateTransition) as exc:
                code = (
                    ErrorCode.INVOICE_HAS_PAYMENTS
                    if isinstance(exc, InvoiceHasPayments)
                    else ErrorCode.INVALID_STATE_TRANSITION
                )
                raise ConflictError(str(exc), code=code) from exc
            saved = await uow.invoices.update(invoice)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.INVOICE,
                entity_id=saved.id,
                action=AuditAction.CANCEL,
                before=None,
                after={"reason": reason},
                ip_address=ip,
            )
            return saved

    async def search(self, company_id: uuid.UUID, **kwargs) -> tuple[list[Invoice], int]:
        async with self._uow_factory() as uow:
            return await uow.invoices.search(company_id, **kwargs)

    async def generate_pdf(
        self, company_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> tuple[str, str]:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            company = await uow.companies.get_by_id(company_id)
            customer = await uow.customers.get_by_id(company_id, invoice.customer_id)
            if not company or not customer:
                raise NotFoundError("Company or customer not found")

            pdf_data = await self._pdf.generate_invoice_pdf(
                company={
                    "legal_name": company.legal_name,
                    "gstin": company.gstin,
                    "state_code": company.state_code,
                    "address": company.address,
                    "upi_id": company.upi_id,
                    "upi_payee_name": company.upi_payee_name,
                },
                customer={
                    "name": customer.name,
                    "gstin": customer.gstin.value if customer.gstin else None,
                    "state_code": customer.state_code,
                    "phone": customer.phone.value,
                    "email": customer.email,
                    "billing_address": customer.billing_address,
                },
                invoice=self._invoice_to_dict(invoice),
            )
            path = f"{BLOB_INVOICE_PREFIX}/{company_id}/{invoice.id}.pdf"
            await self._storage.upload(path, pdf_data, "application/pdf")
            invoice.pdf_blob_path = path
            await uow.invoices.update(invoice)
            url = await self._storage.get_signed_url(path, PDF_SIGNED_URL_TTL_SECONDS)
            return path, url

    async def download_pdf_bytes(
        self, company_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> tuple[bytes, str]:
        path, _ = await self.generate_pdf(company_id, invoice_id)
        data = await self._storage.download(path)
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            filename = f"{invoice.invoice_number or invoice.id}.pdf"
        return data, filename

    async def share_whatsapp(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> str:
        path, url = await self.generate_pdf(company_id, invoice_id)
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            customer = await uow.customers.get_by_id(company_id, invoice.customer_id)
            if not invoice or not customer:
                raise NotFoundError("Invoice or customer not found")
            message = (
                f"Invoice {invoice.invoice_number} from KuberAIQ. "
                f"Amount due: ₹{invoice.amount_due.amount}. PDF: {url}"
            )
            provider_id = await self._notifier.send_message(
                channel=ReminderChannel.WHATSAPP,
                to=customer.phone.e164,
                message=message,
                template_name=WHATSAPP_TEMPLATE_INVOICE_SHARE,
            )
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.INVOICE,
                entity_id=invoice_id,
                action=AuditAction.REMINDER_SENT,
                before=None,
                after={"pdf_path": path, "provider_id": provider_id},
                ip_address=ip,
            )
            return provider_id

    async def register_irn(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        irn: str,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> Invoice:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            try:
                invoice.register_irn(irn)
            except (InvalidStateTransition, ValueError) as exc:
                code = (
                    ErrorCode.INVALID_STATE_TRANSITION
                    if isinstance(exc, InvalidStateTransition)
                    else ErrorCode.VALIDATION_ERROR
                )
                raise ValidationAppError(str(exc), code=code) from exc
            saved = await uow.invoices.update(invoice)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.INVOICE,
                entity_id=saved.id,
                action=AuditAction.UPDATE,
                before=None,
                after={"irn": saved.irn},
                ip_address=ip,
            )
            return saved

    async def create_payment_link(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> dict:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            customer = await uow.customers.get_by_id(company_id, invoice.customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            if invoice.amount_due.amount <= 0:
                raise ConflictError("Invoice has no outstanding amount", code=ErrorCode.CONFLICT)
            if invoice.payment_link_url:
                return {"url": invoice.payment_link_url, "provider": "razorpay"}

            if self._is_mock_billing_mode():
                invoice.payment_link_url = (
                    f"https://payments.mock.kuberaiq.com/invoice/{invoice.id}?amount={invoice.amount_due.amount}"
                )
            else:
                client = RazorpayClient()
                data = await client.create_payment_link(
                    amount_paise=int(invoice.amount_due.amount * 100),
                    customer_name=customer.name,
                    customer_email=customer.email,
                    customer_contact=customer.phone.e164.lstrip("+"),
                    reference_id=f"inv-{invoice.id}",
                    description=f"Payment for invoice {invoice.invoice_number or invoice.id}",
                )
                invoice.payment_link_url = data.get("short_url") or data.get("payment_link")
            await uow.invoices.update(invoice)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.INVOICE,
                entity_id=invoice.id,
                action=AuditAction.UPDATE,
                before=None,
                after={"payment_link_url": invoice.payment_link_url},
                ip_address=ip,
            )
            return {"url": invoice.payment_link_url, "provider": "razorpay"}

    async def gst_report(
        self, company_id: uuid.UUID, from_date: date, to_date: date
    ) -> dict:
        async with self._uow_factory() as uow:
            invoices, _ = await uow.invoices.search(
                company_id,
                from_date=from_date,
                to_date=to_date,
                status=InvoiceStatus.ISSUED,
                page=1,
                page_size=10000,
            )
            for status in (InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.PAID, InvoiceStatus.OVERDUE):
                more, _ = await uow.invoices.search(
                    company_id,
                    from_date=from_date,
                    to_date=to_date,
                    status=status,
                    page=1,
                    page_size=10000,
                )
                invoices.extend(more)
            return {
                "taxable_amount": sum((i.taxable_amount.amount for i in invoices), Decimal("0")),
                "cgst_amount": sum((i.cgst_amount.amount for i in invoices), Decimal("0")),
                "sgst_amount": sum((i.sgst_amount.amount for i in invoices), Decimal("0")),
                "igst_amount": sum((i.igst_amount.amount for i in invoices), Decimal("0")),
                "total_tax": sum((i.total_tax.amount for i in invoices), Decimal("0")),
                "grand_total": sum((i.grand_total.amount for i in invoices), Decimal("0")),
                "invoice_count": len(invoices),
            }

    async def _enrich_items_from_catalog(
        self,
        uow,
        company_id: uuid.UUID,
        items: list[InvoiceItemInput],
    ) -> list[InvoiceItemInput]:
        enriched: list[InvoiceItemInput] = []
        for item in items:
            if not item.product_id:
                enriched.append(item)
                continue
            product = await uow.products.get_by_id(company_id, item.product_id)
            if not product:
                enriched.append(item)
                continue
            hsn_sac = item.hsn_sac or product.hsn_sac
            if not hsn_sac:
                suggestion = suggest_hsn_from_name(item.description or product.name)
                hsn_sac = suggestion.hsn_sac if suggestion else None
            enriched.append(
                InvoiceItemInput(
                    description=item.description or product.name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    gst_rate=item.gst_rate,
                    hsn_sac=hsn_sac,
                    unit=item.unit or product.unit,
                    product_id=item.product_id,
                )
            )
        return enriched

    async def _decrement_stock_for_invoice(
        self,
        uow,
        *,
        company_id: uuid.UUID,
        invoice: Invoice,
        actor_id: uuid.UUID,
    ) -> None:
        for item in invoice.items:
            if not item.product_id:
                continue
            product = await uow.products.get_by_id(company_id, item.product_id)
            if not product or product.stock_qty <= 0:
                continue
            before_qty = product.stock_qty
            product.stock_qty = max(Decimal("0"), product.stock_qty - item.quantity)
            await uow.products.update(product)
            delta = product.stock_qty - before_qty
            if delta != 0:
                await uow.stock_movements.create_invoice_sale(
                    company_id=company_id,
                    product_id=product.id,
                    delta=delta,
                    qty_after=product.stock_qty,
                    invoice_id=invoice.id,
                    actor_id=actor_id,
                )

    @staticmethod
    def _build_items(items: list[InvoiceItemInput]) -> list[InvoiceItem]:
        if not items:
            raise ValidationAppError("At least one line item is required")
        return [
            InvoiceItem(
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

    def _build_invoice(
        self,
        *,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        issue_date: date,
        due_date: date,
        items: list[InvoiceItemInput],
        created_by: uuid.UUID,
    ) -> Invoice:
        if due_date < issue_date:
            raise ValidationAppError("Due date must be on or after issue date")
        return Invoice(
            company_id=company_id,
            customer_id=customer_id,
            issue_date=issue_date,
            due_date=due_date,
            items=self._build_items(items),
            created_by=created_by,
        )

    @staticmethod
    def _is_mock_billing_mode() -> bool:
        from app.core.config import settings

        return settings.use_mock_billing

    @staticmethod
    def _invoice_to_dict(invoice: Invoice) -> dict:
        doc_title = "TAX INVOICE"
        if invoice.document_type == DocumentType.CREDIT_NOTE:
            doc_title = "CREDIT NOTE"
        return {
            "invoice_number": invoice.invoice_number,
            "document_type": invoice.document_type.value,
            "document_title": doc_title,
            "original_invoice_number": None,
            "credit_reason": invoice.credit_reason,
            "issue_date": str(invoice.issue_date),
            "due_date": str(invoice.due_date),
            "status": invoice.status,
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
                for i in invoice.items
            ],
            "taxable_amount": float(invoice.taxable_amount.amount),
            "cgst_amount": float(invoice.cgst_amount.amount),
            "sgst_amount": float(invoice.sgst_amount.amount),
            "igst_amount": float(invoice.igst_amount.amount),
            "total_tax": float(invoice.total_tax.amount),
            "round_off": float(invoice.round_off.amount),
            "grand_total": float(invoice.grand_total.amount),
            "amount_due": float(invoice.amount_due.amount),
        }
