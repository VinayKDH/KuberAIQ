"""ORM ↔ domain mapping for Customer."""
from __future__ import annotations

from app.domain.entities.customer import Customer
from app.domain.value_objects.gstin import Gstin
from app.domain.value_objects.phone import Phone
from app.infrastructure.db.models.customer import CustomerModel


class CustomerMapper:
    @staticmethod
    def to_domain(model: CustomerModel) -> Customer:
        return Customer(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            phone=Phone(model.phone),
            email=model.email,
            gstin=Gstin.parse_optional(model.gstin),
            billing_address=model.billing_address,
            notes=model.notes,
        )

    @staticmethod
    def to_model(entity: Customer) -> CustomerModel:
        return CustomerModel(
            id=entity.id,
            company_id=entity.company_id,
            name=entity.name,
            phone=entity.phone.value,
            email=entity.email,
            gstin=entity.gstin.value if entity.gstin else None,
            state_code=entity.state_code,
            billing_address=entity.billing_address,
            notes=entity.notes,
        )

    @staticmethod
    def update_model(model: CustomerModel, entity: Customer) -> None:
        model.name = entity.name
        model.phone = entity.phone.value
        model.email = entity.email
        model.gstin = entity.gstin.value if entity.gstin else None
        model.state_code = entity.state_code
        model.billing_address = entity.billing_address
        model.notes = entity.notes
