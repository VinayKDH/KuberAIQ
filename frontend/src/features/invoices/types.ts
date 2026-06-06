export interface InvoiceCustomer {
  id: string;
  name: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  status: string;
  customer: InvoiceCustomer;
  issue_date: string;
  due_date: string;
  grand_total: number;
  amount_due: number;
}

export interface InvoiceListParams {
  page?: number;
  page_size?: number;
  q?: string;
  status?: string;
  customer_id?: string;
  from?: string;
  to?: string;
  sort?: string;
}
