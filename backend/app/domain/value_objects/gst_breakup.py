"""GST breakup value object: the CGST/SGST/IGST split for a taxable amount."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.constants import GST_TOLERANCE
from app.domain.value_objects.money import Money


@dataclass(frozen=True, slots=True)
class GstBreakup:
    taxable: Money
    cgst: Money
    sgst: Money
    igst: Money

    @property
    def total_tax(self) -> Money:
        return self.cgst + self.sgst + self.igst

    @property
    def total(self) -> Money:
        return self.taxable + self.total_tax

    @property
    def is_intra_state(self) -> bool:
        return self.igst.is_zero and not (self.cgst.is_zero and self.sgst.is_zero)

    def is_consistent(self) -> bool:
        """Guardrail check: CGST == SGST for intra-state; exactly one mode is used."""
        if not self.igst.is_zero:
            return self.cgst.is_zero and self.sgst.is_zero
        delta = (self.cgst.amount - self.sgst.amount).copy_abs()
        return delta <= GST_TOLERANCE
