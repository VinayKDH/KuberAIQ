import { apiClient, downloadBlob, PaginatedResponse } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type {
  ConvertQuotationResponse,
  CreateQuotationInput,
  Quotation,
  QuotationListParams,
  UpdateQuotationInput,
} from "./types";

export function fetchQuotations(params?: QuotationListParams) {
  return apiClient<PaginatedResponse<Quotation>>(API_PATHS.QUOTATIONS, { params });
}

export function fetchQuotation(id: string) {
  return apiClient<Quotation>(`${API_PATHS.QUOTATIONS}/${id}`);
}

export function createQuotation(input: CreateQuotationInput) {
  return apiClient<Quotation>(API_PATHS.QUOTATIONS, { method: "POST", body: input });
}

export function updateQuotation(id: string, input: UpdateQuotationInput) {
  return apiClient<Quotation>(`${API_PATHS.QUOTATIONS}/${id}`, { method: "PATCH", body: input });
}

export function sendQuotation(id: string) {
  return apiClient<Quotation>(API_PATHS.QUOTATION_SEND(id), { method: "POST" });
}

export function convertQuotation(id: string) {
  return apiClient<ConvertQuotationResponse>(API_PATHS.QUOTATION_CONVERT(id), { method: "POST" });
}

export function fetchQuotationPdf(id: string) {
  return apiClient<{ path: string; signed_url: string }>(API_PATHS.QUOTATION_PDF(id));
}

export function downloadQuotationPdf(id: string, filename: string) {
  return downloadBlob(API_PATHS.QUOTATION_PDF_DOWNLOAD(id), filename);
}
