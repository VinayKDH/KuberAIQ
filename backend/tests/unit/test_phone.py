"""Phone value object tests."""
from __future__ import annotations

import pytest

from app.domain.exceptions import InvalidPhone
from app.domain.value_objects.phone import Phone


def test_normalize_indian_phone() -> None:
    p = Phone("+919876543210")
    assert p.value == "9876543210"
    assert p.e164 == "+919876543210"


def test_invalid_phone() -> None:
    with pytest.raises(InvalidPhone):
        Phone("12345")
