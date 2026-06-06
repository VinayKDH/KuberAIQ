"""Money value object — Decimal-based, currency-aware, paise-precise."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.core.constants import CURRENCY_CODE, MONEY_QUANTIZE
from app.domain.exceptions import InvalidMoney


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str = CURRENCY_CODE

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        if self.amount.is_nan() or self.amount.is_infinite():
            raise InvalidMoney("Amount must be a finite number")
        object.__setattr__(self, "amount", self.amount.quantize(MONEY_QUANTIZE, ROUND_HALF_UP))

    @classmethod
    def zero(cls) -> "Money":
        return cls(Decimal("0"))

    @classmethod
    def of(cls, value: Decimal | int | float | str) -> "Money":
        return cls(Decimal(str(value)))

    def _check(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise InvalidMoney("Currency mismatch")

    def __add__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Decimal | int | float) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._check(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._check(other)
        return self.amount <= other.amount

    @property
    def is_negative(self) -> bool:
        return self.amount < Decimal("0")

    @property
    def is_zero(self) -> bool:
        return self.amount == Decimal("0")
