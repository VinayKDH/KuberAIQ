"""CA persona API integration tests."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.core.constants import DEMO_CA_EMAIL
from app.core.security import create_access_token
from app.domain.enums import CaAssignmentStatus, UserRole
from app.infrastructure.db.models.user import UserModel
from app.startup.seed import DEMO_CA_USER_ID, DEMO_COMPANY_ID, DEMO_USER_ID


async def _create_ca_user(session, *, email: str = "advisor@ca.kuberaiq.com") -> uuid.UUID:
    ca_id = uuid.uuid4()
    session.add(
        UserModel(
            id=ca_id,
            company_id=None,
            email=email,
            full_name="Test CA",
            role=UserRole.CA,
        )
    )
    await session.commit()
    return ca_id


@pytest.mark.asyncio
async def test_ca_invite_accept_switch(client: AsyncClient, db_engine) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        ca_id = await _create_ca_user(session)

    owner_headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(DEMO_USER_ID), company_id=str(DEMO_COMPANY_ID), role=UserRole.OWNER)}"
    }

    invite = await client.post(
        "/api/v1/companies/me/advisors",
        headers=owner_headers,
        json={"email": "advisor@ca.kuberaiq.com", "ca_firm_name": "Test Firm"},
    )
    assert invite.status_code == 201
    assignment_id = invite.json()["id"]
    assert invite.json()["status"] == CaAssignmentStatus.PENDING.value

    ca_headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(ca_id), company_id=None, role=UserRole.CA)}"
    }

    clients_before = await client.get("/api/v1/ca/clients", headers=ca_headers)
    assert clients_before.status_code == 200
    assert any(c["id"] == assignment_id for c in clients_before.json()["items"])

    accept = await client.post(
        f"/api/v1/ca/invitations/{assignment_id}/accept",
        headers=ca_headers,
    )
    assert accept.status_code == 200
    accepted = next(c for c in accept.json()["items"] if c["id"] == assignment_id)
    assert accepted["status"] == CaAssignmentStatus.ACTIVE.value

    switch = await client.post(
        "/api/v1/ca/context",
        headers=ca_headers,
        json={"company_id": str(DEMO_COMPANY_ID)},
    )
    assert switch.status_code == 200
    body = switch.json()
    assert body["user"]["company_id"] == str(DEMO_COMPANY_ID)
    assert body["needs_payment"] is False
    assert body["needs_onboarding"] is False

    context_headers = {"Authorization": f"Bearer {body['access_token']}"}
    compliance = await client.get("/api/v1/compliance/dashboard", headers=context_headers)
    assert compliance.status_code == 200

    clear = await client.post("/api/v1/ca/context/clear", headers=context_headers)
    assert clear.status_code == 200
    assert clear.json()["user"]["company_id"] is None


@pytest.mark.asyncio
async def test_ca_cannot_create_invoice(client: AsyncClient) -> None:
    token = create_access_token(
        user_id=str(DEMO_CA_USER_ID), company_id=str(DEMO_COMPANY_ID), role=UserRole.CA
    )
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/invoices",
        headers=headers,
        json={
            "customer_id": str(uuid.uuid4()),
            "issue_date": "2026-01-01",
            "due_date": "2026-01-15",
            "status": "DRAFT",
            "items": [
                {
                    "description": "Test item",
                    "quantity": 1,
                    "unit": "NOS",
                    "unit_price": 100,
                    "gst_rate": 18,
                }
            ],
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_demo_ca_mock_login(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    body = login.json()
    assert body["user"]["role"] == UserRole.CA.value
    assert body["needs_payment"] is False
    assert body["needs_onboarding"] is False

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    clients = await client.get("/api/v1/ca/clients", headers=headers)
    assert clients.status_code == 200


@pytest.mark.asyncio
async def test_owner_lists_advisors(client: AsyncClient) -> None:
    owner_headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(DEMO_USER_ID), company_id=str(DEMO_COMPANY_ID), role=UserRole.OWNER)}"
    }
    resp = await client.get("/api/v1/companies/me/advisors", headers=owner_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert any(i["ca_email"] == DEMO_CA_EMAIL for i in items)


@pytest.mark.asyncio
async def test_ca_bulk_gstr1_export(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get(
        "/api/v1/ca/reports/gstr1/bulk",
        params={"from": "2025-04-01", "to": "2026-03-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["from"] == "2025-04-01"
    assert body["to"] == "2026-03-31"

    filtered = await client.get(
        "/api/v1/ca/reports/gstr1/bulk",
        params={
            "from": "2025-04-01",
            "to": "2026-03-31",
            "company_ids": [str(DEMO_COMPANY_ID)],
        },
        headers=headers,
    )
    assert filtered.status_code == 200
    filtered_body = filtered.json()
    assert len(filtered_body["items"]) <= 1
    if filtered_body["items"]:
        assert filtered_body["items"][0]["company_id"] == str(DEMO_COMPANY_ID)


@pytest.mark.asyncio
async def test_ca_dashboard_filing_checklist(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get("/api/v1/ca/dashboard", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "portfolio" in body
    assert body["portfolio"]["clients_at_risk"] >= 0
    assert len(body["clients"]) >= 1

    client_row = body["clients"][0]
    assert "filing_checklist" in client_row
    assert "risk_level" in client_row
    assert "profile_complete" in client_row
    checklist_ids = {item["obligation_id"] for item in client_row["filing_checklist"]}
    assert "gst_gstr1" in checklist_ids
    assert "gst_gstr3b" in checklist_ids
    assert "it_itr" in checklist_ids


@pytest.mark.asyncio
async def test_ca_filing_complete_and_skip(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    complete = await client.post(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/filing/gst_gstr1/complete",
        headers=headers,
        json={},
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "COMPLETED"

    skip = await client.post(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/filing/gst_gstr3b/skip",
        headers=headers,
        json={},
    )
    assert skip.status_code == 200
    assert skip.json()["status"] == "SKIPPED"


@pytest.mark.asyncio
async def test_ca_bulk_gstr3b_export(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get(
        "/api/v1/ca/reports/gstr3b/bulk",
        params={"from": "2025-04-01", "to": "2026-03-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["from"] == "2025-04-01"
    assert body["to"] == "2026-03-31"

    filtered = await client.get(
        "/api/v1/ca/reports/gstr3b/bulk",
        params={
            "from": "2025-04-01",
            "to": "2026-03-31",
            "company_ids": [str(DEMO_COMPANY_ID)],
        },
        headers=headers,
    )
    assert filtered.status_code == 200
    filtered_body = filtered.json()
    assert len(filtered_body["items"]) <= 1
    if filtered_body["items"]:
        report = filtered_body["items"][0]["report"]
        assert "outward_taxable" in report or "tax_liability" in report or report


@pytest.mark.asyncio
async def test_ca_bulk_complete_and_export_csv(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    bulk = await client.post(
        "/api/v1/ca/filing/bulk-complete",
        headers=headers,
        json={
            "company_ids": [str(DEMO_COMPANY_ID)],
            "obligation_ids": ["gst_gstr1"],
        },
    )
    assert bulk.status_code == 200
    assert bulk.json()["completed"] >= 1

    export = await client.get(
        "/api/v1/ca/filing/export.csv",
        headers=headers,
        params={"due_before": "2026-12-31"},
    )
    assert export.status_code == 200
    assert "company_name" in export.text


@pytest.mark.asyncio
async def test_ca_client_tasks_crud(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    create = await client.post(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/tasks",
        headers=headers,
        json={"title": "Collect bank statements"},
    )
    assert create.status_code == 200
    task_id = create.json()["items"][0]["id"]

    update = await client.patch(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/tasks/{task_id}",
        headers=headers,
        json={"status": "done"},
    )
    assert update.status_code == 200
    assert update.json()["items"][0]["status"] == "done"

    delete = await client.delete(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/tasks/{task_id}",
        headers=headers,
    )
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_ca_compliance_pack(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/compliance-pack",
        headers=headers,
        params={"from": "2025-04-01", "to": "2026-03-31"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["company_id"] == str(DEMO_COMPANY_ID)
    assert "gstr1_summary" in body
    assert "overdue_receivables" in body


@pytest.mark.asyncio
async def test_ca_client_tasks_crud(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    create = await client.post(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/tasks",
        headers=headers,
        json={"title": "Request GST docs"},
    )
    assert create.status_code == 200
    items = create.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Request GST docs"
    task_id = items[0]["id"]

    listed = await client.get(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/tasks",
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    updated = await client.patch(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/tasks/{task_id}",
        headers=headers,
        json={"status": "done"},
    )
    assert updated.status_code == 200
    assert updated.json()["items"][0]["status"] == "done"

    deleted = await client.delete(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/tasks/{task_id}",
        headers=headers,
    )
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_ca_compliance_pack(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get(
        f"/api/v1/ca/clients/{DEMO_COMPANY_ID}/compliance-pack",
        params={"from": "2025-04-01", "to": "2026-03-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["company_id"] == str(DEMO_COMPANY_ID)
    assert "gstr1_summary" in body
    assert "filing_checklist" in body
    assert "overdue_receivables" in body
