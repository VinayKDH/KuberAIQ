"""Money value object tests."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.exceptions import InvalidMoney
from app.domain.value_objects.money import Money


def test_money_arithmetic() -> None:
    a = Money.of(100)
    b = Money.of(50)
    assert (a + b).amount == Decimal("150.00")
    assert (a - b).amount == Decimal("50.00")


def test_money_currency_mismatch() -> None:
    with pytest.raises(InvalidMoney):
        Money.of(100) + Money(Decimal("1"), "USD")
