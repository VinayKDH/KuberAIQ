"""HSN/SAC → GST rate lookup and product-name suggestions for Indian GST."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.constants import (
    ALLOWED_GST_RATES,
    DEFAULT_PRODUCT_GST_RATE,
    HSN_EXACT_GST_RATES,
    HSN_PREFIX_GST_RATES,
    PRODUCT_NAME_HSN_HINTS,
)


@dataclass(frozen=True)
class HsnSuggestion:
    hsn_sac: str
    gst_rate: Decimal
    source: str


def _normalize_hsn(hsn_sac: str) -> str:
    return "".join(ch for ch in hsn_sac.strip().upper() if ch.isalnum())


def lookup_gst_rate(hsn_sac: str | None) -> Decimal | None:
    """Return default GST rate for an HSN/SAC code, or None if unknown."""
    code = _normalize_hsn(hsn_sac or "")
    if not code:
        return None
    exact = HSN_EXACT_GST_RATES.get(code)
    if exact is not None:
        return Decimal(exact)
    for prefix, rate in HSN_PREFIX_GST_RATES:
        if code.startswith(prefix):
            return Decimal(rate)
    return None


def suggest_hsn_from_name(name: str) -> HsnSuggestion | None:
    """Suggest HSN/SAC and GST rate from a product name keyword match."""
    lowered = name.strip().lower()
    if not lowered:
        return None
    for keyword, (hsn_sac, rate) in PRODUCT_NAME_HSN_HINTS.items():
        if keyword in lowered:
            return HsnSuggestion(hsn_sac=hsn_sac, gst_rate=Decimal(rate), source="name_hint")
    return None


def resolve_product_tax_fields(
    *,
    name: str,
    hsn_sac: str | None,
    gst_rate: Decimal | None,
) -> tuple[str | None, Decimal]:
    """Resolve HSN/SAC and GST rate for product create/update."""
    resolved_hsn = _normalize_hsn(hsn_sac) if hsn_sac and hsn_sac.strip() else None
    if not resolved_hsn:
        suggestion = suggest_hsn_from_name(name)
        if suggestion:
            resolved_hsn = suggestion.hsn_sac

    resolved_rate = gst_rate
    if resolved_hsn:
        looked_up = lookup_gst_rate(resolved_hsn)
        if looked_up is not None and resolved_rate is None:
            resolved_rate = looked_up

    if resolved_rate is None:
        resolved_rate = DEFAULT_PRODUCT_GST_RATE

    if resolved_rate not in ALLOWED_GST_RATES:
        resolved_rate = DEFAULT_PRODUCT_GST_RATE

    return resolved_hsn, resolved_rate
