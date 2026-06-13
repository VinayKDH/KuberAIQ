import { apiClient } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type { AuthTokens } from "@/lib/auth";
import type {
  CaClientsResponse,
  CaDashboardResponse,
  AdvisorsResponse,
  InviteAdvisorPayload,
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
