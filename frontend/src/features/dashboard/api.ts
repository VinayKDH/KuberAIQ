import { apiClient } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type { DashboardData, DashboardParams } from "./types";

export function fetchDashboard(params?: DashboardParams) {
  return apiClient<DashboardData>(API_PATHS.DASHBOARD, { params });
}
