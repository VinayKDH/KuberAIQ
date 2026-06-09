import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import {
  convertQuotation,
  createQuotation,
  downloadQuotationPdf,
  fetchQuotation,
  fetchQuotationPdf,
  fetchQuotations,
  sendQuotation,
  updateQuotation,
} from "./api";
import type { CreateQuotationInput, QuotationListParams, UpdateQuotationInput } from "./types";

export function useQuotations(params?: QuotationListParams) {
  return useQuery({
    queryKey: QUERY_KEYS.QUOTATIONS(params),
    queryFn: () => fetchQuotations(params),
  });
}

export function useQuotation(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.QUOTATION(id),
    queryFn: () => fetchQuotation(id),
    enabled: Boolean(id),
  });
}

export function useCreateQuotation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateQuotationInput) => createQuotation(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quotations"] }),
  });
}

export function useUpdateQuotation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateQuotationInput }) =>
      updateQuotation(id, input),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["quotations"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.QUOTATION(id) });
    },
  });
}

export function useSendQuotation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => sendQuotation(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["quotations"] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.QUOTATION(id) });
    },
  });
}

export function useConvertQuotation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => convertQuotation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["quotations"] });
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
    },
  });
}

export function useQuotationPdf() {
  return useMutation({
    mutationFn: (id: string) => fetchQuotationPdf(id),
  });
}

export function useDownloadQuotationPdf() {
  return useMutation({
    mutationFn: ({ id, filename }: { id: string; filename: string }) =>
      downloadQuotationPdf(id, filename),
  });
}
