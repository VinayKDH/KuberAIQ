"""Invoice API integration tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_invoice(client: AsyncClient, auth_headers: dict) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "ABC Traders", "phone": "9876543210"},
        headers=auth_headers,
    )
    assert cust.status_code == 201
    customer_id = cust.json()["id"]

    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-06",
            "due_date": "2026-06-21",
            "status": "ISSUED",
            "items": [
                {
                    "description": "OPC 53 Grade Cement",
                    "hsn_sac": "2523",
                    "quantity": 50,
                    "unit": "BAG",
                    "unit_price": 350.0,
                    "gst_rate": 18,
                }
            ],
        },
        headers=auth_headers,
    )
    assert inv.status_code == 201
    body = inv.json()
    assert body["status"] == "ISSUED"
    assert float(body["grand_total"]) == 20650.0
    assert body["invoice_number"] is not None

    listing = await client.get("/api/v1/invoices?status=ISSUED", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1
    assert listing.json()["items"][0]["customer"]["name"]


@pytest.mark.asyncio
async def test_record_payment(client: AsyncClient, auth_headers: dict) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "Pay Test Co", "phone": "9123456789"},
        headers=auth_headers,
    )
    customer_id = cust.json()["id"]
    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-06",
            "due_date": "2026-06-21",
            "status": "ISSUED",
            "items": [
                {
                    "description": "Item",
                    "quantity": 1,
                    "unit_price": 1000.0,
                    "gst_rate": 18,
                }
            ],
        },
        headers=auth_headers,
    )
    invoice_id = inv.json()["id"]
    pay = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"amount": 590.0, "paid_on": "2026-06-10", "method": "UPI"},
        headers=auth_headers,
    )
    assert pay.status_code == 201
    assert float(pay.json()["amount"]) == 590.0


async def _create_issued_invoice(client: AsyncClient, auth_headers: dict) -> str:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "PDF Test Co", "phone": "9111222333"},
        headers=auth_headers,
    )
    customer_id = cust.json()["id"]
    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-06",
            "due_date": "2026-06-21",
            "status": "ISSUED",
            "items": [
                {
                    "description": "Cement",
                    "quantity": 1,
                    "unit_price": 1000.0,
                    "gst_rate": 18,
                }
            ],
        },
        headers=auth_headers,
    )
    assert inv.status_code == 201
    return inv.json()["id"]


@pytest.mark.asyncio
async def test_invoice_pdf_metadata_and_download(client: AsyncClient, auth_headers: dict) -> None:
    invoice_id = await _create_issued_invoice(client, auth_headers)

    meta = await client.get(f"/api/v1/invoices/{invoice_id}/pdf", headers=auth_headers)
    assert meta.status_code == 200
    body = meta.json()
    assert body["path"].endswith(".pdf")
    assert body["signed_url"]

    download = await client.get(
        f"/api/v1/invoices/{invoice_id}/pdf/download",
        headers=auth_headers,
    )
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_invoice_pdf_includes_upi_when_configured(
    client: AsyncClient, auth_headers: dict
) -> None:
    await client.patch(
        "/api/v1/companies/me",
        json={"upi_id": "merchant@upi", "upi_payee_name": "Demo Traders"},
        headers=auth_headers,
    )
    invoice_id = await _create_issued_invoice(client, auth_headers)
    download = await client.get(
        f"/api/v1/invoices/{invoice_id}/pdf/download",
        headers=auth_headers,
    )
    assert download.status_code == 200
    assert download.content[:4] == b"%PDF"
    assert len(download.content) > 1000


@pytest.mark.asyncio
async def test_share_invoice_whatsapp(client: AsyncClient, auth_headers: dict) -> None:
    invoice_id = await _create_issued_invoice(client, auth_headers)
    response = await client.post(
        f"/api/v1/invoices/{invoice_id}:share-whatsapp",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["provider_message_id"]


@pytest.mark.asyncio
async def test_list_and_reverse_payment(client: AsyncClient, auth_headers: dict) -> None:
    invoice_id = await _create_issued_invoice(client, auth_headers)
    pay = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"amount": 590.0, "paid_on": "2026-06-10", "method": "UPI"},
        headers=auth_headers,
    )
    assert pay.status_code == 201
    payment_id = pay.json()["id"]

    listing = await client.get(
        f"/api/v1/invoices/{invoice_id}/payments",
        headers=auth_headers,
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    reversed_pay = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments/{payment_id}:reverse",
        headers=auth_headers,
    )
    assert reversed_pay.status_code == 200

    invoice = await client.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
    assert invoice.json()["status"] == "ISSUED"
    assert float(invoice.json()["amount_due"]) == float(invoice.json()["grand_total"])
