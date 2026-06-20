export interface CaClientAssignment {
  id: string;
  ca_user_id: string;
  company_id: string;
  status: string;
  invited_by: string;
  ca_firm_name?: string | null;
  created_at?: string | null;
  company_name?: string | null;
  gstin?: string | null;
  ca_email?: string | null;
  ca_full_name?: string | null;
}

export interface CaClientsResponse {
  items: CaClientAssignment[];
}

export interface CaUpcomingFiling {
  title?: string | null;
  due_date?: string | null;
  status?: string | null;
  obligation_id?: string | null;
}

export interface CaFilingChecklistItem {
  obligation_id: string;
  title: string;
  due_date?: string | null;
  status: string;
  period_key?: string | null;
}

export interface CaDashboardClient {
  company_id: string;
  company_name: string;
  gstin?: string | null;
  upcoming_filings: CaUpcomingFiling[];
  filing_checklist: CaFilingChecklistItem[];
  health_score?: number | null;
  overdue_total?: number | null;
  profile_complete?: boolean;
  filings_due_soon?: number;
  compliance_overdue?: number;
  compliance_due_this_week?: number;
  risk_level?: "high" | "medium" | "low";
}

export interface CaPortfolioSummary {
  avg_health_score?: number | null;
  clients_at_risk: number;
  total_overdue: number;
  filings_due_soon: number;
}

export interface CaBulkGstrResponse {
  from: string;
  to: string;
  items: Array<{
    company_id: string;
    company_name: string;
    gstin?: string | null;
    report: Record<string, unknown>;
  }>;
}

export interface CaDashboardResponse {
  clients: CaDashboardClient[];
  client_count: number;
  portfolio?: CaPortfolioSummary | null;
}

export interface AdvisorsResponse {
  items: CaClientAssignment[];
}

export interface InviteAdvisorPayload {
  email: string;
  ca_firm_name?: string;
}

export interface CaClientTask {
  id: string;
  company_id: string;
  title: string;
  description?: string | null;
  due_date?: string | null;
  status: string;
  created_at?: string | null;
}

export interface CaClientTasksResponse {
  items: CaClientTask[];
}

export interface CaBulkFilingResponse {
  completed: number;
}

