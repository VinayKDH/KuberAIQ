"""Audit log API schemas."""
from __future__ import annotations

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    id: str
    entity_type: str
    entity_id: str | None
    action: str
    actor_user_id: str | None
    ip_address: str | None
    created_at: str


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int
