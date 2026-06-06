"""Indian phone number value object (normalised to 10 digits)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.constants import INDIA_COUNTRY_CODE, INDIA_PHONE_REGEX
from app.domain.exceptions import InvalidPhone

_PATTERN = re.compile(INDIA_PHONE_REGEX)


@dataclass(frozen=True, slots=True)
class Phone:
    value: str  # normalised 10-digit national number

    def __post_init__(self) -> None:
        raw = re.sub(r"[\s\-()]", "", self.value)
        raw = raw.removeprefix("+")
        if raw.startswith(INDIA_COUNTRY_CODE) and len(raw) == 12:
            raw = raw[len(INDIA_COUNTRY_CODE):]
        if not _PATTERN.match(raw):
            raise InvalidPhone(f"'{self.value}' is not a valid Indian mobile number")
        object.__setattr__(self, "value", raw)

    @property
    def e164(self) -> str:
        return f"+{INDIA_COUNTRY_CODE}{self.value}"
