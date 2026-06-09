import { apiClient, PaginatedResponse } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type {
  BulkReminderPreview,
  CallTodayInvoice,
  CollectionsDashboard,
  OverdueInvoice,
  OverdueListParams,
  ReminderPreview,
  ReminderResponse,
} from "./types";

export function fetchOverdueInvoices(params?: OverdueListParams) {
  return apiClient<PaginatedResponse<OverdueInvoice>>(API_PATHS.COLLECTIONS_OVERDUE, {
    params,
  });
}

export function fetchCollectionsDashboard() {
  return apiClient<CollectionsDashboard>(API_PATHS.COLLECTIONS_DASHBOARD);
}

export function fetchCallToday() {
  return apiClient<CallTodayInvoice[]>(API_PATHS.COLLECTIONS_CALL_TODAY);
}

export function sendReminder(invoiceId: string, language = "en") {
  return apiClient<ReminderResponse>(API_PATHS.COLLECTIONS_REMINDERS, {
    method: "POST",
    body: { invoice_id: invoiceId, language },
  });
}

export function previewReminder(invoiceId: string, language = "en") {
  return apiClient<ReminderPreview>(API_PATHS.COLLECTIONS_REMINDER_PREVIEW, {
    params: { invoice_id: invoiceId, language },
  });
}

export function bulkReminderPreview() {
  return apiClient<BulkReminderPreview>(API_PATHS.COLLECTIONS_BULK_PREVIEW, {
    method: "POST",
  });
}

export function bulkSendReminders() {
  return apiClient<ReminderResponse[]>(API_PATHS.COLLECTIONS_BULK_SEND, {
    method: "POST",
  });
}
