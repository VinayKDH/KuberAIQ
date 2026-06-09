import { apiClient } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type {
  ComplianceAlertsPreview,
  ComplianceCalendarResponse,
  ComplianceDashboard,
  ComplianceObligationsResponse,
  UpdateComplianceProfilePayload,
} from "./types";

export function fetchComplianceDashboard() {
  return apiClient<ComplianceDashboard>(API_PATHS.COMPLIANCE_DASHBOARD);
}

export function fetchComplianceObligations() {
  return apiClient<ComplianceObligationsResponse>(API_PATHS.COMPLIANCE_OBLIGATIONS);
}

export function fetchComplianceCalendar(days = 90) {
  return apiClient<ComplianceCalendarResponse>(API_PATHS.COMPLIANCE_CALENDAR, {
    params: { days: String(days) },
  });
}

export function completeComplianceObligation(
  obligationId: string,
  body: { period_key?: string; notes?: string },
) {
  return apiClient(API_PATHS.COMPLIANCE_COMPLETE(obligationId), {
    method: "POST",
    body,
  });
}

export function updateComplianceProfile(body: UpdateComplianceProfilePayload) {
  return apiClient(API_PATHS.COMPLIANCE_PROFILE, { method: "PATCH", body });
}

export function fetchComplianceAlertsPreview() {
  return apiClient<ComplianceAlertsPreview>(API_PATHS.COMPLIANCE_ALERTS_PREVIEW);
}
