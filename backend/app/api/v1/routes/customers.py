"""Customer routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import AuthContext, get_client_ip, get_container, get_tenant_context, require_msme_roles
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.customer import (
    CreateCustomerRequest,
    CustomerHistoryResponse,
    CustomerResponse,
    UpdateCustomerRequest,
)
from app.application.services.customer_service import CreateCustomerInput, UpdateCustomerInput
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/customers", tags=["customers"])


def _to_response(customer) -> CustomerResponse:
    return CustomerResponse(
        id=str(customer.id),
        name=customer.name,
        phone=customer.phone.value,
        email=customer.email,
        gstin=customer.gstin.value if customer.gstin else None,
        state_code=customer.state_code,
        billing_address=customer.billing_address,
        notes=customer.notes,
    )


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CreateCustomerRequest,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> CustomerResponse:
    customer = await container.customer_service.create(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        data=CreateCustomerInput(**body.model_dump()),
        ip=get_client_ip(request),
    )
    return _to_response(customer)


@router.get("/check-phone")
async def check_phone(
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    phone: str = Query(..., min_length=10, max_length=13),
) -> dict:
    async with container.uow_factory() as uow:
        existing = await uow.customers.find_by_phone(auth.company_id, phone.strip())
    return {"exists": existing is not None, "customer_id": str(existing.id) if existing else None}


@router.get("", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
) -> PaginatedResponse[CustomerResponse]:
    items, total = await container.customer_service.search(auth.company_id, q, page, page_size)
    return PaginatedResponse(
        items=[_to_response(c) for c in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CustomerResponse:
    customer = await container.customer_service.get(auth.company_id, customer_id)
    return _to_response(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: uuid.UUID,
    body: UpdateCustomerRequest,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> CustomerResponse:
    customer = await container.customer_service.update(
        company_id=auth.company_id,
        customer_id=customer_id,
        actor_id=auth.user_id,
        data=UpdateCustomerInput(**body.model_dump(exclude_unset=True)),
        ip=get_client_ip(request),
    )
    return _to_response(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_customer(
    customer_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> Response:
    await container.customer_service.delete(
        company_id=auth.company_id,
        customer_id=customer_id,
        actor_id=auth.user_id,
        ip=get_client_ip(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{customer_id}/history", response_model=CustomerHistoryResponse)
async def customer_history(
    customer_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CustomerHistoryResponse:
    history = await container.customer_service.history(auth.company_id, customer_id)
    return CustomerHistoryResponse(
        customer=_to_response(history["customer"]),
        total_billed=history["total_billed"],
        total_paid=history["total_paid"],
        outstanding=history["outstanding"],
        aging=history["aging"],
    )


@router.get("/{customer_id}/statement.pdf")
async def download_customer_statement(
    customer_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> Response:
    data, filename = await container.customer_service.download_statement_bytes(
        auth.company_id, customer_id
    )
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
