export interface OverdueInvoice {
  id: string;
  invoice_number: string;
  customer_name: string;
  customer_phone: string;
  due_date: string;
  days_overdue: number;
  amount_due: number;
  last_reminder_at?: string;
  last_reminder_channel?: string;
}

export interface CollectionsDashboard {
  total_overdue: number;
  overdue_count: number;
  reminded_today: number;
}

export interface OverdueListParams {
  page?: number;
  page_size?: number;
  sort?: string;
}
