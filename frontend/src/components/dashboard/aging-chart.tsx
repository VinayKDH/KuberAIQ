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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AGING_BUCKET_LABELS } from "@/lib/constants";
import { formatINR } from "@/lib/format";
import type { AgingBucket } from "@/features/dashboard/types";

interface AgingChartProps {
  data: AgingBucket[];
}

export function AgingChart({ data }: AgingChartProps) {
  const chartData = data.map((item) => ({
    bucket: AGING_BUCKET_LABELS[item.bucket] ?? item.bucket,
    outstanding: item.outstanding,
    invoices: item.invoices,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Receivables Aging</CardTitle>
        <CardDescription>Outstanding amounts by aging bucket</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="bucket" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number) => formatINR(value)}
                contentStyle={{
                  backgroundColor: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                }}
              />
              <Bar dataKey="outstanding" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
