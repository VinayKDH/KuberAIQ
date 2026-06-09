export interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string | null;
  gstin?: string | null;
  state_code?: string | null;
  billing_address?: string | null;
  notes?: string | null;
  created_at?: string | null;
}

export interface CreateCustomerInput {
  name: string;
  phone: string;
  email?: string;
  gstin?: string;
  billing_address?: string;
  notes?: string;
}

export type UpdateCustomerInput = Partial<CreateCustomerInput>;

export interface CustomerHistory {
  customer: Customer;
  total_billed: number | string;
  total_paid: number | string;
  outstanding: number | string;
  aging: Record<string, number | string>;
}

export interface CustomerListParams {
  page?: number;
  page_size?: number;
  q?: string;
  sort?: string;
}
