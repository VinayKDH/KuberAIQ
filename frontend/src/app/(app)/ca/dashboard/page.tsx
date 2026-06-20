"use client";

import { useMemo, useState } from "react";
import { AlertCircle, Building2 } from "lucide-react";
import Link from "next/link";
import { CaBulkGstrPanel } from "@/components/ca/ca-bulk-gstr-panel";
import { CaClientHealthBadges } from "@/components/ca/ca-client-health-badges";
import { CaClientTasksPanel } from "@/components/ca/ca-client-tasks-panel";
import { CaCompliancePackButton } from "@/components/ca/ca-compliance-pack-button";
import { CaDashboardSummary } from "@/components/ca/ca-dashboard-summary";
import { CaFilingChecklist } from "@/components/ca/ca-filing-checklist";
import { CaFilingWorkspaceToolbar } from "@/components/ca/ca-filing-workspace-toolbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCaDashboard } from "@/features/ca/hooks";
import { CA_COPY, ROUTES } from "@/lib/constants";
import { formatDate, formatINR } from "@/lib/format";

type RiskFilter = "all" | "at-risk" | "healthy";

export default function CaDashboardPage() {
  const { data, isLoading } = useCaDashboard();
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [dueBefore, setDueBefore] = useState("");
  const allClients = data?.clients ?? [];

  const clients = useMemo(() => {
    let filtered = allClients;
    if (riskFilter === "at-risk") {
      filtered = filtered.filter((c) => c.risk_level === "high" || c.risk_level === "medium");
    } else if (riskFilter === "healthy") {
      filtered = filtered.filter((c) => c.risk_level === "low");
    }
    if (dueBefore) {
      filtered = filtered.filter((client) =>
        (client.filing_checklist ?? []).some((item) => {
          if (!item.due_date) return false;
          return item.due_date <= dueBefore;
        }),
      );
    }
    return filtered;
  }, [allClients, riskFilter, dueBefore]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{CA_COPY.DASHBOARD_TITLE}</h2>
          <p className="text-muted-foreground">{CA_COPY.DASHBOARD_DESCRIPTION}</p>
        </div>
        <Link
          href={ROUTES.CA_CLIENTS}
          className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
        >
          Manage clients
        </Link>
      </div>

      <CaDashboardSummary
        clients={allClients}
        portfolio={data?.portfolio}
        loading={isLoading}
      />

      {!isLoading && allClients.length > 0 && <CaBulkGstrPanel clients={allClients} />}

      {!isLoading && allClients.length > 0 && (
        <CaFilingWorkspaceToolbar
          clients={allClients}
          dueBefore={dueBefore}
          onDueBeforeChange={setDueBefore}
        />
      )}

      {!isLoading && allClients.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant={riskFilter === "all" ? "default" : "outline"}
            onClick={() => setRiskFilter("all")}
          >
            {CA_COPY.FILTER_ALL}
          </Button>
          <Button
            size="sm"
            variant={riskFilter === "at-risk" ? "default" : "outline"}
            onClick={() => setRiskFilter("at-risk")}
          >
            {CA_COPY.FILTER_AT_RISK}
          </Button>
          <Button
            size="sm"
            variant={riskFilter === "healthy" ? "default" : "outline"}
            onClick={() => setRiskFilter("healthy")}
          >
            {CA_COPY.FILTER_HEALTHY}
          </Button>
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading filing overview…</p>
      ) : clients.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {clients.map((client) => (
            <Card key={client.company_id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2">
                    <Building2 className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <CardTitle className="text-base">{client.company_name}</CardTitle>
                      {client.gstin ? (
                        <CardDescription>GSTIN {client.gstin}</CardDescription>
                      ) : (
                        <CardDescription className="text-destructive">No GSTIN on file</CardDescription>
                      )}
                    </div>
                  </div>
                  <CaClientHealthBadges client={client} />
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {(client.overdue_total ?? 0) > 0 && (
                  <p className="text-sm text-destructive">
                    Overdue receivables: {formatINR(client.overdue_total ?? 0)}
                  </p>
                )}
                {client.health_score != null && (
                  <p className="text-sm">
                    Compliance health:{" "}
                    <span className="font-medium">{client.health_score}%</span>
                  </p>
                )}
                <CaFilingChecklist
                  companyId={client.company_id}
                  items={client.filing_checklist ?? []}
                  profileComplete={client.profile_complete}
                />
                <CaClientTasksPanel companyId={client.company_id} />
                <CaCompliancePackButton
                  companyId={client.company_id}
                  companyName={client.company_name}
                />
                {client.upcoming_filings.length ? (
                  <ul className="space-y-2 text-sm">
                    {client.upcoming_filings.map((filing, index) => (
                      <li
                        key={`${filing.obligation_id}-${index}`}
                        className="flex items-start gap-2 rounded-md border p-2"
                      >
                        <AlertCircle className="mt-0.5 h-4 w-4 text-amber-600" />
                        <div>
                          <p className="font-medium">{filing.title ?? filing.obligation_id}</p>
                          {filing.due_date && (
                            <p className="text-muted-foreground">
                              Due {formatDate(filing.due_date)} · {filing.status}
                            </p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">No other upcoming filings.</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : allClients.length ? (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            No clients match this filter.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            {CA_COPY.NO_CLIENTS}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
