import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import {
  bulkReminderPreview,
  bulkSendReminders,
  fetchCallToday,
  fetchCollectionsDashboard,
  fetchOverdueInvoices,
  previewReminder,
  sendReminder,
} from "./api";
import type { OverdueListParams } from "./types";

export function useOverdueInvoices(params?: OverdueListParams) {
  return useQuery({
    queryKey: QUERY_KEYS.COLLECTIONS_OVERDUE(params),
    queryFn: () => fetchOverdueInvoices(params),
  });
}

export function useCollectionsDashboard() {
  return useQuery({
    queryKey: QUERY_KEYS.COLLECTIONS_DASHBOARD,
    queryFn: fetchCollectionsDashboard,
  });
}

export function useCallToday() {
  return useQuery({
    queryKey: QUERY_KEYS.COLLECTIONS_CALL_TODAY,
    queryFn: fetchCallToday,
  });
}

export function useSendReminder(language = "en") {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (invoiceId: string) => sendReminder(invoiceId, language),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}

export function useReminderPreview(invoiceId: string, enabled: boolean, language = "en") {
  return useQuery({
    queryKey: ["collections", "reminder-preview", invoiceId, language],
    queryFn: () => previewReminder(invoiceId, language),
    enabled: enabled && !!invoiceId,
  });
}

export function useBulkReminderPreview() {
  return useMutation({
    mutationFn: () => bulkReminderPreview(),
  });
}

export function useBulkSendReminders() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => bulkSendReminders(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}
