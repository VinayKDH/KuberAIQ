"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CASHFLOW_FORECAST_DISCLAIMER } from "@/lib/constants";
import type { CashflowForecastDay } from "@/features/dashboard/types";
import { formatINR } from "@/lib/format";

interface CashflowForecastChartProps {
  data: CashflowForecastDay[];
}

export function CashflowForecastChart({ data }: CashflowForecastChartProps) {
  const chartData = data.map((item) => ({
    label: item.date.slice(5),
    cumulative_balance: item.cumulative_balance,
    expected_inflow: item.expected_inflow,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>30-day cashflow forecast</CardTitle>
        <CardDescription>{CASHFLOW_FORECAST_DISCLAIMER}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  formatINR(value),
                  name === "cumulative_balance" ? "Cumulative receivables" : "Due on date",
                ]}
                contentStyle={{
                  backgroundColor: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                }}
              />
              <Line
                type="monotone"
                dataKey="cumulative_balance"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
