import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import { fetchDashboard } from "./api";
import type { DashboardParams } from "./types";

export function useDashboard(params?: DashboardParams) {
  return useQuery({
    queryKey: QUERY_KEYS.DASHBOARD(params?.from, params?.to),
    queryFn: () => fetchDashboard(params),
  });
}
