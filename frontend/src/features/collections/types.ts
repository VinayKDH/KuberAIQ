export interface OverdueInvoice {
  id: string;
  invoice_number: string;
  customer_name: string;
  customer_phone?: string | null;
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

export interface ReminderResponse {
  reminder_id: string;
  status: string;
  provider_message_id?: string | null;
}

export interface ReminderPreview {
  invoice_id: string;
  customer_name: string;
  days_overdue: number;
  amount_due: number;
  language: string;
  message: string;
}

export interface BulkReminderPreview {
  count: number;
  total_outstanding: number;
}

export interface OverdueListParams {
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface CallTodayInvoice {
  id: string;
  invoice_id: string;
  invoice_number: string | null;
  customer_name: string;
  customer_phone?: string | null;
  amount_due: number;
  days_overdue: number;
  days_until_due: number;
  priority_score: number;
  due_date: string;
  last_reminder_at?: string | null;
  last_reminder_channel?: string | null;
}
