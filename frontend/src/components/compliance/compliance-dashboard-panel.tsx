"use client";

import Link from "next/link";
import { AlertTriangle, CalendarClock, CheckSquare, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ComplianceCalendarPanel } from "@/components/compliance/compliance-calendar-panel";
import { ComplianceObligationsPanel } from "@/components/compliance/compliance-obligations-panel";
import { ComplianceOverview } from "@/components/compliance/compliance-overview";
import { ComplianceProfileSettings } from "@/components/compliance/compliance-profile-settings";
import { useComplianceDashboard, useComplianceObligations } from "@/features/compliance/hooks";
import {
  COMPLIANCE_COPY,
  COMPLIANCE_STATUS_LABELS,
  COMPLIANCE_STATUS_VARIANTS,
  ROUTES,
} from "@/lib/constants";
import { formatDate, formatINR } from "@/lib/format";

export function ComplianceDashboardPanel() {
  const dashboardQuery = useComplianceDashboard();
  const obligationsQuery = useComplianceObligations();

  if (dashboardQuery.isLoading || obligationsQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (dashboardQuery.isError || obligationsQuery.isError || !dashboardQuery.data || !obligationsQuery.data) {
    return (
      <p className="text-sm text-destructive">
        {dashboardQuery.error instanceof Error
          ? dashboardQuery.error.message
          : obligationsQuery.error instanceof Error
            ? obligationsQuery.error.message
            : "Failed to load compliance center"}
      </p>
    );
  }

  const data = dashboardQuery.data;
  const obligations = obligationsQuery.data;

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">{data.disclaimer}</p>

      <ComplianceOverview
        summary={obligations.summary}
        profileComplete={obligations.profile_complete}
      />

      <Tabs defaultValue="obligations">
        <TabsList>
          <TabsTrigger value="obligations">Obligations</TabsTrigger>
          <TabsTrigger value="calendar">Calendar</TabsTrigger>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="obligations" className="space-y-4 pt-4">
          {obligations.profile_complete ? (
            <ComplianceObligationsPanel
              obligationsByCategory={obligations.obligations_by_category}
              notApplicable={obligations.not_applicable}
            />
          ) : (
            <ComplianceProfileSettings profile={obligations.profile} />
          )}
        </TabsContent>

        <TabsContent value="calendar" className="pt-4">
          <ComplianceCalendarPanel />
        </TabsContent>

        <TabsContent value="profile" className="pt-4">
          <ComplianceProfileSettings profile={obligations.profile} />
        </TabsContent>

        <TabsContent value="insights" className="space-y-6 pt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <CalendarClock className="h-5 w-5 text-muted-foreground" />
                <CardTitle>{COMPLIANCE_COPY.DEADLINES_TITLE}</CardTitle>
              </div>
              <CardDescription>GSTR-1, GSTR-3B, and TDS deposit dates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.deadlines.length ? (
                data.deadlines.map((deadline) => (
                  <div key={`${deadline.type}-${deadline.due_date}-${deadline.title}`} className="rounded-md border p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium">{deadline.title}</p>
                      <Badge variant={COMPLIANCE_STATUS_VARIANTS[deadline.status] ?? "secondary"}>
                        {COMPLIANCE_STATUS_LABELS[deadline.status] ?? deadline.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Due {formatDate(deadline.due_date)} · {deadline.description}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No deadlines in the next 45 days.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-muted-foreground" />
                <CardTitle>{COMPLIANCE_COPY.EINVOICE_TITLE}</CardTitle>
              </div>
              <CardDescription>{COMPLIANCE_COPY.EINVOICE_THRESHOLD}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <Metric label={COMPLIANCE_COPY.YTD_TURNOVER} value={formatINR(data.e_invoice.ytd_turnover)} />
                <Metric
                  label="E-invoicing status"
                  value={data.e_invoice.requires_e_invoice ? "Required" : "Monitor threshold"}
                />
                <Metric label={COMPLIANCE_COPY.PENDING_IRN} value={String(data.e_invoice.pending_count)} />
              </div>

              {data.e_invoice.pending_invoices.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Invoices needing IRN</p>
                  {data.e_invoice.pending_invoices.map((inv) => (
                    <Link
                      key={inv.invoice_id}
                      href={ROUTES.INVOICE_DETAIL(inv.invoice_id)}
                      className="flex items-center justify-between rounded-md border p-3 text-sm hover:bg-muted/50"
                    >
                      <span>
                        {inv.invoice_number ?? "Invoice"} · {formatDate(inv.issue_date)}
                      </span>
                      <span className="flex items-center gap-2">
                        <Badge variant={COMPLIANCE_STATUS_VARIANTS[inv.urgency] ?? "outline"}>
                          {inv.days_since_issue}d
                        </Badge>
                        {formatINR(inv.grand_total)}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <CheckSquare className="h-5 w-5 text-muted-foreground" />
                <CardTitle>{COMPLIANCE_COPY.CHECKLIST_TITLE}</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.checklist.map((item) => (
                <div key={item.id} className="flex gap-3 rounded-md border p-3">
                  <AlertTriangle
                    className={`mt-0.5 h-4 w-4 shrink-0 ${
                      item.priority === "HIGH" ? "text-destructive" : "text-muted-foreground"
                    }`}
                  />
                  <div>
                    <p className="font-medium">{item.title}</p>
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}
