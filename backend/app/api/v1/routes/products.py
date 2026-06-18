"""Product routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import AuthContext, get_client_ip, get_container, get_tenant_context, require_roles
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.product import (
    CreateProductRequest,
    HsnLookupResponse,
    ProductResponse,
    UpdateProductRequest,
)
from app.application.services.product_service import CreateProductInput, UpdateProductInput
from app.domain.services.hsn_gst_lookup import lookup_gst_rate, suggest_hsn_from_name
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/products", tags=["products"])


def _to_response(product) -> ProductResponse:
    return ProductResponse(
        id=str(product.id),
        name=product.name,
        description=product.description,
        hsn_sac=product.hsn_sac,
        unit=product.unit,
        default_price=product.default_price,
        gst_rate=product.gst_rate,
        stock_qty=product.stock_qty,
        is_active=product.is_active,
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: CreateProductRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> ProductResponse:
    product = await container.product_service.create(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        data=CreateProductInput(**body.model_dump()),
        ip=get_client_ip(request),
    )
    return _to_response(product)


@router.get("/hsn-lookup", response_model=HsnLookupResponse)
async def lookup_hsn_gst(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    hsn_sac: str | None = None,
    name: str | None = None,
) -> HsnLookupResponse:
    _ = auth
    if hsn_sac:
        rate = lookup_gst_rate(hsn_sac)
        if rate is not None:
            normalized = "".join(ch for ch in hsn_sac.strip().upper() if ch.isalnum())
            return HsnLookupResponse(hsn_sac=normalized, gst_rate=rate, source="catalog")
        return HsnLookupResponse(hsn_sac=hsn_sac.strip(), gst_rate=None, source=None)
    if name:
        suggestion = suggest_hsn_from_name(name)
        if suggestion:
            return HsnLookupResponse(
                hsn_sac=suggestion.hsn_sac,
                gst_rate=suggestion.gst_rate,
                source=suggestion.source,
                matched_label=suggestion.matched_label,
            )
    return HsnLookupResponse()


@router.get("", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    active_only: bool = True,
) -> PaginatedResponse[ProductResponse]:
    items, total = await container.product_service.search(
        auth.company_id, q, page, page_size, active_only=active_only
    )
    return PaginatedResponse(
        items=[_to_response(p) for p in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> ProductResponse:
    product = await container.product_service.get(auth.company_id, product_id)
    return _to_response(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    body: UpdateProductRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> ProductResponse:
    product = await container.product_service.update(
        company_id=auth.company_id,
        product_id=product_id,
        actor_id=auth.user_id,
        data=UpdateProductInput(**body.model_dump(exclude_unset=True)),
        ip=get_client_ip(request),
    )
    return _to_response(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def deactivate_product(
    product_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> Response:
    await container.product_service.deactivate(
        company_id=auth.company_id,
        product_id=product_id,
        actor_id=auth.user_id,
        ip=get_client_ip(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
