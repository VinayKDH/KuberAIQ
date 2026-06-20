"""Product catalog use-case orchestration."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.core.constants import ALLOWED_GST_RATES, AuditAction, EntityType, ErrorCode
from app.core.errors import NotFoundError, ValidationAppError
from app.domain.entities.product import Product
from app.domain.services.hsn_gst_lookup import lookup_gst_rate, resolve_product_tax_fields


@dataclass
class CreateProductInput:
    name: str
    default_price: Decimal
    gst_rate: Decimal | None = None
    description: str | None = None
    hsn_sac: str | None = None
    unit: str = "NOS"
    stock_qty: Decimal = Decimal("0")


@dataclass
class UpdateProductInput:
    name: str | None = None
    description: str | None = None
    hsn_sac: str | None = None
    unit: str | None = None
    default_price: Decimal | None = None
    gst_rate: Decimal | None = None
    stock_qty: Decimal | None = None
    is_active: bool | None = None


class ProductService:
    def __init__(self, uow_factory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: CreateProductInput,
        ip: str | None = None,
    ) -> Product:
        hsn_sac, gst_rate = resolve_product_tax_fields(
            name=data.name.strip(),
            hsn_sac=data.hsn_sac,
            gst_rate=data.gst_rate,
        )
        self._validate_gst_rate(gst_rate)
        product = Product(
            company_id=company_id,
            name=data.name.strip(),
            description=data.description,
            hsn_sac=hsn_sac,
            unit=data.unit,
            default_price=data.default_price,
            gst_rate=gst_rate,
            stock_qty=data.stock_qty,
        )
        async with self._uow_factory() as uow:
            saved = await uow.products.create(product)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.PRODUCT,
                entity_id=saved.id,
                action=AuditAction.CREATE,
                before=None,
                after={"name": saved.name},
                ip_address=ip,
            )
            return saved

    async def get(self, company_id: uuid.UUID, product_id: uuid.UUID) -> Product:
        async with self._uow_factory() as uow:
            product = await uow.products.get_by_id(company_id, product_id)
            if not product:
                raise NotFoundError("Product not found")
            return product

    async def search(
        self,
        company_id: uuid.UUID,
        q: str | None,
        page: int,
        page_size: int,
        *,
        active_only: bool = True,
    ) -> tuple[list[Product], int]:
        async with self._uow_factory() as uow:
            return await uow.products.search(
                company_id, q=q, active_only=active_only, page=page, page_size=page_size
            )

    async def list_low_stock(
        self, company_id: uuid.UUID, *, threshold: Decimal | None = None
    ) -> list[Product]:
        from app.core.constants import LOW_STOCK_THRESHOLD_DEFAULT

        limit_threshold = threshold if threshold is not None else Decimal(str(LOW_STOCK_THRESHOLD_DEFAULT))
        async with self._uow_factory() as uow:
            return await uow.products.list_low_stock(
                company_id, threshold=limit_threshold, limit=50
            )

    async def update(
        self,
        *,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: UpdateProductInput,
        ip: str | None = None,
    ) -> Product:
        async with self._uow_factory() as uow:
            product = await uow.products.get_by_id(company_id, product_id)
            if not product:
                raise NotFoundError("Product not found")
            before = {"name": product.name, "is_active": product.is_active}
            if data.name is not None:
                product.rename(data.name)
            if data.description is not None:
                product.description = data.description
            if data.hsn_sac is not None:
                product.hsn_sac = data.hsn_sac.strip() or None
                if data.gst_rate is None and product.hsn_sac:
                    looked_up = lookup_gst_rate(product.hsn_sac)
                    if looked_up is not None:
                        product.gst_rate = looked_up
            if data.unit is not None:
                product.unit = data.unit
            if data.default_price is not None:
                product.default_price = data.default_price
            if data.gst_rate is not None:
                self._validate_gst_rate(data.gst_rate)
                product.gst_rate = data.gst_rate
            if data.stock_qty is not None:
                product.stock_qty = data.stock_qty
            if data.is_active is not None:
                if data.is_active:
                    product.activate()
                else:
                    product.deactivate()
            saved = await uow.products.update(product)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.PRODUCT,
                entity_id=saved.id,
                action=AuditAction.UPDATE,
                before=before,
                after={"name": saved.name, "is_active": saved.is_active},
                ip_address=ip,
            )
            return saved

    async def deactivate(
        self,
        *,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> None:
        async with self._uow_factory() as uow:
            product = await uow.products.get_by_id(company_id, product_id)
            if not product:
                raise NotFoundError("Product not found")
            await uow.products.soft_delete(company_id, product_id)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.PRODUCT,
                entity_id=product_id,
                action=AuditAction.DELETE,
                before={"name": product.name},
                after=None,
                ip_address=ip,
            )

    @staticmethod
    def _validate_gst_rate(rate: Decimal) -> None:
        if rate not in ALLOWED_GST_RATES:
            raise ValidationAppError(
                f"GST rate {rate}% not allowed",
                code=ErrorCode.VALIDATION_ERROR,
            )
