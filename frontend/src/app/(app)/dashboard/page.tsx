"use client";

import { AlertCircle, Clock, IndianRupee } from "lucide-react";
import { AgingChart } from "@/components/dashboard/aging-chart";
import { MetricCard } from "@/components/dashboard/metric-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/features/dashboard/hooks";
import { formatINR } from "@/lib/format";

export default function DashboardPage() {
  const { data, isLoading, isError, error } = useDashboard();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Overview</h2>
        <p className="text-muted-foreground">Your business at a glance</p>
      </div>

      {isError && (
        <Card className="border-destructive/50">
          <CardContent className="flex items-center gap-2 pt-6 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error instanceof Error ? error.message : "Failed to load dashboard"}</span>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          title="Revenue (Paid)"
          value={data?.revenue ?? 0}
          icon={IndianRupee}
          description="Total collected in period"
          loading={isLoading}
        />
        <MetricCard
          title="Pending"
          value={data?.pending ?? 0}
          icon={Clock}
          variant="warning"
          description="Issued, not yet due"
          loading={isLoading}
        />
        <MetricCard
          title="Overdue"
          value={data?.overdue ?? 0}
          icon={AlertCircle}
          variant="danger"
          description="Past due receivables"
          loading={isLoading}
        />
      </div>

      {isLoading ? (
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[300px] w-full" />
          </CardContent>
        </Card>
      ) : data?.aging?.length ? (
        <AgingChart data={data.aging} />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Receivables Aging</CardTitle>
            <CardDescription>No aging data available yet</CardDescription>
          </CardHeader>
        </Card>
      )}

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
    </div>
  );
}
