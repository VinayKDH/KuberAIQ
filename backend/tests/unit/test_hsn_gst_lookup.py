"""Tests for HSN/SAC GST lookup."""
from __future__ import annotations

from decimal import Decimal

from app.domain.services.hsn_gst_lookup import (
    lookup_gst_rate,
    resolve_product_tax_fields,
    suggest_hsn_from_name,
)


def test_lookup_gst_rate_exact_code() -> None:
    assert lookup_gst_rate("0406") == Decimal("5")
    assert lookup_gst_rate("2523") == Decimal("28")


def test_lookup_gst_rate_prefix_fallback() -> None:
    assert lookup_gst_rate("040610") == Decimal("5")


def test_suggest_hsn_from_name() -> None:
    paneer = suggest_hsn_from_name("Fresh Paneer 1kg")
    assert paneer is not None
    assert paneer.hsn_sac == "0406"
    assert paneer.gst_rate == Decimal("5")

    khoya = suggest_hsn_from_name("Khoya")
    assert khoya is not None
    assert khoya.hsn_sac == "0402"


def test_resolve_product_tax_fields_from_name() -> None:
    hsn, rate = resolve_product_tax_fields(name="Paneer", hsn_sac=None, gst_rate=None)
    assert hsn == "0406"
    assert rate == Decimal("5")


def test_resolve_product_tax_fields_hsn_overrides_default() -> None:
    hsn, rate = resolve_product_tax_fields(name="Cement", hsn_sac="2523", gst_rate=None)
    assert hsn == "2523"
    assert rate == Decimal("28")
