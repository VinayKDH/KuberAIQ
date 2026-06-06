"""Pure domain exceptions (no framework dependencies).

The API layer maps these to HTTP responses; the domain stays transport-agnostic.
"""
from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain rule violations."""


class InvalidGstin(DomainError):
    pass


class InvalidPhone(DomainError):
    pass


class InvalidMoney(DomainError):
    pass


class InvalidGstRate(DomainError):
    pass


class InvoiceNotEditable(DomainError):
    pass


class InvalidStateTransition(DomainError):
    pass


class PaymentExceedsDue(DomainError):
    pass


class InvoiceHasPayments(DomainError):
    pass
