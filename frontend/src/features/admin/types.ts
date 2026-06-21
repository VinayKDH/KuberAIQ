export interface AdminDashboardMetrics {
  total_tenants: number;
  active_tenants: number;
  suspended_tenants: number;
  active_users: number;
  invoices_this_month: number;
  ai_sessions_total: number;
  ai_tokens_this_month: number;
  collections_volume_this_month: number;
  subscription_breakdown: Record<string, number>;
}

export interface AdminTenantListItem {
  company_id: string;
  legal_name: string;
  gstin: string | null;
  msme_segment: string | null;
  is_active: boolean;
  created_at: string;
  user_count: number;
  invoice_count: number;
  last_activity_at: string | null;
  owner_email: string | null;
  subscription_status: string;
}

export interface AdminTenantListResponse {
  items: AdminTenantListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminTenantDetail {
  company_id: string;
  legal_name: string;
  gstin: string | null;
  state_code: string;
  address: string | null;
  msme_segment: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  owner_email: string | null;
  subscription_status: string;
  plan_code: string | null;
  user_count: number;
  invoice_count: number;
  compliance_overdue_count: number;
  users: Array<{
    id: string;
    email: string;
    full_name: string | null;
    role: string;
    is_active: boolean;
  }>;
  recent_invoices: Array<{
    id: string;
    invoice_number: string | null;
    status: string;
    grand_total: number;
    issue_date: string;
  }>;
  ai_usage: {
    tokens_this_month: number;
    sessions_count: number;
  };
}

export interface AdminUserListItem {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  company_id: string | null;
  company_name: string | null;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AdminUserListResponse {
  items: AdminUserListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminAiUsageResponse {
  tokens_this_month: number;
  tokens_total: number;
  sessions_total: number;
  by_tenant: Array<{
    company_id: string;
    company_name: string;
    tokens_this_month: number;
    tokens_total: number;
    sessions_count: number;
  }>;
}

export interface AdminSystemHealth {
  environment: string;
  auth_mode: string;
  llm_mode: string;
  blob_mode: string;
  whatsapp_mode: string;
  billing_mode: string;
  google_oauth_configured: boolean;
  entra_oauth_configured: boolean;
  azure_openai_configured: boolean;
  azure_blob_configured: boolean;
  whatsapp_configured: boolean;
  razorpay_configured: boolean;
  razorpay_webhook_configured: boolean;
  admin_api_key_configured: boolean;
}

export interface AdminAuditLogItem {
  id: string;
  company_id: string;
  company_name: string | null;
  entity_type: string;
  entity_id: string | null;
  action: string;
  actor_user_id: string | null;
  ip_address: string | null;
  created_at: string;
}

export interface AdminAuditLogListResponse {
  items: AdminAuditLogItem[];
  total: number;
  page: number;
  page_size: number;
}
