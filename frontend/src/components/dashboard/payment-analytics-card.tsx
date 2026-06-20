"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DASHBOARD_METRICS, PAYMENT_COPY } from "@/lib/constants";
import { formatINR } from "@/lib/format";
import { getPreferredLanguage } from "@/lib/i18n";
import type { PaymentAnalytics } from "@/features/dashboard/types";

interface PaymentAnalyticsCardProps {
  analytics?: PaymentAnalytics | null;
  loading?: boolean;
}

export function PaymentAnalyticsCard({ analytics, loading }: PaymentAnalyticsCardProps) {
  const lang = getPreferredLanguage();

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{PAYMENT_COPY.ANALYTICS_TITLE}</CardTitle>
        </CardHeader>
        <CardContent className="h-32 animate-pulse rounded-md bg-muted" />
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{PAYMENT_COPY.ANALYTICS_TITLE}</CardTitle>
        <CardDescription>{PAYMENT_COPY.METHOD_BREAKDOWN}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <p className="text-sm text-muted-foreground">{DASHBOARD_METRICS.collectedWeek[lang]}</p>
            <p className="text-xl font-semibold">{formatINR(analytics?.collected_week ?? 0)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{DASHBOARD_METRICS.collectedMonth[lang]}</p>
            <p className="text-xl font-semibold">{formatINR(analytics?.collected_month ?? 0)}</p>
          </div>
        </div>
        {analytics?.method_breakdown?.length ? (
          <ul className="space-y-1 text-sm">
            {analytics.method_breakdown.map((row) => (
              <li key={row.method} className="flex justify-between">
                <span>{row.method}</span>
                <span className="text-muted-foreground">{formatINR(row.amount)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No payment methods recorded this month.</p>
        )}
      </CardContent>
    </Card>
  );
}
