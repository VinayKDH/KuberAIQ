export interface AgingBucket {
  bucket: string;
  invoices: number;
  outstanding: number;
}

export interface CashflowPeriod {
  period: string;
  expected_inflow: number;
}

export interface TopCustomer {
  customer_id: string;
  name: string;
  revenue: number;
}

export interface DashboardData {
  revenue: number;
  pending: number;
  overdue: number;
  aging: AgingBucket[];
  cashflow: CashflowPeriod[];
  top_customers: TopCustomer[];
}

export interface DashboardParams {
  from?: string;
  to?: string;
}
