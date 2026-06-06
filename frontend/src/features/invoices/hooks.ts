import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import { fetchInvoice, fetchInvoices } from "./api";
import type { InvoiceListParams } from "./types";

export function useInvoices(params?: InvoiceListParams) {
  return useQuery({
    queryKey: QUERY_KEYS.INVOICES(params),
    queryFn: () => fetchInvoices(params),
  });
}

export function useInvoice(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.INVOICE(id),
    queryFn: () => fetchInvoice(id),
    enabled: !!id,
  });
}
