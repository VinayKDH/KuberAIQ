"use client";

import { formatINR } from "@/lib/format";

interface OverdueInvoiceRow {
  invoice_number?: string | null;
  customer_name?: string;
  amount_due?: number;
  days_overdue?: number;
}

interface AssistantDataCardProps {
  intent: string;
  data: Record<string, unknown>;
}

export function AssistantDataCard({ intent, data }: AssistantDataCardProps) {
  if (
    (intent === "list_overdue" || intent === "list_unpaid") &&
    Array.isArray(data.invoices)
  ) {
    const invoices = data.invoices as OverdueInvoiceRow[];
    if (invoices.length === 0) return null;
    return (
      <div className="mt-2 overflow-hidden rounded-md border bg-background text-xs">
        <table className="w-full">
          <thead className="bg-muted/50 text-left">
            <tr>
              <th className="px-2 py-1">Invoice</th>
              <th className="px-2 py-1">Customer</th>
              <th className="px-2 py-1 text-right">Due</th>
            </tr>
          </thead>
          <tbody>
            {invoices.slice(0, 5).map((row, index) => (
              <tr key={`${row.invoice_number}-${index}`} className="border-t">
                <td className="px-2 py-1">{row.invoice_number ?? "—"}</td>
                <td className="px-2 py-1">{row.customer_name ?? "—"}</td>
                <td className="px-2 py-1 text-right">
                  {formatINR(row.amount_due ?? 0)} · {row.days_overdue ?? 0}d
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (intent === "find_customer" && Array.isArray(data.customers)) {
    const customers = data.customers as { name?: string; phone?: string }[];
    if (customers.length === 0) return null;
    return (
      <div className="mt-2 overflow-hidden rounded-md border bg-background text-xs">
        <ul className="divide-y">
          {customers.slice(0, 5).map((row, index) => (
            <li key={`${row.name}-${index}`} className="px-2 py-1.5">
              <span className="font-medium">{row.name ?? "—"}</span>
              {row.phone ? <span className="text-muted-foreground"> · {row.phone}</span> : null}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  if (intent === "get_dashboard") {
    return (
      <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
        <div className="rounded-md border bg-background p-2">
          <p className="text-muted-foreground">Revenue</p>
          <p className="font-medium">{formatINR(Number(data.revenue ?? 0))}</p>
        </div>
        <div className="rounded-md border bg-background p-2">
          <p className="text-muted-foreground">Pending</p>
          <p className="font-medium">{formatINR(Number(data.pending ?? 0))}</p>
        </div>
        <div className="rounded-md border bg-background p-2">
          <p className="text-muted-foreground">Overdue</p>
          <p className="font-medium">{formatINR(Number(data.overdue ?? 0))}</p>
        </div>
      </div>
    );
  }

  return null;
}
