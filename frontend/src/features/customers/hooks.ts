import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import {
  createCustomer,
  fetchCustomer,
  fetchCustomerHistory,
  fetchCustomerLedger,
  fetchCustomers,
  updateCustomer,
} from "./api";
import type { CreateCustomerInput, CustomerListParams, UpdateCustomerInput } from "./types";

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

export function useCustomerHistory(id: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.CUSTOMER(id), "history"],
    queryFn: () => fetchCustomerHistory(id),
    enabled: !!id,
  });
}

export function useCustomerLedger(id: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.CUSTOMER(id), "ledger"],
    queryFn: () => fetchCustomerLedger(id),
    enabled: !!id,
  });
}

export function useCreateCustomer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateCustomerInput) => createCustomer(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
    },
  });
}

export function useUpdateCustomer(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: UpdateCustomerInput) => updateCustomer(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CUSTOMER(id) });
    },
  });
}
