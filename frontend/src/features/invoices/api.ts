import { apiClient, downloadBlob, PaginatedResponse } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type {
  CreateCreditNoteInput,
  CreateInvoiceInput,
  CreditNote,
  Invoice,
  InvoiceListParams,
  Payment,
  RecordPaymentInput,
} from "./types";

export function fetchInvoices(params?: InvoiceListParams) {
  return apiClient<PaginatedResponse<Invoice>>(API_PATHS.INVOICES, { params });
}

export function fetchInvoice(id: string) {
  return apiClient<Invoice>(`${API_PATHS.INVOICES}/${id}`);
}

export function createInvoice(input: CreateInvoiceInput) {
  return apiClient<Invoice>(API_PATHS.INVOICES, {
    method: "POST",
    body: input,
  });
}

export function issueInvoice(id: string) {
  return apiClient<Invoice>(`${API_PATHS.INVOICES}/${id}:issue`, { method: "POST" });
}

export function cancelInvoice(id: string, reason: string) {
  return apiClient<Invoice>(`${API_PATHS.INVOICES}/${id}:cancel`, {
    method: "POST",
    body: { reason },
  });
}

export function recordPayment(invoiceId: string, input: RecordPaymentInput) {
  return apiClient(`${API_PATHS.INVOICES}/${invoiceId}/payments`, {
    method: "POST",
    body: input,
  });
}

export function fetchInvoicePayments(invoiceId: string) {
  return apiClient<Payment[]>(`${API_PATHS.INVOICES}/${invoiceId}/payments`);
}

export function reversePayment(invoiceId: string, paymentId: string) {
  return apiClient<Payment>(
    `${API_PATHS.INVOICES}/${invoiceId}/payments/${paymentId}:reverse`,
    { method: "POST" },
  );
}

export function downloadInvoicePdf(id: string) {
  return downloadBlob(`${API_PATHS.INVOICES}/${id}/pdf/download`, `invoice-${id}.pdf`);
}

export function shareInvoiceWhatsApp(id: string) {
  return apiClient<{ provider_message_id: string }>(
    `${API_PATHS.INVOICES}/${id}:share-whatsapp`,
    { method: "POST" },
  );
}

export function createInvoicePaymentLink(id: string) {
  return apiClient<{ url: string | null; provider: string }>(API_PATHS.INVOICE_PAYMENT_LINK(id), {
    method: "POST",
  });
}

export function registerInvoiceIrn(id: string, irn: string) {
  return apiClient<Invoice>(`${API_PATHS.INVOICES}/${id}/irn`, {
    method: "POST",
    body: { irn },
  });
}

export function fetchCreditNotes(invoiceId: string) {
  return apiClient<CreditNote[]>(API_PATHS.INVOICE_CREDIT_NOTES(invoiceId));
}

export function createCreditNote(invoiceId: string, input: CreateCreditNoteInput) {
  return apiClient<CreditNote>(API_PATHS.INVOICE_CREDIT_NOTES(invoiceId), {
    method: "POST",
    body: input,
  });
}
