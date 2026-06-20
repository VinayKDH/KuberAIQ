import { apiClient } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type { AuthTokens } from "@/lib/auth";
import { downloadBlob } from "@/lib/api-client";
import type {
  CaBulkFilingResponse,
  CaClientTasksResponse,
  CaClientsResponse,
  CaDashboardResponse,
  AdvisorsResponse,
  InviteAdvisorPayload,
  CaBulkGstrResponse,
} from "./types";

export function fetchCaClients() {
  return apiClient<CaClientsResponse>(API_PATHS.CA_CLIENTS);
}

export function fetchCaDashboard() {
  return apiClient<CaDashboardResponse>(API_PATHS.CA_DASHBOARD);
}

export function acceptCaInvite(assignmentId: string) {
  return apiClient<CaClientsResponse>(API_PATHS.CA_ACCEPT_INVITE(assignmentId), {
    method: "POST",
  });
}

export function switchCaContext(companyId: string) {
  return apiClient<AuthTokens>(API_PATHS.CA_CONTEXT, {
    method: "POST",
    body: { company_id: companyId },
  });
}

export function clearCaContext() {
  return apiClient<AuthTokens>(API_PATHS.CA_CONTEXT_CLEAR, { method: "POST" });
}

export function fetchAdvisors() {
  return apiClient<AdvisorsResponse>(API_PATHS.ADVISORS);
}

export function inviteAdvisor(body: InviteAdvisorPayload) {
  return apiClient(API_PATHS.ADVISORS, { method: "POST", body });
}

export function revokeAdvisor(assignmentId: string) {
  return apiClient(API_PATHS.ADVISOR_REVOKE(assignmentId), { method: "DELETE" });
}

export function fetchCaBulkGstr1(params: {
  from: string;
  to: string;
  companyIds?: string[];
}) {
  const search = new URLSearchParams({ from: params.from, to: params.to });
  params.companyIds?.forEach((id) => search.append("company_ids", id));
  return apiClient<CaBulkGstrResponse>(`${API_PATHS.CA_GSTR1_BULK}?${search.toString()}`);
}

export function fetchCaBulkGstr3b(params: {
  from: string;
  to: string;
  companyIds?: string[];
}) {
  const search = new URLSearchParams({ from: params.from, to: params.to });
  params.companyIds?.forEach((id) => search.append("company_ids", id));
  return apiClient<CaBulkGstrResponse>(`${API_PATHS.CA_GSTR3B_BULK}?${search.toString()}`);
}

export function completeCaClientFiling(
  companyId: string,
  obligationId: string,
  periodKey?: string | null,
) {
  return apiClient(API_PATHS.CA_FILING_COMPLETE(companyId, obligationId), {
    method: "POST",
    body: { period_key: periodKey ?? null },
  });
}

export function skipCaClientFiling(
  companyId: string,
  obligationId: string,
  periodKey?: string | null,
) {
  return apiClient(API_PATHS.CA_FILING_SKIP(companyId, obligationId), {
    method: "POST",
    body: { period_key: periodKey ?? null },
  });
}

export function bulkCompleteCaFilings(body: {
  companyIds: string[];
  obligationIds: string[];
  periodKey?: string | null;
}) {
  return apiClient<CaBulkFilingResponse>(API_PATHS.CA_FILING_BULK_COMPLETE, {
    method: "POST",
    body: {
      company_ids: body.companyIds,
      obligation_ids: body.obligationIds,
      period_key: body.periodKey ?? null,
    },
  });
}

export function exportCaFilingCsv(params?: { dueBefore?: string; dueAfter?: string }) {
  return downloadBlob(
    API_PATHS.CA_FILING_EXPORT,
    "filing-status.csv",
    {
      due_before: params?.dueBefore,
      due_after: params?.dueAfter,
    },
  );
}

export function fetchCaClientTasks(companyId: string) {
  return apiClient<CaClientTasksResponse>(API_PATHS.CA_CLIENT_TASKS(companyId));
}

export function createCaClientTask(companyId: string, body: { title: string; description?: string }) {
  return apiClient<CaClientTasksResponse>(API_PATHS.CA_CLIENT_TASKS(companyId), {
    method: "POST",
    body,
  });
}

export function updateCaClientTask(
  companyId: string,
  taskId: string,
  body: { title?: string; description?: string; due_date?: string; status?: string },
) {
  return apiClient<CaClientTasksResponse>(API_PATHS.CA_CLIENT_TASK(companyId, taskId), {
    method: "PATCH",
    body,
  });
}

export function deleteCaClientTask(companyId: string, taskId: string) {
  return apiClient<void>(API_PATHS.CA_CLIENT_TASK(companyId, taskId), {
    method: "DELETE",
  });
}

export function fetchCaCompliancePack(companyId: string, from: string, to: string) {
  const search = new URLSearchParams({ from, to });
  return apiClient<Record<string, unknown>>(
    `${API_PATHS.CA_COMPLIANCE_PACK(companyId)}?${search.toString()}`,
  );
}
