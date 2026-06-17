import { apiClient, downloadBlob, PaginatedResponse } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type {
  CreateCustomerInput,
  Customer,
  CustomerHistory,
  CustomerLedger,
  CustomerListParams,
  UpdateCustomerInput,
} from "./types";

export function fetchCustomers(params?: CustomerListParams) {
  return apiClient<PaginatedResponse<Customer>>(API_PATHS.CUSTOMERS, { params });
}

export function fetchCustomer(id: string) {
  return apiClient<Customer>(`${API_PATHS.CUSTOMERS}/${id}`);
}

export function fetchCustomerHistory(id: string) {
  return apiClient<CustomerHistory>(`${API_PATHS.CUSTOMERS}/${id}/history`);
}

export function fetchCustomerLedger(id: string) {
  return apiClient<CustomerLedger>(API_PATHS.CUSTOMER_LEDGER(id));
}

export function createCustomer(input: CreateCustomerInput) {
  return apiClient<Customer>(API_PATHS.CUSTOMERS, {
    method: "POST",
    body: input,
  });
}

export function updateCustomer(id: string, input: UpdateCustomerInput) {
  return apiClient<Customer>(`${API_PATHS.CUSTOMERS}/${id}`, {
    method: "PATCH",
    body: input,
  });
}

export function downloadCustomerStatement(id: string, fallbackFilename: string) {
  return downloadBlob(API_PATHS.CUSTOMER_STATEMENT(id), fallbackFilename);
}
