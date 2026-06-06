import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import { fetchCustomer, fetchCustomers } from "./api";
import type { CustomerListParams } from "./types";

export function useCustomers(params?: CustomerListParams) {
  return useQuery({
    queryKey: QUERY_KEYS.CUSTOMERS(params),
    queryFn: () => fetchCustomers(params),
  });
}

export function useCustomer(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.CUSTOMER(id),
    queryFn: () => fetchCustomer(id),
    enabled: !!id,
  });
}
