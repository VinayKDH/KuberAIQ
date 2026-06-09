"""API tests for credit notes and GSTR exports."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _create_issued_invoice(client: AsyncClient, headers: dict[str, str]) -> str:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "CN Customer", "phone": "9123456780"},
        headers=headers,
    )
    customer_id = cust.json()["id"]
    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-01",
            "due_date": "2026-06-15",
            "status": "ISSUED",
            "items": [
                {
                    "description": "Goods",
                    "quantity": "2",
                    "unit_price": "1000",
                    "gst_rate": "18",
                    "unit": "NOS",
                    "hsn_sac": "8471",
                }
            ],
        },
        headers=headers,
    )
    assert inv.status_code == 201
    return inv.json()["id"]


@pytest.mark.asyncio
async def test_credit_note_reduces_outstanding(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    invoice_id = await _create_issued_invoice(client, auth_headers)
    before = await client.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
    amount_due_before = float(before.json()["amount_due"])

    cn = await client.post(
        f"/api/v1/invoices/{invoice_id}/credit-notes",
        json={"reason": "Returned goods"},
        headers=auth_headers,
    )
    assert cn.status_code == 201
    assert cn.json()["invoice_number"].startswith("CN/")

    after = await client.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
    assert float(after.json()["amount_due"]) < amount_due_before

    listing = await client.get(f"/api/v1/invoices/{invoice_id}/credit-notes", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


@pytest.mark.asyncio
async def test_gstr_exports(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await _create_issued_invoice(client, auth_headers)
    gstr1 = await client.get(
        "/api/v1/invoices/reports/gstr1?from=2026-06-01&to=2026-06-30",
        headers=auth_headers,
    )
    assert gstr1.status_code == 200
    data = gstr1.json()
    assert "b2b" in data
    assert "metadata" in data

    gstr3b = await client.get(
        "/api/v1/invoices/reports/gstr3b?from=2026-06-01&to=2026-06-30",
        headers=auth_headers,
    )
    assert gstr3b.status_code == 200
    assert float(gstr3b.json()["outward_taxable"]) > 0


@pytest.mark.asyncio
async def test_compliance_alerts_preview(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.get("/api/v1/compliance/alerts/preview", headers=auth_headers)
    assert resp.status_code == 200
    assert "alerts" in resp.json()
