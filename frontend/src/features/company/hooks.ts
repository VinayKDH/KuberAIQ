import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { API_PATHS, QUERY_KEYS, type MsmeLoginSegmentId } from "@/lib/constants";
import {
  isMsmeSegmentId,
  resolveMsmeSegment,
  setStoredMsmeSegment,
} from "@/lib/msme-segment";

export interface CompanyProfile {
  id: string;
  legal_name: string;
  gstin: string | null;
  state_code: string;
  address: string | null;
  invoice_prefix: string;
  upi_id?: string | null;
  upi_payee_name?: string | null;
  auto_reminders_enabled?: boolean;
  default_reminder_language?: string;
  msme_segment?: string | null;
}

export function useCompanyProfile() {
  return useQuery({
    queryKey: QUERY_KEYS.COMPANY,
    queryFn: () => apiClient<CompanyProfile>(API_PATHS.COMPANY_ME),
  });
}

export function useMsmeSegment(): MsmeLoginSegmentId {
  const { data: company } = useCompanyProfile();
  useEffect(() => {
    if (isMsmeSegmentId(company?.msme_segment)) {
      setStoredMsmeSegment(company.msme_segment);
    }
  }, [company?.msme_segment]);
  return resolveMsmeSegment(company?.msme_segment);
}

export function isValidMsmeSegment(value: string | null | undefined): value is MsmeLoginSegmentId {
  return isMsmeSegmentId(value);
}
