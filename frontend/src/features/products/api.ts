import { apiClient, PaginatedResponse } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import type {
  AdjustStockInput,
  CreateProductInput,
  HsnLookupResult,
  Product,
  ProductListParams,
  UpdateProductInput,
} from "./types";

export function fetchProducts(params?: ProductListParams) {
  return apiClient<PaginatedResponse<Product>>(API_PATHS.PRODUCTS, { params });
}

export function fetchProduct(id: string) {
  return apiClient<Product>(`${API_PATHS.PRODUCTS}/${id}`);
}

export function createProduct(input: CreateProductInput) {
  return apiClient<Product>(API_PATHS.PRODUCTS, { method: "POST", body: input });
}

export function updateProduct(id: string, input: UpdateProductInput) {
  return apiClient<Product>(`${API_PATHS.PRODUCTS}/${id}`, { method: "PATCH", body: input });
}

export function deactivateProduct(id: string) {
  return apiClient<void>(`${API_PATHS.PRODUCTS}/${id}`, { method: "DELETE" });
}

export function adjustProductStock(id: string, input: AdjustStockInput) {
  return apiClient<Product>(API_PATHS.PRODUCT_STOCK(id), { method: "POST", body: input });
}

export function lookupHsnGst(params: { hsn_sac?: string; name?: string }) {
  return apiClient<HsnLookupResult>(API_PATHS.PRODUCTS_HSN_LOOKUP, { params });
}
