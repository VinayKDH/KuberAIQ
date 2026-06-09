"""Applicability engine — determines which MSME obligations apply to a company."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.constants import (
    COMPLIANCE_ENTITY_TYPE_DEFAULT,
    COMPLIANCE_GSTR1_FREQUENCY_MONTHLY,
    COMPLIANCE_OBLIGATION_STATUS_NOT_APPLICABLE,
    COMPLIANCE_TURNOVER_BAND_ORDER,
    E_INVOICE_TURNOVER_THRESHOLD,
)
from app.domain.compliance.catalog import CATALOG_BY_ID, COMPLIANCE_CATALOG, ComplianceObligationDef


@dataclass(frozen=True, slots=True)
class CompanyComplianceProfile:
    gstin: str | None
    state_code: str
    entity_type: str
    turnover_band: str | None
    gstr1_filing_frequency: str
    employee_count: int | None
    has_tds_applicable: bool
    udyam_number: str | None
    ytd_turnover: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class ApplicabilityResult:
    obligation: ComplianceObligationDef
    applies: bool
    reason: str
    effective_frequency: str


def profile_is_complete(profile: CompanyComplianceProfile) -> bool:
    return bool(profile.turnover_band and profile.entity_type)


def _band_rank(band: str | None) -> int:
    if not band:
        return -1
    try:
        return COMPLIANCE_TURNOVER_BAND_ORDER.index(band)
    except ValueError:
        return -1


def _meets_min_turnover(profile: CompanyComplianceProfile, min_band: str | None) -> bool:
    if min_band is None:
        return True
    if min_band == "BELOW_40L" and profile.ytd_turnover >= E_INVOICE_TURNOVER_THRESHOLD:
        return True
    return _band_rank(profile.turnover_band) >= _band_rank(min_band)


def evaluate_applicability(
    obligation: ComplianceObligationDef,
    profile: CompanyComplianceProfile,
) -> ApplicabilityResult:
    if obligation.requires_gstin and not profile.gstin:
        return ApplicabilityResult(
            obligation=obligation,
            applies=False,
            reason="Requires GST registration (GSTIN on company profile).",
            effective_frequency=obligation.frequency,
        )

    if obligation.entity_types and profile.entity_type not in obligation.entity_types:
        return ApplicabilityResult(
            obligation=obligation,
            applies=False,
            reason=f"Not applicable to {profile.entity_type.replace('_', ' ').title()} entities.",
            effective_frequency=obligation.frequency,
        )

    if obligation.requires_tds and not profile.has_tds_applicable:
        return ApplicabilityResult(
            obligation=obligation,
            applies=False,
            reason="Mark TDS as applicable in compliance profile if you deduct tax at source.",
            effective_frequency=obligation.frequency,
        )

    if obligation.min_employees is not None:
        count = profile.employee_count or 0
        if count < obligation.min_employees:
            return ApplicabilityResult(
                obligation=obligation,
                applies=False,
                reason=f"Requires at least {obligation.min_employees} employees (you have {count}).",
                effective_frequency=obligation.frequency,
            )

    if not _meets_min_turnover(profile, obligation.min_turnover_band):
        return ApplicabilityResult(
            obligation=obligation,
            applies=False,
            reason="Turnover band does not meet threshold for this obligation.",
            effective_frequency=obligation.frequency,
        )

    effective_frequency = obligation.frequency
    if obligation.uses_gstr1_frequency:
        effective_frequency = (
            "quarterly"
            if profile.gstr1_filing_frequency == "QUARTERLY"
            else "monthly"
        )

    if obligation.id == "gst_einvoice" and profile.ytd_turnover < E_INVOICE_TURNOVER_THRESHOLD:
        if _band_rank(profile.turnover_band) < _band_rank("_100L_500L"):
            return ApplicabilityResult(
                obligation=obligation,
                applies=False,
                reason="E-invoicing applies when FY turnover crosses ₹10 lakh.",
                effective_frequency=effective_frequency,
            )

    if obligation.id == "other_udyam" and not profile.udyam_number:
        return ApplicabilityResult(
            obligation=obligation,
            applies=True,
            reason="Add Udyam number to track renewal reminders.",
            effective_frequency=effective_frequency,
        )

    reason = "Applicable based on your business profile."
    if obligation.state_aware:
        reason = f"State-specific rules may apply (state code {profile.state_code})."

    return ApplicabilityResult(
        obligation=obligation,
        applies=True,
        reason=reason,
        effective_frequency=effective_frequency,
    )


def applicable_obligations(profile: CompanyComplianceProfile) -> list[ApplicabilityResult]:
    if not profile_is_complete(profile):
        return []
    return [evaluate_applicability(item, profile) for item in COMPLIANCE_CATALOG]


def not_applicable_obligations(profile: CompanyComplianceProfile) -> list[ApplicabilityResult]:
    return [
        result
        for result in (
            evaluate_applicability(item, profile) for item in COMPLIANCE_CATALOG
        )
        if not result.applies
    ]


def default_profile_from_company(
    *,
    gstin: str | None,
    state_code: str,
    entity_type: str | None,
    turnover_band: str | None,
    gstr1_filing_frequency: str | None,
    employee_count: int | None,
    has_tds_applicable: bool,
    udyam_number: str | None,
    ytd_turnover: Decimal = Decimal("0"),
) -> CompanyComplianceProfile:
    return CompanyComplianceProfile(
        gstin=gstin,
        state_code=state_code,
        entity_type=entity_type or COMPLIANCE_ENTITY_TYPE_DEFAULT,
        turnover_band=turnover_band,
        gstr1_filing_frequency=gstr1_filing_frequency or COMPLIANCE_GSTR1_FREQUENCY_MONTHLY,
        employee_count=employee_count,
        has_tds_applicable=has_tds_applicable,
        udyam_number=udyam_number,
        ytd_turnover=ytd_turnover,
    )
