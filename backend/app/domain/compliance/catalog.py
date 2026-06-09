"""Structured catalog of Indian MSME compliance obligations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ObligationCategory = Literal["GST", "INCOME_TAX", "LABOUR", "MCA", "OTHER"]
ObligationFrequency = Literal["monthly", "quarterly", "annual", "event_based"]
ObligationPriority = Literal["HIGH", "MEDIUM", "LOW"]


@dataclass(frozen=True, slots=True)
class ComplianceObligationDef:
    id: str
    category: ObligationCategory
    title: str
    description: str
    frequency: ObligationFrequency
    priority: ObligationPriority
    action_route: str | None
    requires_gstin: bool = False
    entity_types: frozenset[str] | None = None
    min_turnover_band: str | None = None
    requires_tds: bool = False
    min_employees: int | None = None
    state_aware: bool = False
    uses_gstr1_frequency: bool = False


COMPLIANCE_CATALOG: tuple[ComplianceObligationDef, ...] = (
    ComplianceObligationDef(
        id="gst_gstr1",
        category="GST",
        title="GSTR-1 (Outward Supplies)",
        description="File outward supply details on the GST portal. Due by the 11th of the following month (or quarter-end + 13 days for QRMP).",
        frequency="monthly",
        priority="HIGH",
        action_route="/settings?tab=reports",
        requires_gstin=True,
        uses_gstr1_frequency=True,
    ),
    ComplianceObligationDef(
        id="gst_gstr3b",
        category="GST",
        title="GSTR-3B (Summary Return)",
        description="File summary return and pay GST liability. Due by the 20th of the following month (or 22nd/24th for QRMP).",
        frequency="monthly",
        priority="HIGH",
        action_route="/settings?tab=reports",
        requires_gstin=True,
        uses_gstr1_frequency=True,
    ),
    ComplianceObligationDef(
        id="gst_gstr9",
        category="GST",
        title="GSTR-9 (Annual Return)",
        description="Annual consolidated GST return for registered taxpayers. Typically due by 31 December after FY end.",
        frequency="annual",
        priority="HIGH",
        action_route="/settings?tab=reports",
        requires_gstin=True,
    ),
    ComplianceObligationDef(
        id="gst_einvoice",
        category="GST",
        title="E-Invoice (IRN Registration)",
        description="Generate Invoice Reference Number on IRP for B2B invoices when turnover exceeds the e-invoice threshold.",
        frequency="event_based",
        priority="HIGH",
        action_route="/compliance",
        requires_gstin=True,
        min_turnover_band="BELOW_40L",
    ),
    ComplianceObligationDef(
        id="gst_eway",
        category="GST",
        title="E-Way Bill",
        description="Generate e-way bill for movement of goods above ₹50,000 where applicable.",
        frequency="event_based",
        priority="MEDIUM",
        action_route="/invoices",
        requires_gstin=True,
    ),
    ComplianceObligationDef(
        id="it_itr",
        category="INCOME_TAX",
        title="Income Tax Return (ITR)",
        description="File annual ITR based on entity type. Non-audit cases typically due by 31 July.",
        frequency="annual",
        priority="HIGH",
        action_route="/settings",
    ),
    ComplianceObligationDef(
        id="it_tds_deposit",
        category="INCOME_TAX",
        title="TDS Deposit",
        description="Deposit tax deducted at source by the 7th of the following month when TDS is applicable.",
        frequency="monthly",
        priority="HIGH",
        action_route="/settings",
        requires_tds=True,
    ),
    ComplianceObligationDef(
        id="it_advance_tax",
        category="INCOME_TAX",
        title="Advance Tax Installments",
        description="Pay advance tax in four installments (15 Jun, 15 Sep, 15 Dec, 15 Mar) if tax liability exceeds ₹10,000.",
        frequency="quarterly",
        priority="MEDIUM",
        action_route="/settings",
        min_turnover_band="_40L_100L",
    ),
    ComplianceObligationDef(
        id="labour_pf",
        category="LABOUR",
        title="EPF Returns & Payment",
        description="Monthly PF contribution and ECR filing when 20 or more employees are on payroll.",
        frequency="monthly",
        priority="HIGH",
        action_route="/settings",
        min_employees=20,
    ),
    ComplianceObligationDef(
        id="labour_esi",
        category="LABOUR",
        title="ESI Contribution",
        description="Monthly ESI contribution when 10 or more employees earn up to ₹21,000 per month.",
        frequency="monthly",
        priority="HIGH",
        action_route="/settings",
        min_employees=10,
    ),
    ComplianceObligationDef(
        id="labour_prof_tax",
        category="LABOUR",
        title="Professional Tax",
        description="State-specific professional tax registration and periodic payment. Rules vary by state.",
        frequency="monthly",
        priority="MEDIUM",
        action_route="/settings",
        state_aware=True,
        min_employees=1,
    ),
    ComplianceObligationDef(
        id="mca_annual",
        category="MCA",
        title="MCA Annual Filing (AOC-4 / MGT-7)",
        description="Annual ROC filing for companies and LLPs within 30–60 days of AGM.",
        frequency="annual",
        priority="HIGH",
        action_route="/settings",
        entity_types=frozenset({"LLP", "PRIVATE_LIMITED", "PUBLIC_LIMITED"}),
    ),
    ComplianceObligationDef(
        id="other_udyam",
        category="OTHER",
        title="Udyam Registration Renewal",
        description="Udyam registration is lifetime but details should be updated periodically. Renewal reminder every 5 years.",
        frequency="event_based",
        priority="LOW",
        action_route="/settings",
    ),
    ComplianceObligationDef(
        id="other_shop_establishment",
        category="OTHER",
        title="Shop & Establishment Act",
        description="State-specific shop licence renewal and display of registration certificate at premises.",
        frequency="annual",
        priority="MEDIUM",
        action_route="/settings",
        state_aware=True,
    ),
)

CATALOG_BY_ID: dict[str, ComplianceObligationDef] = {item.id: item for item in COMPLIANCE_CATALOG}
