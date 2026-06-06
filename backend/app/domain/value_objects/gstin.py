"""GSTIN value object with format + checksum validation.

GSTIN = 15 chars: 2 (state code) + 10 (PAN) + 1 (entity) + 'Z' + 1 (checksum).
The 15th char is a checksum over the first 14 using a base-36 weighted algorithm.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.constants import GSTIN_LENGTH, GSTIN_REGEX
from app.domain.exceptions import InvalidGstin

_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_CODE = {c: i for i, c in enumerate(_ALPHABET)}
_PATTERN = re.compile(GSTIN_REGEX)


def _checksum(first14: str) -> str:
    factor = 2
    total = 0
    code_point = len(_ALPHABET)
    for ch in reversed(first14):
        digit = _CODE[ch] * factor
        digit = (digit // code_point) + (digit % code_point)
        total += digit
        factor = 1 if factor == 2 else 2
    check_val = (code_point - (total % code_point)) % code_point
    return _ALPHABET[check_val]


@dataclass(frozen=True, slots=True)
class Gstin:
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip().upper()
        object.__setattr__(self, "value", v)
        if len(v) != GSTIN_LENGTH or not _PATTERN.match(v):
            raise InvalidGstin(f"GSTIN '{v}' is not a valid 15-character GSTIN")
        if _checksum(v[:14]) != v[14]:
            raise InvalidGstin(f"GSTIN '{v}' has an invalid checksum")

    @property
    def state_code(self) -> str:
        return self.value[:2]

    @classmethod
    def parse_optional(cls, value: str | None) -> "Gstin | None":
        if value is None or not value.strip():
            return None
        return cls(value)
