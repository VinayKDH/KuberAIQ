import { apiClient, PaginatedResponse } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type { Invoice, InvoiceListParams } from "./types";

export function fetchInvoices(params?: InvoiceListParams) {
  return apiClient<PaginatedResponse<Invoice>>(API_PATHS.INVOICES, { params });
}

export function fetchInvoice(id: string) {
  return apiClient<Invoice>(`${API_PATHS.INVOICES}/${id}`);
}
