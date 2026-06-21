"""Admin portal API schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AdminAuthVerifyResponse(BaseModel):
    ok: bool = True
    environment: str


class AdminDashboardMetrics(BaseModel):
    total_tenants: int
    active_tenants: int
    suspended_tenants: int
    active_users: int
    invoices_this_month: int
    ai_sessions_total: int
    ai_tokens_this_month: int
    collections_volume_this_month: float
    subscription_breakdown: dict[str, int]


class AdminTenantListItem(BaseModel):
    company_id: str
    legal_name: str
    gstin: str | None
    msme_segment: str | None
    is_active: bool
    created_at: str
    user_count: int
    invoice_count: int
    last_activity_at: str | None
    owner_email: str | None
    subscription_status: str


class AdminTenantListResponse(BaseModel):
    items: list[AdminTenantListItem]
    total: int
    page: int
    page_size: int


class AdminTenantUserItem(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool


class AdminTenantInvoiceItem(BaseModel):
    id: str
    invoice_number: str | None
    status: str
    grand_total: float
    issue_date: str


class AdminTenantAiUsage(BaseModel):
    tokens_this_month: int
    sessions_count: int


class AdminTenantDetail(BaseModel):
    company_id: str
    legal_name: str
    gstin: str | None
    state_code: str
    address: str | None
    msme_segment: str | None
    is_active: bool
    created_at: str
    updated_at: str
    owner_email: str | None
    subscription_status: str
    plan_code: str | None
    user_count: int
    invoice_count: int
    compliance_overdue_count: int
    users: list[AdminTenantUserItem]
    recent_invoices: list[AdminTenantInvoiceItem]
    ai_usage: AdminTenantAiUsage


class AdminUserListItem(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    company_id: str | None
    company_name: str | None
    is_active: bool
    created_at: str
    last_login_at: str | None = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    page_size: int


class AdminAiUsageTenantItem(BaseModel):
    company_id: str
    company_name: str
    tokens_this_month: int
    tokens_total: int
    sessions_count: int


class AdminAiUsageResponse(BaseModel):
    tokens_this_month: int
    tokens_total: int
    sessions_total: int
    by_tenant: list[AdminAiUsageTenantItem]


class AdminSystemHealthResponse(BaseModel):
    environment: str
    auth_mode: str
    llm_mode: str
    blob_mode: str
    whatsapp_mode: str
    billing_mode: str
    google_oauth_configured: bool
    entra_oauth_configured: bool
    azure_openai_configured: bool
    azure_blob_configured: bool
    whatsapp_configured: bool
    razorpay_configured: bool
    razorpay_webhook_configured: bool
    admin_api_key_configured: bool


class AdminAuditLogItem(BaseModel):
    id: str
    company_id: str
    company_name: str | None
    entity_type: str
    entity_id: str | None
    action: str
    actor_user_id: str | None
    ip_address: str | None
    created_at: str


class AdminAuditLogListResponse(BaseModel):
    items: list[AdminAuditLogItem]
    total: int
    page: int
    page_size: int


class AdminTenantStatusUpdate(BaseModel):
    is_active: bool


class AdminTenantStatusResponse(BaseModel):
    company_id: str
    is_active: bool


class AdminDemoResetResponse(BaseModel):
    ok: bool
    message: str
