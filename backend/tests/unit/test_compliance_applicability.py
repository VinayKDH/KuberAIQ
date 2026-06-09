"""Tests for compliance applicability engine."""
from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from app.domain.compliance.catalog import CATALOG_BY_ID
from app.domain.services.compliance_applicability import (
    CompanyComplianceProfile,
    default_profile_from_company,
    evaluate_applicability,
    profile_is_complete,
)
from app.domain.services.compliance_dates import (
    due_date_for_obligation,
    gstr1_due_for_period,
    gstr9_due_for_fy,
    itr_due_for_fy,
    period_key_monthly,
)


def _profile(**overrides) -> CompanyComplianceProfile:
    base = default_profile_from_company(
        gstin="27AAPFU0939F1ZV",
        state_code="27",
        entity_type="PROPRIETORSHIP",
        turnover_band="_40L_100L",
        gstr1_filing_frequency="MONTHLY",
        employee_count=5,
        has_tds_applicable=False,
        udyam_number=None,
        ytd_turnover=Decimal("500000"),
    )
    return replace(base, **overrides) if overrides else base


def test_profile_complete_requires_turnover_band() -> None:
    profile = _profile(turnover_band=None)
    assert profile_is_complete(profile) is False


def test_gstr1_requires_gstin() -> None:
    result = evaluate_applicability(CATALOG_BY_ID["gst_gstr1"], _profile(gstin=None))
    assert result.applies is False
    assert "GSTIN" in result.reason


def test_tds_only_when_flagged() -> None:
    result = evaluate_applicability(CATALOG_BY_ID["it_tds_deposit"], _profile(has_tds_applicable=False))
    assert result.applies is False
    result = evaluate_applicability(CATALOG_BY_ID["it_tds_deposit"], _profile(has_tds_applicable=True))
    assert result.applies is True


def test_pf_requires_twenty_employees() -> None:
    result = evaluate_applicability(CATALOG_BY_ID["labour_pf"], _profile(employee_count=10))
    assert result.applies is False
    result = evaluate_applicability(CATALOG_BY_ID["labour_pf"], _profile(employee_count=25))
    assert result.applies is True


def test_mca_only_for_companies() -> None:
    result = evaluate_applicability(
        CATALOG_BY_ID["mca_annual"], _profile(entity_type="PROPRIETORSHIP")
    )
    assert result.applies is False
    result = evaluate_applicability(
        CATALOG_BY_ID["mca_annual"], _profile(entity_type="PRIVATE_LIMITED")
    )
    assert result.applies is True


def test_gstr1_quarterly_frequency() -> None:
    result = evaluate_applicability(
        CATALOG_BY_ID["gst_gstr1"], _profile(gstr1_filing_frequency="QUARTERLY")
    )
    assert result.applies is True
    assert result.effective_frequency == "quarterly"


def test_due_date_for_gstr1_monthly() -> None:
    from datetime import date

    period_end = date(2026, 6, 30)
    key, due = due_date_for_obligation(
        "gst_gstr1",
        today=period_end,
        frequency="monthly",
    )
    assert key == period_key_monthly(period_end)
    assert due == gstr1_due_for_period(period_end)


def test_annual_itr_due_date() -> None:
    from datetime import date

    today = date(2026, 6, 1)
    key, due = due_date_for_obligation("it_itr", today=today, frequency="annual")
    assert key.startswith("FY")
    assert due == itr_due_for_fy(date(2027, 3, 31))


def test_gstr9_annual_due() -> None:
    fy_end = __import__("datetime").date(2027, 3, 31)
    assert gstr9_due_for_fy(fy_end) == __import__("datetime").date(2027, 12, 31)
