"""Aggregates all v1 API routers."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    ai,
    audit,
    auth,
    billing,
    collections,
    companies,
    compliance,
    customers,
    dashboard,
    invoices,
    payments,
    products,
    quotations,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(billing.router)
api_router.include_router(companies.router)
api_router.include_router(audit.router)
api_router.include_router(customers.router)
api_router.include_router(products.router)
api_router.include_router(invoices.router)
api_router.include_router(quotations.router)
api_router.include_router(payments.router)
api_router.include_router(collections.router)
api_router.include_router(dashboard.router)
api_router.include_router(compliance.router)
api_router.include_router(ai.router)
api_router.include_router(webhooks.router)
