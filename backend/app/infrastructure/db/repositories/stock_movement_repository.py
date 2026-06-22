"""Stock movement repository."""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import STOCK_MOVEMENT_REASON_COUNTER_SALE, STOCK_REFERENCE_COUNTER_BILL
from app.domain.entities.stock_movement import StockMovement
from app.infrastructure.db.mappers.stock_movement_mapper import StockMovementMapper


class SqlAlchemyStockMovementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, movement: StockMovement) -> StockMovement:
        model = StockMovementMapper.to_model(movement)
        self._session.add(model)
        await self._session.flush()
        return StockMovementMapper.to_domain(model)

    async def create_counter_sale(
        self,
        *,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        delta: Decimal,
        qty_after: Decimal,
        invoice_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> StockMovement:
        movement = StockMovement(
            company_id=company_id,
            product_id=product_id,
            delta=delta,
            qty_after=qty_after,
            reason=STOCK_MOVEMENT_REASON_COUNTER_SALE,
            reference_type=STOCK_REFERENCE_COUNTER_BILL,
            reference_id=invoice_id,
            created_by=actor_id,
        )
        return await self.create(movement)
