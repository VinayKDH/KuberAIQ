"use client";

import { useMemo } from "react";
import { IndianRupee, Users, CalendarClock } from "lucide-react";
import { MetricCard } from "@/components/dashboard/metric-card";
import { CA_COPY, CA_FILING_DUE_SOON_DAYS } from "@/lib/constants";
import type { CaDashboardClient } from "@/features/ca/types";

interface CaDashboardSummaryProps {
  clients: CaDashboardClient[];
  loading?: boolean;
}

function countFilingsDueSoon(clients: CaDashboardClient[]): number {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() + CA_FILING_DUE_SOON_DAYS);

  return clients.reduce((total, client) => {
    const soon = client.upcoming_filings.filter((filing) => {
      if (!filing.due_date) return false;
      const due = new Date(filing.due_date);
      return due <= cutoff;
    });
    return total + soon.length;
  }, 0);
}

export function CaDashboardSummary({ clients, loading }: CaDashboardSummaryProps) {
  const totalOverdue = useMemo(
    () => clients.reduce((sum, client) => sum + (client.overdue_total ?? 0), 0),
    [clients],
  );
  const filingsDueSoon = useMemo(() => countFilingsDueSoon(clients), [clients]);

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <MetricCard
        title={CA_COPY.PORTFOLIO_CLIENTS}
        value={clients.length}
        icon={Users}
        description="Active MSME assignments"
        loading={loading}
        formatAsCurrency={false}
      />
      <MetricCard
        title={CA_COPY.PORTFOLIO_OVERDUE}
        value={totalOverdue}
        icon={IndianRupee}
        variant={totalOverdue > 0 ? "danger" : "default"}
        description="Across all client receivables"
        loading={loading}
      />
      <MetricCard
        title={CA_COPY.PORTFOLIO_DUE_SOON}
        value={filingsDueSoon}
        icon={CalendarClock}
        variant={filingsDueSoon > 0 ? "warning" : "default"}
        description={`Filings due in ${CA_FILING_DUE_SOON_DAYS} days`}
        loading={loading}
        formatAsCurrency={false}
      />
    </div>
  );
}
