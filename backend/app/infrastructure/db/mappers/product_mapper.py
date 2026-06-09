"""ORM ↔ domain mapping for Product."""
from __future__ import annotations

from app.domain.entities.product import Product
from app.infrastructure.db.models.product import ProductModel


class ProductMapper:
    @staticmethod
    def to_domain(model: ProductModel) -> Product:
        return Product(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            description=model.description,
            hsn_sac=model.hsn_sac,
            unit=model.unit,
            default_price=model.default_price,
            gst_rate=model.gst_rate,
            is_active=model.is_active,
        )

    @staticmethod
    def to_model(entity: Product) -> ProductModel:
        return ProductModel(
            id=entity.id,
            company_id=entity.company_id,
            name=entity.name,
            description=entity.description,
            hsn_sac=entity.hsn_sac,
            unit=entity.unit,
            default_price=entity.default_price,
            gst_rate=entity.gst_rate,
            is_active=entity.is_active,
        )

    @staticmethod
    def update_model(model: ProductModel, entity: Product) -> None:
        model.name = entity.name
        model.description = entity.description
        model.hsn_sac = entity.hsn_sac
        model.unit = entity.unit
        model.default_price = entity.default_price
        model.gst_rate = entity.gst_rate
        model.is_active = entity.is_active
