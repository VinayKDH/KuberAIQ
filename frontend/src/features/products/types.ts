export interface Product {
  id: string;
  name: string;
  description: string | null;
  hsn_sac: string | null;
  unit: string;
  default_price: number | string;
  gst_rate: number | string;
  is_active: boolean;
}

export interface ProductListParams {
  q?: string;
  page?: number;
  page_size?: number;
  active_only?: boolean;
}

export interface CreateProductInput {
  name: string;
  description?: string | null;
  hsn_sac?: string | null;
  unit?: string;
  default_price: number;
  gst_rate?: number;
}

export interface HsnLookupResult {
  hsn_sac: string | null;
  gst_rate: number | string | null;
  source: string | null;
}

export interface UpdateProductInput {
  name?: string;
  description?: string | null;
  hsn_sac?: string | null;
  unit?: string;
  default_price?: number;
  gst_rate?: number;
  is_active?: boolean;
}

export interface ProductPickerValue {
  product_id?: string;
  description: string;
  hsn_sac?: string;
  unit: string;
  unit_price: number;
  gst_rate: number;
}
