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
    assert paneer.matched_label == "Paneer / cheese"

    khoya = suggest_hsn_from_name("Khoya")
    assert khoya is not None
    assert khoya.hsn_sac == "0402"

    cement = suggest_hsn_from_name("OPC 53 Grade Cement")
    assert cement is not None
    assert cement.hsn_sac == "2523"
    assert cement.gst_rate == Decimal("28")

    steel = suggest_hsn_from_name("TMT Steel Rod 12mm")
    assert steel is not None
    assert steel.hsn_sac == "7214"

    spices = suggest_hsn_from_name("Turmeric Powder 500g")
    assert spices is not None
    assert spices.hsn_sac == "0910"

    ac = suggest_hsn_from_name("1.5 Ton Split AC")
    assert ac is not None
    assert ac.hsn_sac == "8415"

    tyre = suggest_hsn_from_name("MRF Car Tyre 195/65")
    assert tyre is not None
    assert tyre.hsn_sac == "4011"
    assert tyre.gst_rate == Decimal("28")


def test_resolve_product_tax_fields_from_name() -> None:
    hsn, rate = resolve_product_tax_fields(name="Paneer", hsn_sac=None, gst_rate=None)
    assert hsn == "0406"
    assert rate == Decimal("5")


def test_resolve_product_tax_fields_hsn_overrides_default() -> None:
    hsn, rate = resolve_product_tax_fields(name="Cement", hsn_sac="2523", gst_rate=None)
    assert hsn == "2523"
    assert rate == Decimal("28")
