import { API_PATHS } from "@/lib/constants";
import { apiClient } from "@/lib/api-client";
import type { AuthTokens } from "@/lib/auth";

export interface BillingStatus {
  subscription_status: string;
  subscription_active: boolean;
  needs_payment: boolean;
  needs_onboarding: boolean;
  plan_code: string;
  amount_paise: number;
  current_period_end: string | null;
}

export interface CheckoutSession {
  key_id: string | null;
  order_id: string;
  amount_paise: number;
  currency: string;
  plan_code: string;
  mock_billing: boolean;
}

export function fetchBillingStatus() {
  return apiClient<BillingStatus>(API_PATHS.BILLING_STATUS);
}

export function createCheckout() {
  return apiClient<CheckoutSession>(API_PATHS.BILLING_CHECKOUT, { method: "POST" });
}

export function verifyPayment(input: {
  order_id: string;
  payment_id: string;
  signature: string;
}) {
  return apiClient<AuthTokens>(API_PATHS.BILLING_VERIFY, {
    method: "POST",
    body: input,
  });
}

export function mockActivateSubscription() {
  return apiClient<AuthTokens>(API_PATHS.BILLING_MOCK_ACTIVATE, { method: "POST" });
}
