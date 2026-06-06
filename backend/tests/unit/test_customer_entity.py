"""Customer entity domain tests."""
from __future__ import annotations

import uuid

import pytest

from app.domain.entities.customer import Customer
from app.domain.value_objects.phone import Phone


def test_customer_rename() -> None:
    customer = Customer(
        company_id=uuid.uuid4(),
        name="Old Name",
        phone=Phone("9876543210"),
    )
    customer.rename("New Name")
    assert customer.name == "New Name"


def test_customer_empty_name_raises() -> None:
    customer = Customer(
        company_id=uuid.uuid4(),
        name="Valid",
        phone=Phone("9876543210"),
    )
    with pytest.raises(ValueError):
        customer.rename("   ")
