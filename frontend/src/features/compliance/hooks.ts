import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import {
  completeComplianceObligation,
  fetchComplianceCalendar,
  fetchComplianceDashboard,
  fetchComplianceObligations,
  fetchComplianceAlertsPreview,
  updateComplianceProfile,
} from "./api";
import type { UpdateComplianceProfilePayload } from "./types";

export function useComplianceDashboard() {
  return useQuery({
    queryKey: QUERY_KEYS.COMPLIANCE,
    queryFn: fetchComplianceDashboard,
  });
}

export function useComplianceObligations() {
  return useQuery({
    queryKey: QUERY_KEYS.COMPLIANCE_OBLIGATIONS,
    queryFn: fetchComplianceObligations,
  });
}

export function useComplianceCalendar(days = 90) {
  return useQuery({
    queryKey: QUERY_KEYS.COMPLIANCE_CALENDAR(days),
    queryFn: () => fetchComplianceCalendar(days),
  });
}

export function useComplianceAlertsPreview() {
  return useQuery({
    queryKey: QUERY_KEYS.COMPLIANCE_ALERTS,
    queryFn: fetchComplianceAlertsPreview,
  });
}

export function useCompleteComplianceObligation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      obligationId,
      periodKey,
      notes,
    }: {
      obligationId: string;
      periodKey: string;
      notes?: string;
    }) => completeComplianceObligation(obligationId, { period_key: periodKey, notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["compliance"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.DASHBOARD() });
    },
  });
}

export function useUpdateComplianceProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateComplianceProfilePayload) => updateComplianceProfile(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["compliance"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.COMPANY });
    },
  });
}
