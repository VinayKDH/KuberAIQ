"""Company profile use-case orchestration."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.application.ports.repositories import CompanyRecord, UserRecord
from app.core.constants import DEFAULT_INVOICE_PREFIX, AuditAction, EntityType, ErrorCode
from app.core.errors import ConflictError, ForbiddenError, ValidationAppError
from app.domain.exceptions import DomainError, InvalidGstin
from app.domain.value_objects.gstin import Gstin
from app.application.services.billing_service import BillingService


@dataclass
class OnboardCompanyInput:
    legal_name: str
    gstin: str
    address: str
    invoice_prefix: str = DEFAULT_INVOICE_PREFIX


@dataclass
class UpdateCompanyInput:
    legal_name: str | None = None
    gstin: str | None = None
    address: str | None = None
    invoice_prefix: str | None = None
    upi_id: str | None = None
    upi_payee_name: str | None = None
    auto_reminders_enabled: bool | None = None
    default_reminder_language: str | None = None
    entity_type: str | None = None
    turnover_band: str | None = None
    gstr1_filing_frequency: str | None = None
    employee_count: int | None = None
    udyam_number: str | None = None
    has_tds_applicable: bool | None = None


class CompanyService:
    def __init__(self, uow_factory, billing_service: BillingService | None = None) -> None:
        self._uow_factory = uow_factory
        self._billing = billing_service or BillingService(uow_factory)

    async def onboard(
        self,
        *,
        user_id: uuid.UUID,
        data: OnboardCompanyInput,
        ip: str | None = None,
    ) -> dict:
        try:
            gstin = Gstin(data.gstin.strip().upper())
        except DomainError as exc:
            raise ValidationAppError(str(exc), code=ErrorCode.GSTIN_INVALID) from exc

        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise ForbiddenError("User not found")
            if user.company_id is not None:
                raise ConflictError("Company already configured", code=ErrorCode.CONFLICT)
            if not await self._billing.is_active(user_id):
                raise ForbiddenError("Subscription payment required before onboarding")

            gstin_value = gstin.value
            if await uow.companies.get_by_gstin(gstin_value):
                raise ConflictError(
                    "This GSTIN is already registered to another business",
                    code=ErrorCode.GSTIN_CONFLICT,
                )

            company = CompanyRecord(
                id=uuid.uuid4(),
                legal_name=data.legal_name.strip(),
                gstin=gstin_value,
                state_code=gstin.state_code,
                address=data.address.strip(),
                invoice_prefix=data.invoice_prefix.strip() or DEFAULT_INVOICE_PREFIX,
            )
            saved_company = await uow.companies.create(company)
            user = await uow.users.assign_company(user_id, saved_company.id)
            await uow.audit.log(
                company_id=saved_company.id,
                actor_user_id=user_id,
                entity_type=EntityType.COMPANY,
                entity_id=saved_company.id,
                action=AuditAction.CREATE,
                before=None,
                after={"legal_name": saved_company.legal_name, "gstin": saved_company.gstin},
                ip_address=ip,
            )
            await uow.commit()

        return await self._billing.build_token_response(user)

    async def get_profile(self, company_id: uuid.UUID) -> CompanyRecord:
        async with self._uow_factory() as uow:
            company = await uow.companies.get_by_id(company_id)
            if not company:
                raise ValidationAppError("Company not found")
            return company

    async def update_profile(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: UpdateCompanyInput,
        ip: str | None = None,
    ) -> CompanyRecord:
        async with self._uow_factory() as uow:
            company = await uow.companies.get_by_id(company_id)
            if not company:
                raise ValidationAppError("Company not found")

            gstin_value = company.gstin
            state_code = company.state_code
            if data.gstin is not None:
                try:
                    parsed = Gstin(data.gstin.strip().upper())
                    gstin_value = str(parsed)
                    state_code = parsed.state_code
                except DomainError as exc:
                    raise ValidationAppError(str(exc), code=ErrorCode.GSTIN_INVALID) from exc

            updated = CompanyRecord(
                id=company.id,
                legal_name=(data.legal_name or company.legal_name).strip(),
                gstin=gstin_value,
                state_code=state_code,
                address=(data.address if data.address is not None else company.address),
                invoice_prefix=(data.invoice_prefix or company.invoice_prefix).strip(),
                upi_id=(data.upi_id.strip() if data.upi_id is not None else company.upi_id),
                upi_payee_name=(
                    data.upi_payee_name.strip()
                    if data.upi_payee_name is not None
                    else company.upi_payee_name
                ),
                auto_reminders_enabled=(
                    data.auto_reminders_enabled
                    if data.auto_reminders_enabled is not None
                    else company.auto_reminders_enabled
                ),
                default_reminder_language=(
                    data.default_reminder_language
                    if data.default_reminder_language is not None
                    else company.default_reminder_language
                ),
                entity_type=(
                    data.entity_type if data.entity_type is not None else company.entity_type
                ),
                turnover_band=(
                    data.turnover_band if data.turnover_band is not None else company.turnover_band
                ),
                gstr1_filing_frequency=(
                    data.gstr1_filing_frequency
                    if data.gstr1_filing_frequency is not None
                    else company.gstr1_filing_frequency
                ),
                employee_count=(
                    data.employee_count
                    if data.employee_count is not None
                    else company.employee_count
                ),
                udyam_number=(
                    data.udyam_number.strip()
                    if data.udyam_number is not None
                    else company.udyam_number
                ),
                has_tds_applicable=(
                    data.has_tds_applicable
                    if data.has_tds_applicable is not None
                    else company.has_tds_applicable
                ),
            )
            saved = await uow.companies.update(updated)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.COMPANY,
                entity_id=company_id,
                action=AuditAction.UPDATE,
                before={"legal_name": company.legal_name, "gstin": company.gstin},
                after={"legal_name": saved.legal_name, "gstin": saved.gstin},
                ip_address=ip,
            )
            await uow.commit()
            return saved
