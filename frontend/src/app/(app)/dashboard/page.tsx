"use client";

import { useMemo, useState } from "react";
import { AlertCircle, AlertTriangle, IndianRupee, Clock } from "lucide-react";
import { AgingChart } from "@/components/dashboard/aging-chart";
import { CashflowChart } from "@/components/dashboard/cashflow-chart";
import { CashflowForecastChart } from "@/components/dashboard/cashflow-forecast-chart";
import { ComplianceAlertCard } from "@/components/dashboard/compliance-alert-card";
import { MetricCard } from "@/components/dashboard/metric-card";
import { TopProductsCard } from "@/components/dashboard/top-products-card";
import { ComplianceAlertsPreviewPanel } from "@/components/compliance/compliance-alerts-preview";
import { MsmeComplianceTipsCard } from "@/components/msme/msme-compliance-tips-card";
import { MsmeQuickStartCard } from "@/components/msme/msme-quick-start-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/features/dashboard/hooks";
import { DASHBOARD_METRICS } from "@/lib/constants";
import { financialYearStartIso, formatDate, formatINR, todayIso } from "@/lib/format";
import { getPreferredLanguage, I18N_MESSAGES } from "@/lib/i18n";

export default function DashboardPage() {
  const lang = getPreferredLanguage();
  const i18n = I18N_MESSAGES[lang];
  const [fromDate, setFromDate] = useState(financialYearStartIso);
  const [toDate, setToDate] = useState(todayIso);

  const params = useMemo(
    () => ({ from: fromDate, to: toDate }),
    [fromDate, toDate],
  );
  const { data, isLoading, isError, error } = useDashboard(params);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{i18n.dashboardOverview}</h2>
          <p className="text-muted-foreground">{i18n.dashboardSubtitle}</p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="space-y-1">
            <Label htmlFor="from">From</Label>
            <Input
              id="from"
              type="date"
              value={fromDate}
              max={toDate}
              onChange={(e) => setFromDate(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="to">To</Label>
            <Input
              id="to"
              type="date"
              value={toDate}
              min={fromDate}
              max={todayIso()}
              onChange={(e) => setToDate(e.target.value)}
            />
          </div>
        </div>
      </div>

      <MsmeQuickStartCard />

      <div className="grid gap-4 lg:grid-cols-2">
        <MsmeComplianceTipsCard />
        <ComplianceAlertsPreviewPanel />
      </div>

      {isError && (
        <Card className="border-destructive/50">
          <CardContent className="flex items-center gap-2 pt-6 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error instanceof Error ? error.message : "Failed to load dashboard"}</span>
          </CardContent>
        </Card>
      )}

      {data?.cashflow_alert?.triggered && (
        <Card className="border-amber-500/50 bg-amber-50/50 dark:bg-amber-950/20">
          <CardContent className="flex items-start gap-3 pt-6">
            <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-600" />
            <div>
              <p className="font-medium text-amber-900 dark:text-amber-100">Cashflow alert</p>
              <p className="text-sm text-amber-800 dark:text-amber-200">{data.cashflow_alert.message}</p>
              {data.cashflow_alert.shortfall_date && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Buffer: {formatINR(data.cashflow_alert.buffer)} · Minimum projected:{" "}
                  {formatINR(data.cashflow_alert.projected_minimum)}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <ComplianceAlertCard alert={data?.compliance_alert} />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          title={DASHBOARD_METRICS.revenue[lang]}
          value={data?.revenue ?? 0}
          icon={IndianRupee}
          description={DASHBOARD_METRICS.revenueDesc[lang]}
          loading={isLoading}
        />
        <MetricCard
          title={DASHBOARD_METRICS.pending[lang]}
          value={data?.pending ?? 0}
          icon={Clock}
          variant="warning"
          description={DASHBOARD_METRICS.pendingDesc[lang]}
          loading={isLoading}
        />
        <MetricCard
          title={DASHBOARD_METRICS.overdue[lang]}
          value={data?.overdue ?? 0}
          icon={AlertCircle}
          variant="danger"
          description={DASHBOARD_METRICS.overdueDesc[lang]}
          loading={isLoading}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {isLoading ? (
          <>
            <Skeleton className="h-[380px] w-full" />
            <Skeleton className="h-[380px] w-full" />
          </>
        ) : (
          <>
            {data?.aging?.length ? (
              <AgingChart data={data.aging} />
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>Receivables Aging</CardTitle>
                  <CardDescription>No aging data available yet</CardDescription>
                </CardHeader>
              </Card>
            )}
            {data?.cashflow_forecast?.length ? (
              <CashflowForecastChart data={data.cashflow_forecast} />
            ) : data?.cashflow?.length ? (
              <CashflowChart data={data.cashflow} />
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>Expected Cash Inflow</CardTitle>
                  <CardDescription>No upcoming inflows in open invoices</CardDescription>
                </CardHeader>
              </Card>
            )}
          </>
        )}
      </div>

      {!isLoading && data?.cashflow?.length && data?.cashflow_forecast?.length ? (
        <CashflowChart data={data.cashflow} />
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        {data?.top_customers && data.top_customers.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Top Customers</CardTitle>
              <CardDescription>By revenue in selected period</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {data.top_customers.map((customer) => (
                  <li
                    key={customer.customer_id}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="font-medium">{customer.name}</span>
                    <span className="text-muted-foreground">{formatINR(customer.revenue)}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
        {data?.top_products && data.top_products.length > 0 && (
          <TopProductsCard products={data.top_products} />
        )}
      </div>
    </div>
  );
}
