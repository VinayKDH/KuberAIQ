import { apiClient, PaginatedResponse } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type { CollectionsDashboard, OverdueInvoice, OverdueListParams } from "./types";

export function fetchOverdueInvoices(params?: OverdueListParams) {
  return apiClient<PaginatedResponse<OverdueInvoice>>(API_PATHS.COLLECTIONS_OVERDUE, {
    params,
  });
}

export function fetchCollectionsDashboard() {
  return apiClient<CollectionsDashboard>(API_PATHS.COLLECTIONS_DASHBOARD);
}
