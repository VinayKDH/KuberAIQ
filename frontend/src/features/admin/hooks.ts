import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchAdminAiUsage,
  fetchAdminAuditLogs,
  fetchAdminDashboard,
  fetchAdminSystemHealth,
  fetchAdminTenant,
  fetchAdminTenants,
  fetchAdminUsers,
  resetAdminDemoData,
  updateAdminTenantStatus,
} from "@/features/admin/api";
import { QUERY_KEYS } from "@/lib/constants";

export function useAdminDashboard() {
  return useQuery({
    queryKey: QUERY_KEYS.ADMIN_DASHBOARD,
    queryFn: fetchAdminDashboard,
  });
}

export function useAdminTenants(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  active_only?: boolean;
}) {
  return useQuery({
    queryKey: QUERY_KEYS.ADMIN_TENANTS(params),
    queryFn: () => fetchAdminTenants(params),
  });
}

export function useAdminTenant(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.ADMIN_TENANT(id),
    queryFn: () => fetchAdminTenant(id),
    enabled: Boolean(id),
  });
}

export function useAdminUsers(params?: { page?: number; page_size?: number; search?: string }) {
  return useQuery({
    queryKey: QUERY_KEYS.ADMIN_USERS(params),
    queryFn: () => fetchAdminUsers(params),
  });
}

export function useAdminAiUsage() {
  return useQuery({
    queryKey: QUERY_KEYS.ADMIN_AI_USAGE,
    queryFn: fetchAdminAiUsage,
  });
}

export function useAdminSystemHealth() {
  return useQuery({
    queryKey: QUERY_KEYS.ADMIN_SYSTEM,
    queryFn: fetchAdminSystemHealth,
  });
}

export function useAdminAuditLogs(params?: {
  page?: number;
  page_size?: number;
  company_id?: string;
}) {
  return useQuery({
    queryKey: QUERY_KEYS.ADMIN_AUDIT(params),
    queryFn: () => fetchAdminAuditLogs(params),
  });
}

export function useUpdateTenantStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updateAdminTenantStatus(id, is_active),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["admin"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ADMIN_TENANT(variables.id) });
    },
  });
}

export function useResetDemoData() {
  return useMutation({
    mutationFn: resetAdminDemoData,
  });
}
