"use client";

import { Activity, IndianRupee, Users, CalendarClock } from "lucide-react";
import { MetricCard } from "@/components/dashboard/metric-card";
import { CA_COPY, CA_FILING_DUE_SOON_DAYS } from "@/lib/constants";
import type { CaDashboardClient, CaPortfolioSummary } from "@/features/ca/types";

interface CaDashboardSummaryProps {
  clients: CaDashboardClient[];
  portfolio?: CaPortfolioSummary | null;
  loading?: boolean;
}

export function CaDashboardSummary({ clients, portfolio, loading }: CaDashboardSummaryProps) {
  const totalOverdue =
    portfolio?.total_overdue ??
    clients.reduce((sum, client) => sum + (client.overdue_total ?? 0), 0);
  const filingsDueSoon =
    portfolio?.filings_due_soon ??
    clients.reduce((sum, client) => sum + (client.filings_due_soon ?? 0), 0);
  const clientsAtRisk =
    portfolio?.clients_at_risk ??
    clients.filter((c) => c.risk_level === "high").length;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        title={CA_COPY.PORTFOLIO_CLIENTS}
        value={clients.length}
        icon={Users}
        description="Active MSME assignments"
        loading={loading}
        formatAsCurrency={false}
      />
      <MetricCard
        title={CA_COPY.PORTFOLIO_HEALTH}
        value={portfolio?.avg_health_score ?? 0}
        icon={Activity}
        variant={
          portfolio?.avg_health_score != null && portfolio.avg_health_score < 70
            ? "warning"
            : "default"
        }
        description={
          portfolio?.avg_health_score != null ? "Across active clients" : "No health data yet"
        }
        loading={loading}
        formatAsCurrency={false}
      />
      <MetricCard
        title={CA_COPY.PORTFOLIO_AT_RISK}
        value={clientsAtRisk}
        icon={Users}
        variant={clientsAtRisk > 0 ? "danger" : "default"}
        description="Need attention this week"
        loading={loading}
        formatAsCurrency={false}
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
      <MetricCard
        title={CA_COPY.PORTFOLIO_OVERDUE}
        value={totalOverdue}
        icon={IndianRupee}
        variant={totalOverdue > 0 ? "danger" : "default"}
        description="Across all client receivables"
        loading={loading}
      />
    </div>
  );
}
