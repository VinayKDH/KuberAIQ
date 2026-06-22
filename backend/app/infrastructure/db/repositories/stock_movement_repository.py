"""Stock movement repository."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.stock_movement import StockMovement
from app.infrastructure.db.mappers.stock_movement_mapper import StockMovementMapper
from app.infrastructure.db.models.stock_movement import StockMovementModel


class SqlAlchemyStockMovementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, movement: StockMovement) -> StockMovement:
        model = StockMovementMapper.to_model(movement)
        self._session.add(model)
        await self._session.flush()
        return StockMovementMapper.to_domain(model)
