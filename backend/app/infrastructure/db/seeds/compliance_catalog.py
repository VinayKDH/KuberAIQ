"""Seed data for compliance obligation catalog."""
from __future__ import annotations

from app.domain.compliance.catalog import COMPLIANCE_CATALOG


def compliance_catalog_rows() -> list[dict]:
    return [
        {
            "id": item.id,
            "category": item.category,
            "title": item.title,
            "description": item.description,
            "frequency": item.frequency,
            "priority": item.priority,
            "action_route": item.action_route,
            "sort_order": idx,
        }
        for idx, item in enumerate(COMPLIANCE_CATALOG)
    ]
