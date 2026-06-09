"""GST and tax compliance deadline helpers for Indian MSMEs."""
from __future__ import annotations

from datetime import date, timedelta

from app.core.constants import (
    COMPLIANCE_ADVANCE_TAX_DAYS,
    COMPLIANCE_GSTR1_DUE_DAY,
    COMPLIANCE_GSTR3B_DUE_DAY,
    COMPLIANCE_GSTR9_DUE_DAY,
    COMPLIANCE_GSTR9_DUE_MONTH,
    COMPLIANCE_ITR_DUE_DAY,
    COMPLIANCE_ITR_DUE_MONTH,
    COMPLIANCE_MCA_DUE_DAY,
    COMPLIANCE_MCA_DUE_MONTH,
    COMPLIANCE_PF_DUE_DAY,
    COMPLIANCE_ESI_DUE_DAY,
    COMPLIANCE_PROF_TAX_DUE_DAY,
    COMPLIANCE_SHOP_EST_DUE_DAY,
    COMPLIANCE_SHOP_EST_DUE_MONTH,
    COMPLIANCE_TDS_DUE_DAY,
    FINANCIAL_YEAR_START_MONTH,
)


def _month_end(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def gstr1_due_for_period(period_end: date) -> date:
    year, month = _next_month(period_end.year, period_end.month)
    return date(year, month, COMPLIANCE_GSTR1_DUE_DAY)


def gstr3b_due_for_period(period_end: date) -> date:
    year, month = _next_month(period_end.year, period_end.month)
    return date(year, month, COMPLIANCE_GSTR3B_DUE_DAY)


def tds_deposit_due_for_period(period_end: date) -> date:
    year, month = _next_month(period_end.year, period_end.month)
    return date(year, month, COMPLIANCE_TDS_DUE_DAY)


def upcoming_gst_periods(today: date, count: int = 3) -> list[tuple[str, date, date]]:
    """Return (label, period_start, period_end) for recent and upcoming filing periods."""
    periods: list[tuple[str, date, date]] = []
    year, month = today.year, today.month
    for _ in range(count + 1):
        start = date(year, month, 1)
        end = _month_end(year, month)
        label = start.strftime("%b %Y")
        periods.append((label, start, end))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(periods[-count:]))


def financial_year_label(today: date) -> str:
    if today.month >= FINANCIAL_YEAR_START_MONTH:
        start_year = today.year
    else:
        start_year = today.year - 1
    end_year_short = (start_year + 1) % 100
    return f"FY{start_year}-{end_year_short:02d}"


def financial_year_end(today: date) -> date:
    return _fy_end_for_date(today)


def _fy_end_for_date(today: date) -> date:
    """March 31 ending the current Indian financial year."""
    if today.month >= FINANCIAL_YEAR_START_MONTH:
        return date(today.year + 1, 3, 31)
    return date(today.year, 3, 31)


def period_key_monthly(period_end: date) -> str:
    return period_end.strftime("%Y-%m")


def period_key_quarterly(period_end: date) -> str:
    quarter = (period_end.month - 1) // 3 + 1
    return f"{period_end.year}-Q{quarter}"


def period_key_annual(today: date) -> str:
    return financial_year_label(today)


def quarterly_period_end(today: date) -> date:
    month = today.month
    quarter_end_month = ((month - 1) // 3 + 1) * 3
    return _month_end(today.year, quarter_end_month)


def gstr1_due_for_quarter(quarter_end: date) -> date:
    return quarter_end + timedelta(days=13)


def gstr3b_due_for_quarter(quarter_end: date) -> date:
    return quarter_end + timedelta(days=22)


def gstr9_due_for_fy(fy_end: date) -> date:
    return date(fy_end.year, COMPLIANCE_GSTR9_DUE_MONTH, COMPLIANCE_GSTR9_DUE_DAY)


def itr_due_for_fy(fy_end: date) -> date:
    return date(fy_end.year, COMPLIANCE_ITR_DUE_MONTH, COMPLIANCE_ITR_DUE_DAY)


def mca_annual_due_for_fy(fy_end: date) -> date:
    return date(fy_end.year, COMPLIANCE_MCA_DUE_MONTH, COMPLIANCE_MCA_DUE_DAY)


def advance_tax_installments(fy_end: date) -> list[tuple[str, date]]:
    fy_start_year = fy_end.year - 1
    results: list[tuple[str, date]] = []
    for idx, (month, day) in enumerate(COMPLIANCE_ADVANCE_TAX_DAYS, start=1):
        year = fy_start_year if month >= FINANCIAL_YEAR_START_MONTH else fy_end.year
        results.append((f"Q{idx}", date(year, month, day)))
    return results


def pf_due_for_period(period_end: date) -> date:
    year, month = _next_month(period_end.year, period_end.month)
    return date(year, month, COMPLIANCE_PF_DUE_DAY)


def esi_due_for_period(period_end: date) -> date:
    year, month = _next_month(period_end.year, period_end.month)
    return date(year, month, COMPLIANCE_ESI_DUE_DAY)


def prof_tax_due_for_period(period_end: date) -> date:
    year, month = _next_month(period_end.year, period_end.month)
    return date(year, month, COMPLIANCE_PROF_TAX_DUE_DAY)


def shop_establishment_due(fy_end: date) -> date:
    return date(fy_end.year, COMPLIANCE_SHOP_EST_DUE_MONTH, COMPLIANCE_SHOP_EST_DUE_DAY)


def udyam_renewal_due(today: date) -> date:
    return date(today.year, 12, 31)


def current_period_end(today: date, frequency: str) -> date:
    if frequency == "quarterly":
        return quarterly_period_end(today)
    if frequency == "annual":
        return _fy_end_for_date(today)
    if frequency == "event_based":
        return today
    return _month_end(today.year, today.month)


def due_date_for_obligation(
    obligation_id: str,
    *,
    today: date,
    frequency: str,
    period_end: date | None = None,
) -> tuple[str, date]:
    """Return (period_key, due_date) for the current filing period."""
    end = period_end or current_period_end(today, frequency)

    if obligation_id in {"gst_gstr1", "gst_gstr3b", "it_tds_deposit", "labour_pf", "labour_esi", "labour_prof_tax"}:
        if frequency == "quarterly" and obligation_id in {"gst_gstr1", "gst_gstr3b"}:
            key = period_key_quarterly(end)
            due = gstr1_due_for_quarter(end) if obligation_id == "gst_gstr1" else gstr3b_due_for_quarter(end)
            return key, due
        key = period_key_monthly(end)
        due_map = {
            "gst_gstr1": gstr1_due_for_period,
            "gst_gstr3b": gstr3b_due_for_period,
            "it_tds_deposit": tds_deposit_due_for_period,
            "labour_pf": pf_due_for_period,
            "labour_esi": esi_due_for_period,
            "labour_prof_tax": prof_tax_due_for_period,
        }
        return key, due_map[obligation_id](end)

    if obligation_id in {"gst_gstr9", "it_itr", "mca_annual", "other_shop_establishment"}:
        fy_end = _fy_end_for_date(today)
        key = period_key_annual(today)
        due_map = {
            "gst_gstr9": gstr9_due_for_fy,
            "it_itr": itr_due_for_fy,
            "mca_annual": mca_annual_due_for_fy,
            "other_shop_establishment": shop_establishment_due,
        }
        return key, due_map[obligation_id](fy_end)

    if obligation_id == "it_advance_tax":
        fy_end = _fy_end_for_date(today)
        for label, due in advance_tax_installments(fy_end):
            if due >= today - timedelta(days=1):
                return f"{period_key_annual(today)}-{label}", due
        label, due = advance_tax_installments(fy_end)[-1]
        return f"{period_key_annual(today)}-{label}", due

    if obligation_id == "gst_einvoice":
        return period_key_monthly(end), end + timedelta(days=30)

    if obligation_id == "gst_eway":
        return period_key_monthly(end), end

    if obligation_id == "other_udyam":
        return period_key_annual(today), udyam_renewal_due(today)

    key = period_key_monthly(end)
    return key, end
