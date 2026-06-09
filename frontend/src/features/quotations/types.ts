export type QuotationStatus =
  | "DRAFT"
  | "SENT"
  | "ACCEPTED"
  | "REJECTED"
  | "EXPIRED"
  | "CONVERTED";

export interface QuotationLineInput {
  description: string;
  quantity: number;
  unit_price: number;
  gst_rate: number;
  hsn_sac?: string;
  unit?: string;
  product_id?: string;
}

export interface QuotationItem extends QuotationLineInput {
  line_no: number;
  taxable_amount: number | string;
  cgst_amount: number | string;
  sgst_amount: number | string;
  igst_amount: number | string;
  line_total: number | string;
}

export interface Quotation {
  id: string;
  quotation_number: string | null;
  status: QuotationStatus;
  customer_id: string;
  customer?: { id: string; name: string };
  issue_date: string;
  valid_until: string;
  items: QuotationItem[];
  taxable_amount: number | string;
  cgst_amount: number | string;
  sgst_amount: number | string;
  igst_amount: number | string;
  total_tax: number | string;
  round_off: number | string;
  grand_total: number | string;
  place_of_supply?: string | null;
  pdf_blob_path?: string | null;
  converted_invoice_id?: string | null;
}

export interface QuotationListParams {
  q?: string;
  status?: QuotationStatus;
  customer_id?: string;
  page?: number;
  page_size?: number;
}

export interface CreateQuotationInput {
  customer_id: string;
  issue_date: string;
  valid_until: string;
  items: QuotationLineInput[];
}

export interface UpdateQuotationInput {
  customer_id?: string;
  issue_date?: string;
  valid_until?: string;
  items?: QuotationLineInput[];
}

export interface ConvertQuotationResponse {
  quotation: Quotation;
  invoice_id: string;
}
