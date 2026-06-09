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
import { CASHFLOW_DISCLAIMER } from "@/lib/constants";
import type { CashflowPeriod } from "@/features/dashboard/types";
import { formatINR, formatPeriodLabel } from "@/lib/format";

interface CashflowChartProps {
  data: CashflowPeriod[];
}

export function CashflowChart({ data }: CashflowChartProps) {
  const chartData = data.map((item) => ({
    period: formatPeriodLabel(item.period),
    expected_inflow: item.expected_inflow,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Expected Cash Inflow</CardTitle>
        <CardDescription>{CASHFLOW_DISCLAIMER}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="period" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number) => formatINR(value)}
                contentStyle={{
                  backgroundColor: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                }}
              />
              <Bar dataKey="expected_inflow" fill="hsl(var(--chart-2))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
