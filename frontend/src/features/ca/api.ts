import { apiClient } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type { AuthTokens } from "@/lib/auth";
import type {
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
