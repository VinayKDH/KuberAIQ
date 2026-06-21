"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AdminMetricCard } from "@/components/admin/admin-metric-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAdminDashboard } from "@/features/admin/hooks";
import { ADMIN_COPY } from "@/lib/constants";
import { formatINR } from "@/lib/format";

export default function AdminDashboardPage() {
  const { data, isLoading, isError } = useAdminDashboard();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-28 bg-zinc-800" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return <p className="text-red-400">{ADMIN_COPY.ERROR}</p>;
  }

  const subChart = Object.entries(data.subscription_breakdown).map(([status, count]) => ({
    status,
    count,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{ADMIN_COPY.DASHBOARD_TITLE}</h2>
        <p className="text-zinc-400">{ADMIN_COPY.DASHBOARD_SUBTITLE}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <AdminMetricCard title="Total tenants" value={data.total_tenants} />
        <AdminMetricCard title="Active tenants" value={data.active_tenants} />
        <AdminMetricCard title="Suspended" value={data.suspended_tenants} />
        <AdminMetricCard title="Active users" value={data.active_users} />
        <AdminMetricCard title="Invoices (month)" value={data.invoices_this_month} />
        <AdminMetricCard title="AI sessions" value={data.ai_sessions_total} />
        <AdminMetricCard
          title="AI tokens (month)"
          value={data.ai_tokens_this_month.toLocaleString()}
        />
        <AdminMetricCard
          title="Collections (month)"
          value={formatINR(data.collections_volume_this_month)}
        />
      </div>

      {subChart.length > 0 ? (
        <Card className="border-zinc-800 bg-zinc-950">
          <CardHeader>
            <CardTitle className="text-zinc-100">Subscription breakdown</CardTitle>
          </CardHeader>
          <CardContent className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={subChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                <XAxis dataKey="status" stroke="#a1a1aa" fontSize={12} />
                <YAxis stroke="#a1a1aa" fontSize={12} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(240 6% 10%)",
                    border: "1px solid hsl(240 4% 16%)",
                    borderRadius: 8,
                  }}
                />
                <Bar dataKey="count" fill="hsl(160 84% 39%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
