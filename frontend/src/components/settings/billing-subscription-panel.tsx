"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { CreditCard, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchBillingStatus } from "@/features/billing/api";
import { BILLING_SETTINGS, QUERY_KEYS, ROUTES } from "@/lib/constants";
import { formatDate } from "@/lib/format";

function statusLabel(status: string): string {
  return BILLING_SETTINGS.STATUS_LABELS[status] ?? status;
}

function statusNote(billing: Awaited<ReturnType<typeof fetchBillingStatus>>): string {
  if (billing.needs_payment && billing.subscription_status === "PENDING") {
    return BILLING_SETTINGS.PENDING_NOTE;
  }
  if (billing.needs_payment) {
    return BILLING_SETTINGS.EXPIRED_NOTE;
  }
  return BILLING_SETTINGS.ACTIVE_NOTE;
}

export function BillingSubscriptionPanel() {
  const router = useRouter();
  const { data: billing, isLoading, refetch } = useQuery({
    queryKey: QUERY_KEYS.BILLING_STATUS,
    queryFn: fetchBillingStatus,
  });

  const amountInr = billing ? (billing.amount_paise / 100).toLocaleString("en-IN") : "—";
  const note = billing ? statusNote(billing) : null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{BILLING_SETTINGS.TITLE}</CardTitle>
        </div>
        <CardDescription>{BILLING_SETTINGS.DESCRIPTION}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading subscription…</p>
        ) : billing ? (
          <>
            <dl className="grid gap-3 sm:grid-cols-2">
              <div>
                <dt className="text-xs font-medium uppercase text-muted-foreground">
                  {BILLING_SETTINGS.PLAN_LABEL}
                </dt>
                <dd className="mt-1 text-sm font-medium">{billing.plan_name}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase text-muted-foreground">
                  {BILLING_SETTINGS.STATUS_LABEL}
                </dt>
                <dd className="mt-1 text-sm font-medium">
                  {statusLabel(billing.subscription_status)}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase text-muted-foreground">
                  {BILLING_SETTINGS.AMOUNT_LABEL}
                </dt>
                <dd className="mt-1 text-sm font-medium">₹{amountInr} / month</dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase text-muted-foreground">
                  {BILLING_SETTINGS.VALID_UNTIL_LABEL}
                </dt>
                <dd className="mt-1 text-sm font-medium">
                  {billing.current_period_end
                    ? formatDate(billing.current_period_end)
                    : "—"}
                </dd>
              </div>
            </dl>
            {note && <p className="text-sm text-muted-foreground">{note}</p>}
            <div className="flex flex-wrap gap-2">
              {billing.needs_payment ? (
                <Button onClick={() => router.push(ROUTES.SUBSCRIBE)}>
                  {billing.subscription_status === "PENDING"
                    ? BILLING_SETTINGS.PAY_CTA
                    : BILLING_SETTINGS.RENEW_CTA}
                </Button>
              ) : (
                <Button variant="outline" onClick={() => router.push(ROUTES.SUBSCRIBE)}>
                  {BILLING_SETTINGS.RENEW_CTA}
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={() => refetch()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
            </div>
          </>
        ) : (
          <p className="text-sm text-destructive">Could not load subscription status.</p>
        )}
      </CardContent>
    </Card>
  );
}
