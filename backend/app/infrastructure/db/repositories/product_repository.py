"""SQLAlchemy implementation of ProductRepository."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.product import Product
from app.infrastructure.db.mappers.product_mapper import ProductMapper
from app.infrastructure.db.models.product import ProductModel


class SqlAlchemyProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, product: Product) -> Product:
        model = ProductMapper.to_model(product)
        self._session.add(model)
        await self._session.flush()
        return ProductMapper.to_domain(model)

    async def get_by_id(self, company_id: uuid.UUID, product_id: uuid.UUID) -> Product | None:
        stmt = select(ProductModel).where(
            ProductModel.company_id == company_id,
            ProductModel.id == product_id,
            ProductModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return ProductMapper.to_domain(model) if model else None

    async def update(self, product: Product) -> Product:
        stmt = select(ProductModel).where(
            ProductModel.id == product.id,
            ProductModel.company_id == product.company_id,
            ProductModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        ProductMapper.update_model(model, product)
        await self._session.flush()
        return ProductMapper.to_domain(model)

    async def soft_delete(self, company_id: uuid.UUID, product_id: uuid.UUID) -> None:
        stmt = select(ProductModel).where(
            ProductModel.company_id == company_id,
            ProductModel.id == product_id,
            ProductModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.deleted_at = datetime.now(timezone.utc)
        model.is_active = False

    async def search(
        self,
        company_id: uuid.UUID,
        *,
        q: str | None = None,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        base = select(ProductModel).where(
            ProductModel.company_id == company_id,
            ProductModel.deleted_at.is_(None),
        )
        if active_only:
            base = base.where(ProductModel.is_active.is_(True))
        if q:
            pattern = f"%{q.lower()}%"
            base = base.where(
                or_(
                    func.lower(ProductModel.name).like(pattern),
                    func.lower(ProductModel.description).like(pattern),
                    ProductModel.hsn_sac.ilike(pattern),
                )
            )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = (
            base.order_by(ProductModel.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        items = [ProductMapper.to_domain(m) for m in result.scalars().all()]
        return items, total
