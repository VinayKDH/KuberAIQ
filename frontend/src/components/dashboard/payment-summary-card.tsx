"use client";

import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PAYMENT_COPY } from "@/lib/constants";
import { formatDate, formatINR } from "@/lib/format";
import type { PaymentSummary } from "@/features/dashboard/types";

interface PaymentSummaryCardProps {
  summary?: PaymentSummary | null;
  loading?: boolean;
}

export function PaymentSummaryCard({ summary, loading }: PaymentSummaryCardProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{PAYMENT_COPY.RECENT_TITLE}</CardTitle>
        </CardHeader>
        <CardContent className="h-24 animate-pulse rounded-md bg-muted" />
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{PAYMENT_COPY.RECENT_TITLE}</CardTitle>
        <CardDescription>
          Collected today: {formatINR(summary?.collected_today ?? 0)}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!summary?.recent_payments?.length ? (
          <p className="text-sm text-muted-foreground">{PAYMENT_COPY.RECENT_EMPTY}</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {summary.recent_payments.map((payment) => (
              <li key={payment.id} className="flex items-center justify-between gap-2">
                <div>
                  <Link
                    href={`/invoices/${payment.invoice_id}`}
                    className="font-medium hover:underline"
                  >
                    {payment.invoice_number ?? "Invoice"}
                  </Link>
                  <p className="text-muted-foreground">
                    {formatDate(payment.paid_on)} · {payment.method}
                  </p>
                </div>
                <span>{formatINR(payment.amount)}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
