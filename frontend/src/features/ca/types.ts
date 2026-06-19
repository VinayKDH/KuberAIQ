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

export interface CaDashboardClient {
  company_id: string;
  company_name: string;
  gstin?: string | null;
  upcoming_filings: CaUpcomingFiling[];
  health_score?: number | null;
  overdue_total?: number | null;
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
}

export interface AdvisorsResponse {
  items: CaClientAssignment[];
}

export interface InviteAdvisorPayload {
  email: string;
  ca_firm_name?: string;
}
