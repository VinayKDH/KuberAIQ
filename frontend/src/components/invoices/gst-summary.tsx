"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Invoice } from "@/features/invoices/types";
import { formatINR } from "@/lib/format";

interface GstSummaryProps {
  invoice: Pick<
    Invoice,
    | "taxable_amount"
    | "cgst_amount"
    | "sgst_amount"
    | "igst_amount"
    | "total_tax"
    | "round_off"
    | "grand_total"
    | "amount_paid"
    | "amount_due"
  >;
}

export function GstSummary({ invoice }: GstSummaryProps) {
  const rows = [
    { label: "Taxable amount", value: invoice.taxable_amount },
    { label: "CGST", value: invoice.cgst_amount },
    { label: "SGST", value: invoice.sgst_amount },
    { label: "IGST", value: invoice.igst_amount },
    { label: "Total tax", value: invoice.total_tax },
    { label: "Round off", value: invoice.round_off },
    { label: "Grand total", value: invoice.grand_total, bold: true },
  ];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">GST summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {rows.map((row) => (
          <div key={row.label} className="flex justify-between gap-4">
            <span className="text-muted-foreground">{row.label}</span>
            <span className={row.bold ? "font-semibold" : ""}>
              {formatINR(row.value ?? 0)}
            </span>
          </div>
        ))}
        {invoice.amount_paid !== undefined && (
          <>
            <div className="flex justify-between gap-4 border-t pt-2">
              <span className="text-muted-foreground">Amount paid</span>
              <span>{formatINR(invoice.amount_paid ?? 0)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Amount due</span>
              <span className="font-semibold text-destructive">
                {formatINR(invoice.amount_due ?? 0)}
              </span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
