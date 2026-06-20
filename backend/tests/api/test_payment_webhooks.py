"""Invoice payment webhook tests."""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid

import pytest
from httpx import AsyncClient

from app.core.constants import RAZORPAY_INVOICE_REFERENCE_PREFIX, RAZORPAY_PAYMENT_REFERENCE_PREFIX
from app.core.security import create_access_token
from app.domain.enums import InvoiceStatus, UserRole
from app.startup.seed import DEMO_COMPANY_ID, DEMO_USER_ID


def _signature(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _payment_link_paid_payload(invoice_id: uuid.UUID, *, payment_id: str = "pay_test123") -> dict:
    return {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "reference_id": f"{RAZORPAY_INVOICE_REFERENCE_PREFIX}{invoice_id}",
                    "amount": 118000,
                }
            },
            "payment": {
                "entity": {
                    "id": payment_id,
                    "amount": 118000,
                }
            },
        },
    }


async def _create_issued_invoice(client: AsyncClient, headers: dict[str, str]) -> str:
    customer = await client.post(
        "/api/v1/customers",
        json={"name": "Webhook Customer", "phone": "9876501234"},
        headers=headers,
    )
    assert customer.status_code == 201
    customer_id = customer.json()["id"]

    create = await client.post(
        "/api/v1/invoices",
        headers=headers,
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-20",
            "due_date": "2026-07-05",
            "status": "ISSUED",
            "items": [
                {
                    "description": "Test item",
                    "quantity": "1",
                    "unit_price": "1000",
                    "gst_rate": "18",
                }
            ],
        },
    )
    assert create.status_code == 201
    return create.json()["id"]


@pytest.mark.asyncio
async def test_invoice_webhook_marks_invoice_paid(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import config as config_mod

    secret = "whsec_invoice_test"
    monkeypatch.setattr(config_mod.settings, "use_mock_billing", False)
    monkeypatch.setattr(config_mod.settings, "razorpay_key_id", "rzp_test")
    monkeypatch.setattr(config_mod.settings, "razorpay_key_secret", "secret")
    monkeypatch.setattr(config_mod.settings, "razorpay_webhook_secret", secret)

    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(DEMO_USER_ID), company_id=str(DEMO_COMPANY_ID), role=UserRole.OWNER)}"
    }
    invoice_id = await _create_issued_invoice(client, headers)

    payload = _payment_link_paid_payload(uuid.UUID(invoice_id))
    raw = json.dumps(payload).encode()
    sig = _signature(raw, secret)
    webhook = await client.post(
        "/api/v1/payments/webhooks/razorpay",
        content=raw,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert webhook.status_code == 204

    invoice = await client.get(f"/api/v1/invoices/{invoice_id}", headers=headers)
    assert invoice.json()["status"] == InvoiceStatus.PAID.value

    payments = await client.get(f"/api/v1/invoices/{invoice_id}/payments", headers=headers)
    assert payments.status_code == 200
    assert len(payments.json()) == 1
    assert payments.json()[0]["reference"] == f"{RAZORPAY_PAYMENT_REFERENCE_PREFIX}pay_test123"


@pytest.mark.asyncio
async def test_invoice_webhook_idempotent(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import config as config_mod

    secret = "whsec_invoice_test"
    monkeypatch.setattr(config_mod.settings, "use_mock_billing", False)
    monkeypatch.setattr(config_mod.settings, "razorpay_key_id", "rzp_test")
    monkeypatch.setattr(config_mod.settings, "razorpay_key_secret", "secret")
    monkeypatch.setattr(config_mod.settings, "razorpay_webhook_secret", secret)

    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(DEMO_USER_ID), company_id=str(DEMO_COMPANY_ID), role=UserRole.OWNER)}"
    }
    invoice_id = await _create_issued_invoice(client, headers)
    payload = _payment_link_paid_payload(uuid.UUID(invoice_id), payment_id="pay_dup")
    raw = json.dumps(payload).encode()
    sig = _signature(raw, secret)

    for _ in range(2):
        resp = await client.post(
            "/api/v1/payments/webhooks/razorpay",
            content=raw,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
        )
        assert resp.status_code == 204

    payments = await client.get(f"/api/v1/invoices/{invoice_id}/payments", headers=headers)
    assert len(payments.json()) == 1


@pytest.mark.asyncio
async def test_payment_summary_and_analytics(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    summary = await client.get("/api/v1/payments/summary", headers=auth_headers)
    assert summary.status_code == 200
    assert "collected_today" in summary.json()

    analytics = await client.get("/api/v1/payments/analytics", headers=auth_headers)
    assert analytics.status_code == 200
    body = analytics.json()
    assert "collected_week" in body
    assert "method_breakdown" in body


@pytest.mark.asyncio
async def test_csv_apply_match(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    from decimal import Decimal

    overdue = await client.get("/api/v1/collections/overdue", headers=auth_headers)
    items = overdue.json()["items"]
    if not items:
        pytest.skip("No overdue invoices in seed data")

    invoice_id = items[0]["invoice_id"]
    amount = Decimal(str(items[0]["amount_due"]))
    apply = await client.post(
        "/api/v1/payments/import-csv/apply",
        headers=auth_headers,
        json={
            "items": [
                {
                    "invoice_id": invoice_id,
                    "amount": str(amount),
                    "method": "BANK_TRANSFER",
                    "reference": "csv-test-ref",
                }
            ]
        },
    )
    assert apply.status_code == 200
    assert apply.json()["applied"] == 1
