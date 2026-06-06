"""Aggregates all v1 API routers."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import ai, auth, collections, customers, dashboard, invoices, payments, webhooks

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(invoices.router)
api_router.include_router(payments.router)
api_router.include_router(collections.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
api_router.include_router(webhooks.router)
