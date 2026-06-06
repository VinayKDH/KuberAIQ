import { apiClient, PaginatedResponse } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type { Customer, CustomerListParams } from "./types";

export function fetchCustomers(params?: CustomerListParams) {
  return apiClient<PaginatedResponse<Customer>>(API_PATHS.CUSTOMERS, { params });
}

export function fetchCustomer(id: string) {
  return apiClient<Customer>(`${API_PATHS.CUSTOMERS}/${id}`);
}
