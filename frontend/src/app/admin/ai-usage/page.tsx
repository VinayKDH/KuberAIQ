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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAdminAiUsage } from "@/features/admin/hooks";
import { ADMIN_COPY } from "@/lib/constants";

export default function AdminAiUsagePage() {
  const { data, isLoading, isError } = useAdminAiUsage();

  if (isLoading) {
    return <p className="text-zinc-500">{ADMIN_COPY.LOADING}</p>;
  }

  if (isError || !data) {
    return <p className="text-red-400">{ADMIN_COPY.ERROR}</p>;
  }

  const chartData = data.by_tenant.slice(0, 10).map((row) => ({
    name: row.company_name.length > 18 ? `${row.company_name.slice(0, 18)}…` : row.company_name,
    tokens: row.tokens_this_month,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{ADMIN_COPY.AI_USAGE_TITLE}</h2>
        <p className="text-zinc-400">{ADMIN_COPY.AI_USAGE_SUBTITLE}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <AdminMetricCard
          title="Tokens this month"
          value={data.tokens_this_month.toLocaleString()}
        />
        <AdminMetricCard title="Tokens all time" value={data.tokens_total.toLocaleString()} />
        <AdminMetricCard title="AI sessions" value={data.sessions_total} />
      </div>

      {chartData.length > 0 ? (
        <Card className="border-zinc-800 bg-zinc-950">
          <CardHeader>
            <CardTitle>Top tenants by tokens (month)</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 24 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                <XAxis type="number" stroke="#a1a1aa" fontSize={12} />
                <YAxis type="category" dataKey="name" stroke="#a1a1aa" fontSize={11} width={120} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(240 6% 10%)",
                    border: "1px solid hsl(240 4% 16%)",
                    borderRadius: 8,
                  }}
                />
                <Bar dataKey="tokens" fill="hsl(217 91% 60%)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      ) : null}

      <div className="rounded-lg border border-zinc-800">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800">
              <TableHead>Tenant</TableHead>
              <TableHead>Tokens (month)</TableHead>
              <TableHead>Tokens (total)</TableHead>
              <TableHead>Sessions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.by_tenant.map((row) => (
              <TableRow key={row.company_id} className="border-zinc-800">
                <TableCell>{row.company_name}</TableCell>
                <TableCell>{row.tokens_this_month.toLocaleString()}</TableCell>
                <TableCell>{row.tokens_total.toLocaleString()}</TableCell>
                <TableCell>{row.sessions_count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
