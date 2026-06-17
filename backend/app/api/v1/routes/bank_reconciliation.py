"""Bank reconciliation routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import AuthContext, get_container, require_roles
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/import-csv")
async def import_payments_csv(
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    file: UploadFile = File(...),
) -> dict:
    raw = await file.read()
    suggestions = await container.payment_service.suggest_matches_from_csv(
        auth.company_id, raw.decode("utf-8")
    )
    return {"items": suggestions, "count": len(suggestions)}
