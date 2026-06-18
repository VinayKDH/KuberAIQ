"""HSN/SAC → GST rate lookup and product-name suggestions for Indian GST."""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from app.core.constants import (
    ALLOWED_GST_RATES,
    DEFAULT_PRODUCT_GST_RATE,
    HSN_EXACT_GST_RATES,
    HSN_PREFIX_GST_RATES,
)
from app.core.gst_product_catalog import GST_PRODUCT_CATALOG, GstProductCatalogEntry

_WORD_BOUNDARY = re.compile(r"[^\w]+", re.UNICODE)
_MIN_NAME_MATCH_SCORE = 200


@dataclass(frozen=True)
class HsnSuggestion:
    hsn_sac: str
    gst_rate: Decimal
    source: str
    matched_label: str | None = None


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


def _keyword_score(query: str, keyword: str) -> int:
    """Higher score = better match (longer keyword / whole-word beats substring)."""
    q = query.lower().strip()
    k = keyword.lower().strip()
    if len(k) < 2 or not q:
        return 0
    if q == k:
        return 1000 + len(k)
    padded = f" {_WORD_BOUNDARY.sub(' ', q)} "
    token = f" {k} "
    if token in padded:
        return 500 + len(k)
    if k in q:
        return 200 + len(k)
    return 0


def _best_catalog_match(name: str) -> tuple[int, GstProductCatalogEntry, str] | None:
    best: tuple[int, GstProductCatalogEntry, str] | None = None
    for entry in GST_PRODUCT_CATALOG:
        for keyword in entry.keywords:
            score = _keyword_score(name, keyword)
            if score <= 0:
                continue
            if best is None or score > best[0]:
                best = (score, entry, keyword)
    return best


def suggest_hsn_from_name(name: str) -> HsnSuggestion | None:
    """Suggest HSN/SAC and GST rate by matching product name to GST catalogue."""
    cleaned = name.strip()
    if not cleaned:
        return None

    match = _best_catalog_match(cleaned)
    if match is None or match[0] < _MIN_NAME_MATCH_SCORE:
        return None

    _, entry, _keyword = match
    rate = lookup_gst_rate(entry.hsn_sac) or Decimal(entry.gst_rate)
    return HsnSuggestion(
        hsn_sac=entry.hsn_sac,
        gst_rate=rate,
        source="catalog",
        matched_label=entry.label,
    )


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
