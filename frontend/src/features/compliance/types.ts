export interface ComplianceDeadline {
  type: string;
  title: string;
  due_date: string;
  status: string;
  description: string;
}

export interface PendingEInvoice {
  invoice_id: string;
  invoice_number: string | null;
  issue_date: string;
  grand_total: number;
  days_since_issue: number;
  urgency: string;
}

export interface ComplianceAlert {
  triggered: boolean;
  overdue_count: number;
  due_this_week_count: number;
  health_score: number;
  message: string;
}

export interface ComplianceDashboard {
  disclaimer: string;
  deadlines: ComplianceDeadline[];
  e_invoice: {
    threshold: number;
    ytd_turnover: number;
    requires_e_invoice: boolean;
    pending_count: number;
    pending_invoices: PendingEInvoice[];
  };
  checklist: Array<{
    id: string;
    title: string;
    description: string;
    priority: string;
  }>;
  compliance_alert?: ComplianceAlert;
}

export interface ComplianceSummary {
  total_applicable: number;
  pending: number;
  completed: number;
  overdue: number;
  due_this_week: number;
  health_score: number;
}

export interface ComplianceObligation {
  id: string;
  category: string;
  title: string;
  description: string;
  frequency: string;
  priority: string;
  action_route: string | null;
  period_key: string;
  due_date: string;
  status: string;
  completed_at: string | null;
}

export interface ComplianceProfile {
  entity_type: string | null;
  turnover_band: string | null;
  gstr1_filing_frequency: string | null;
  employee_count: number | null;
  has_tds_applicable: boolean;
  udyam_number: string | null;
  has_gstin: boolean;
}

export interface ComplianceObligationsResponse {
  profile_complete: boolean;
  disclaimer: string;
  summary: ComplianceSummary;
  obligations: ComplianceObligation[];
  obligations_by_category: Record<string, ComplianceObligation[]>;
  not_applicable: Array<{
    id: string;
    category: string;
    title: string;
    reason: string;
  }>;
  profile: ComplianceProfile;
}

export interface ComplianceCalendarEvent {
  obligation_id: string;
  title: string;
  category: string;
  due_date: string;
  status: string;
  period_key: string;
  priority: string;
}

export interface ComplianceCalendarResponse {
  days: number;
  profile_complete: boolean;
  events: ComplianceCalendarEvent[];
}

export interface UpdateComplianceProfilePayload {
  entity_type?: string;
  turnover_band?: string;
  gstr1_filing_frequency?: string;
  employee_count?: number;
  udyam_number?: string;
  has_tds_applicable?: boolean;
}

export interface ComplianceAlertPreviewItem {
  id: string;
  title: string;
  due_date: string;
  days_until_due: number;
  status: string;
  category: string;
}

export interface ComplianceAlertsPreview {
  count: number;
  alerts: ComplianceAlertPreviewItem[];
  due_soon_days: number;
}
