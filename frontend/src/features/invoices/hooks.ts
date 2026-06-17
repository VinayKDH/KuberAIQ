import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import {
  cancelInvoice,
  createInvoice,
  fetchInvoice,
  fetchInvoices,
  fetchInvoicePayments,
  issueInvoice,
  recordPayment,
  reversePayment,
  shareInvoiceWhatsApp,
  downloadInvoicePdf,
  registerInvoiceIrn,
  createCreditNote,
  fetchCreditNotes,
  createInvoicePaymentLink,
} from "./api";
import type { CreateInvoiceInput, CreateCreditNoteInput, InvoiceListParams, RecordPaymentInput } from "./types";

export function useInvoices(params?: InvoiceListParams) {
  return useQuery({
    queryKey: QUERY_KEYS.INVOICES(params),
    queryFn: () => fetchInvoices(params),
  });
}

export function useInvoice(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.INVOICE(id),
    queryFn: () => fetchInvoice(id),
    enabled: !!id,
  });
}

export function useInvoicePayments(invoiceId: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.INVOICE(invoiceId), "payments"],
    queryFn: () => fetchInvoicePayments(invoiceId),
    enabled: !!invoiceId,
  });
}

export function useCreateInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateInvoiceInput) => createInvoice(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useIssueInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => issueInvoice(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.INVOICE(id) });
    },
  });
}

export function useCancelInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => cancelInvoice(id, reason),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.INVOICE(id) });
    },
  });
}

export function useRecordPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ invoiceId, input }: { invoiceId: string; input: RecordPaymentInput }) =>
      recordPayment(invoiceId, input),
    onSuccess: (_data, { invoiceId }) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.INVOICE(invoiceId) });
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEYS.INVOICE(invoiceId), "payments"] });
      queryClient.invalidateQueries({ queryKey: ["collections"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDownloadInvoicePdf() {
  return useMutation({
    mutationFn: (id: string) => downloadInvoicePdf(id),
  });
}

export function useShareInvoiceWhatsApp() {
  return useMutation({
    mutationFn: (id: string) => shareInvoiceWhatsApp(id),
  });
}

export function useCreateInvoicePaymentLink() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => createInvoicePaymentLink(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.INVOICE(id) });
    },
  });
}

export function useRegisterInvoiceIrn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, irn }: { id: string; irn: string }) => registerInvoiceIrn(id, irn),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.INVOICE(id) });
      queryClient.invalidateQueries({ queryKey: ["compliance"] });
    },
  });
}

export function useReversePayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ invoiceId, paymentId }: { invoiceId: string; paymentId: string }) =>
      reversePayment(invoiceId, paymentId),
    onSuccess: (_data, { invoiceId }) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.INVOICE(invoiceId) });
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEYS.INVOICE(invoiceId), "payments"] });
      queryClient.invalidateQueries({ queryKey: ["collections"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useCreditNotes(invoiceId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.CREDIT_NOTES(invoiceId),
    queryFn: () => fetchCreditNotes(invoiceId),
    enabled: Boolean(invoiceId),
  });
}

export function useCreateCreditNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ invoiceId, input }: { invoiceId: string; input: CreateCreditNoteInput }) =>
      createCreditNote(invoiceId, input),
    onSuccess: (_data, { invoiceId }) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.INVOICE(invoiceId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CREDIT_NOTES(invoiceId) });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
