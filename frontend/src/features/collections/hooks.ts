import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import { fetchCollectionsDashboard, fetchOverdueInvoices } from "./api";
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
