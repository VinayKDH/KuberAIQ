"use client";

import { AlertCircle, Building2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCaDashboard } from "@/features/ca/hooks";
import { CA_COPY, ROUTES } from "@/lib/constants";
import { formatDate } from "@/lib/format";

export default function CaDashboardPage() {
  const { data, isLoading } = useCaDashboard();

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

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading filing overview…</p>
      ) : data?.clients.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.clients.map((client) => (
            <Card key={client.company_id}>
              <CardHeader>
                <div className="flex items-start gap-2">
                  <Building2 className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <CardTitle className="text-base">{client.company_name}</CardTitle>
                    {client.gstin && (
                      <CardDescription>GSTIN {client.gstin}</CardDescription>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {client.health_score != null && (
                  <p className="text-sm">
                    Compliance health:{" "}
                    <span className="font-medium">{client.health_score}%</span>
                  </p>
                )}
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
                  <p className="text-sm text-muted-foreground">No upcoming filings.</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
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
