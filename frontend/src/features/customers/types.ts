export interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string;
  gstin?: string;
  state_code?: string;
  created_at: string;
}

export interface CustomerListParams {
  page?: number;
  page_size?: number;
  q?: string;
  sort?: string;
}
