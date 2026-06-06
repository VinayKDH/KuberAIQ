"""GSTIN value object tests."""
from __future__ import annotations

import pytest

from app.domain.exceptions import InvalidGstin
from app.domain.value_objects.gstin import Gstin


def test_valid_gstin() -> None:
    g = Gstin("27AAPFU0939F1ZV")
    assert g.state_code == "27"
    assert g.value == "27AAPFU0939F1ZV"


def test_invalid_gstin_raises() -> None:
    with pytest.raises(InvalidGstin):
        Gstin("INVALID")
