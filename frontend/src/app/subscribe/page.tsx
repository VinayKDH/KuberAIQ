"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Check, CreditCard, Lock, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  createCheckout,
  fetchBillingStatus,
  mockActivateSubscription,
  verifyPayment,
} from "@/features/billing/api";
import {
  API_PATHS,
  APP_NAME,
  RAZORPAY_CHECKOUT_SCRIPT_URL,
  ROUTES,
  SUBSCRIPTION_PAGE,
} from "@/lib/constants";
import { useCanonicalOriginRedirect } from "@/hooks/use-canonical-origin";
import { apiClient, formatApiError } from "@/lib/api-client";
import {
  clearSession,
  getStoredUser,
  isAuthenticated,
  isMockBillingEnabled,
  storeSession,
  type AuthTokens,
  type AuthUser,
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

function SubscribeSteps({ activeStep }: { activeStep: number }) {
  return (
    <ol className="flex items-center justify-center gap-2 text-xs sm:gap-4 sm:text-sm">
      {SUBSCRIPTION_PAGE.STEPS.map((label, index) => {
        const done = index < activeStep;
        const active = index === activeStep;
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-semibold ${
                done
                  ? "bg-primary text-primary-foreground"
                  : active
                    ? "border-2 border-primary text-primary"
                    : "border border-muted-foreground/30 text-muted-foreground"
              }`}
            >
              {done ? <Check className="h-3.5 w-3.5" /> : index + 1}
            </span>
            <span className={active ? "font-medium text-foreground" : "text-muted-foreground"}>
              {label}
            </span>
            {index < SUBSCRIPTION_PAGE.STEPS.length - 1 && (
              <span className="hidden h-px w-6 bg-border sm:block" aria-hidden />
            )}
          </li>
        );
      })}
    </ol>
  );
}

export default function SubscribePage() {
  const router = useRouter();
  const redirecting = useCanonicalOriginRedirect();
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [amountPaise, setAmountPaise] = useState(99900);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace(ROUTES.LOGIN);
      return;
    }

    setUser(getStoredUser());

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
    setSuccess(true);
    storeSession(tokens);
    setTimeout(() => {
      router.replace(postLoginRoute(tokens));
    }, 1200);
  };

  const handleMockPay = async () => {
    setError(null);
    setPaying(true);
    try {
      const tokens = await mockActivateSubscription();
      afterPayment(tokens);
    } catch (err) {
      setError(formatApiError(err, "Payment failed"));
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

      const stored = getStoredUser();
      const rzp = new window.Razorpay({
        key: checkout.key_id,
        amount: checkout.amount_paise,
        currency: checkout.currency,
        name: APP_NAME,
        description: SUBSCRIPTION_PAGE.PLAN_NAME,
        order_id: checkout.order_id,
        prefill: {
          email: checkout.prefill_email ?? stored?.email,
          name: checkout.prefill_name ?? stored?.full_name,
        },
        notes: { plan: checkout.plan_code },
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
        modal: {
          ondismiss: () => {
            setPaying(false);
            setError(SUBSCRIPTION_PAGE.PAYMENT_CANCELLED);
          },
        },
        theme: { color: "#0f766e" },
      });
      rzp.open();
    } catch (err) {
      setError(formatApiError(err, "Payment failed"));
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
    <div className="flex min-h-screen flex-col bg-muted/30">
      <header className="border-b bg-background/80 px-4 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <Link href={ROUTES.HOME} className="text-lg font-semibold text-primary">
            {APP_NAME}
          </Link>
          {user?.email && (
            <p className="text-sm text-muted-foreground">
              {SUBSCRIPTION_PAGE.ACCOUNT_LABEL}: {user.email}
            </p>
          )}
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-lg space-y-6">
          <SubscribeSteps activeStep={SUBSCRIPTION_PAGE.STEP_ACTIVE} />

          <Card>
            <CardHeader className="text-center">
              <CardTitle>{SUBSCRIPTION_PAGE.TITLE}</CardTitle>
              <CardDescription>{SUBSCRIPTION_PAGE.DESCRIPTION}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="rounded-xl border-2 border-primary/20 bg-primary/5 p-6 text-center">
                <p className="text-sm font-medium text-primary">{SUBSCRIPTION_PAGE.PLAN_NAME}</p>
                <p className="mt-2 text-4xl font-bold tracking-tight">₹{amountInr}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {SUBSCRIPTION_PAGE.BILLING_CYCLE}
                </p>
              </div>

              <ul className="space-y-2.5 text-sm">
                {SUBSCRIPTION_PAGE.FEATURES.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              {success ? (
                <div
                  className="flex items-center justify-center gap-2 rounded-lg border border-primary/30 bg-primary/10 p-4 text-sm font-medium text-primary"
                  role="status"
                >
                  <ShieldCheck className="h-5 w-5" />
                  {SUBSCRIPTION_PAGE.PAYMENT_SUCCESS}
                </div>
              ) : (
                <>
                  {error && (
                    <p className="text-sm text-destructive" role="alert">
                      {error}
                    </p>
                  )}
                  <Button
                    className="w-full"
                    size="lg"
                    onClick={handleRazorpayPay}
                    disabled={paying}
                  >
                    <CreditCard className="mr-2 h-4 w-4" />
                    {paying ? SUBSCRIPTION_PAGE.PAYING : SUBSCRIPTION_PAGE.PAY_CTA}
                  </Button>
                  <p className="flex items-center justify-center gap-1.5 text-center text-xs text-muted-foreground">
                    <Lock className="h-3.5 w-3.5" />
                    {SUBSCRIPTION_PAGE.SECURE_NOTE}
                  </p>
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
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
