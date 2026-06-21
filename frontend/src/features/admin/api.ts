import { API_PATHS } from "@/lib/constants";
import { adminClient } from "@/lib/admin-auth";
import type {
  AdminAiUsageResponse,
  AdminAuditLogListResponse,
  AdminDashboardMetrics,
  AdminSystemHealth,
  AdminTenantDetail,
  AdminTenantListResponse,
  AdminUserListResponse,
} from "@/features/admin/types";

export function fetchAdminDashboard() {
  return adminClient<AdminDashboardMetrics>(API_PATHS.ADMIN_DASHBOARD);
}

export function fetchAdminTenants(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  active_only?: boolean;
}) {
  return adminClient<AdminTenantListResponse>(API_PATHS.ADMIN_TENANTS, { params });
}

export function fetchAdminTenant(id: string) {
  return adminClient<AdminTenantDetail>(API_PATHS.ADMIN_TENANT_DETAIL(id));
}

export function updateAdminTenantStatus(id: string, is_active: boolean) {
  return adminClient<{ company_id: string; is_active: boolean }>(
    API_PATHS.ADMIN_TENANT_STATUS(id),
    { method: "PATCH", body: { is_active } },
  );
}

export function fetchAdminUsers(params?: { page?: number; page_size?: number; search?: string }) {
  return adminClient<AdminUserListResponse>(API_PATHS.ADMIN_USERS, { params });
}

export function fetchAdminAiUsage() {
  return adminClient<AdminAiUsageResponse>(API_PATHS.ADMIN_AI_USAGE);
}

export function fetchAdminSystemHealth() {
  return adminClient<AdminSystemHealth>(API_PATHS.ADMIN_SYSTEM_HEALTH);
}

export function fetchAdminAuditLogs(params?: {
  page?: number;
  page_size?: number;
  company_id?: string;
}) {
  return adminClient<AdminAuditLogListResponse>(API_PATHS.ADMIN_AUDIT_LOGS, { params });
}

export function resetAdminDemoData() {
  return adminClient<{ ok: boolean; message: string }>(API_PATHS.ADMIN_DEMO_RESET, {
    method: "POST",
  });
}
