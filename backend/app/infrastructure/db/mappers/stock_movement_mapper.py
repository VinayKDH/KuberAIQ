"""Stock movement ORM ↔ domain mapper."""
from __future__ import annotations

from app.domain.entities.stock_movement import StockMovement
from app.infrastructure.db.models.stock_movement import StockMovementModel


class StockMovementMapper:
    @staticmethod
    def to_domain(model: StockMovementModel) -> StockMovement:
        return StockMovement(
            id=model.id,
            company_id=model.company_id,
            product_id=model.product_id,
            delta=model.delta,
            qty_after=model.qty_after,
            reason=model.reason,
            reference_type=model.reference_type,
            reference_id=model.reference_id,
            created_by=model.created_by,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(entity: StockMovement) -> StockMovementModel:
        return StockMovementModel(
            id=entity.id,
            company_id=entity.company_id,
            product_id=entity.product_id,
            delta=entity.delta,
            qty_after=entity.qty_after,
            reason=entity.reason,
            reference_type=entity.reference_type,
            reference_id=entity.reference_id,
            created_by=entity.created_by,
        )
