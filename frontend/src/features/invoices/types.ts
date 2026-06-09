export interface InvoiceCustomer {
  id: string;
  name: string;
}

export interface InvoiceItem {
  line_no: number;
  description: string;
  hsn_sac?: string | null;
  quantity: number | string;
  unit: string;
  unit_price: number | string;
  gst_rate: number | string;
  taxable_amount: number | string;
  cgst_amount: number | string;
  sgst_amount: number | string;
  igst_amount: number | string;
  line_total: number | string;
}

export interface Invoice {
  id: string;
  invoice_number: string | null;
  status: string;
  customer_id: string;
  customer?: InvoiceCustomer | null;
  issue_date: string;
  due_date: string;
  items?: InvoiceItem[];
  taxable_amount?: number | string;
  cgst_amount?: number | string;
  sgst_amount?: number | string;
  igst_amount?: number | string;
  total_tax?: number | string;
  round_off?: number | string;
  grand_total: number | string;
  amount_paid?: number | string;
  amount_due: number | string;
  place_of_supply?: string | null;
  pdf_blob_path?: string | null;
  irn?: string | null;
  irn_generated_at?: string | null;
}

export interface InvoiceLineInput {
  description: string;
  quantity: number;
  unit_price: number;
  gst_rate: number;
  hsn_sac?: string;
  unit?: string;
  product_id?: string;
}

export interface CreateInvoiceInput {
  customer_id: string;
  issue_date: string;
  due_date: string;
  status: "DRAFT" | "ISSUED";
  items: InvoiceLineInput[];
}

export interface RecordPaymentInput {
  amount: number;
  paid_on: string;
  method: string;
  reference?: string;
  note?: string;
}

export interface Payment {
  id: string;
  invoice_id: string;
  amount: number | string;
  paid_on: string;
  method: string;
  reference?: string | null;
  note?: string | null;
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

export interface CreditNote {
  id: string;
  invoice_number: string | null;
  status: string;
  issue_date: string;
  grand_total: number | string;
  credit_reason: string | null;
  original_invoice_id: string;
}

export interface CreateCreditNoteInput {
  reason: string;
}
