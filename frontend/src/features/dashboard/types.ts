export interface AgingBucket {
  bucket: string;
  invoices: number;
  outstanding: number;
}

export interface CashflowPeriod {
  period: string;
  expected_inflow: number;
}

export interface CashflowForecastDay {
  date: string;
  expected_inflow: number;
  cumulative_balance: number;
}

export interface CashflowAlert {
  triggered: boolean;
  projected_minimum: number;
  buffer: number;
  shortfall_date: string | null;
  message: string;
}

export interface TopCustomer {
  customer_id: string;
  name: string;
  revenue: number;
}

export interface TopProduct {
  description: string;
  revenue: number;
  share_pct: number;
}

export interface ComplianceAlert {
  triggered: boolean;
  overdue_count: number;
  due_this_week_count: number;
  health_score: number;
  message: string;
}

export interface PaymentSummary {
  collected_today: number;
  recent_payments: Array<{
    id: string;
    invoice_id: string;
    invoice_number?: string | null;
    amount: number;
    paid_on: string;
    method: string;
  }>;
}

export interface PaymentAnalytics {
  collected_week: number;
  collected_month: number;
  method_breakdown: Array<{ method: string; amount: number }>;
}

export interface DashboardData {
  revenue: number;
  pending: number;
  overdue: number;
  aging: AgingBucket[];
  cashflow: CashflowPeriod[];
  cashflow_forecast: CashflowForecastDay[];
  cashflow_alert: CashflowAlert;
  compliance_alert?: ComplianceAlert | null;
  top_customers: TopCustomer[];
  top_products: TopProduct[];
  payment_summary?: PaymentSummary | null;
  payment_analytics?: PaymentAnalytics | null;
}

export interface DashboardParams {
  from?: string;
  to?: string;
}
