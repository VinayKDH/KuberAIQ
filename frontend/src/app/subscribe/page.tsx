"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, CreditCard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  createCheckout,
  fetchBillingStatus,
  mockActivateSubscription,
  verifyPayment,
} from "@/features/billing/api";
import { API_PATHS, APP_NAME, RAZORPAY_CHECKOUT_SCRIPT_URL, ROUTES, SUBSCRIPTION_PAGE } from "@/lib/constants";
import { useCanonicalOriginRedirect } from "@/hooks/use-canonical-origin";
import { apiClient, formatApiError } from "@/lib/api-client";
import {
  clearSession,
  isAuthenticated,
  isMockBillingEnabled,
  storeSession,
  type AuthTokens,
} from "@/lib/auth";
import { postLoginRoute, type MeGate } from "@/lib/session-routing";

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void };
  }
}

function loadRazorpayScript(): Promise<void> {
  if (window.Razorpay) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = RAZORPAY_CHECKOUT_SCRIPT_URL;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Razorpay"));
    document.body.appendChild(script);
  });
}

export default function SubscribePage() {
  const router = useRouter();
  const redirecting = useCanonicalOriginRedirect();
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [amountPaise, setAmountPaise] = useState(99900);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace(ROUTES.LOGIN);
      return;
    }

    apiClient<MeGate>(API_PATHS.ME)
      .then(async (me) => {
        const redirect = postLoginRoute(me);
        if (redirect !== ROUTES.SUBSCRIBE) {
          router.replace(redirect);
          return;
        }
        const status = await fetchBillingStatus();
        setAmountPaise(status.amount_paise);
        setLoading(false);
      })
      .catch(() => {
        clearSession();
        router.replace(ROUTES.LOGIN);
      });
  }, [router]);

  const afterPayment = (tokens: AuthTokens) => {
    storeSession(tokens);
    router.replace(postLoginRoute(tokens));
  };

  const handleMockPay = async () => {
    setError(null);
    setPaying(true);
    try {
      const tokens = await mockActivateSubscription();
      afterPayment(tokens);
    } catch (err) {
      setError(formatApiError(err, "Payment failed"));
    } finally {
      setPaying(false);
    }
  };

  const handleRazorpayPay = async () => {
    setError(null);
    setPaying(true);
    try {
      const checkout = await createCheckout();
      if (checkout.mock_billing) {
        const tokens = await mockActivateSubscription();
        afterPayment(tokens);
        return;
      }
      await loadRazorpayScript();
      if (!checkout.key_id || !window.Razorpay) {
        throw new Error("Payment gateway is not configured");
      }
      const rzp = new window.Razorpay({
        key: checkout.key_id,
        amount: checkout.amount_paise,
        currency: checkout.currency,
        name: APP_NAME,
        description: SUBSCRIPTION_PAGE.PLAN_NAME,
        order_id: checkout.order_id,
        handler: async (response: {
          razorpay_order_id: string;
          razorpay_payment_id: string;
          razorpay_signature: string;
        }) => {
          try {
            const tokens = await verifyPayment({
              order_id: response.razorpay_order_id,
              payment_id: response.razorpay_payment_id,
              signature: response.razorpay_signature,
            });
            afterPayment(tokens);
          } catch (err) {
            setError(formatApiError(err, "Payment verification failed"));
            setPaying(false);
          }
        },
        theme: { color: "#0f766e" },
      });
      rzp.open();
    } catch (err) {
      setError(formatApiError(err, "Payment failed"));
    } finally {
      setPaying(false);
    }
  };

  if (redirecting || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const amountInr = (amountPaise / 100).toLocaleString("en-IN");

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4 py-12">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <CardTitle>{SUBSCRIPTION_PAGE.TITLE}</CardTitle>
          <CardDescription>{SUBSCRIPTION_PAGE.DESCRIPTION}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="rounded-lg border bg-background p-6 text-center">
            <p className="text-sm text-muted-foreground">{SUBSCRIPTION_PAGE.PLAN_NAME}</p>
            <p className="mt-2 text-4xl font-bold">₹{amountInr}</p>
            <p className="text-sm text-muted-foreground">{SUBSCRIPTION_PAGE.BILLING_CYCLE}</p>
          </div>
          <ul className="space-y-2 text-sm">
            {SUBSCRIPTION_PAGE.FEATURES.map((feature) => (
              <li key={feature} className="flex items-start gap-2">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
          {error && (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}
          <Button className="w-full" size="lg" onClick={handleRazorpayPay} disabled={paying}>
            <CreditCard className="mr-2 h-4 w-4" />
            {paying ? SUBSCRIPTION_PAGE.PAYING : SUBSCRIPTION_PAGE.PAY_CTA}
          </Button>
          {isMockBillingEnabled() && (
            <Button
              variant="outline"
              className="w-full"
              onClick={handleMockPay}
              disabled={paying}
            >
              {SUBSCRIPTION_PAGE.MOCK_PAY_CTA}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
